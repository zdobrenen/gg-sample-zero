terraform {
    backend "s3" {
        bucket = "petrichorai-terraform-state"
        key    = "budwatch/iot-stream.tfstate"
        region = "us-west-2"
    }
}

data "terraform_remote_state" "main" {
    backend = "s3"
    config {
        bucket = "petrichorai-terraform-state"
        key    = "budwatch/iot-stream.tfstate"
        region = "us-west-2"
    }
}
