
# Train Ticket：A Benchmark Microservice System

This repo contains the source code, forked from https://github.com/fudanselab/train-ticket, and the deployment and data collection scripts used for [our FSE'22 paper](https://github.com/lizeyan/DejaVu).


We deployed train-ticket on a five-node cluster. The nodes were named as `lzy-k8s-1.cluster.peidan.me`, `lzy-k8s-2.cluster.peidan.me`, etc.
We built the images of micro-services ourselves and pushed them to a private registry (`docker.peidan.me`).
We used crontab to periodically run fault injection tasks and collect data automatically.


## File Description
|Path|Description|
|---|---|
|`chaos`|Fault injection scripts|
|`deployment/kubernetes-manifests/k8s-with-jaeger`|The deployment scripts we used|
|`deployment/*`|Not used. The same as upstream repo.|
|`FDG_data_collection/`|Data collection scripts|
|`conduct_one_exp_and_collect_metrics.py`|The runnable script conducts a fault injection task and collects the corresponding metrics|
|`ts-*`|The micro-services' source code|
|`workload/`|Load generator scripts|
|`restart.sh`|A runnable script to delete and redeploy train-ticket|
|`crontab.conf`|Crontab configuration to periodically run fault injection tasks|



## Citation
``` bibtex
@inproceedings{li2022actionable,
  title = {Actionable and Interpretable Fault Localization for Recurring Failures in Online Service Systems},
  booktitle = {Proceedings of the 2022 30th {{ACM Joint Meeting}} on {{European Software Engineering Conference}} and {{Symposium}} on the {{Foundations}} of {{Software Engineering}}},
  author = {Li, Zeyan and Zhao, Nengwen and Li, Mingjie and Lu, Xianglin and Wang, Lixin and Chang, Dongdong and Cao, Li and Zhang, Wenchi and Sui, Kaixin and Wang, Yanhua and Du, Xu and Duan, Guoqing and Pei, Dan},
  year = {2022},
  month = nov,
  series = {{{ESEC}}/{{FSE}} 2022}
}
```
