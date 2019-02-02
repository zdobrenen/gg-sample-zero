output "aurora_datalake_cluster" {
    value = {
        host = "${aws_rds_cluster.datalake_cluster.endpoint}"
        name = "${var.database_name}"
        username = "${var.master_username}"
        password = "${var.master_password}"
    }
}

