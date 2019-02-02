import json

def gen_group_role_doc():
    role_doc = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "greengrass.amazonaws.com"
                ]
            },
            "Action": "sts:AssumeRole"
        }]
    }
    return json.dumps(role_doc)


def gen_group_policy_doc(region):

    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "greengrass:*"
                ],
                "Resource": [
                    "*"
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:*"
                ],
                "Resource": [
                    "*"
                ]
            }
        ]
    }
    return json.dumps(policy_doc)


def gen_core_policy_doc(region):
	policy_doc = {
		"Version": "2012-10-17",
		"Statement": [
			{
				"Effect": "Allow",
				"Action": [
					"iot:*"
				],
				"Resource": ["arn:aws:iot:{}:*:*".format(region)]
			},
			{
				"Effect": "Allow",
				"Action": [
					"greengrass:*",
				],
				"Resource": ["*"]
			}
		]
	}
	return json.dumps(policy_doc)


def gen_device_policy_doc(region):
	policy_doc = {
		"Version": "2012-10-17",
		"Statement": [
			{
				"Effect": "Allow",
				"Action": [
					"iot:*",
				],
				"Resource": ["arn:aws:iot:{}:*:*".format(region)]
			},
			{
				"Effect": "Allow",
				"Action": [
					"greengrass:*",
				],
				"Resource": ["*"]
			}
		]
	}
	return json.dumps(policy_doc)


def gen_lambda_role_doc():
    role_doc = {
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "lambda.amazonaws.com"
                ]
            },
            "Action": "sts:AssumeRole"
        }]
    }
    return json.dumps(role_doc)


def gen_lambda_policy_doc(region):

    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogGroup"
                ],
                "Resource": [
                    "arn:aws:logs:{}:*:*".format(region)
                ]
            },
            {
                "Effect": "Allow",
                "Action": [
                    "logs:CreateLogStream",
                    "logs:PutLogEvents"
                ],
                "Resource": [
                    "arn:aws:logs:{}:*:*:/aws/lambda/*:*".format(region)
                ]
            }
        ]
    }
    return json.dumps(policy_doc)
