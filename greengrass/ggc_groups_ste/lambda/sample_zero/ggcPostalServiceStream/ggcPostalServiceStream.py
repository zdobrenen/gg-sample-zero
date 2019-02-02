import greengrasssdk
import time
import json
import boto3
import datetime
import itertools
import threading

from influxdb import InfluxDBClient


# Creating a ggc and influxdb clients
gg_client = greengrasssdk.client('iot-data')
db_client = InfluxDBClient('localhost', 8086, 'root', 'root', 'postal_service')

try:
    db_client.create_database('postal_service')
    db_client.create_retention_policy('ttl_1h_policy', '1h', 1, default=True)
except Exception as e:
    print(e)


def function_handler(event, context):

    print(event)

    device_name = event.pop('device')
    datetime_ts = event.pop('datetime')

    JSONBody = [{
        'measurement': device_name,
        'time': datetime_ts,
        'fields': event
    }]

    db_client.write_points(JSONBody)
