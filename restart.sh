#!/usr/bin/env bash
# shellcheck disable=SC2164
cd "$(dirname "$0")"
export KUBECONFIG=/etc/kubernetes/admin.conf


kubectl delete --wait=true -n train-ticket-bot -f workload/bots.yml &
kubectl delete --wait=true -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part3.yml &
kubectl delete --wait=true -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part2.yml &
kubectl delete --wait=true -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part1.yml &
wait


build_docker () {
  docker build workload -t docker.peidan.me/lizytalk/train-ticket-bot:latest
  docker push docker.peidan.me/lizytalk/train-ticket-bot:latest
}

build_docker &

kubectl apply -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part1.yml
bash deployment/kubernetes-manifests/k8s-with-jaeger/wait_for.sh pod -n tt
kubectl apply -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part2.yml
bash deployment/kubernetes-manifests/k8s-with-jaeger/wait_for.sh pod -n tt
kubectl apply -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part3.yml
bash deployment/kubernetes-manifests/k8s-with-jaeger/wait_for.sh pod -n tt

wait

docker run --rm --entrypoint "" docker.peidan.me/lizytalk/train-ticket-bot:latest python3 create_users.py || echo "failed to add users"

kubectl apply -n train-ticket-bot -f workload/bots.yml
