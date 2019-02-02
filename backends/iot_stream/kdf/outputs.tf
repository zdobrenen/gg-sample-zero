
output "firehose_stream_delivery" {
    value = {
        arn = "${aws_kinesis_firehose_delivery_stream.stream_delivery.arn}"
    }
}
