from pathlib import Path
from typing import Optional
from yaml import CDumper, dump


def apply_istio_experiment(
        failure_type: str, svc: str, uri_prefix: Optional[str],
        output_dir: Path, kube_config: Path, percentage: int = 100,
):
    pass
