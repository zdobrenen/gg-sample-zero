from setuptools import setup
from os import path


setup(
    name='ggc_custom_sdk',
    version='1.0.0',
    description='AWS Greengrass file-based setup tool',
    packages=['ggc_custom_sdk'],
    install_requires=[
        'fire',
        'boto3',
        'botocore',
        'pyyaml',
        'requests'
    ],
    zip_safe=False
)
