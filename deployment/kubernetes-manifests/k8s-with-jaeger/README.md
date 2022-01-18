## Install TS

1. build images
   ```bash
   cd train-ticket  # the root directory of the project
   make
   ```
   
2. ```bash
   kubectl apply -f es-jaeger.yml
   ```

4. apply the ts-deployment-part*.yml one by one

## Install Prometheus

1. ``` bash
   helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
   helm repo update
   kubectl create namespace monitoring
   helm install kube-prometheus-stack prometheus-community/kube-prometheus-stack -n monitoring
   ```

## Install Istio for Tracing

1. Install Istio
   ```bash
   helm repo add istio https://istio-release.storage.googleapis.com/charts
   helm repo update
   kubectl create namespace istio-system
   helm install -f istio-base.yml istio-base istio/base -n istio-system
   helm install -f istiod.yml  istiod istio/istiod -n istio-system --wait
   kubectl create namespace istio-ingress
   kubectl label namespace istio-ingress istio-injection=enabled
   helm install istio-ingress istio/gateway -n istio-ingress --wait
   ```
   
2. enable injection
   ```bash
   kubectl label namespace tt istio-injection=enabled
   kubectl delete pod -n tt -l online-service-system=train-ticket
   kubectl describe pod -n tt  -l online-service-system=train-ticket
   ```
   