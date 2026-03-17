output "api_url" {
  value = aws_apigatewayv2_api.http.api_endpoint
}

output "documents_bucket" {
  value = aws_s3_bucket.documents.bucket
}

output "lambda_function_name" {
  value = aws_lambda_function.api.function_name
}

output "lambda_function_arn" {
  value = aws_lambda_function.api.arn
}
