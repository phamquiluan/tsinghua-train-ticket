#!/usr/bin/env bash
set -eu

echo
echo "Start pushing image"
echo
docker images | grep "$1/ts" | awk 'BEGIN{OFS=":"}{print $1,$2}' | xargs -I {} docker push {}
