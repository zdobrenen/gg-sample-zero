from rest_handler import IoTTelemetryAPI
from rest_models import IoTTelemetryModel

from schema import Schema


class IoTTelemetry(IoTTelemetryModel):

    name = 'iot-telemetry'

    SCHEMA = Schema({
    })


class IoTTelemetryResource(IoTTelemetryAPI):

    model_cls = IoTTelemetry

    def __init__(self):
        super(IoTTelemetryResource, self).__init__()


get = IoTTelemetryResource().get_api_methods()
