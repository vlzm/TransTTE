---
title: "Training"
weight: 5
bookCollapseSection: true
math: true
---

# Training

This page describes how the TransTTE checkpoints shipped with the repository were trained.
For turning raw road graphs and trips into the tensors the model consumes, see
[Data Preparation]({{< relref "/docs/training/data-preparation" >}}).

> ⚠️ There is **no standalone training script** in this repository. Training was run through
> the **fairseq CLI** against the vendored, modified Graphormer under
> `graphormer/app/graphormer_repo/`. What is published here is the **evaluation pipeline**
> plus the **trained checkpoints**
> (`graphormer/app/models/{abakan,omsk}/checkpoint_{best,last}.pt`); training is reproduced
> by driving fairseq over the registered PyG datasets.

## Framework

The model is built on **[fairseq](https://github.com/facebookresearch/fairseq)**, which is
**source-built** during the Graphormer Docker image build by
[`install.sh`]({{< relref "/docs/running/graphormer" >}}) — fairseq is cloned into
`graphormer_repo/` and installed editable. On top of fairseq, the Graphormer task,
criterion, and model live under `graphormer/app/graphormer_repo/graphormer/`.

## Best configuration

| Setting | Value |
|--|--|
| Architecture | **Graphormer-SLIM** |
| Layers \\(L\\) | **12** |
| Hidden dimension \\(d\\) | **80** |
| Optimizer | **AdamW** |

The reimplementation exploits a property specific to road trips: the **spatial-encoding**
bias (the shortest-path distance between nodes, see the
[Method]({{< relref "/docs/research/method" >}}) page) is shared across attention layers,
so it is **cached** rather than recomputed at every layer. This alone sped up training by
**almost 10×**.

## Hardware and time

| | |
|--|--|
| GPUs | **5× Tesla V100** |
| RAM | **460 GB** |
| Training time (TransTTE) | **2.5–5 hours** |

For comparison, the baselines took longer to train: **WDR ≈ 7 h**, **MURAT ≈ 5.5 h**. See
[Results]({{< relref "/docs/research/results" >}}) for the accuracy those runs produced.

## Datasets as fairseq inputs

The two city road graphs are registered as **PyG datasets** so fairseq can iterate over
them:

- `graphormer/app/graphormer_repo/graphormer/data/pyg_datasets/mydata_abakan.py`
- `graphormer/app/graphormer_repo/graphormer/data/pyg_datasets/mydata_omsk.py`

Graph objects are assembled by
[`data_class.py`](https://github.com/vlzm/TransTTE/blob/main/graphormer/app/data_class.py)
(`single_geo_Abakan`, `full_geo_Abakan`, `GraphormerPYGDataset_predict`, …), and the
evaluation iterator that produces per-edge weights is wired in
[`evaluate_points.py`](https://github.com/vlzm/TransTTE/blob/main/graphormer/app/evaluate_points.py).
That same eval path is what the
[Graphormer service]({{< relref "/docs/architecture/graphormer-service" >}}) runs to serve
`POST /get_weights`.
