## Install ChaosMesh

1. ```bash
    helm repo add chaos-mesh https://charts.chaos-mesh.org
    helm install chaos-mesh chaos-mesh/chaos-mesh -n=chaos-testing
   ```
   
2. Generate Tokens
    ```bash
   kubectl apply -f rbac.yml
   kubectl describe -n tt secrets account-tt-manager-mysvh
    ```