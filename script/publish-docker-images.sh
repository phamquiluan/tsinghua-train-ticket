#!/usr/bin/env bash
set -eux

repo=${1}
tag=${2:-$(git rev-parse --short HEAD)}

echo
echo "Publishing images, Repo: ${repo}, Tag: ${tag}"
echo
for dir in ts-*; do
    if [[ -d $dir ]]; then
        if [[ -n $(ls "$dir" | grep -i Dockerfile) ]]; then
            echo "build ${dir}"
	    # Must use `buildx` as docker build tool
            docker buildx build --push -t "${repo}"/"${dir}":"${tag}" "$dir"
        fi
    fi
done
