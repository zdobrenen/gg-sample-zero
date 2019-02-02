from __future__ import print_function

import json
import urllib
import boto3
import random
import StringIO
import psycopg2


TABLE_NAME = "telemetry"

COLUMN_NAME = [
    ('device', 'text'),
    ('current_active', 'integer'),
    ('current_inactive', 'integer'),
    ('total_active', 'integer'),
    ('total_inactive', 'integer'),
    ('running', 'boolean'),
    ('time', 'timestamp')
]

print('Loading function')


s3_client = boto3.client('s3')
ssm_client = boto3.client('ssm')

rds_config = ssm_client.get_parameters(
    Names=[
        'iotDatalakeHostname',
        'iotDatalakeDatabase',
        'iotDatalakeUsername',
        'iotDatalakePassword'
    ],
    WithDecryption=True
)

rds_config = {param['Name']: param['Value']
    for param in rds_config['Parameters']}

try:
    conn = psycopg2.connect("host='{}' dbname='{}' user='{}' password='{}'".format(
        rds_config['iotDatalakeHostname'],
        rds_config['iotDatalakeDatabase'],
        rds_config['iotDatalakeUsername'],
        rds_config['iotDatalakePassword']
    ))

    curs = conn.cursor(cursor_factory = psycopg2.extras.RealDictCursor)
except Exception as e:
    print('cannot connect to database')
    print(e)


try:
    curs.execute("""
    CREATE TABLE {}({})
    """.format(TABLE_NAME, ', '.join('{} {}'.format(c[0], c[1]) for c in COLUMN_NAME)))
    conn.commit()
except Exception as e:
    print('database table already exists')
    print(e)
    conn.rollback()


def function_handler(event, context):

    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.unquote_plus(event['Records'][0]['s3']['object']['key'].encode('utf8'))

    master_io = StringIO.StringIO()

    s3_client.download_fileobj(Fileobj=master_io, Bucket=bucket, Key=key)
    master_io.seek(0)

    try:
        curs.copy_from(master_io, TABLE_NAME, columns=[c[0] for c in COLUMN_NAME], sep=",")
        conn.commit()
    except Exception as e:
        print('database failed to load bucket: {} key: {}'.format(bucket, key))
        print(e)

    return '{}/{}'.format(bucket, key)
