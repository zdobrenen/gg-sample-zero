resource "aws_cloudwatch_log_group" "stream_delivery" {
    name = "${var.firehose_stream_name}"
}


resource "aws_cloudwatch_log_stream" "stream_delivery" {
    name           = "${var.firehose_stream_name}"
    log_group_name = "${aws_cloudwatch_log_group.stream_delivery.name}"
}


resource "aws_kinesis_firehose_delivery_stream" "stream_delivery" {
    name        = "${var.firehose_stream_name}"
    destination = "extended_s3"

    extended_s3_configuration {
        role_arn   = "${aws_iam_role.stream_delivery.arn}"
        bucket_arn = "${var.s3_stream_bucket["arn"]}"
        prefix     = "IoTData/"

        buffer_interval = 60
        buffer_size     = 1

        processing_configuration = [{
            enabled = "true"
            processors = [{
                type = "Lambda"
                parameters = [
                    {
                        parameter_name = "LambdaArn"
                        parameter_value = "${var.lambda_stream_processor["arn"]}:$LATEST"
                    },
                    {
                        parameter_name = "BufferSizeInMBs"
                        parameter_value = "1"
                    },
                    {
                        parameter_name = "BufferIntervalInSeconds"
                        parameter_value = "60"
                    }
                ]
            }]
        }]

        cloudwatch_logging_options {
            enabled         = "true"
            log_group_name  = "${var.firehose_stream_name}"
            log_stream_name = "${var.firehose_stream_name}"
        }
    }
}


resource "aws_iam_role" "stream_delivery" {
  name = "${var.firehose_stream_name}_role"

  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "firehose.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}


resource "aws_iam_role_policy" "stream_delivery" {
	name = "${var.firehose_stream_name}_role-policy"
	role = "${aws_iam_role.stream_delivery.id}"
	policy = <<EOF
{
	"Version": "2012-10-17",
	"Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "lambda:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "s3:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "log:*"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

