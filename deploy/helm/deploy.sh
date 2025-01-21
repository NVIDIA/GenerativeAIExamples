# /bin/bash

kubectl create namespace rag
kubectl create secret -n rag docker-registry ngc-secret --docker-server=nvcr.io --docker-username='$oauthtoken' --docker-password=$NVIDIA_API_KEY
kubectl label secret ngc-secret -n rag app.kubernetes.io/managed-by=Helm
kubectl annotate secret ngc-secret -n rag meta.helm.sh/release-name=rag meta.helm.sh/release-namespace=rag

helm upgrade --install rag . -n rag \
  --set imagePullSecret.password=$NVIDIA_API_KEY \
  --set nvidia-nim-llama-32-nv-embedqa-1b-v2.nim.ngcAPIKey=$NVIDIA_API_KEY \
  --set text-reranking-nim.nim.ngcAPIKey=$NVIDIA_API_KEY \
  --set nim-llm.model.ngcAPIKey=$NVIDIA_API_KEY \

echo "Listing pods..."
kubectl get pods -n rag

echo "Listing services..."
kubectl get svc -n rag
