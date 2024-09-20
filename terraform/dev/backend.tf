terraform {
  backend "s3" {
    bucket = "meu-bucket-terraform-pedro-silveira"
    key    = "terraform.tfstate"
    region = "us-east-1"
  }
}
