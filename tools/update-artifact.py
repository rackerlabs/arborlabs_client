# Copyright 2014 - Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


'''
##########################
Run this script on one of solum-api nodes
##########################
'''

import sqlalchemy as sa
from sqlalchemy.sql import text
import subprocess
import yaml


USER = 'root'
PASSWORD = 'solum'
HOST = '127.0.0.1'
DB = 'solum'
BACKUP_FILE = '/tmp/arbor-db.sql'

DB_CONN = 'mysql://{user}:{password}@{host}/{db}?charset=utf8'
BACKUP_CMD = 'mysqldump --host={host} --user={user} --password={password} --databases {db}'


# Borrowed from solum.common.yamlutils
if hasattr(yaml, 'CSafeLoader'):
    yaml_loader = yaml.CSafeLoader
else:
    yaml_loader = yaml.SafeLoader

if hasattr(yaml, 'CSafeDumper'):
    yaml_dumper = yaml.CSafeDumper
else:
    yaml_dumper = yaml.SafeDumper


def backup_db():
    cmd = BACKUP_CMD.format(host=HOST, user=USER, password=PASSWORD, db=DB)

    print '=====Dumping solum db into %s' % BACKUP_FILE

    with open(BACKUP_FILE, 'w') as bf:
        runbk = subprocess.Popen(cmd.split(), stdout=bf)
        returncode = runbk.wait()

    if returncode != 0:
        print 'mysqldump failed, exit.'
        exit(1)

def update_db():
    records = []
    engine = sa.create_engine(DB_CONN.format(user=USER, password=PASSWORD, host=HOST, db=DB))

    print '=====Reading solum db...'
    results = engine.execute('select id, raw_content from plan')
    for row in results:
        rc = yaml.load(row['raw_content'], yaml_loader)
        for arti in rc['artifacts']:
            if arti['artifact_type'] == 'heroku':
                arti['artifact_type'] = 'chef'
        new_rc = yaml.dump(rc, Dumper=yaml_dumper)
        records.append((new_rc, row['id']))

    print '=====Updating solum db...'
    sql_cmd = 'update plan set raw_content = :content where id = :plan_id'
    with engine.begin() as handle:
        for rec in records:
            handle.execute(text(sql_cmd), content=rec[0], plan_id=rec[1])
    print '=====All done.'


if __name__ == '__main__':
    backup_db()
    update_db()
