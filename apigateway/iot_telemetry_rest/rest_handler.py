import json

from functools import wraps

from rest_models import IoTTelemetryModel


def handle_api_error(func):
    """
        This define a decorator to format the HTTP response of the lambda:
        - a status code
        - the body of the response as a string
    """

    @wraps(func)
    def wrapped_func(*args, **kwargs):
        try:
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': json.dumps(func(*args, **kwargs)),
            }
        except Exception as e:
            return {
                'statusCode': 500,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Credentials': True,
                },
                'body': str(e),
            }
    return wrapped_func


class IoTTelemetryAPI(object):

    model_cls = IoTTelemetryModel()

    def __init__(self):
        super(IoTTelemetryAPI, self).__init__()


    @handle_api_error
    def get(self, event, context):
        obj_id = event['pathParameters']['id']

        return self.model_cls.pull(obj_id)


    def get_api_methods(self):
        return self.get
