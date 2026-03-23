# ==============================================================================
# Variables
# ==============================================================================
# All configurable parameters for the infrastructure.
# Override these in environments/dev/terraform.tfvars or environments/prod/terraform.tfvars
# ==============================================================================

# ──────────────────────── General ────────────────────────

variable "aws_region" {
  description = "AWS region to deploy all resources"
  type        = string
  default     = "ap-south-1"
}

variable "environment" {
  description = "Deployment environment (dev/prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Name of the project — used as prefix for all resources"
  type        = string
  default     = "mlops-sentiment"
}

# ──────────────────────── VPC ────────────────────────

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

# ──────────────────────── EKS ────────────────────────

variable "cluster_name" {
  description = "Name for the EKS cluster"
  type        = string
  default     = "mlops-sentiment-cluster"
}

variable "cluster_version" {
  description = "Kubernetes version for the EKS cluster"
  type        = string
  default     = "1.31"
}

variable "node_instance_types" {
  description = "EC2 instance types for EKS worker nodes"
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_min_size" {
  description = "Minimum number of worker nodes"
  type        = number
  default     = 1
}

variable "node_max_size" {
  description = "Maximum number of worker nodes"
  type        = number
  default     = 3
}

variable "node_desired_size" {
  description = "Desired number of worker nodes"
  type        = number
  default     = 2
}
