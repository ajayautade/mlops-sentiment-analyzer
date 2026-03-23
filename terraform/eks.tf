# ==============================================================================
# EKS Cluster Module
# ==============================================================================
# Provisions a fully managed Kubernetes control plane and worker node group.
# Uses EKS module v20+ with AL2023 AMI and IRSA for pod-level IAM.
# ==============================================================================

module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.8"

  cluster_name    = var.cluster_name
  cluster_version = var.cluster_version

  # Network configuration — deploy into our VPC's private subnets
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  # Public API access so we can run kubectl from our laptop
  cluster_endpoint_public_access = true

  # Enable IRSA (IAM Roles for Service Accounts)
  # Allows Kubernetes pods to assume specific IAM roles (e.g., for S3 access)
  enable_irsa = true

  # Enable the EKS cluster to manage EBS CSI Driver (for persistent volumes)
  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent              = true
      service_account_role_arn = module.ebs_csi_irsa.iam_role_arn
    }
  }

  # ──────────── Managed Node Group ────────────
  eks_managed_node_groups = {
    ml_workers = {
      name = "${var.project_name}-nodes"

      min_size     = var.node_min_size
      max_size     = var.node_max_size
      desired_size = var.node_desired_size

      # t3.medium: 2 vCPU, 4GB RAM — sufficient for DistilBERT model serving
      instance_types = var.node_instance_types
      capacity_type  = "ON_DEMAND"

      # AL2023 — AWS retired AL2 EKS AMIs in November 2025
      ami_type = "AL2023_x86_64_STANDARD"

      # Disk size for model cache + container images
      disk_size = 30

      labels = {
        role        = "ml-worker"
        environment = var.environment
      }
    }
  }

  # Allow access from the current user/role to manage the cluster
  enable_cluster_creator_admin_permissions = true

  tags = {
    Name        = var.cluster_name
    Application = "mlops-sentiment-analyzer"
  }
}

# ──────────── EBS CSI Driver IRSA ────────────
# IAM Role for the EBS CSI driver to manage persistent volumes

module "ebs_csi_irsa" {
  source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  version = "~> 5.34"

  role_name             = "${var.project_name}-ebs-csi-role"
  attach_ebs_csi_policy = true

  oidc_providers = {
    main = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:ebs-csi-controller-sa"]
    }
  }

  tags = {
    Name = "${var.project_name}-ebs-csi-irsa"
  }
}
