import random
import shlex
import subprocess
import time
from datetime import datetime, timedelta
from pathlib import Path

import pytz

BASE = Path(__file__).parent


def main():
    current_dt = datetime.now(tz=pytz.timezone("Asia/Shanghai"))
    pod_number = random.choices([1, 2, 3], weights=[0.9, 0.09, 0.01])[0]
    print(f"{pod_number=}")
    if current_dt.hour in {0, 1}:
        experiment_type = "node-cpu-stress"
    elif current_dt.hour in {2, 3}:
        experiment_type = "node-memory-stress"
    elif current_dt.hour in {4, 5}:
        experiment_type = "pod-cpu-stress"
    elif current_dt.hour in {6, 7}:
        experiment_type = "pod-memory-stress"
    elif current_dt.hour in {8, 9}:
        experiment_type = "pod-failure"
    elif current_dt.hour in {18, 19}:
        experiment_type = "pod-network-delay"
    elif current_dt.hour in {20, 21}:
        experiment_type = "pod-network-loss"
    elif current_dt.hour in {22, 23}:
        experiment_type = "pod-network-corrupt"
    else:
        raise RuntimeError(f"Invalid {current_dt=}")
    output_dir = (BASE / 'output' / f"{current_dt.strftime('%H-at-%Y-%m-%d-%H-%M')}").resolve()
    print(f"{output_dir=}")
    apply_chaos_cmd = (
        f"python3 {(BASE / 'chaos' / 'apply_one_experiment.py').resolve()} "
        f"--experiment_type {experiment_type} "
        f"--selected_pod_number {pod_number} "
        f"--kube_config kube.conf "
        f"--output_dir '{(output_dir / 'chaos').resolve()}'"
    )
    print(apply_chaos_cmd)
    # print(subprocess.run(shlex.split(apply_chaos_cmd), capture_output=True).stdout.decode())
    # time.sleep(60 * 5)
    reset_cmd = (
        f"bash {(BASE /'deployment'/'kubernetes-manifests'/'k8s-with-jaeger'/'reset.sh').resolve()}"
    )
    # reset_job = subprocess.Popen(shlex.split(reset_cmd))

    collect_cmd = (
        f"python3 {(BASE/'FDG_data_collection'/'run_collect_metrics.py').resolve()} "
        f"--begin_time='{((current_dt - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M'))}' "
        f"--end_time='{((current_dt + timedelta(minutes=5)).strftime('%Y-%m-%d %H:%M'))}' "
        f"--output_dir '{(output_dir / 'metrics').resolve()}'"
    )
    print(reset_cmd)
    print(collect_cmd)
    # collect_job = subprocess.Popen(shlex.split(collect_cmd))
    # reset_job.communicate()
    # collect_job.communicate()


if __name__ == '__main__':
    main()
