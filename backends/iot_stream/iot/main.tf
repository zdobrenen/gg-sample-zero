resource "aws_iot_topic_rule" "iot_stream" {
	count = "${length(var.iot_device_topics)}"

  	name        = "iot_stream"
  	description = "IoT Device data stream"
  	enabled     = "true"
  	sql         = "SELECT * FROM '${var.iot_device_topics[count.index]}'"
  	sql_version = "2015-10-08"

	firehose {
		delivery_stream_name = "${var.firehose_stream_name}"
		role_arn  = "${aws_iam_role.iot_stream_role.arn}"
	}
}


resource "aws_iam_role" "iot_stream_role" {
	name = "iot-stream-role"
	assume_role_policy = <<EOF
{
	"Version": "2012-10-17",
	"Statement": [{
		"Effect": "Allow",
		"Principal": {
			"Service": "iot.amazonaws.com"
		},
		"Action": "sts:AssumeRole"
	}]
}
EOF
}


resource "aws_iam_role_policy" "iot_stream_policy" {
	name = "iot-stream-role-policy"
	role = "${aws_iam_role.iot_stream_role.id}"
	policy = <<EOF
{
	"Version": "2012-10-17",
	"Statement": [{
		"Effect": "Allow",
		"Action": [
			"firehose:*"
		],
		"Resource": "*"
	}]
}
EOF
}
