import json
import os
import random
import shutil
import subprocess
import time
from pathlib import Path
from typing import Literal, Dict

from loguru import logger
from tap import tap
from yaml import load, CLoader


class Config(tap.Tap):
    output_dir: Path = None
    experiment_type: Literal[
        'node-cpu-stress', 'node-memory-stress',
        'pod-cpu-stress', 'pod-memory-stress',
        'pod-cpu-stress-multiple', 'pod-memory-stress-multiple',
    ]
    kube_config: str = os.environ.get('KUBECONFIG', "./kube.conf")

    def process_args(self) -> None:
        if self.output_dir is None:
            self.output_dir = Path(f"./applied_chaos_experiments/{time.time()}")
        self.output_dir = self.output_dir.resolve()
        logger.info(f"{self.output_dir=}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def configure(self) -> None:
        self.add_argument("-e", "--experiment-type", type=str)


BASE_DIR = Path(__file__).resolve().parent


def apply_experiment(config: Config, exp_config_path: Path):
    # apply k8s config
    with open(exp_config_path, "r") as f:
        exp_config: Dict = load(f, Loader=CLoader)
    namespace = exp_config["metadata"]["namespace"]
    name = exp_config["metadata"]["name"]
    kind = exp_config["kind"]
    try:
        os.system(f"kubectl --kubeconfig {config.kube_config} apply -f {exp_config_path}")
        # copy config
        shutil.copy(exp_config_path, config.output_dir / exp_config_path.name)
        # wait for injection end
        while True:
            pod_description: Dict = json.loads(subprocess.getoutput(
                f"kubectl --kubeconfig {config.kube_config} get -n {namespace} {kind}/{name} -o json"
            ))
            status = {_['type']: (_['status'].lower() == "true") for _ in pod_description["status"]["conditions"]}
            logger.info(f"{status=}")
            if status["AllRecovered"] and status['Selected'] and not status['AllInjected'] and not status["Paused"]:
                logger.info("All injection recovered")
                with open(config.output_dir / "pod_description.json", "w+") as f:
                    json.dump(pod_description, f)
                break
            time.sleep(5)
        # write all events
        with open(config.output_dir / "events.txt", "w+") as f:
            print(subprocess.getoutput(
                f"kubectl --kubeconfig {config.kube_config} "
                f"get events -n {namespace} --field-selector involvedObject.name={name}"
            ), file=f)
    except Exception as e:
        logger.exception(f"Encounter error when applying an experiment: {e}", exception=e)
    finally:
        os.system(f"kubectl --kubeconfig {config.kube_config} delete -f {exp_config_path}")


def main(config: Config):
    logger.add(config.output_dir / "chaos_experiment.log", mode="a")
    if config.experiment_type in {'node-cpu-stress', "node-memory-stress"}:
        exp_config_path = random.choice(list((BASE_DIR / 'experiments' / config.experiment_type).glob("*.yml")))
    elif config.experiment_type in {
        'pod-cpu-stress', 'pod-memory-stress', "pod-cpu-stress-multiple", "pod-memory-stress-multiple"
    }:
        exp_config_path = BASE_DIR / "experiments" / f"{config.experiment_type}.yml"
    else:
        raise NotImplementedError(f"Experiment type {config.experiment_type} is not implemented")
    logger.info(f"Applying {config.experiment_type} config: {exp_config_path}")
    apply_experiment(config, exp_config_path)




if __name__ == '__main__':
    main(Config().parse_args())
