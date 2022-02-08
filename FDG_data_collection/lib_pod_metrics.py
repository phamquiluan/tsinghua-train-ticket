import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

import pandas as pd
import requests
from loguru import logger

from config import Config

__all__ = ["collect_pod_metrics"]

INSTANCE_METRIC_QUERIES = {
    # CPU metrics
    "cpu_usage": 'sum by (pod) (rate(container_cpu_usage_seconds_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]) * 100)',
    "cpu_system_usage": 'sum by (pod) (rate(container_cpu_system_seconds_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]) * 100)',
    "cpu_user_usage": 'sum by (pod) (rate(container_cpu_user_seconds_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]) * 100)',
    # Memory metrics
    "memory_usage_bytes": 'sum by (pod) (container_memory_usage_bytes{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"})',
    "memory_working_set_bytes": 'sum by (pod) (container_memory_working_set_bytes{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"})',
    "memory_rss_bytes": 'sum by (pod) (container_memory_rss{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"})',
    "memory_mapped_file_bytes": 'sum by (pod) (container_memory_mapped_file{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"})',
    "memory_cache_bytes": 'sum by (pod) (container_memory_cache{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"})',
    "memory_failures_total": 'sum by (pod) (increase(container_memory_failures_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    # Network metrics
    "network_receive_packets_total": 'sum by (pod) (rate(container_network_receive_packets_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "network_transmit_packets_total": 'sum by (pod) (rate(container_network_transmit_packets_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "network_receive_bytes_total": 'sum by (pod) (rate(container_network_receive_bytes_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "network_transmit_bytes_total": 'sum by (pod) (rate(container_network_transmit_bytes_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "network_receive_errors_total": 'sum by (pod) (rate(container_network_receive_errors_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "network_transmit_errors_total": 'sum by (pod) (rate(container_network_transmit_errors_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "network_receive_packets_dropped_total": 'sum by (pod) (rate(container_network_receive_packets_dropped_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "network_transmit_packets_dropped_total": 'sum by (pod) (rate(container_network_transmit_packets_dropped_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    # Disk metrics
    "fs_io_current": 'sum by (pod) (container_fs_io_current{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"})',
    "fs_io_seconds_total": 'sum by (pod) (rate(container_fs_io_time_seconds_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "fs_read_seconds": 'sum by (pod) (rate(container_fs_read_seconds_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "fs_read_bytes": 'sum by (pod) (rate(container_fs_reads_bytes_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "fs_read_total": 'sum by (pod) (rate(container_fs_reads_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "fs_read_merged_total": 'sum by (pod) (rate(container_fs_reads_merged_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "fs_write_seconds": 'sum by (pod) (rate(container_fs_write_seconds_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "fs_write_bytes": 'sum by (pod) (rate(container_fs_writes_bytes_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "fs_write_total": 'sum by (pod) (rate(container_fs_writes_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "fs_write_merged_total": 'sum by (pod) (rate(container_fs_writes_merged_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "fs_sector_reads_total": 'sum by (pod) (rate(container_fs_sector_reads_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
    "fs_sector_writes_total": 'sum by (pod) (rate(container_fs_sector_writes_total{name=~".+", namespace="tt", job="kubelet", service="kube-prometheus-stack-kubelet"}[1m]))',
}


def parse_response(metric_name: str, rsp: Dict) -> Optional[pd.DataFrame]:
    try:
        data = rsp["data"]
        assert data['resultType'] == 'matrix'
        records = []
        for series in data['result']:
            name = f"{series['metric']['pod']}##{metric_name}"
            for point in series['values']:
                records.append(point + [name])
        return pd.DataFrame(data=records, columns=['timestamp', 'value', 'name'])
    except KeyError as e:
        logger.error(f"parse response error for {metric_name=}", excetpion=e)
        return None


def collect_pod_metrics(config: Config):
    metric_df_list = []

    data_queue = Queue()

    def process_response_worker():
        while True:
            __metric_name, __rsp = data_queue.get()
            __rsp_df = parse_response(__metric_name, __rsp)
            if __rsp_df is not None:
                metric_df_list.append(__rsp_df)
            data_queue.task_done()

    def query_prometheus_and_process_response(__metric_name: str, __query: str):
        __rsp = requests.get(f"{config.prometheus_url}/api/v1/query_range", params={
            "query": __query,
            "start": int(config.begin_time.timestamp()),
            "end": int(config.end_time.timestamp()),
            "step": 60,
        })
        data_queue.put((__metric_name, __rsp.json()))

    threading.Thread(target=process_response_worker, daemon=True).start()
    with ThreadPoolExecutor(max_workers=10) as executor:
        for metric_name, query in INSTANCE_METRIC_QUERIES.items():
            logger.info(f"{metric_name=} {query=}")
            executor.submit(query_prometheus_and_process_response, metric_name, query)
    data_queue.join()
    metric_df = pd.concat(metric_df_list, ignore_index=True).astype({
        "timestamp": "int",
        "value": "float",
        "name": "str",
    })
    metric_df.to_pickle(str((config.output_dir / "pod_metrics.pkl").resolve()))
