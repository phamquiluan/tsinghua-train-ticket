import gzip
import json
import logging
import re
from pprint import pformat

import pandas as pd
from pyprof import profile
from tqdm import tqdm

from config import Config
from es_index_iterator import query_index_by_time_range_and_save_to_file
from utils import tags_dict


@profile
def collect_spans(config: Config):
    with gzip.open(config.output_dir / "spans.txt.gz", "wt") as f:
        query_index_by_time_range_and_save_to_file(
            es=config.es, index=config.es_index,
            min_time=config.begin_time, max_time=config.end_time,
            output_file=f
        )


@profile
def collect_traces_from_spans(config: Config):
    data = {
        "spanID": [],
        "traceID": [],
        "timestamp": [],
        "serviceName": [],
        "operationName": [],
        "parentSpanID": [],
        "duration": [],
        "error": [],
        "kind": [],
        "pod": [],
    }
    with gzip.open(config.output_dir / "spans.txt.gz", "r") as f:
        for line in tqdm(f, desc="reading spans"):
            span = json.loads(line)
            trace_id = span["traceID"]
            span_id = span["spanID"]
            parent_span_id = None
            for reference in span['references']:
                if reference['refType'] == 'CHILD_OF':
                    parent_span_id = reference['spanID']
            tags = tags_dict(span['tags'])
            data["spanID"].append(span_id)
            data["traceID"].append(trace_id)
            data['timestamp'].append(span['startTime'] * 1e3)
            data["serviceName"].append(span['process']['serviceName'].split(".")[0])
            data['operationName'].append(span['operationName'])
            data['parentSpanID'].append(parent_span_id)
            data['duration'].append(span['duration'])
            data['error'].append(is_span_error(tags))
            data['kind'].append(tags.get("span.kind", None))
            try:
                data["pod"].append(tags.get("node_id", "x~x~unknown").split("~")[2].split(".")[0])
            except IndexError:
                data["pod"].append(None)
    traces_df = pd.DataFrame(data=data).astype({
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
        return False


@profile
def collect_service_metrics(config):
    collect_spans(config)
    collect_traces_from_spans(config)
    traces_df = pd.read_pickle(str((config.output_dir / "traces.pkl").resolve()))
    traces_df['timestamp'] = traces_df['timestamp'].dt.floor('min').dt.to_pydatetime()
    traces_df['timestamp'] = traces_df['timestamp'].map(lambda _: int(_.timestamp()))
    children_durations = traces_df.groupby("parentSpanID")['duration'].sum()
    traces_df['process_time'] = traces_df.apply(lambda x: x['duration'] - children_durations.get(x['spanID'], 0),
                                                axis=1)

    def get_business_metrics(attr="serviceName"):
        groupby = traces_df.groupby([attr, 'timestamp'])
        count_df = groupby.size().reset_index(name='value')
        count_df['metric_kind'] = 'count'
        cost_df = groupby['duration'].mean().map(lambda _: _ * 1e-3).reset_index(name='value')
        cost_df['metric_kind'] = 'cost'
        proc_df = groupby['process_time'].mean().map(lambda _: _ * 1e-3).reset_index(name='value')
        proc_df['metric_kind'] = 'proc'
        succ_rate_df = (1 - groupby['error'].sum() / groupby.size()).reset_index(name='value')
        succ_rate_df['metric_kind'] = 'succ_rate'

        ret_df = pd.concat([count_df, cost_df, proc_df, succ_rate_df])
        ret_df['name'] = ret_df.apply(lambda _: f"{_[attr]}##{_['metric_kind']}", axis=1)
        return ret_df
    service_metrics = get_business_metrics("serviceName")
    service_metrics.to_pickle(config.output_dir / 'service_business_metrics.pkl')
    pod_metrics = get_business_metrics("pod")
    pod_metrics.to_pickle(config.output_dir / 'pod_business_metrics.pkl')
