# Terraform Infrastructure

## Quick Start

```bash
# Initialize Terraform
terraform init

# Plan for dev environment
terraform plan -var-file=environments/dev/terraform.tfvars

# Apply infrastructure
terraform apply -var-file=environments/dev/terraform.tfvars

# Connect kubectl to the new cluster
aws eks --region ap-south-1 update-kubeconfig --name mlops-sentiment-dev
```

## What Gets Created

| Resource | Purpose |
|----------|---------|
| VPC + 2 AZ Subnets | Network foundation |
| EKS Cluster (v1.31) | Kubernetes control plane |
| Managed Node Group | Worker nodes (t3.medium) |
| ECR Repository | Docker image registry |
| S3 Bucket | AI model artifact storage |
| ArgoCD | GitOps continuous delivery |
| Prometheus + Grafana | Monitoring & dashboards |

## Environment Files

- `environments/dev/terraform.tfvars` — Development (smaller, cheaper)
- `environments/prod/terraform.tfvars` — Production (larger, HA)

## Destroy

```bash
terraform destroy -var-file=environments/dev/terraform.tfvars
```
