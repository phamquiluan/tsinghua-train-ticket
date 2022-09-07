## Important Note
Image name and node name are hardcoded. So remember to change them.


## Preliminary
I have five nodes, named lzy-k8s-1, lzy-k8s-2, lzy-k8s-3, lzy-k8s-4, lzy-k8s-6.
I will put elastic-search and mongodb data on lzy-k8s-6, and I am not going to inject node-level faults on it.

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
   kubectl apply -f kube-prometheus-stack.pv.yml
   helm upgrade --install -f kube-prometheus-stack.yml kube-prometheus-stack prometheus-community/kube-prometheus-stack -n monitoring
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
   
## Install Metric Service for `kubectl top`

```bash
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm upgrade --install metrics-server --set args={"--kubelet-insecure-tls=true"} metrics-server/metrics-server
```

## Install MongoDB Exporter
We need to add a PodMonitor
```bash
kubectl apply -f mongo-pod-monitor.yml
```

## Install JMX Exporter

1. prepare the following NFS volume
   ```
   volumes:
      - name: JMX_exporter
        nfs:
          path: /train-ticket/deployment/kubernetes-manifests/k8s-with-jaeger/JMX_exporter
          server: lzy-k8s-1.cluster.peidan.me
   ```

2. add a PodMonitor
   ```
   kubectl apply -f jmx-exporter-monitor.yml
   ```