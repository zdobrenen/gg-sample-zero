# AWS GreenGreen Custom SDK


A starter project to bring up (and clean-up!) AWS Greengrass with infrastructure as code.
If you followed the GreenGrass [Getting Started Guide](https://docs.aws.amazon.com/greengrass/latest/developerguide/gg-gs.html), here you find automation and project structure for orchestrating fleets of Greengrass
Groups, Devices and Lambdas.


Greengrass Custom SDK allows for automated generation of command-line interfaces for working
with Groups and Devices, preserving Greengrass resource state locally and (optional) remotely in
AWS S3.


## Prerequisites

Install sshpass

Linux

```bash
sudo apt-get install sshpass
```

OS X

```bash
brew install https://raw.githubusercontent.com/kadwanev/bigboybrew/master/Library/Formula/sshpass.rb
```

## Installation

```bash
git clone git@github.com:zdobrenen/gg-sample-zero.git
```

```bash
cd gg-sample-zero/greengrass
```

```bash
make install
```

## Group Commands

1.) Create GreenGrass Group

```bash
make create-group GROUP=<GROUP_NAME>
```

2.) Config GreenGrass Group

```bash
make config-group GROUP=<GROUP_NAME> pi_host=<pi-ip-address> pi_user=<pi-username> pi_pass=<pi-password>
```

3.) Deploy GreenGrass Group

```bash
make deploy-group GROUP=<GROUP_NAME>
```

4.) Update GreenGrass Group (TODO)

```bash
make update-group GROUP=<GROUP_NAME>
```

5.) Delete GreenGrass Group

```bash
make delete-group GROUP=<GROUP_NAME>
```

## Device Commands

1.) Deploy Greengrass Device

```bash
make deploy-device GROUP=<GROUP_NAME> DEVICE=<DEVICE_NAME> pi_host=<pi-ip-address> pi_user=<pi-username> pi_pass=<pi-password>
```


## Project Structure

```bash
.
|
|-- Makefile
|-- README.md
|-- requirements.txt
|-- ggc_custom_sdk/
|-- ggc_groups_ste/
    |-- device/
    |   |-- <GROUP_NAME>/
    |       |-- <DEVICE_NAME>/
    |           |-- config.json
    |           |-- discovery.py
    |           |-- <DEVICE_NAME>.py
    |           |-- playbook.yml
    |           |-- requirements.txt
    |           |-- systemd.service.j2
    |-- groups/
    |   |-- <GROUP_NAME>/
    |       |-- commands.py
    |       |-- config.json
    |       |-- playbook.yml
    |       |-- .gg/
    |           |-- state.json
    |           |-- archives/
    |           |-- certs/
    |           |-- config/
    |-- lambda/
        |-- <GROUP_NAME>/
            |-- <LAMBDA_NAME>/
                |-- greengrass_common/
                |-- greengrass_ipc_python_sdk/
                |-- greengrasssdk/
                |-- <LAMBDA_NAME>.py
```

---

## Exploring Sample Zero

Sample Zero is intended to demonstrate how to structure a Greengrass application suite using the Custom SDK.
While also showcasing advanced features of Greengrass for acting on device events and collecting/ processing
device telemetry.

NOTE: This example application leverages [InfluxDB](https://www.influxdata.com/) for persisting device telemetry locally
on the Greengrass Core device. Please, refer to [pi-image-gen](https://bitbucket.org/petrichorai-budwatch/pi-image-gen/src/grassbian/)
for building a custom raspbian image with pre-requisites already installed and configured. Or, if you have
successfully followed the Greengrass Getting Started guide and have an operational Greengrass Core, refer
to [InfluxDB Installation](https://docs.influxdata.com/influxdb/v1.7/introduction/installation/).

### Materials:

    1.) One or more Raspberry Pi(s) Wifi enabled
    2.) Two LEDs (preferrably blue and yellow)
    3.) Two Buttons
    4.) breadboard
    5.) jumper wires
    6.) raspberry pi wedge breakout board (optional)


### Wiring Guide:
![Simple Zero Wiring](https://bitbucket.org/petrichorai-budwatch/aws-budwatch/raw/32c29b2ada2179add4802b94297bfe549637d9ae/greengrass/simple_zero_wiring.jpg)


### Setup:

#### Deploy Greengrass Group Resources and Configure Core Device

```bash
make create-group GROUP=sample_zero
```

After the group is created, in the AWS IoT console, choose Greengrass, then Groups and finally sample_zero.
In the Greengrass group console, choose Settings. Under Local Connection Detection, select 
Automatically detect and override connection information.

```bash
make config-group GROUP=sample_zero pi_host=<pi-ip-address> pi_user=pi pi_pass=raspberry
```

```bash
make deploy-group GROUP=sample_zero
```


#### Deploy Greengrass Device Clients

```bash
make deploy-device GROUP=sample_zero DEVICE=ggdBTNPressBlue pi_host=<pi-ip-address> pi_user=pi pi_pass=raspberry
```

```bash
make deploy-device GROUP=sample_zero DEVICE=ggdLEDLightBlue pi_host=<pi-ip-address> pi_user=pi pi_pass=raspberry
```

```bash
make deploy-device GROUP=sample_zero DEVICE=ggdBTNPressYellow pi_host=<pi-ip-address> pi_user=pi pi_pass=raspberry
```

```bash
make deploy-device GROUP=sample_zero DEVICE=ggdLEDLightYellow pi_host=<pi-ip-address> pi_user=pi pi_pass=raspberry
```

### Testing:

After your deployment is complete, in the AWS IoT console, choose Test. In Subscription topic, type 
postal/telemetry/stream/forward. For Quality of Service, select 0. For MQTT payload display, select
Display payloads as strings, and then choose Subscribe to topic.

You should begin to receive message payloads that look similar the below example,

```json
{
    "GG_LED_BLUE": [
      {
        "current_inactive": 0,
        "current_active": 157,
        "total_active": 4107,
        "total_inactive": 56020,
        "running": true,
        "time": "2018-11-16T21:33:11.742875136Z"
      },
      {
        "current_inactive": 0,
        "current_active": 162,
        "total_active": 4112,
        "total_inactive": 56020,
        "running": true,
        "time": "2018-11-16T21:33:16.751570944Z"
      },
      {
        "current_inactive": 0,
        "current_active": 167,
        "total_active": 4117,
        "total_inactive": 56020,
        "running": true,
        "time": "2018-11-16T21:33:21.760572928Z"
      }
    ],
    "GG_BTN_BLUE": [
      {
        "current_inactive": 0,
        "current_active": 160,
        "total_active": 4110,
        "total_inactive": 56272,
        "running": true,
        "time": "2018-11-16T21:33:13.62720384Z"
      },
      {
        "current_inactive": 0,
        "current_active": 165,
        "total_active": 4115,
        "total_inactive": 56272,
        "running": true,
        "time": "2018-11-16T21:33:18.63602304Z"
      },
      {
        "current_inactive": 0,
        "current_active": 170,
        "total_active": 4120,
        "total_inactive": 56272,
        "running": true,
        "time": "2018-11-16T21:33:23.64492288Z"
      }
    ],
    "GG_LED_YELLOW": [
      {
        "current_inactive": 55978,
        "current_active": 0,
        "total_active": 2428,
        "total_inactive": 57379,
        "running": false,
        "time": "2018-11-16T21:33:10.809793024Z"
      },
      {
        "current_inactive": 55983,
        "current_active": 0,
        "total_active": 2428,
        "total_inactive": 57384,
        "running": false,
        "time": "2018-11-16T21:33:15.817725952Z"
      },
      {
        "current_inactive": 55988,
        "current_active": 0,
        "total_active": 2428,
        "total_inactive": 57389,
        "running": false,
        "time": "2018-11-16T21:33:20.827266048Z"
      }
    ],
    "GG_BTN_YELLOW": [
      {
        "current_inactive": 55977,
        "current_active": 0,
        "total_active": 2427,
        "total_inactive": 57185,
        "running": false,
        "time": "2018-11-16T21:33:12.718610176Z"
      },
      {
        "current_inactive": 55982,
        "current_active": 0,
        "total_active": 2427,
        "total_inactive": 57190,
        "running": false,
        "time": "2018-11-16T21:33:17.728486144Z"
      },
      {
        "current_inactive": 55987,
        "current_active": 0,
        "total_active": 2427,
        "total_inactive": 57195,
        "running": false,
        "time": "2018-11-16T21:33:22.736103168Z"
      }
    ]
}
```

### Cleanup:

#### Delete Greengrass Group Resources and Reset Core Device

```bash
make delete-group GROUP=sample_zero
```


---

## Deep Dive


[commands.py](https://bitbucket.org/petrichorai-budwatch/aws-budwatch/src/develop/greengrass/ggc_groups_ste/groups/sample_zero/commands.py)
```python
import fire

from ggc_custom_sdk.groups import GroupCommands
from ggc_custom_sdk.utils import gen_group_path


class SampleZeroGroupCommands(GroupCommands):

    GROUP_PATH = gen_group_path(__file__)


    def __init__(self):
        super(SampleZeroGroupCommands, self).__init__()



def main():
    fire.Fire(SampleZeroGroupCommands())


if __name__ == '__main__':
    main()

```
