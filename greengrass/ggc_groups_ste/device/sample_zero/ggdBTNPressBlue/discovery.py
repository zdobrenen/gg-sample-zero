# /*
# * Copyright 2010-2017 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# *
# * Licensed under the Apache License, Version 2.0 (the "License").
# * You may not use this file except in compliance with the License.
# * A copy of the License is located at
# *
# *  http://aws.amazon.com/apache2.0
# *
# * or in the "license" file accompanying this file. This file is distributed
# * on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# * express or implied. See the License for the specific language governing
# * permissions and limitations under the License.
# */


import os
import sys
import re
import time
import uuid
import json
import logging
import argparse
from AWSIoTPythonSDK.core.greengrass.discovery.providers import DiscoveryInfoProvider
from AWSIoTPythonSDK.core.protocol.connection.cores import ProgressiveBackOffCore
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from AWSIoTPythonSDK.exception.AWSIoTExceptions import DiscoveryInvalidRequestException, DiscoveryFailure


MAX_DISCOVERY_RETRIES = 10
GROUP_CA_PATH = "groupCA/"
CA_NAME = "root-ca.crt"       # stores GGC CA cert
GGC_ADDR_NAME = "ggc-host"    # stores GGC host address



# function does basic regex check to see if value might be an ip address
def isIpAddress(value):
    match = re.match(r'^\d{1,3}\.\d{1,3}\.\d{1,3}', value)
    if match:
        return True
    return False


# function reads host GGC ip address from filePath
def getGGCAddr(filePath):
    f = open(filePath, "r")
    return f.readline()


def discover(host, rootCAPath, certificatePath, privateKeyPath, thingName, devicePath):
    # Progressive back off core
    backOffCore = ProgressiveBackOffCore()

    # Discover GGCs
    discoveryInfoProvider = DiscoveryInfoProvider()
    discoveryInfoProvider.configureEndpoint(host)
    discoveryInfoProvider.configureCredentials(rootCAPath, certificatePath, privateKeyPath)
    discoveryInfoProvider.configureTimeout(10)  # 10 sec

    print("Iot end point: {}".format(host))
    print("Iot CA Path: {}".format(rootCAPath))
    print("GGAD cert path: {}".format(certificatePath))
    print("GGAD private key path: {}".format(privateKeyPath))
    print("GGAD thing name : {}".format(thingName))

    retryCount = MAX_DISCOVERY_RETRIES
    discovered = False
    groupCA = None
    coreInfo = None
    while retryCount != 0:
        try:
            discoveryInfo = discoveryInfoProvider.discover(thingName)
            groupList = discoveryInfo.getAllGroups()

            if len(groupList) > 1:
                raise DiscoveryFailure("Discovered more groups than expected")

            caList   = discoveryInfo.getAllCas()
            coreList = discoveryInfo.getAllCores()

            # We only pick the first ca and core info
            groupId, ca = caList[0]
            coreInfo    = coreList[0]
            print("Discovered GGC: %s from Group: %s" % (coreInfo.coreThingArn, groupId))

            hostAddr = ""

            # In this example Ip detector lambda is turned on which reports
            # the GGC hostAddr to the CIS (Connectivity Information Service) that stores the
            # connectivity information for the AWS Greengrass core associated with your group.
            # This is the information used by discovery and the list of host addresses
            # could be outdated or wrong and you would normally want to
            # validate it in a better way.
            # For simplicity, we will assume the first host address that looks like an ip
            # is the right one to connect to GGC.
            # Note: this can also be set manually via the update-connectivity-info CLI
            connList = coreInfo.connectivityInfoList
            print connList

            for addr in connList:
                hostAddr = addr.host

                if isIpAddress(hostAddr):
                    print('Check: {}'.format(hostAddr))

            print("Discovered GGC Host Address: " + hostAddr)
            print("Now we persist the connectivity/identity information...")
            groupCA = '{}/{}'.format(devicePath, GROUP_CA_PATH + CA_NAME)
            ggcHostPath = '{}/{}'.format(devicePath, GROUP_CA_PATH + GGC_ADDR_NAME)
            if not os.path.exists('{}/{}'.format(devicePath, GROUP_CA_PATH)):
                os.makedirs('{}/{}'.format(devicePath, GROUP_CA_PATH))
            groupCAFile = open(groupCA, "w")
            groupCAFile.write(ca)
            groupCAFile.close()
            groupHostFile = open(ggcHostPath, "w")
            groupHostFile.write(hostAddr)
            groupHostFile.close()

            discovered = True
            print("Now proceed to the connecting flow...")
            break
        except DiscoveryInvalidRequestException as e:
            print("Invalid discovery request detected!")
            print("Type: " + str(type(e)))
            print("Error message: " + e.message)
            print("Stopping...")
            break
        except BaseException as e:
            print("Error in discovery!")
            print("Type: " + str(type(e)))
            print("Error message: " + e.message)
            retryCount -= 1
            print("\n"+str(retryCount) + "/" + str(MAX_DISCOVERY_RETRIES) + " retries left\n")
            print("Backing off...\n")
            backOffCore.backOff()

        else:
            if not discovered:
                print("Discovery failed after %d retries. Exiting...\n" % (MAX_DISCOVERY_RETRIES))
                sys.exit(-1)
