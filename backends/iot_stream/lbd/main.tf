
data "archive_file" "stream_processor" {
    type        = "zip"
    source_dir  = "${path.module}/lambdas/iotStreamProcessor"
    output_path = "${path.module}/lambdas/iotStreamProcessor.zip"
}


resource "aws_lambda_function" "stream_processor" {
    filename = "${path.module}/lambdas/iotStreamProcessor.zip"
    source_code_hash = "${data.archive_file.stream_processor.output_base64sha256}"
    function_name = "iotStreamProcessor"
    role = "${aws_iam_role.stream_processor.arn}"
    handler = "iotStreamProcessor.function_handler"
    runtime = "python2.7"
    timeout = 60
}



resource "aws_iam_role" "stream_processor" {
  name = "iot_stream_processor_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "stream_processor" {
	name = "iot_stream_processor_role-policy"
	role = "${aws_iam_role.stream_processor.id}"
	policy = <<EOF
{
	"Version": "2012-10-17",
	"Statement": [
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


data "archive_file" "migration_processor" {
    type        = "zip"
    source_dir  = "${path.module}/lambdas/rdsMigrationProcessor"
    output_path = "${path.module}/lambdas/rdsMigrationProcessor.zip"
}


resource "aws_lambda_function" "migration_processor" {
    filename = "${path.module}/lambdas/rdsMigrationProcessor.zip"
    source_code_hash = "${data.archive_file.migration_processor.output_base64sha256}"
    function_name = "rdsMigrationProcessor"
    role = "${aws_iam_role.migration_processor.arn}"
    handler = "rdsMigrationProcessor.function_handler"
    runtime = "python2.7"
}



resource "aws_iam_role" "migration_processor" {
  name = "rds_migration_processor_role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow",
      "Sid": ""
    }
  ]
}
EOF
}


resource "aws_iam_role_policy" "migration_processor" {
	name = "iot_migration_processor_role-policy"
	role = "${aws_iam_role.migration_processor.id}"
	policy = <<EOF
{
	"Version": "2012-10-17",
	"Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "log:*"
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
                "ssm:*"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2:CreateNetworkInterface",
                "ec2:DescribeNetworkInterfaces",
                "ec2:DeleteNetworkInterface"
            ],
            "Resource": "*"
        }
    ]
}
EOF
}

