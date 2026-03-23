# ==============================================================================
# VPC Module (Virtual Private Cloud)
# ==============================================================================
# Creates a production-grade network foundation with public and private subnets
# across two Availability Zones for high availability.
# ==============================================================================

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.5"

  name = "${var.project_name}-vpc"
  cidr = var.vpc_cidr

  # Span at least 2 AZs for high availability (EKS requirement)
  azs             = ["${var.aws_region}a", "${var.aws_region}b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  # NAT Gateway: allows private subnets to pull Docker images from ECR
  enable_nat_gateway   = true
  single_nat_gateway   = true  # Cost saving for dev; use one_nat_gateway_per_az in prod
  enable_dns_hostnames = true
  enable_dns_support   = true

  # Tags required by Kubernetes for automatic LoadBalancer subnet discovery
  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = 1
    "kubernetes.io/cluster/${var.cluster_name}"  = "shared"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"            = 1
    "kubernetes.io/cluster/${var.cluster_name}"   = "shared"
  }

  tags = {
    Name = "${var.project_name}-vpc"
  }
}
