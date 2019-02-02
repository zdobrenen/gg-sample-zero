import boto3
import json
import os

from schema import Schema


iot_client = boto3.client('iot-data')



class IoTShadowModel(object):

    SCHEMA = Schema(dict)


    @classmethod
    def validate(cls, obj_payload):
        assert cls.SCHEMA._schema == dict or type(cls.SCHEMA._schema) == dict
        return cls.SCHEMA.validate(obj_payload)


    @classmethod
    def pull(cls, obj_id):

        resp = iot_client.get_thing_shadow(
            thingName=obj_id
        )
        return resp['payload'].read()


    @classmethod
    def push(cls, obj_id, obj_payload):

        payload = cls.validate(obj_payload)
        payload = {
            'state': {
                'desired': payload
            }
        }

        resp = iot_client.update_thing_shadow(
            thingName=obj_id,
            payload=json.dumps(payload)
        )
        return resp['payload'].read()

