# Copyright 2013 - Noorul Islam K M
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import re
import sys

import fixtures
import mock
import six
from stevedore import extension
from testtools import matchers

from solumclient.openstack.common.apiclient import auth
from solumclient import solum
from solumclient.tests import base
from solumclient.v1 import assembly

FAKE_ENV = {'OS_USERNAME': 'username',
            'OS_PASSWORD': 'password',
            'OS_TENANT_NAME': 'tenant_name',
            'OS_AUTH_URL': 'http://no.where'}


class MockEntrypoint(object):
    def __init__(self, name, plugin):
        self.name = name
        self.plugin = plugin


class BaseFakePlugin(auth.BaseAuthPlugin):
    def _do_authenticate(self, http_client):
        pass

    def token_and_endpoint(self, endpoint_type, service_type):
        pass


class TestSolum(base.TestCase):
    """Test the Solum CLI."""

    re_options = re.DOTALL | re.MULTILINE

    # Patch os.environ to avoid required auth info.
    def make_env(self, exclude=None):
        env = dict((k, v) for k, v in FAKE_ENV.items() if k != exclude)
        self.useFixture(fixtures.MonkeyPatch('os.environ', env))

    @mock.patch.object(extension.ExtensionManager, "map")
    def shell(self, argstr, mock_mgr_map):
        class FakePlugin(BaseFakePlugin):
            def authenticate(self, cls):
                cls.request(
                    "POST", "http://auth/tokens",
                    json={"fake": "me"}, allow_redirects=True)

        mock_mgr_map.side_effect = (
            lambda func: func(MockEntrypoint("fake", FakePlugin)))

        orig = sys.stdout
        try:
            sys.stdout = six.StringIO()
            argv = [__file__, ]
            argv.extend(argstr.split())
            self.useFixture(
                fixtures.MonkeyPatch('sys.argv', argv))
            solum.main()
        except SystemExit:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            self.assertEqual(exc_value.code, 0)
        finally:
            out = sys.stdout.getvalue()
            sys.stdout.close()
            sys.stdout = orig

        return out

    def test_help(self):
        required = [
            '.*?^Solum Python Command Line Client',
            '.*?^usage:'
            '.*?^positional arguments'
            '.*?^optional arguments'

        ]
        for argstr in ['--help', 'help']:
            help_text = self.shell(argstr)
            for r in required:
                self.assertThat(help_text,
                                matchers.MatchesRegex(r,
                                                      self.re_options))

    @mock.patch.object(assembly.AssemblyManager, "list")
    def test_assembly_list(self, mock_assembly_list):
        self.make_env()
        required = [
            '.*?^Solum Python Command Line Client',
            '.*?\[\]'
        ]

        mock_assembly_list.side_effect = (
            lambda: []
        )

        out = self.shell("assembly list")
        for r in required:
            self.assertThat(out,
                            matchers.MatchesRegex(r,
                                                  self.re_options))