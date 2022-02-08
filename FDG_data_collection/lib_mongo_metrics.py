import threading
from queue import Queue
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

import pandas as pd
import requests
from loguru import logger

from config import Config

__all__ = ["collect_mongo_metrics"]

INSTANCE_METRIC_QUERIES = {
    # Operations
    'mongodb_mongod_metrics_ttl_deleted_documents_total': 'sum (rate(mongodb_mongod_metrics_ttl_deleted_documents_total[1m])) by (pod)',
    'mongodb_mongod_op_counters_repl_total': 'sum (rate(mongodb_mongod_op_counters_repl_total{type!~"(command|query|getmore)"}[1m])) by (pod)',
    'mongodb_op_counters_total': 'sum (rate(mongodb_op_counters_total{type!="command"}[1m])) by (pod)',
    'mongodb_document_operations': 'sum (rate(mongodb_mongod_metrics_document_total[1m])) by (pod)',
    'mongodb_queued_operations': 'sum (mongodb_mongod_global_lock_current_queue) by (pod)',
    # Connections
    'mongodb_connections': 'sum (mongodb_connections{state="current"}) by (pod)',
    # Cursors
    'mongodb_cursors': 'sum (mongodb_mongod_metrics_cursor_open) by (pod)',
    # Query efficiency
    'mongodb_document_query_efficiency': 'sum(increase(mongodb_mongod_metrics_query_executor_total{state="scanned_objects"}[5m])) by (pod) / (sum(increase(mongodb_mongod_metrics_document_total{state="returned"}[5m])) by (pod) + 1e-3)',
    'mongodb_index_query_efficiency': 'sum(increase(mongodb_mongod_metrics_query_executor_total{state="scanned"}[5m])) by (pod) / (sum(increase(mongodb_mongod_metrics_document_total{state="returned"}[5m])) by (pod) + 1e-3)',
    # Scanned and moved objects
    'mongodb_scanned': 'sum (rate(mongodb_mongod_metrics_query_executor_total{state="scanned"}[1m])) by (pod)',
    'mongodb_scanned_objects': 'sum (rate(mongodb_mongod_metrics_query_executor_total{state="scanned_objects"}[1m])) by (pod)',
    'mongodb_moved_objects': 'sum (rate(mongodb_mongod_metrics_record_moves_total[1m])) by (pod)',
    # Get last error
    'mongodb_get_last_error_write_time': 'sum (rate(mongodb_mongod_metrics_get_last_error_wtime_total_milliseconds[1m])) by (pod)',
    'mongodb_get_last_error_write_operations': 'sum (rate(mongodb_mongod_metrics_get_last_error_wtime_num_total[1m])) by (pod)',
    # Assert events
    'mongodb_assert_events': 'sum (rate(mongodb_asserts_total[1m])) by (pod)',
    # Page faults
    'mongodb_page_faults': 'sum (rate(mongodb_extra_info_page_faults_total[1m])) by (pod)',
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


def collect_mongo_metrics(config: Config):
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
    metric_df.to_pickle(str((config.output_dir / "mongo_metrics.pkl").resolve()))
