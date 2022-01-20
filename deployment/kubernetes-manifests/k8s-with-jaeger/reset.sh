#!/usr/bin/env bash

# shellcheck disable=SC2164
cd "$(dirname "$0")"

kubectl delete -n tt -f ts-deployment-part3.yml
kubectl delete -n tt -f ts-deployment-part2.yml
kubectl delete -n tt -f ts-deployment-part1.yml

echo waiting for pods to be deleted
while test "$(kubectl get -n tt pods | wc -l)" -gt "1"; do
  echo \#pods in namespace tt is "$(kubectl get -n tt pods | wc -l)"
  sleep 1
done

kubectl apply -n tt -f ts-deployment-part1.yml
bash wait_for.sh pod -n tt
kubectl apply -n tt -f ts-deployment-part2.yml
bash wait_for.sh pod -n tt
kubectl apply -n tt -f ts-deployment-part3.yml
bash wait_for.sh pod -n tt
