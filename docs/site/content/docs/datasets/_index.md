---
title: "Datasets"
weight: 4
bookToc: true
---

# Datasets

TransTTE is trained and served on two Russian cities, **Abakan** and **Omsk**. Each is a
road graph plus a set of real trips. For every trip there are two possible targets: the
**real travel time** (the quantity this study estimates) and the **real trip length**.

> The Omsk dataset is a contribution of the paper — a new, large TTE benchmark released
> alongside the model. The data is for research use only; requests go to the address in the
> [repository README](https://github.com/Vloods/TransTTE_demo).

## Road network

Both cities are represented as directed road graphs — intersections are nodes, road
segments are edges. Omsk is roughly 3–4× the size of Abakan.

| | Abakan | Omsk |
|--|--:|--:|
| Nodes | 65 524 | 231 688 |
| Edges | 340 012 | 1 149 492 |
| Clustering | 0.5278 | 0.53 |
| Usage median | 12 | 8 |

The **edge count is the length of every weight list** in the system — 340 012 for Abakan,
1 149 492 for Omsk. That is the ordering the [weight-handoff contract]({{< relref
"/docs/architecture/weight-contract" >}}) pins down.

## Trips

| | Abakan | Omsk |
|--|--:|--:|
| Trips number | 119 986 | 120 000 |
| Coverage | 0.535 | 0.392 |
| Average time (s) | 433.61 | 622.67 |
| Average length (m) | 3 656.34 | 4 268.72 |

*Coverage* is the fraction of graph edges touched by at least one trip — the two cities are
comparable in trip count, but Abakan's smaller graph is more densely covered.

## Collection and filtering

Trips were collected over a one-month window starting **1 December 2020**. Raw GPS trips are
noisy, so they are filtered before use — trips are dropped by:

- **route rebuild count** (how often the navigator re-planned mid-trip),
- **minimum and maximum trip length**, and
- **total trip time** bounds.

What survives is map-matched onto the road graph to produce the node/edge sequences the
model and the ETA network consume.

## Features

Beyond the graph structure, the serving path enriches routes with auxiliary features (used
by the [neural ETA]({{< relref "/docs/architecture/eta-paths" >}})):

- **Node embeddings** — DeepGraphInfomax + GraphSAGE embeddings per node (`dgi_*` CSVs),
  learned offline; see [Training → Data Preparation]({{< relref
  "/docs/training/data-preparation" >}}).
- **Weather** — hourly meteorological records (`meteoData.csv`).
- **Time features** — hour-of-day bucket and weekday/weekend flag.

## How the data flows into the system

1. The graph is registered as a PyG dataset (`mydata_abakan.py`, `mydata_omsk.py`) and the
   [Graphormer model]({{< relref "/docs/architecture/graphormer-service" >}}) predicts a
   travel time per edge.
2. Those per-edge weights, plus the derived routing objectives, are cached as pickles.
3. The [backend]({{< relref "/docs/architecture/backend-service" >}}) loads the graph and
   weights to route and estimate ETAs.

None of these binary assets live in git — see [Data & Model Assets]({{< relref
"/docs/running/data-assets" >}}) for where to download them.
