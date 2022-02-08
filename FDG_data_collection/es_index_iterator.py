import json
import random
import threading
import time
from datetime import datetime
from pathlib import Path
from queue import Queue
from typing import Optional, Iterator, Dict, List

from elasticsearch import Elasticsearch
from loguru import logger
from tqdm import tqdm

from background_writer import BackgroundTextWriter


def query_index_by_time_range(
        index: str, es: Elasticsearch,
        min_time: Optional[datetime] = None, max_time: Optional[datetime] = None, step: int = 10000,
) -> Iterator[List[Dict]]:
    body = {
        "query": {"bool": {"must": [], "must_not": [], "should": []}},
        "sort": ['_doc'], "aggs": {}
    }

    time_range_body = {"range": {"startTimeMillis": {"format": "epoch_millis"}}}
    if min_time is not None:
        time_range_body["range"]["startTimeMillis"]["gte"] = int(min_time.timestamp() * 1000)
    if max_time is not None:
        time_range_body["range"]["startTimeMillis"]["lte"] = int(max_time.timestamp() * 1000)
    body["query"]["bool"]["must"].append(time_range_body)

    logger.debug(f"query_index_by_time_range body: {body}")
    rsp = None
    retry_counts = 0
    while rsp is None:
        try:
            rsp = es.search(index=index, body=dict(**body, size=step), scroll='5m', timeout='5m')
        except Exception as e:
            logger.warning(f"Exception in search: {e}. Retry")
            rsp = None
            retry_counts += 1
            time.sleep(random.randint(1, 10))
            if retry_counts > 100:
                raise RuntimeError("get search error for too many times")
    total = rsp['hits']['total']["value"]
    scroll_id = rsp['_scroll_id']
    scroll_size = total

    rets = rsp["hits"]["hits"]
    yield rets
    total -= len(rets)
    del rets, rsp

    with tqdm(total=total, desc=f"{index=} {min_time}-{max_time}") as pbar:
        while scroll_size > 0:
            try:
                _rsp = es.scroll(scroll_id=scroll_id, scroll='5m')
            except Exception as e:
                logger.warning(f"Exception in scroll: {e}. Retry")
                continue
            scroll_id = _rsp['_scroll_id']
            scroll_size = len(_rsp['hits']['hits'])
            pbar.update(scroll_size)
            total -= scroll_size
            _rets = _rsp["hits"]["hits"]
            yield _rets

    es.clear_scroll(scroll_id=scroll_id)


def query_index_by_time_range_and_save_to_file(
        index: str, es: Elasticsearch,
        output_file: Path,
        min_time: Optional[datetime] = None, max_time: Optional[datetime] = None,
        step: int = 10000,
):
    with open(output_file, 'w+') as f:
        with BackgroundTextWriter(f) as writer:
            span_count = 0
            for batch in query_index_by_time_range(index, es, min_time, max_time, step):
                for record in batch:
                    span_count += 1
                    writer(json.dumps(record['_source']))
            logger.debug("Waiting for background writer to finish, span_count: {}".format(span_count))
        logger.debug("Background writer finished")
