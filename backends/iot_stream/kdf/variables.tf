
variable "firehose_stream_name" {
    description = ""
}

variable "lambda_stream_processor" {
    description = ""
    type        = "map"
}


variable "s3_stream_bucket" {
    description = ""
    type        = "map"
}
