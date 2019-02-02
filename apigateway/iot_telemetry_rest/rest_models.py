import boto3
import json
import os
import psycopg2
import psycopg2.extras
import datetime

from schema import Schema

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



def serialize_record(record):
    record['time'] = record['time'].strftime("%Y-%m-%d %H:%M:%S")
    return record



class IoTTelemetryModel(object):

    SCHEMA = Schema(dict)


    @classmethod
    def validate(cls, obj_payload):
        assert cls.SCHEMA._schema == dict or type(cls.SCHEMA._schema) == dict
        return cls.SCHEMA.validate(obj_payload)


    @classmethod
    def pull(cls, obj_id):

        curs.execute("""
            SELECT * FROM telemetry
            WHERE device='{}'
            ORDER BY time DESC
            LIMIT 10
            """.format(obj_id))

        return {'records': [serialize_record(record) for record in (curs or [])]}
