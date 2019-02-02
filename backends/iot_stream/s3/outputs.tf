
output "s3_stream_bucket" {
    value = {
        id  = "${aws_s3_bucket.stream_bucket.id}"
        arn = "${aws_s3_bucket.stream_bucket.arn}"
        bucket_domain_name = "${aws_s3_bucket.stream_bucket.bucket_domain_name}"
    }
}
