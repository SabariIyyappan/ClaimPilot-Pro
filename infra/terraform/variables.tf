variable "project_name" {
  type        = string
  description = "Project/service name prefix."
  default     = "claimpilot-pro"
}

variable "environment" {
  type        = string
  description = "Environment name."
  default     = "demo"
}

variable "aws_region" {
  type        = string
  description = "AWS region."
  default     = "us-east-1"
}

variable "lambda_package_path" {
  type        = string
  description = "Path to the Lambda deployment zip."
  default     = "../../dist/backend-lambda.zip"
}

variable "cors_allowed_origins" {
  type        = list(string)
  description = "Allowed frontend origins for API Gateway and FastAPI CORS."
  default     = ["https://example.vercel.app"]
}

variable "cors_allow_origin_regex" {
  type        = string
  description = "Optional regex for dynamic preview domains, e.g. Vercel previews."
  default     = "https://([a-z0-9-]+\\.)*vercel\\.app$"
}

variable "gemini_api_key" {
  type        = string
  sensitive   = true
  description = "Gemini API key for model calls."
}

variable "documents_bucket_name" {
  type        = string
  description = "S3 bucket name for uploaded documents. Leave empty for automatic naming."
  default     = ""
}

variable "lambda_memory_size" {
  type        = number
  description = "Lambda memory size in MB."
  default     = 1024
}

variable "lambda_timeout" {
  type        = number
  description = "Lambda timeout in seconds."
  default     = 30
}
