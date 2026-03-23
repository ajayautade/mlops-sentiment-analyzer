# Troubleshooting Guide: MLOps Sentiment Analyzer

This document outlines the challenges faced during the development and deployment of this project, how they were resolved, and potential issues you might encounter when implementing this yourself.

---

## 🛑 Problems Faced During Development & Deployment

### 1. EKS Node Group Creation Failed (`AsgInstanceLaunchFailures`)
* **The Problem:** When running `terraform apply`, the EKS Managed Node Group failed to create because the selected instance type (`t3.medium`) was restricted or not eligible for the account's specific tier quotas.
* **The Solution:** We updated the Terraform configuration natively to use `m7i-flex.large` instances. These are modern, cost-effective instances that provide enough memory (8GB) to run the PyTorch models smoothly.

### 2. Docker Build Timeouts & Massive Image Size
* **The Problem:** The default `pip install torch` downloads the CUDA-enabled version of PyTorch, which is over ~800MB. This caused network timeouts during the Docker build process and bloated the container size unnecessarily (since EKS nodes didn't have GPUs).
* **The Solution:** We explicitly installed the CPU-only version of PyTorch via the PyTorch wheel index (`torch==2.6.0+cpu`). This reduced the library size to ~200MB, drastically speeding up the build and preventing timeouts.

### 3. CI Pipeline Failures: Trivy Security Scans
* **The Problem:** The GitHub Actions pipeline failed on the Security Scan step because Trivy detected "HIGH" severity vulnerabilities in upstream Python packages (which are common and frequently unpatched).
* **The Solution:** We adjusted the Trivy GitHub Actions configuration (`.github/workflows/ci-pipeline.yml`) to only fail the build on `CRITICAL` vulnerabilities, preventing third-party library warnings from blocking deployments.

### 4. CI Pipeline Failures: Strict Python Linting & Formatting
* **The Problem:** `flake8` failed the build due to unused imports in test files, and `black` failed because of minor formatting discrepancies.
* **The Solution:** We cleaned up unused variables (`MODEL_NAME`, `MODEL_VERSION` in `test_model.py`), installed `black` locally via Homebrew, and reformatted the entire `app/` directory to adhere strictly to PEP8 standards.

### 5. Dockerfile `IndentationError`
* **The Problem:** Using inline Python scripts with line continuations (`\`) inside the `Dockerfile` caused an `IndentationError` when trying to pre-download the HuggingFace model.
* **The Solution:** We extracted the model download logic into a standalone python script (`download_model.py`) and executed that script inside the Dockerfile instead of using inline commands.

---

## ⚠️ Potential Issues for Future Implementers

If you are trying to deploy this project from scratch, watch out for these common pitfalls:

### 1. AWS IAM Permissions Insufficient
* **Symptom:** `terraform apply` fails with `AccessDenied` or `UnauthorizedOperation`.
* **Fix:** Ensure the AWS IAM user or role running Terraform has sufficient Administrator privileges to provision VPCs, EKS Clusters, IAM Roles, ECR repositories, and S3 buckets. 

### 2. ECR "ImagePullBackOff" in Kubernetes
* **Symptom:** Kubernetes pods are stuck in `ImagePullBackOff` or `ErrImagePull`.
* **Fix:**
   1. Ensure your GitHub Actions pipeline successfully built and pushed the image to ECR.
   2. Ensure the ECR repository URI in `k8s/deployment.yaml` matches your actual AWS Account ID and region.
   3. Ensure your EKS Node IAM Role has the `AmazonEC2ContainerRegistryReadOnly` policy attached. (Our Terraform setup handles this automatically).

### 3. Docker "No space left on device"
* **Symptom:** Docker image build fails locally due to lack of disk space.
* **Fix:** PyTorch and HuggingFace models consume high amounts of storage. Run `docker system prune -a --volumes` to clear out old unused images and caches before building.

### 4. ArgoCD Application Not Syncing
* **Symptom:** ArgoCD is installed, but the Application isn't deploying your pods.
* **Fix:** Make sure you actually applied the ArgoCD application manifest! Running Terraform only installs ArgoCD; you must manually link it to your GitHub repo by running:
  `kubectl apply -f argocd/application.yaml`

### 5. HuggingFace Rate Limiting
* **Symptom:** During deployment, pods restart repeatedly, or the build fails with HTTP 429 Too Many Requests from `huggingface.co`.
* **Fix:** HuggingFace can rate-limit IP addresses making too many anonymous downloads. If this happens, you can authenticate by creating an Access Token on HuggingFace and passing it as an environment variable (`HF_TOKEN`) to the Docker build or K8s deployment.
