#!/usr/bin/env bash
# shellcheck disable=SC2164
cd "$(dirname "$0")"
export KUBECONFIG=/etc/kubernetes/admin.conf


kubectl delete --wait=true -n train-ticket-bot -f workload/bots.yml &
kubectl delete --wait=true -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part3.yml &
kubectl delete --wait=true -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part2.yml &
kubectl delete --wait=true -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part1.yml &
wait

echo waiting for pods to be deleted
while test "$(kubectl get -n tt pods | wc -l)" -gt "1"; do
  echo \#pods in namespace tt is "$(kubectl get -n tt pods | wc -l)"
  sleep 10
done


build_docker () {
  docker build workload -t docker.peidan.me/lizytalk/train-ticket-bot:latest
  docker push docker.peidan.me/lizytalk/train-ticket-bot:latest
}

build_docker &

until kubectl apply -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part1.yml
do
  sleep 30
done
bash deployment/kubernetes-manifests/k8s-with-jaeger/wait_for.sh pod -n tt
until kubectl apply -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part2.yml
do
  sleep 30
done
bash deployment/kubernetes-manifests/k8s-with-jaeger/wait_for.sh pod -n tt
until kubectl apply -n tt -f deployment/kubernetes-manifests/k8s-with-jaeger/ts-deployment-part3.yml
do
  sleep 30
done
bash deployment/kubernetes-manifests/k8s-with-jaeger/wait_for.sh pod -n tt

wait

max_retry=10
counter=0
until docker run --rm --entrypoint "" -t -e TRAIN_TICKET_URL="http://$(hostname):32677" docker.peidan.me/lizytalk/train-ticket-bot:latest python3 create_users.py
do
   sleep 60
   [[ counter -eq $max_retry ]] && echo "Failed!" && exit 1
   echo "Trying again. Try #$counter"
   ((counter++))
done

kubectl apply -n train-ticket-bot -f workload/bots.yml
