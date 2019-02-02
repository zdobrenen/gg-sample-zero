from __future__ import print_function

import boto3
import base64
import json
import re

from dateutil.parser import parse


print('Loading function')


batch = boto3.client('batch')


DB_ACTION = 'INSERT'
DB_OWNER  = 'telemetrydb'
DB_TABLE  = 'devices'


def dump_telemetry(telemetry):

    lookup_ref = [
        'current_active',
        'current_inactive',
        'total_active',
        'total_inactive',
        'running',
        'time'
    ]
    return ','.join([str(telemetry.get(elem, 'null'))
        if not elem == 'time' else parse(telemetry.get(elem)).strftime("%Y-%m-%d %H:%M:%S")
        for elem in lookup_ref])


def function_handler(event, context):

    output = []
    for record in event['records']:

        payload = base64.b64decode(record['data'])
        payload = json.loads(payload)

        output_data = ''
        for device, telemetry in payload.iteritems():
            for row in telemetry:

                output_data += '{},{}\n'.format(device, dump_telemetry(row))

        output_record = {
            "recordId": record['recordId'],
            "result": "Ok",
            "data": base64.b64encode(output_data)
        }

        output.append(output_record)

    return {"records": output}
