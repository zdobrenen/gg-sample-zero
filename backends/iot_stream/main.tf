provider "aws" {
  access_key = "${var.aws_access_key}"
  secret_key = "${var.aws_secret_key}"
  region     = "${var.aws_region}"
}


module "iot" {
	source               = "./iot"
	iot_device_topics    = "${var.iot_device_topics}"
    firehose_stream_name = "${var.firehose_stream_name}"
}


module "kdf" {
    source                  = "./kdf"
    firehose_stream_name    = "${var.firehose_stream_name}"
    lambda_stream_processor = "${module.lbd.lambda_stream_processor}"
    s3_stream_bucket        = "${module.s3.s3_stream_bucket}"
}


module "lbd" {
    source = "./lbd"
    aurora_datalake_cluster = "${module.rds.aurora_datalake_cluster}"
}


module "rds" {
    source = "./rds"
    environment = "${var.environment}"
    database_name = "${var.rds_database_name}"
    master_username = "${var.rds_master_username}"
    master_password = "${var.rds_master_password}"
}


module "s3" {
    source = "./s3"
    lambda_migration_processor = "${module.lbd.lambda_migration_processor}"
}
