import os
from datetime import datetime, timedelta
from pathlib import Path

from dateutil.parser import parse as parse_datetime
from elasticsearch import Elasticsearch
from loguru import logger
from pytz import timezone
from tap import Tap


class Config(Tap):
    prometheus_url: str = os.environ.get('PROMETHEUS_URL', "http://lzy-k8s-1.cluster.peidan.me:9090")
    es_url: str = os.environ.get(
        'ES_URL', "http://elastic:1Je40I6x4Fu9T5mYXtk70K3l@lzy-k8s-1.cluster.peidan.me:9200"
    ),
    es_index: str = "jaeger-span-*"
    kube_config: str = os.environ.get('KUBECONFIG', "./kube.conf")
    begin_time: datetime = None
    end_time: datetime = None
    output_dir: Path = None

    # can only be set by the process_args method
    es: Elasticsearch = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, explicit_bool=True, **kwargs)

    def process_args(self) -> None:
        if self.end_time is None and self.begin_time is not None:
            logger.info("end_time is None, set it to begin_time + 1 hour")
            self.end_time = self.begin_time + timedelta(hours=1)
        elif self.end_time is not None and self.begin_time is None:
            logger.info("begin time is None, set it to end time - 1 hour")
            self.begin_time = self.end_time - timedelta(hours=1)
        elif self.end_time is None and self.begin_time is None:
            raise ValueError("begin_time and end_time are both None")
        self.begin_time = timezone("Asia/Shanghai").localize(self.begin_time)
        self.end_time = timezone("Asia/Shanghai").localize(self.end_time)
        self.end_time = self.end_time.replace(second=59, microsecond=999999)

        if self.output_dir is None:
            self.output_dir = Path(f"./collected_metrics/{self.begin_time.isoformat()}-{self.end_time.isoformat()}")
        logger.info(f"{self.output_dir=}")
        self.output_dir.mkdir(parents=True, exist_ok=True)

        assert self.es is None
        self.es = Elasticsearch(self.es_url)

    def configure(self) -> None:
        self.add_argument('--begin_time', type=parse_datetime)
        self.add_argument('--end_time', type=parse_datetime)
        self.add_argument('--output_dir', type=Path)