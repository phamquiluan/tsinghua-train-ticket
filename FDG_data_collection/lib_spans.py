import json
import logging
import re
from collections import defaultdict
from pprint import pformat
from typing import Dict

import pandas as pd
from pandas import DatetimeTZDtype
from pyprof import profile
from tqdm import tqdm

from es_index_iterator import query_index_by_time_range_and_save_to_file
from config import Config
from utils import tags_dict


@profile
def collect_spans(config: Config):
    query_index_by_time_range_and_save_to_file(
        es=config.es, index=config.es_index,
        min_time=config.begin_time, max_time=config.end_time,
        step=1000,
        output_file=config.output_dir / "spans.txt"
    )


@profile
def collect_traces_from_spans(config: Config):
    traces: defaultdict[str, Dict[str, Dict]] = defaultdict(dict)
    with open(config.output_dir / "spans.txt", "r") as f:
        for line in tqdm(f, desc="reading spans"):
            span = json.loads(line)
            trace_id = span["traceID"]
            span_id = span["spanID"]
            parent_span_id = None
            for reference in span['references']:
                if reference['refType'] == 'CHILD_OF':
                    parent_span_id = reference['spanID']
            tags = tags_dict(span['tags'])
            traces[trace_id][span_id] = {
                "spanID": span_id,
                "traceID": trace_id,
                "timestamp": span["startTime"] * 1e3,
                "serviceName": span['process']['serviceName'],
                "operationName": span['operationName'],
                'parentSpanID': parent_span_id,
                "duration": span['duration'],
                "error": is_span_error(tags),
                "kind": tags.get("span.kind", None),
            }
    traces_df = pd.DataFrame.from_records(
        sum([list(trace.values()) for trace in traces.values()], [])
    ).astype({
        "spanID": "string",
        "traceID": "string",
        "timestamp": "datetime64[ns, UTC]",
        "serviceName": "category",
        "operationName": "category",
        "parentSpanID": "string",
        "duration": "float",
        "error": "bool",
        "kind": "category",
    })
    traces_df["timestamp"] = traces_df['timestamp'].dt.tz_convert("Asia/Shanghai")
    traces_df.to_pickle(str((config.output_dir / "traces.pkl").resolve()))


def is_span_error(tags: dict) -> bool:
    if (key := 'status.code') in tags:
        return int(tags[key]) != 0
    elif (key := 'http.status_code') in tags:
        return str(tags[key])[0] in {"4", "5"}
    elif (key := 'grpc.status_code') in tags or (key := 'otel.status_code') in tags:
        return str(tags[key]).lower() != "ok"
    elif (key := "status.message") in tags:
        return bool(re.match(r"(?i)(exception)|(error)|(fail)", tags[key].lower()))
    else:
        logging.error("Unrecognized tags: {}".format(pformat(tags.keys())))
        raise RuntimeError(f"status code key not found in tags: {tags.keys()}")


@profile
def collect_service_metrics(config):
    collect_spans(config)
    collect_traces_from_spans(config)
    traces_df = pd.read_pickle(str((config.output_dir / "traces.pkl").resolve()))
    traces_df['timestamp'] = traces_df['timestamp'].dt.floor('min').dt.to_pydatetime()
    traces_df['timestamp'] = traces_df['timestamp'].map(lambda _: int(_.timestamp()))
    children_durations = traces_df.groupby("parentSpanID")['duration'].sum()
    traces_df['process_time'] = traces_df.apply(lambda x: x['duration'] - children_durations.get(x['spanID'], 0), axis=1)

    groupby = traces_df.groupby(['serviceName', 'timestamp'])
    count_df = groupby.size().reset_index(name='value')
    count_df['metric_kind'] = 'count'
    cost_df = groupby['duration'].mean().map(lambda _: _ * 1e-3).reset_index(name='value')
    cost_df['metric_kind'] = 'cost'
    proc_df = groupby['process_time'].mean().map(lambda _: _ * 1e-3).reset_index(name='value')
    proc_df['metric_kind'] = 'proc'
    succ_rate_df = (1 - groupby['error'].sum() / groupby.size()).reset_index(name='value')
    succ_rate_df['metric_kind'] = 'succ_rate'

    ret_df = pd.concat([count_df, cost_df, proc_df, succ_rate_df])
    ret_df['name'] = ret_df.apply(lambda _: f"{_['serviceName']}##{_['metric_kind']}", axis=1)
    ret_df.to_pickle(config.output_dir / 'metrics.pkl')