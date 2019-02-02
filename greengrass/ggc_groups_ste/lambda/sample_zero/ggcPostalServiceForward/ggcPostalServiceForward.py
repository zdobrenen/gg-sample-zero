import greengrasssdk
import time
import json
import boto3
import datetime
import itertools
import threading

from threading import Timer
from influxdb import InfluxDBClient


# Creating a ggc and influxdb clients
gg_client = greengrasssdk.client('iot-data')
db_client = InfluxDBClient('localhost', 8086, 'root', 'root', 'postal_service')


# Define lambda globals
FORWARD_MQ_CHANNEL = 'postal/telemetry/stream/forward'

GGC_BTN_B_SHADOW_NAME = 'GG_BTN_BLUE'
GGC_BTN_Y_SHADOW_NAME = 'GG_BTN_YELLOW'
GGC_LED_Y_SHADOW_NAME = 'GG_LED_YELLOW'
GGC_LED_B_SHADOW_NAME = 'GG_LED_BLUE'

SHADOW_NAMES = [
    GGC_BTN_B_SHADOW_NAME,
    GGC_BTN_Y_SHADOW_NAME,
    GGC_LED_Y_SHADOW_NAME,
    GGC_LED_B_SHADOW_NAME
]


class PostalThread(threading.Thread):

    def __init__(self, threadID, name):
        threading.Thread.__init__(self)

        self.threadID = threadID
        self.name     = name

    def run(self):

        while True:

            telemetry_query = "SELECT * FROM {} WHERE time > now() - 15s;".format(
                ", ".join(SHADOW_NAMES))

            results = db_client.query(telemetry_query)

            payload = {d: list(results.get_points(d)) for d in SHADOW_NAMES}
            JSONPayload = json.dumps(payload).encode()

            gg_client.publish(
                topic=FORWARD_MQ_CHANNEL,
                payload=JSONPayload
            )

            time.sleep(15)


postal_thread = PostalThread(1, 'Postal-Thread')
postal_thread.start()


def function_handler(event, context):
    pass
