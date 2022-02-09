import json
import os
import random
import re
import shlex
import shutil
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Literal, Dict

from loguru import logger
from tap import tap
from yaml import load, CLoader, dump


class Config(tap.Tap):
    output_dir: Path = None
    experiment_type: str
    kube_config: str = os.environ.get('KUBECONFIG', "./kube.conf")
    selected_pod_number: int = 1
    duration: str = "5m"

    def process_args(self) -> None:
        if self.output_dir is None:
            self.output_dir = Path(f"./applied_chaos_experiments/{self.experiment_type}-{datetime.now()}")
        self.output_dir = self.output_dir.resolve()
        logger.info(f"{self.output_dir=}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def configure(self) -> None:
        self.add_argument("-e", "--experiment_type", type=str)
        self.add_argument("-n", "--selected_pod_number", type=int, default=1)


BASE_DIR = Path(__file__).resolve().parent


def apply_experiment(config: Config, exp_config_path: Path):
    # apply k8s config
    with open(exp_config_path, "r") as f:
        exp_config: Dict = load(f, Loader=CLoader)
    namespace = exp_config["metadata"]["namespace"]
    name = exp_config["metadata"]["name"]
    kind = exp_config["kind"]
    if exp_config["spec"].get("mode", "") == "fixed":
        exp_config["spec"]["value"] = f"{config.selected_pod_number}"
    exp_config["spec"]["duration"] = config.duration
    selected_events_displayed = False
    try:
        logger.info(f"Config:\n{dump(exp_config)}")
        subprocess.check_output(
            shlex.split(f"kubectl --kubeconfig {config.kube_config} apply -f -"),
            input=dump(exp_config), text=True,
        )
        # copy config
        shutil.copy(exp_config_path, config.output_dir / exp_config_path.name)
        # wait for injection end
        while True:
            pod_description: Dict = json.loads(subprocess.getoutput(
                f"kubectl --kubeconfig {config.kube_config} get -n {namespace} {kind}/{name} -o json"
            ))
            try:
                status = {_['type']: (_['status'].lower() == "true") for _ in pod_description["status"]["conditions"]}
            except KeyError:
                time.sleep(5)
                continue
            logger.info(f"{status=}")
            if status["AllRecovered"] and status['Selected'] and not status['AllInjected'] and not status["Paused"]:
                logger.info("All injection recovered")
                with open(config.output_dir / "pod_description.json", "w+") as f:
                    json.dump(pod_description, f, indent=4)
                break
            if status["Selected"] and not selected_events_displayed:
                print(subprocess.getoutput(
                    f"kubectl --kubeconfig {config.kube_config} "
                    f"get events -n {namespace} --field-selector involvedObject.uid={pod_description['metadata']['uid']} "
                ))
                selected_events_displayed = True
            time.sleep(5)
        # write all events
        with open(config.output_dir / "events.txt", "w+") as f:
            print(subprocess.getoutput(
                f"kubectl --kubeconfig {config.kube_config} "
                f"get events -n {namespace} --field-selector involvedObject.uid={pod_description['metadata']['uid']} "
            ), file=f)
    except Exception as e:
        logger.exception(f"Encounter error when applying an experiment: {e}", exception=e)
    finally:
        os.system(f"kubectl --kubeconfig {config.kube_config} delete -f {exp_config_path}")


NODE_MAP = {
    f"http://lzy-k8s-{i}.cluster.peidan.me:22777": f"node{i}" for i in range(1, 7)
}


def get_ground_truths(config: Config):
    events_path = config.output_dir / "events.txt"
    if not events_path.exists():
        logger.error(f"{events_path=} does not exist")
        return []
    targets = []
    with open(events_path, "r") as f:
        for line in f:
            match = re.match(r".*Successfully apply chaos for (?P<target>\S+)", line)
            if match:
                targets.append(match.group("target"))
    if config.experiment_type in {"pod-cpu-stress"}:
        return [f"{_.split('/')[1]} CPU" for _ in targets]  # Pod CPU
    elif config.experiment_type in {"pod-memory-stress"}:
        return [f"{_.split('/')[1]} Memory" for _ in targets]  # Pod Memory
    elif config.experiment_type in {"node-cpu-stress"}:
        return [f"{NODE_MAP[_]} CPU" for _ in targets]  # Node CPU
    elif config.experiment_type in {"node-memory-stress"}:
        return [f"{NODE_MAP[_]} Memory" for _ in targets]  # Node Memory
    elif config.experiment_type == "pod-network-delay":
        return [f"{_.split('/')[1]}" for _ in targets]  # Pod
    elif config.experiment_type == "pod-network-loss":
        return [f"{_.split('/')[1]}" for _ in targets]  # Pod
    elif config.experiment_type == "pod-network-corrupt":
        return [f"{_.split('/')[1]}" for _ in targets]  # Pod
    elif config.experiment_type == "pod-failure":
        return [f"{_.split('/')[1]}" for _ in targets]  # Pod
    else:
        raise NotImplementedError(f"{config.experiment_type=}")


def main(config: Config):
    logger.add(config.output_dir / "chaos_experiment.log", mode="a")
    if config.experiment_type in {'node-cpu-stress', "node-memory-stress"}:
        exp_config_path = random.choice(list((BASE_DIR / 'experiments' / config.experiment_type).glob("*.yml")))
    else:
        exp_config_path = BASE_DIR / "experiments" / f"{config.experiment_type}.yml"
    if not exp_config_path.exists():
        raise RuntimeError(f"{exp_config_path=} does not exist")
    logger.info(f"Applying {config.experiment_type} config: {exp_config_path}")
    apply_experiment(config, exp_config_path)
    ground_truths = get_ground_truths(config)
    logger.info(f"{ground_truths=}")
    with open(config.output_dir / "ground_truths.json", "w+") as f:
        json.dump(ground_truths, f)


if __name__ == '__main__':
    main(Config().parse_args())
