import json
import shlex
import subprocess
import time
from pathlib import Path
from typing import Optional

from yaml import dump, CDumper


def apply_istio_experiment(
        failure_type: str, svc: str,
        output_dir: Path, kube_config: Path, percentage: int = 100, uri_prefix: Optional[str] = None,
        delay_seconds: int = 3, http_status: int = 404, duration_seconds: int = 300,
        http_method: Optional[str] = None,
):
    output_dir.mkdir(parents=True, exist_ok=True)
    name = f"istio-http-fault-{failure_type}-{svc}-{'with' if uri_prefix is not None else 'without'}url"
    virtual_service_config: dict = {
        'apiVersion': 'networking.istio.io/v1beta1', 'kind': 'VirtualService',
        'metadata': {'namespace': 'tt', 'name': name},
        'spec': {
            'hosts': [svc],
            'http': [
                {
                    'route': [{'destination': {'host': svc}}]
                },
                {
                    'route': [{'destination': {'host': svc}}]
                }
            ]
        }
    }
    if failure_type == "delay":
        virtual_service_config["spec"]["http"][0]["fault"] = {
            'delay': {'fixedDelay': f'{delay_seconds}s', 'percentage': {'value': percentage}}
        }
    else:
        virtual_service_config["spec"]["http"][0]["fault"] = {
            'abort': {'httpStatus': f'{http_status}', 'percentage': {'value': percentage}}
        }

    if uri_prefix is not None:
        if "match" not in virtual_service_config["spec"]["http"][0]:
            virtual_service_config["spec"]["http"][0]["match"] = []
        virtual_service_config["spec"]["http"][0]["match"].append({'uri': {'prefix': uri_prefix}})
    if http_method is not None:
        if "match" not in virtual_service_config["spec"]["http"][0]:
            virtual_service_config["spec"]["http"][0]["match"] = []
        virtual_service_config["spec"]["http"][0]["match"].append({'method': {'exact': http_method}})

    with open(output_dir / "params.yml", "w+") as f:
        json.dump(dict(
            failure_type=failure_type, svc=svc, uri_prefix=uri_prefix, http_method=http_method,
            http_status=http_status, delay_seconds=delay_seconds, percentage=percentage,
            duration_seconds=duration_seconds
        ), f)

    with open(output_dir / "fault.yml", "w+") as f:
        dump(virtual_service_config, f, CDumper)

    subprocess.check_output(
        shlex.split(f"kubectl --kubeconfig {kube_config} apply -f {output_dir / 'fault.yml'}"),
    )

    time.sleep(duration_seconds)

    subprocess.check_output(
        shlex.split(f"kubectl --kubeconfig {kube_config} delete -f {output_dir / 'fault.yml'}"),
    )
