import pandas as pd
from loguru import logger
from pyprof import profile

from config import Config
from lib_spans import collect_traces_from_spans, collect_spans


@profile
def collect_business_metrics(config):
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


@profile
def collect_metrics(config: Config):
    collect_spans(config)
    collect_traces_from_spans(config)
    collect_business_metrics(config)


if __name__ == '__main__':
    with profile("main", report_printer=lambda _: logger.info(f"\n{_}")):
        collect_metrics(Config().parse_args())
