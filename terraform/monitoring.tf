# ==============================================================================
# Monitoring Stack — Prometheus + Grafana
# ==============================================================================
# Installs the kube-prometheus-stack Helm chart which bundles:
# - Prometheus (metrics collection)
# - Grafana (dashboards & visualization)
# - Alertmanager (alerting)
# - Node Exporter & kube-state-metrics
# ==============================================================================

resource "helm_release" "monitoring" {
  name             = "monitoring"
  repository       = "https://prometheus-community.github.io/helm-charts"
  chart            = "kube-prometheus-stack"
  version          = "68.4.0"
  namespace        = "monitoring"
  create_namespace = true

  wait    = true
  timeout = 600

  # ──────────── Grafana Configuration ────────────

  # Expose Grafana via LoadBalancer (for demo; use Ingress in production)
  set {
    name  = "grafana.service.type"
    value = "LoadBalancer"
  }

  # Default admin credentials (change in production!)
  set {
    name  = "grafana.adminUser"
    value = "admin"
  }

  set {
    name  = "grafana.adminPassword"
    value = "admin"
  }

  # ──────────── Prometheus Configuration ────────────

  # Enable pod monitors for scraping our AI app /metrics endpoint
  set {
    name  = "prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues"
    value = "false"
  }

  set {
    name  = "prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues"
    value = "false"
  }

  # Resource limits for Prometheus (AI metrics can be memory-heavy)
  set {
    name  = "prometheus.prometheusSpec.resources.requests.memory"
    value = "512Mi"
  }

  set {
    name  = "prometheus.prometheusSpec.resources.requests.cpu"
    value = "250m"
  }

  depends_on = [module.eks]
}
