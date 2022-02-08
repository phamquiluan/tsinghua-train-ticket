from pathlib import Path

from loguru import logger
from pyprof import profile
from yaml import load, dump, CLoader
from config import Config
from lib_jvm_metrics import collect_jvm_metrics
from lib_mongo_metrics import collect_mongo_metrics
from lib_node_metrics import collect_node_metrics
from lib_pod_metrics import collect_pod_metrics
from lib_spans import collect_service_metrics


@profile
def collect_metrics(config: Config):
    logger.add(config.output_dir / "collect_metrics.log", mode="a")
    complete_graph_config(config)
    collect_service_metrics(config)
    collect_node_metrics(config)
    collect_pod_metrics(config)
    collect_jvm_metrics(config)
    collect_mongo_metrics(config)


@profile
def complete_graph_config(config: Config):
    import pandas as pd
    import io
    import subprocess
    pod_config = pd.read_csv(io.StringIO(
        subprocess.getoutput(f"kubectl --kubeconfig={config.kube_config} get -n tt pod -o custom-columns=NAME:metadata.name,NODE:status.hostIP")
    ), delimiter=r"\s+")
    nodes_map = {
        k: f'node{i}' for i, k in enumerate(sorted(
            pod_config['NODE'].unique()
        ), 1)
    }
    pod_config["NODE"] = pod_config["NODE"].map(nodes_map)
    with open(Path(__file__).parent / "graph.yml", 'r') as f:
        graph_config = load(f, Loader=CLoader)
    graph_config.append({
        "class": "edge",
        "type": "pod-node",
        "params": {
            "pod": pod_config["NAME"].to_list(),
            "node": pod_config["NODE"].to_list(),
        },
        "src": "{pod}",
        "dst": "{node}"
    })
    with open(config.output_dir / "graph.yml", "w+") as f:
        dump(graph_config, f)


if __name__ == '__main__':
    with profile("main", report_printer=lambda _: logger.info(f"\n{_}")):
        collect_metrics(Config().parse_args())
