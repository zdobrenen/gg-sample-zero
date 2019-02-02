
resource "aws_rds_cluster" "datalake_cluster" {
    cluster_identifier      = "datalake-cluster"
    engine                  = "aurora-postgresql"
    availability_zones      = ["us-west-2a", "us-west-2b", "us-west-2c"]
    database_name           = "${var.database_name}"
    master_username         = "${var.master_username}"
    master_password         = "${var.master_password}"
    skip_final_snapshot     = "true"
}


resource "aws_rds_cluster_instance" "datalake_cluster" {
    count               = 1
    identifier          = "datalake-cluster-${count.index}"
    cluster_identifier  = "${aws_rds_cluster.datalake_cluster.id}"
    engine              = "aurora-postgresql"
    instance_class      = "db.r4.large"
    publicly_accessible = "true"
}


resource "aws_ssm_parameter" "datalake_hostname" {
    name        = "iotDatalakeHostname"
    description = "Datalake Hostname Parameter"
    type        = "String"
    value       = "${aws_rds_cluster.datalake_cluster.endpoint}"
}


resource "aws_ssm_parameter" "datalake_database" {
    name        = "iotDatalakeDatabase"
    description = "Datalake Database Parameter"
    type        = "String"
    value       = "${var.database_name}"
}


resource "aws_ssm_parameter" "datalake_username" {
    name        = "iotDatalakeUsername"
    description = "Datalake Username Parameter"
    type        = "SecureString"
    value       = "${var.master_username}"
}


resource "aws_ssm_parameter" "datalake_password" {
    name        = "iotDatalakePassword"
    description = "Datalake Password Parameter"
    type        = "SecureString"
    value       = "${var.master_password}"
}
