# ==============================================================================
# Production Environment Variables
# ==============================================================================
# Usage: terraform apply -var-file=environments/prod/terraform.tfvars
# ==============================================================================

aws_region      = "ap-south-1"
environment     = "prod"
project_name    = "mlops-sentiment"
cluster_name    = "mlops-sentiment-prod"
cluster_version = "1.31"
vpc_cidr        = "10.1.0.0/16"

# Larger nodes and higher availability for production
node_instance_types = ["t3.large"]
node_min_size       = 2
node_max_size       = 5
node_desired_size   = 3
