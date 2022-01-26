import threading
from queue import Queue
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
    "cpu_busy_system": 'sum by (instance)(rate(node_cpu_seconds_total{mode="system",job="node-exporter"}[1m])) * 100',
    "cpu_busy_user": 'sum by (instance)(rate(node_cpu_seconds_total{mode="user",job="node-exporter"}[1m])) * 100',
    "cpu_busy_user_nice": 'sum by (instance)(rate(node_cpu_seconds_total{mode="nice",job="node-exporter"}[1m])) * 100',
    "cpu_busy_IOWait": 'sum by (instance)(rate(node_cpu_seconds_total{mode="iowait",job="node-exporter"}[1m])) * 100',
    "cpu_busy_IRQs": 'sum by (instance)(rate(node_cpu_seconds_total{mode=~".*irq",job="node-exporter"}[1m])) * 100',
    "cpu_busy_softIRQs": 'sum by (instance)(rate(node_cpu_seconds_total{mode="softirq",job="node-exporter"}[1m])) * 100',
    "cpu_busy_steal": 'sum by (instance)(rate(node_cpu_seconds_total{mode="steal",job="node-exporter"}[1m])) * 100',
    "cpu_busy_guest": 'sum by (instance)(rate(node_cpu_seconds_total{mode="guest",job="node-exporter"}[1m])) * 100',
    "cpu_busy_others": 'sum by (instance)(rate(node_cpu_seconds_total{mode!="idle",mode!="user",mode!="system",mode!="iowait",mode!="irq",mode!="softirq",job="node-exporter"}[1m])) * 100',
    ## Memory metrics
    "memory_inactive_bytes": 'node_memory_Inactive_bytes{job="node-exporter"}',
    "memory_active_bytes": 'node_memory_Active_bytes{job="node-exporter"}',
    "memory_committed_AS_bytes": 'node_memory_Committed_AS_bytes{job="node-exporter"}',
    "memory_commit_limit_bytes": 'node_memory_CommitLimit_bytes{job="node-exporter"}',
    "memory_inactive_file_bytes": 'node_memory_Inactive_file_bytes{job="node-exporter"}',
    "memory_inactive_anon_bytes": 'node_memory_Inactive_anon_bytes{job="node-exporter"}',
    "memory_active_file_bytes": 'node_memory_Active_file_bytes{job="node-exporter"}',
    "memory_active_anon_bytes": 'node_memory_Active_anon_bytes{job="node-exporter"}',
    "memory_writeback_bytes": 'node_memory_Writeback_bytes{job="node-exporter"}',
    "memory_writeback_tmp_bytes": 'node_memory_WritebackTmp_bytes{job="node-exporter"}',
    "memory_dirty_bytes": 'node_memory_Dirty_bytes{job="node-exporter"}',
    "memory_mapped_bytes": 'node_memory_Mapped_bytes{job="node-exporter"}',
    "memory_shmem_bytes": 'node_memory_Shmem_bytes{job="node-exporter"}',
    "memory_shmem_huge_pages_bytes": 'node_memory_ShmemHugePages_bytes{job="node-exporter"}',
    "memory_shmem_pmd_mapped_bytes": 'node_memory_ShmemPmdMapped_bytes{job="node-exporter"}',
    "memory_S_unreclaim_bytes": 'node_memory_SUnreclaim_bytes{job="node-exporter"}',
    "memory_S_reclaimable_bytes": 'node_memory_SReclaimable_bytes{job="node-exporter"}',
    "memory_Vmalloc_chunk_bytes": 'node_memory_VmallocChunk_bytes{job="node-exporter"}',
    "memory_Vmalloc_total_bytes": 'node_memory_VmallocTotal_bytes{job="node-exporter"}',
    "memory_Vmalloc_used_bytes": 'node_memory_VmallocUsed_bytes{job="node-exporter"}',
    "memory_anon_huge_pages_bytes": 'node_memory_AnonHugePages_bytes{job="node-exporter"}',
    "memory_anon_pages_bytes": 'node_memory_AnonPages_bytes{job="node-exporter"}',
    "memory_kernel_stack_bytes": 'node_memory_KernelStack_bytes{job="node-exporter"}',
    "memory_per_cpu_bytes": 'node_memory_Percpu_bytes{job="node-exporter"}',
    "memory_huge_pages_bytes": 'node_memory_HugePages_Total{job="node-exporter"}',
    "memory_huge_page_size_bytes": 'node_memory_Hugepagesize_bytes{job="node-exporter"}',
    "memory_direct_map_1G_bytes": 'node_memory_DirectMap1G_bytes{job="node-exporter"}',
    "memory_direct_map_2M_bytes": 'node_memory_DirectMap2M_bytes{job="node-exporter"}',
    "memory_direct_map_4K_bytes": 'node_memory_DirectMap4k_bytes{job="node-exporter"}',
    "memory_unevitable_bytes": 'node_memory_Unevictable_bytes{job="node-exporter"}',
    "memory_Mlocked_bytes": 'node_memory_Mlocked_bytes{job="node-exporter"}',
    "memory_pages_in": 'rate(node_vmstat_pgpgin{job="node-exporter"}[1m])',
    "memory_pages_out": 'rate(node_vmstat_pgpgout{job="node-exporter"}[1m])',
    "memory_pages_fault": 'rate(node_vmstat_pgfault{job="node-exporter"}[1m])',
    "memory_pages_major_fault": 'rate(node_vmstat_pgmajfault{job="node-exporter"}[1m])',
    "memory_pages_minor_fault": 'rate(node_vmstat_pgfault{job="node-exporter"}[1m]) - rate(node_vmstat_pgmajfault{job="node-exporter"}[1m])',
    ## Disk metrics
    "disk_reads_completed_total": 'sum by (instance)(rate(node_disk_reads_completed_total{job="node-exporter"}[1m]))',
    "disk_writes_completed_total": 'sum by (instance)(rate(node_disk_writes_completed_total{job="node-exporter"}[1m]))',
    "disk_read_bytes_total": 'sum by (instance)(rate(node_disk_read_bytes_total{job="node-exporter"}[1m]))',
    "disk_written_bytes_total": 'sum by (instance)(rate(node_disk_written_bytes_total{job="node-exporter"}[1m]))',
    "disk_average_read_wait_time": 'sum by (instance)(rate(node_disk_read_time_seconds_total{job="node-exporter"}[1m]) / rate(node_disk_reads_completed_total{job="node-exporter"}[1m]))',
    "disk_average_write_wait_time": 'sum by (instance)(rate(node_disk_write_time_seconds_total{job="node-exporter"}[1m]) / rate(node_disk_writes_completed_total{job="node-exporter"}[1m]))',
    "disk_average_queue_size": 'sum by (instance)(rate(node_disk_io_time_weighted_seconds_total{job="node-exporter"}[1m]))',
    ## Network metrics
    "network_receive_packets_per_second": 'sum by (instance) (rate(node_network_receive_packets_total{job="node-exporter"}[1m]))',
    "network_transmit_packets_per_second": 'sum by (instance) (rate(node_network_transmit_packets_total{job="node-exporter"}[1m]))',
    "network_receive_error_packets": 'sum by (instance) (rate(node_network_receive_errs_total{job="node-exporter"}[1m]))',
    "network_transmit_error_packets": 'sum by (instance) (rate(node_network_transmit_errs_total{job="node-exporter"}[1m]))',
    "network_receive_drop_packets": 'sum by (instance) (rate(node_network_receive_drop_total{job="node-exporter"}[1m]))',
    "network_transmit_drop_packets": 'sum by (instance) (rate(node_network_transmit_drop_total{job="node-exporter"}[1m]))',
    "network_receive_compressed_packets": 'sum by (instance) (rate(node_network_receive_compressed_total{job="node-exporter"}[1m]))',
    "network_transmit_compressed_packets": 'sum by (instance) (rate(node_network_transmit_compressed_total{job="node-exporter"}[1m]))',
    "network_udp_in_errors": 'sum by (instance) (rate(node_netstat_Udp_InErrors{job="node-exporter"}[1m]))',
    "network_udp_no_ports": 'sum by (instance) (rate(node_netstat_Udp_NoPorts{job="node-exporter"}[1m]))',
    "network_udp_lite_in_errors": 'sum by (instance) (rate(node_netstat_UdpLite_InErrors{job="node-exporter"}[1m]))',
    "network_udp_rcv_buf_errors": 'sum by (instance) (rate(node_netstat_Udp_RcvbufErrors{job="node-exporter"}[1m]))',
    "network_udp_snd_buf_errors": 'sum by (instance) (rate(node_netstat_Udp_SndbufErrors{job="node-exporter"}[1m]))',
    "network_tcp_in_segs": 'sum by (instance) (rate(node_netstat_Tcp_InSegs{job="node-exporter"}[1m]))',
    "network_tcp_out_segs": 'sum by (instance) (rate(node_netstat_Tcp_OutSegs{job="node-exporter"}[1m]))',

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

    data_queue = Queue()

    def process_response_worker():
        while True:
            __metric_name, __rsp = data_queue.get()
            __rsp_df = parse_response(metric_name, __rsp)
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
        data_queue.put((metric_name, __rsp.json()))

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
    metric_df.to_pickle(str((config.output_dir / "node_metrics.pkl").resolve()))
