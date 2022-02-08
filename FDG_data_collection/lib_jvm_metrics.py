import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

import pandas as pd
import requests
from loguru import logger

from config import Config

__all__ = ["collect_jvm_metrics"]

INSTANCE_METRIC_QUERIES = {
    # Memory metrics
    'jvm_heap_memory_bytes_used': 'sum by (pod) (jvm_memory_bytes_used{area="heap"})',
    'jvm_nonheap_memory_bytes_used': 'sum by (pod) (jvm_memory_bytes_used{area="nonheap"})',
    'jvm_code_cache_memory_bytes_used': 'sum by (pod) (jvm_memory_pool_bytes_used{pool="Code Cache"})',
    'jvm_code_cache_memory_bytes_committed': 'sum by (pod) (jvm_memory_pool_bytes_committed{pool="Code Cache"})',
    'jvm_metaspace_memory_bytes_committed': 'sum by (pod) (jvm_memory_pool_bytes_committed{pool="Metaspace"})',
    'jvm_compressed_class_space_memory_bytes_committed': 'sum by (pod) (jvm_memory_pool_bytes_committed{pool="Compressed Class Space"})',
    'jvm_PS_eden_space_memory_bytes_committed': 'sum by (pod) (jvm_memory_pool_bytes_committed{pool="PS Eden Space"})',
    'jvm_PS_old_space_memory_bytes_committed': 'sum by (pod) (jvm_memory_pool_bytes_committed{pool="PS Old Gen"})',
    'jvm_PS_supervisor_space_memory_bytes_committed': 'sum by (pod) (jvm_memory_pool_bytes_committed{pool="PS Survivor Space"})',
    # GC metrics
    'jvm_GC_time': 'sum (increase(jvm_gc_collection_seconds_sum{}[1m])) by (pod)',
    'jvm_GC_count': 'sum (increase(jvm_gc_collection_seconds_count{}[1m])) by (pod)',
    # Thread metrics
    'jvm_current_threads': 'sum by (pod) (jvm_threads_current)',
    'jvm_daemon_threads': 'sum by (pod) (jvm_threads_daemon)',
    'jvm_deadlocked_threads': 'sum by (pod) (jvm_threads_deadlocked)',
    # Class loading metrics
    'jvm_class_loaded': 'sum by (pod) (jvm_classes_loaded)',
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


def collect_jvm_metrics(config: Config):
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
    print(metric_df.to_csv(sep="\t", float_format="%3.3f"))  ## TODO: DEBUG
    metric_df.to_pickle(str((config.output_dir / "jvm_metrics.pkl").resolve()))
