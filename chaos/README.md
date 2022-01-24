## Install ChaosMesh

1. ```bash
    helm repo add chaos-mesh https://charts.chaos-mesh.org
    helm install chaos-mesh chaos-mesh/chaos-mesh -n=chaos-testing
   ```
   
2. Generate Tokens
    ```bash
   kubectl apply -f rbac.yml
   kubectl describe secrets account-cluster-manager-losfg
    ```

##  Install ChaosSd


1. check glibc version: `ldd --version`
2. ```bash
   export CHAOSD_VERSION=v1.1.1
   curl -o chaosd-$CHAOSD_VERSION-linux-amd64.tar.gz https://mirrors.chaos-mesh.org/chaosd-$CHAOSD_VERSION-linux-amd64.tar.gz
   tar zxvf chaosd-$CHAOSD_VERSION-linux-amd64.tar.gz && sudo mv chaosd-$CHAOSD_VERSION-linux-amd64 /usr/local/
   ln -s /usr/local/chaosd-${CHAOSD_VERSION}-linux-amd64/chaosd /usr/local/bin/
   ```
3. enable chaosd service in `/etc/supervisor/conf.d/chaosd.conf`
   ```
   apt install -y supervisor
   cat > /etc/supervisor/conf.d/chaosd.conf << EOL
   [program:chaosd]
   command=/usr/local/bin/chaosd server --port 22777
   user=root
   autostart=true
   autorestart=true
   EOL
   supervisorctl reload
   ```
   ! Make sure the port is not occupied by other services by `telnet`, and `lsof` may not work as expected.