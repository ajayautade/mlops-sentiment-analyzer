# ==============================================================================
# ArgoCD Installation via Helm
# ==============================================================================
# Installs ArgoCD on the EKS cluster for GitOps continuous delivery.
# ArgoCD watches the GitHub repo and auto-syncs Kubernetes manifests.
# ==============================================================================

resource "helm_release" "argocd" {
  name             = "argocd"
  repository       = "https://argoproj.github.io/argo-helm"
  chart            = "argo-cd"
  version          = "7.7.12"
  namespace        = "argocd"
  create_namespace = true

  # Wait for all pods to be ready before marking as complete
  wait    = true
  timeout = 600

  # ArgoCD Server configuration
  set {
    name  = "server.service.type"
    value = "LoadBalancer"
  }

  # Disable TLS on ArgoCD server (we'll use AWS ALB for TLS termination)
  set {
    name  = "configs.params.server\\.insecure"
    value = "true"
  }

  depends_on = [module.eks]
}
