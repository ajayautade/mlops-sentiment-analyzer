# ==============================================================================
# Development Environment Variables
# ==============================================================================
# Usage: terraform apply -var-file=environments/dev/terraform.tfvars
# ==============================================================================

aws_region      = "ap-south-1"
environment     = "dev"
project_name    = "mlops-sentiment"
cluster_name    = "mlops-sentiment-dev"
cluster_version = "1.31"
vpc_cidr        = "10.0.0.0/16"

# Smaller nodes for dev to save costs
node_instance_types = ["t3.medium"]
node_min_size       = 1
node_max_size       = 3
node_desired_size   = 2
