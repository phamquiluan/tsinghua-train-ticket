from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

import pandas as pd
import requests
from loguru import logger

from config import Config

__all__ = ["collect_node_metrics"]

INSTANCE_MAPPING = {
    "192.168.65.121:9100": "node1",
    "192.168.65.122:9100": "node2",
    "192.168.65.123:9100": "node3",
    "192.168.65.124:9100": "node4",
    "192.168.65.125:9100": "node5",
    "192.168.65.126:9100": "node6",
}

INSTANCE_METRIC_QUERIES = {
    ## CPU metrics
    # "cpu_busy_system": 'sum by (instance)(rate(node_cpu_seconds_total{mode="system",job="node-exporter"}[1m])) * 100',
    # "cpu_busy_user": 'sum by (instance)(rate(node_cpu_seconds_total{mode="user",job="node-exporter"}[1m])) * 100',
    # "cpu_busy_user_nice": 'sum by (instance)(rate(node_cpu_seconds_total{mode="nice",job="node-exporter"}[1m])) * 100',
    # "cpu_busy_IOWait": 'sum by (instance)(rate(node_cpu_seconds_total{mode="iowait",job="node-exporter"}[1m])) * 100',
    # "cpu_busy_IRQs": 'sum by (instance)(rate(node_cpu_seconds_total{mode=~".*irq",job="node-exporter"}[1m])) * 100',
    # "cpu_busy_softIRQs": 'sum by (instance)(rate(node_cpu_seconds_total{mode="softirq",job="node-exporter"}[1m])) * 100',
    # "cpu_busy_steal": 'sum by (instance)(rate(node_cpu_seconds_total{mode="steal",job="node-exporter"}[1m])) * 100',
    # "cpu_busy_guest": 'sum by (instance)(rate(node_cpu_seconds_total{mode="guest",job="node-exporter"}[1m])) * 100',
    # "cpu_busy_others": 'sum by (instance)(rate(node_cpu_seconds_total{mode!="idle",mode!="user",mode!="system",mode!="iowait",mode!="irq",mode!="softirq",job="node-exporter"}[1m])) * 100',
    ## Memory metrics
}


def parse_response(metric_name: str, rsp: Dict) -> Optional[pd.DataFrame]:
    try:
        data = rsp["data"]
        assert data['resultType'] == 'matrix'
        records = []
        for series in data['result']:
            name = f"{INSTANCE_MAPPING[series['metric']['instance']]}##{metric_name}"
            for point in series['values']:
                records.append(point + [name])
        return pd.DataFrame(data=records, columns=['timestamp', 'value', 'name'])
    except KeyError as e:
        logger.error(f"parse response error for {metric_name=}", excetpion=e)
        return None


def collect_node_metrics(config: Config):
    metric_df_list = []
    for metric_name, query in INSTANCE_METRIC_QUERIES.items():
        logger.info(f"{metric_name=} {query=}")
        rsp = requests.get(f"{config.prometheus_url}/api/v1/query_range", params={
            "query": query,
            "start": int(config.begin_time.timestamp()),
            "end": int(config.end_time.timestamp()),
            "step": 60,
        })
        rsp_df = parse_response(metric_name=metric_name, rsp=rsp.json())
        if rsp_df is not None:
            metric_df_list.append(rsp_df)
    metric_df = pd.concat(metric_df_list, ignore_index=True)
    print(metric_df)  ## TODO: DEBUG
    metric_df.to_pickle(str((config.output_dir / "node_metrics.pkl").resolve()))
