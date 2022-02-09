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
    print(f"=====================start at {current_dt}=====================")
    pod_number = random.choices([1, 2, 3], weights=[0.9, 0.09, 0.01])[0]
    print(f"{pod_number=}")
    # 00:00 is for reset
    if current_dt.hour in {1, 2, 17, 18}:
        experiment_type = "node-cpu-stress"
    elif current_dt.hour in {3, 4, 19, 20}:
        experiment_type = "node-memory-stress"
    elif current_dt.hour in {5, 6, 21, 22}:
        experiment_type = "pod-cpu-stress"
    elif current_dt.hour in {7, 8, 23}:
        experiment_type = "pod-memory-stress"
    elif current_dt.hour in {9, 10}:
        experiment_type = "pod-failure"
    elif current_dt.hour in {11, 12}:
        experiment_type = "pod-network-delay"
    elif current_dt.hour in {13, 14}:
        experiment_type = "pod-network-loss"
    elif current_dt.hour in {15, 16}:
        experiment_type = "pod-network-corrupt"
    else:
        raise RuntimeError(f"Invalid {current_dt=}")
    if experiment_type is not None:
        output_dir = (BASE / 'output' / f"{experiment_type}-at-{current_dt.strftime('%Y-%m-%d-%H-%M')}").resolve()
        print(f"{output_dir=}")
        apply_chaos_cmd = (
            f"python3 {(BASE / 'chaos' / 'apply_one_experiment.py').resolve()} "
            f"--experiment_type {experiment_type} "
            f"--selected_pod_number {pod_number} "
            f"--kube_config kube.conf "
            f"--output_dir '{(output_dir / 'chaos').resolve()}'"
        )
        print(apply_chaos_cmd)
        print(subprocess.run(shlex.split(apply_chaos_cmd), capture_output=True).stdout.decode())
        time.sleep(60 * 11)
        collect_cmd = (
            f"python3 {(BASE/'FDG_data_collection'/'run_collect_metrics.py').resolve()} "
            f"--begin_time='{((current_dt - timedelta(hours=1)).strftime('%Y-%m-%d %H:%M'))}' "
            f"--end_time='{((current_dt + timedelta(minutes=10)).strftime('%Y-%m-%d %H:%M'))}' "
            f"--output_dir '{(output_dir / 'metrics').resolve()}'"
        )
        print(collect_cmd)
        collect_job = subprocess.Popen(shlex.split(collect_cmd))
    else:
        collect_job = None

    if collect_job is not None:
        collect_job.communicate()


if __name__ == '__main__':
    main()
