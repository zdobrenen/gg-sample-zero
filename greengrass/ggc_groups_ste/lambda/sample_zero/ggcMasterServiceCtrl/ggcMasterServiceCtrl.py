import greengrasssdk
import time
import json
import boto3
import datetime
import itertools
import threading



# Creating a ggc and influxdb clients
gg_client = greengrasssdk.client('iot-data')


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


def notify_shadow(device_name, payload):

    JSONPayload = json.dumps({
        'state': {
            'desired': payload
        }
    }).encode()

    gg_client.update_thing_shadow(
        thingName=device_name,
        payload=JSONPayload
    )


class ControlThread(threading.Thread):

    def __init__(self, threadID, name):
        threading.Thread.__init__(self)

        self.threadID = threadID
        self.name     = name


    def run(self):

        while True:

            btn_b_shadow = gg_client.get_thing_shadow(
                thingName=GGC_BTN_B_SHADOW_NAME
            )
            btn_b_shadow = json.loads(btn_b_shadow['payload'])
            btn_b_report = btn_b_shadow['state']['reported']


            btn_y_shadow = gg_client.get_thing_shadow(
                thingName=GGC_BTN_Y_SHADOW_NAME
            )
            btn_y_shadow = json.loads(btn_y_shadow['payload'])
            btn_y_report = btn_y_shadow['state']['reported']


            if btn_b_report.get('running', None) != None and btn_b_report['running'] == True:
                notify_shadow(GGC_LED_B_SHADOW_NAME, {'running': True})

            if btn_b_report.get('running', None) != None and btn_b_report['running'] == False:
                notify_shadow(GGC_LED_B_SHADOW_NAME, {'running': False})

            if btn_y_report.get('running', None) != None and btn_y_report['running'] == True:
                notify_shadow(GGC_LED_Y_SHADOW_NAME, {'running': True})

            if btn_y_report.get('running', None) != None and btn_y_report['running'] == False:
                notify_shadow(GGC_LED_Y_SHADOW_NAME, {'running': False})

            time.sleep(1)


control_thread = ControlThread(1, 'Control-Thread')
control_thread.start()


def function_handler(event, context):
    pass
