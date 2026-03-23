# ==============================================================================
# Outputs
# ==============================================================================
# Important values displayed after terraform apply.
# Used for connecting kubectl, accessing ArgoCD, and CI/CD configuration.
# ==============================================================================

# ──────────────────────── EKS ────────────────────────

output "cluster_name" {
  description = "Name of the EKS cluster"
  value       = module.eks.cluster_name
}

output "cluster_endpoint" {
  description = "Endpoint for the EKS API server"
  value       = module.eks.cluster_endpoint
}

output "cluster_version" {
  description = "Kubernetes version running on EKS"
  value       = module.eks.cluster_version
}

output "configure_kubectl" {
  description = "Command to configure kubectl for the new cluster"
  value       = "aws eks --region ${var.aws_region} update-kubeconfig --name ${module.eks.cluster_name}"
}

# ──────────────────────── ECR ────────────────────────

output "ecr_repository_url" {
  description = "ECR repository URL — use this in Dockerfile push and K8s deployments"
  value       = aws_ecr_repository.app.repository_url
}

output "ecr_login_command" {
  description = "Command to authenticate Docker with ECR"
  value       = "aws ecr get-login-password --region ${var.aws_region} | docker login --username AWS --password-stdin ${aws_ecr_repository.app.repository_url}"
}

# ──────────────────────── S3 ────────────────────────

output "model_artifacts_bucket" {
  description = "S3 bucket name for AI model artifacts"
  value       = aws_s3_bucket.model_artifacts.id
}

# ──────────────────────── ArgoCD ────────────────────────

output "argocd_password_command" {
  description = "Command to get the default ArgoCD admin password"
  value       = "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath=\"{.data.password}\" | base64 -d; echo"
}

# ──────────────────────── Monitoring ────────────────────────

output "grafana_login" {
  description = "Grafana default login credentials"
  value       = "Username: admin | Password: admin"
}

# ──────────────────────── VPC ────────────────────────

output "vpc_id" {
  description = "ID of the created VPC"
  value       = module.vpc.vpc_id
}
