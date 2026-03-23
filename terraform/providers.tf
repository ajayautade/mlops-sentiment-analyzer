# ==============================================================================
# Terraform Configuration & Providers
# ==============================================================================
# Defines required providers with version constraints and authentication
# for AWS, Kubernetes, and Helm.
# ==============================================================================

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.27"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.12"
    }
  }

  # Remote state backend — uncomment after creating the S3 bucket manually
  # or via a separate bootstrap Terraform config
  # backend "s3" {
  #   bucket         = "mlops-sentiment-analyzer-tfstate"
  #   key            = "terraform.tfstate"
  #   region         = "ap-south-1"
  #   dynamodb_table = "terraform-state-lock"
  #   encrypt        = true
  # }
}

# ──────────────────────── AWS Provider ────────────────────────

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "mlops-sentiment-analyzer"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}

# ──────────────────────── Kubernetes Provider ────────────────────────
# Authenticates with EKS using aws eks get-token (no hardcoded creds)

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

# ──────────────────────── Helm Provider ────────────────────────
# Used for installing ArgoCD and monitoring stack via Helm charts

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)

    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args        = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}
