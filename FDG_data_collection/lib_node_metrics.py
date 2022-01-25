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
    # "memory_inactive_bytes": 'node_memory_Inactive_bytes{job="node-exporter"}',
    # "memory_active_bytes": 'node_memory_Active_bytes{job="node-exporter"}',
    # "memory_committed_AS_bytes": 'node_memory_Committed_AS_bytes{job="node-exporter"}',
    # "memory_commit_limit_bytes": 'node_memory_CommitLimit_bytes{job="node-exporter"}',
    # "memory_inactive_file_bytes": 'node_memory_Inactive_file_bytes{job="node-exporter"}',
    # "memory_inactive_anon_bytes": 'node_memory_Inactive_anon_bytes{job="node-exporter"}',
    # "memory_active_file_bytes": 'node_memory_Active_file_bytes{job="node-exporter"}',
    # "memory_active_anon_bytes": 'node_memory_Active_anon_bytes{job="node-exporter"}',
    # "memory_writeback_bytes": 'node_memory_Writeback_bytes{job="node-exporter"}',
    # "memory_writeback_tmp_bytes": 'node_memory_WritebackTmp_bytes{job="node-exporter"}',
    # "memory_dirty_bytes": 'node_memory_Dirty_bytes{job="node-exporter"}',
    # "memory_mapped_bytes": 'node_memory_Mapped_bytes{job="node-exporter"}',
    # "memory_shmem_bytes": 'node_memory_Shmem_bytes{job="node-exporter"}',
    # "memory_shmem_huge_pages_bytes": 'node_memory_ShmemHugePages_bytes{job="node-exporter"}',
    # "memory_shmem_pmd_mapped_bytes": 'node_memory_ShmemPmdMapped_bytes{job="node-exporter"}',
    # "memory_S_unreclaim_bytes": 'node_memory_SUnreclaim_bytes{job="node-exporter"}',
    # "memory_S_reclaimable_bytes": 'node_memory_SReclaimable_bytes{job="node-exporter"}',
    # "memory_Vmalloc_chunk_bytes": 'node_memory_VmallocChunk_bytes{job="node-exporter"}',
    # "memory_Vmalloc_total_bytes": 'node_memory_VmallocTotal_bytes{job="node-exporter"}',
    # "memory_Vmalloc_used_bytes": 'node_memory_VmallocUsed_bytes{job="node-exporter"}',
    # "memory_anon_huge_pages_bytes": 'node_memory_AnonHugePages_bytes{job="node-exporter"}',
    # "memory_anon_pages_bytes": 'node_memory_AnonPages_bytes{job="node-exporter"}',
    # "memory_kernel_stack_bytes": 'node_memory_KernelStack_bytes{job="node-exporter"}',
    # "memory_per_cpu_bytes": 'node_memory_Percpu_bytes{job="node-exporter"}',
    # "memory_huge_pages_bytes": 'node_memory_HugePages_Total{job="node-exporter"}',
    # "memory_huge_page_size_bytes": 'node_memory_Hugepagesize_bytes{job="node-exporter"}',
    # "memory_direct_map_1G_bytes": 'node_memory_DirectMap1G_bytes{job="node-exporter"}',
    # "memory_direct_map_2M_bytes": 'node_memory_DirectMap2M_bytes{job="node-exporter"}',
    # "memory_direct_map_4K_bytes": 'node_memory_DirectMap4k_bytes{job="node-exporter"}',
    # "memory_unevitable_bytes": 'node_memory_Unevictable_bytes{job="node-exporter"}',
    # "memory_Mlocked_bytes": 'node_memory_Mlocked_bytes{job="node-exporter"}',
    # "memory_pages_in": 'rate(node_vmstat_pgpgin{job="node-exporter"}[1m])',
    # "memory_pages_out": 'rate(node_vmstat_pgpgout{job="node-exporter"}[1m])',
    # "memory_pages_fault": 'rate(node_vmstat_pgfault{job="node-exporter"}[1m])',
    # "memory_pages_major_fault": 'rate(node_vmstat_pgmajfault{job="node-exporter"}[1m])',
    # "memory_pages_minor_fault": 'rate(node_vmstat_pgfault{job="node-exporter"}[1m]) - rate(node_vmstat_pgmajfault{job="node-exporter"}[1m])',
    ## Network metrics

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
