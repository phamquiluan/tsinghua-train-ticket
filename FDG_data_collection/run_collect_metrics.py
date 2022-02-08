from loguru import logger
from pyprof import profile

from config import Config
from lib_jvm_metrics import collect_jvm_metrics
from lib_mongo_metrics import collect_mongo_metrics
from lib_pod_metrics import collect_pod_metrics
from lib_spans import collect_service_metrics
from lib_node_metrics import collect_node_metrics


@profile
def collect_metrics(config: Config):
    logger.add(config.output_dir / "collect_metrics.log", mode="a")
    collect_service_metrics(config)
    collect_node_metrics(config)
    collect_pod_metrics(config)
    collect_jvm_metrics(config)
    collect_mongo_metrics(config)


if __name__ == '__main__':
    with profile("main", report_printer=lambda _: logger.info(f"\n{_}")):
        collect_metrics(Config().parse_args())
