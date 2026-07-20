---
title: "Data Preparation"
weight: 1
bookToc: true
---

# Data Preparation

Everything the model and the backend consume is produced offline by the notebooks and
scripts under `preprocessing/` and `algorithms/`. These are **research artifacts**, separate
from the two serving apps — you do not need them to run the demo, only to rebuild the
datasets or retrain. The [Datasets]({{< relref "/docs/datasets" >}}) page covers the
resulting numbers; this page covers how they are built.

## Building the road graphs and features

| Notebook | Produces |
|--|--|
| [`preprocessing/graph_preprocessing.ipynb`](https://github.com/Vloods/TransTTE_demo/blob/main/preprocessing/graph_preprocessing.ipynb) | The city road graphs (nodes / edges) fed to Graphormer and to igraph. |
| [`preprocessing/ETA_additional_features_processing.ipynb`](https://github.com/Vloods/TransTTE_demo/blob/main/preprocessing/ETA_additional_features_processing.ipynb) | The extra ETA features (geometry, time-of-day, etc.). |
| [`preprocessing/gismeteo_parser.ipynb`](https://github.com/Vloods/TransTTE_demo/blob/main/preprocessing/gismeteo_parser.ipynb) | Weather data (feeds `meteoData.csv`). |

Trip filtering (rebuild count, min/max length, total time) and the two targets — real
travel time and real trip length — are described on the
[Datasets]({{< relref "/docs/datasets" >}}) page.

## Node embeddings (DGI + GraphSAGE)

The backend's **neural ETA** path
([`FFNet`]({{< relref "/docs/architecture/eta-paths" >}})) consumes per-node embeddings, not
raw coordinates. Those embeddings are trained with **Deep Graph Infomax (DGI)** over a
**GraphSAGE** encoder in
[`algorithms/stellar_deepgraphinfomax-graphsage.ipynb`](https://github.com/Vloods/TransTTE_demo/blob/main/algorithms/stellar_deepgraphinfomax-graphsage.ipynb).

The output is written as `dgi_*` CSV files that the backend loads at startup — for example
`dgi_sage_abakan_5_5_5_relu_relu_relu_200e_mean_pool_0.0114.csv` under
`backend/app/data/`. The filename encodes the GraphSAGE layer sizes, activations, epochs,
and aggregation used to train it.

## Auxiliary scripts

- [`algorithms/parse_weather.py`](https://github.com/Vloods/TransTTE_demo/blob/main/algorithms/parse_weather.py),
  [`algorithms/get_samples.py`](https://github.com/Vloods/TransTTE_demo/blob/main/algorithms/get_samples.py)
  — weather scraping and trip sampling.
- [`algorithms/inference_ETA.py`](https://github.com/Vloods/TransTTE_demo/blob/main/algorithms/inference_ETA.py),
  [`algorithms/regression.ipynb`](https://github.com/Vloods/TransTTE_demo/blob/main/algorithms/regression.ipynb)
  — the regression-based ETA baseline. Note this baseline uses **TensorFlow/Keras**, unlike
  the serving `FFNet`, which is **PyTorch**.

## Where these outputs go

| Artifact | Consumed by |
|--|--|
| Road graphs | Graphormer PyG datasets + backend `igraph` graphs (`dijkstra.pickle`, `graph_omsk.pkl`) |
| `dgi_*` CSV embeddings | Backend neural ETA ([`FFNet`]({{< relref "/docs/architecture/eta-paths" >}})) |
| `meteoData.csv` | Backend ETA feature vector |
| Per-edge weight lists | Backend routing — see the [weight contract]({{< relref "/docs/architecture/weight-contract" >}}) |

See [Data Assets]({{< relref "/docs/running/data-assets" >}}) for where each of these files
must live on disk to run the services.
