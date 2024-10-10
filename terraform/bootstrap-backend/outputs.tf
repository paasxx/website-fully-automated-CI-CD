# bootstrap-backend/outputs.tf
output "s3_bucket_name" {
  value = aws_s3_bucket.meu_bucket_terraform.bucket
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.terraform_locks.name
}
