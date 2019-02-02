
output "lambda_stream_processor" {
    value = {
        arn = "${aws_lambda_function.stream_processor.arn}" 
    }
}


output "lambda_migration_processor" {
    value = {
        arn = "${aws_lambda_function.migration_processor.arn}" 
    }
}

