from rest_handler import IoTShadowAPI
from rest_models import IoTShadowModel

from schema import Schema


class IoTShadow(IoTShadowModel):

    name = 'iot-shadow'

    SCHEMA = Schema({
        'running': bool
    })


class IoTShadowResource(IoTShadowAPI):

    model_cls = IoTShadow

    def __init__(self):
        super(IoTShadowResource, self).__init__()


get, post = IoTShadowResource().get_api_methods()
