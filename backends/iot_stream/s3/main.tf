resource "aws_s3_bucket" "stream_bucket" {
  bucket = "petrichorai-iot-stream-bucket"
  acl    = "private"
}


resource "aws_lambda_permission" "stream_bucket" {
    statement_id  = "AllowExecutionFromStreamBucket"
    action        = "lambda:InvokeFunction"
    function_name = "${var.lambda_migration_processor["arn"]}"
    principal     = "s3.amazonaws.com"
    source_arn    = "${aws_s3_bucket.stream_bucket.arn}"
}


resource "aws_s3_bucket_notification" "stream_bucket" {
    bucket = "${aws_s3_bucket.stream_bucket.id}"

    lambda_function {
        id                  = "iotdata-upload-event"
        lambda_function_arn = "${var.lambda_migration_processor["arn"]}"
        events              = ["s3:ObjectCreated:*"]
        filter_prefix       = "IoTData/"
    }
}
