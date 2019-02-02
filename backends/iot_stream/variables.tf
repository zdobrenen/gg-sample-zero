variable "aws_access_key" {
	description = "AWS provider access key"
}


variable "aws_secret_key" {
	description = "AWS provider secret key"
}


variable "aws_region" {
	description = "AWS provider region"
}


variable "environment" {
    default = "prod"
}


variable "firehose_stream_name" {
	description = "AWS IoT Delivery Stream"
    default     = "iot_delivery_stream"
}


variable "iot_device_topics" {
	description = ""
	default = [
		"postal/telemetry/stream/forward"
	]
}


variable "rds_database_name" {
    default = "telemetrydb"
}


variable "rds_master_username" {
    default = "tmp_username"
}


variable "rds_master_password" {
    default = "tmp_password"
}
