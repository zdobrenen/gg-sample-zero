import atexit
import datetime
import logging
import time
import json
import os
import discovery
import threading
import itertools

import RPi.GPIO as GPIO

from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient, AWSIoTMQTTShadowClient



# Globl Variables
DEVICE_PATH = '/gg_devices/GG_BTN_YELLOW'
CONFIG_PATH = '{}/config.json'.format(DEVICE_PATH)



class ShadowTelemetryContainer(threading.Thread):

    def __init__(self, shadow_handler, shadow_mqttcli, device, pin, topic):
        threading.Thread.__init__(self)

        self.shadow_handler = shadow_handler
        self.shadow_mqttcli = shadow_mqttcli

        self.device = device
        self.pin    = pin
        self.topic  = topic

        self.running          = False

        self.current_active   = 0
        self.current_inactive = 0

        self.total_active     = 0
        self.total_inactive   = 0


    def setup(self):

		GPIO.setmode(GPIO.BCM)

		try:
			GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			time.sleep(0.5)
			GPIO.add_event_detect(self.pin, GPIO.FALLING, bouncetime=1)

		except Exception as e:
			self.cleanup()

			GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
			time.sleep(0.5)
			GPIO.remove_event_detect(self.pin)
			time.sleep(0.5)
			GPIO.add_event_detect(self.pin, GPIO.FALLING, bouncetime=1)


    def cleanup(self):
        GPIO.cleanup(self.pin)

        os.system('echo {} > /sys/class/gpio/unexport'.format(self.pin))
        time.sleep(1)


    def run(self):

        cycle_size   = 5
        stream_cycle = itertools.cycle(list(xrange(cycle_size)))
        while True:
            count = stream_cycle.next()

            if GPIO.event_detected(self.pin):
				if self.running:
					self.running = False

					jsonpayload = json.dumps({
						'state': {
							'reported': {
								'running': self.running
							}
						}
					}).encode()
					self.shadow_handler.shadowUpdate(jsonpayload, self.callback_update, 5)

				else:
					self.running = True

					jsonpayload = json.dumps({
						'state': {
							'reported': {
								'running': self.running
							}
						}
					}).encode()
					self.shadow_handler.shadowUpdate(jsonpayload, self.callback_update, 5)


            if self.running == True:

                self.current_inactive = 0

                self.current_active += 1
                self.total_active += 1


            if self.running == False:

                self.current_active = 0

                self.current_inactive += 1
                self.total_inactive += 1


            print("~~~~~~~~~~~~~~~~~~~~~~~")
            print("Telemetry:\n")
            print("DateTime: {}".format(datetime.datetime.utcnow().isoformat()))
            print("Running: {}".format(self.running))
            print("Current Active: {}".format(self.current_active))
            print("Current Inactive: {}".format(self.current_inactive))
            print("Total Active: {}".format(self.total_active))
            print("Total Inactive: {}".format(self.total_inactive))
            print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

            if count > 0 and count % cycle_size - 1 == 0:
                self.publish_state()

            time.sleep(1)


    def publish_state(self):

        JSONPayload = json.dumps({
            'datetime': datetime.datetime.utcnow().isoformat(),
            'device': self.device,
            'running': self.running,
            'current_active': self.current_active,
            'current_inactive': self.current_inactive,
            'total_active': self.total_active,
            'total_inactive': self.total_inactive
        }).encode()

        self.shadow_mqttcli.publish(self.topic, JSONPayload, 0)


    def update_state(self, state):

        if not state.get('running', None) == None and state['running'] == True:
            self.running = True

            jsonpayload = json.dumps({
                'state': {
                    'reported': {
                        'running': self.running
                    }
                }
            }).encode()
            self.shadow_handler.shadowUpdate(jsonpayload, self.callback_update, 5)

        if not state.get('running', None) == None and state['running'] == False:
            self.running = False

            jsonpayload = json.dumps({
                'state': {
                    'reported': {
                        'running': self.running
                    }
                }
            }).encode()
            self.shadow_handler.shadowUpdate(jsonpayload, self.callback_update, 5)


    def callback_update(self, payload, responseStatus, token):

        if responseStatus == "timeout":
            print("Update request " + token + " time out!")

        if responseStatus == "accepted":
            payloadDict = json.loads(payload)

            print("~~~~~~~~~~~~~~~~~~~~~~~")
            for k, v in payloadDict.iteritems():
                print("{} : {}".format(k, v))
            print("~~~~~~~~~~~~~~~~~~~~~~~\n\n")

        if responseStatus == "rejected":
            print("Update request " + token + " rejected!")


    def callback_delta(self, payload, responseStatus, token):

        payloadDict = json.loads(payload)
        state       = payloadDict.get('state', {})

        self.update_state(state)

        JSONPayload = json.dumps({
            'state': {
                'reported': state
            }
        }).encode()
        self.shadow_handler.shadowUpdate(JSONPayload, self.callback_update, 5)



if __name__ == '__main__':

    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)

    # Unpack config file
    endpoint        = config['endpoint']
    iotCAPath       = config['rootCAPath']
    certificatePath = config['certificatePath']
    privateKeyPath  = config['privateKeyPath']
    thingName       = config['thingName']
    clientId        = config['clientId']
    deviceParams    = config['deviceParams']


    # Run Discovery service to check which GGC to connect to, if it hasn't been run already
    # Discovery talks with the IoT cloud to get the GGC CA cert and ip address

    if not os.path.isfile('{}/groupCA/root-ca.crt'.format(DEVICE_PATH)):
        discovery.discover(endpoint, iotCAPath, certificatePath, privateKeyPath, clientId, DEVICE_PATH)
    else:
        print("Greengrass core has already been discovered.")


    ggcAddrPath = '{}/{}'.format(DEVICE_PATH, discovery.GROUP_CA_PATH + discovery.GGC_ADDR_NAME)
    rootCAPath  = '{}/{}'.format(DEVICE_PATH, discovery.GROUP_CA_PATH + discovery.CA_NAME)
    ggcAddr     = discovery.getGGCAddr(ggcAddrPath)

    print("GGC Host Address: {}".format(ggcAddr))
    print("GGC Group CA Path: {}".format(rootCAPath))
    print("Private Key of thing Path: {}".format(privateKeyPath))
    print("Certificate of thing Path: {}".format(certificatePath))
    print("Client ID (thing name): {}".format(clientId))
    print("Target shadow thing ID(thing name): {}".format(thingName))


    # Init AWSIoTMQTTShadowClient
    shadow_client = AWSIoTMQTTShadowClient(clientId)
    shadow_client.configureEndpoint(ggcAddr, 8883)
    shadow_client.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

    # Config AWSIoTMQTTShadowClient
    shadow_client.configureAutoReconnectBackoffTime(1, 32, 20)
    shadow_client.configureConnectDisconnectTimeout(10)  # 10 sec
    shadow_client.configureMQTTOperationTimeout(5)  # 5 sec

    # Connect to AWS IoT
    shadow_client.connect()


    # Create a deviceShadow with persistent subscription
    shadow_handler   = shadow_client.createShadowHandlerWithName(thingName, True)
    shadow_mqttcli   = shadow_client.getMQTTConnection()
    shadow_container = ShadowTelemetryContainer(shadow_handler, shadow_mqttcli, **deviceParams)


    # Create a deviceShadow doc
    JSONPayload = json.dumps({
        'state': {
            'reported': {
                'running': False
            }
        }
    }).encode()
    shadow_container.shadow_handler.shadowUpdate(JSONPayload, shadow_container.callback_update, 5)

    # Listen on deltas
    shadow_container.shadow_handler.shadowRegisterDeltaCallback(shadow_container.callback_delta)

    # Start Shadow Threads
    shadow_container.setup()
    shadow_container.start()


    # Loop forever
    while True:
        time.sleep(1)
