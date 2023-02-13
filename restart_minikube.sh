minikube delete
minikube start --cpus=max --memory=max
minikube addons enable dashboard
minikube addons enable registry
minikube addons enable metrics-server
minikube dashboard --port 39563 --url
# make deploy DeployArgs="--with-tracing --with-monitoring"
