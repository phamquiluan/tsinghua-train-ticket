#!/usr/bin/env bash
# shellcheck disable=SC2164
cd "$(dirname "$0")"
export KUBECONFIG=/etc/kubernetes/admin.conf

docker build . -t docker.peidan.me/lizytalk/train-ticket-bot:latest
docker push docker.peidan.me/lizytalk/train-ticket-bot:latest
docker run --rm --entrypoint "" docker.peidan.me/lizytalk/train-ticket-bot:latest python3 create_users.py
kubectl delete -n train-ticket-bot -f bots.yml
kubectl apply -n train-ticket-bot -f bots.yml
