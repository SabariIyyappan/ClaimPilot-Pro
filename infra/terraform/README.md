# API Gateway + Lambda Terraform

This Terraform stack provisions the cheapest practical AWS backend for ClaimPilot Pro when the frontend is hosted on Vercel:

- API Gateway HTTP API
- Lambda backend using a ZIP deployment package
- Private S3 bucket for uploaded documents
- Least-privilege IAM role for Lambda
- CloudWatch log groups for Lambda and API access logs

This stack does not create frontend hosting. The frontend is expected to be deployed on Vercel.

## Prerequisites

- Terraform `>= 1.6`
- AWS credentials with permissions for Lambda, API Gateway, IAM, S3, and CloudWatch
- Vercel project for the frontend

## Usage

Create `terraform.tfvars`:

```hcl
project_name            = "claimpilot-pro"
environment             = "demo"
aws_region              = "us-east-1"
lambda_package_path     = "../../dist/backend-lambda.zip"
cors_allowed_origins    = ["https://your-project.vercel.app"]
cors_allow_origin_regex = "https://([a-z0-9-]+\\.)*vercel\\.app$"
gemini_api_key          = "replace-me"
documents_bucket_name   = "claimpilot-demo-documents-123456789012"
lambda_memory_size      = 1024
lambda_timeout          = 30
```

Deploy:

```bash
pwsh ./scripts/build_lambda_package.ps1
terraform init -upgrade
terraform plan
terraform apply
```

## Outputs

Important outputs after apply:

- `api_url`
- `documents_bucket`
- `lambda_function_name`

Use `api_url` as the frontend `VITE_API_URL` in Vercel.

## Cost profile

This stack removes the always-on services that were driving most of the cost:

- no EC2
- no ALB
- no NAT gateway
- no RDS

At demo scale, cost is usually near zero or very low because API Gateway and Lambda are pay-per-use.
