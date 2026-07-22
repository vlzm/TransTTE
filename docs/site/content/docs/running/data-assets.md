---
title: "Data Assets"
weight: 3
bookToc: true
---

# Data Assets

Neither service runs without large binary assets that are **not in git** — they are
downloaded separately. When a load fails, it is almost always a **missing or renamed asset**
under `data/` or `models/`, not a code bug. File paths are hardcoded relative to each
script's location.

## What to download

| Bundle | Download | Extract to |
|--|--|--|
| Backend data | [Yandex.Disk](https://disk.yandex.ru/d/NHj3ukteUGn-dA) | `backend/app/data/` |
| Graphormer models | [Yandex.Disk](https://disk.yandex.ru/d/rQCIJs_7Q7Li6g) | `graphormer/app/models/` |

## Backend data (`backend/app/data/`)

| File / folder | What it is | Used by |
|--|--|--|
| `SimpleTTE.pth` | `FFNet` weights (152-input feed-forward net) | Neural ETA (Abakan non-Graphormer) |
| `dijkstra.pickle`, `graph_omsk.pkl` | igraph road graphs | Shortest-path routing |
| `clear_nodes.pkl`, `clear_nodes_omsk.pkl` | Node coordinate tables | Snapping endpoints to nodes (`BallTree`) |
| `balltree.pkl` | Prebuilt haversine `BallTree` | Nearest-node lookup |
| `dgi_*.csv` | DGI + GraphSAGE node embeddings | Neural ETA feature vector |
| `meteoData.csv` | Weather data | Neural ETA feature vector |
| `graphormer_weights/` | `weights_abakan.pickle`, `weights_omsk.pickle` | `graphormer_weights` route variant |
| `weights_abakan/`, `weights_omsk/` | Per-objective `*.pkl` weight lists (dist / green / hist / …) | One route `type` each |

Each file in `weights_{city}/` is an **edge-aligned weight list** that becomes a separate
routing objective in the `/get_path` response — see
[Routing Objectives]({{< relref "/docs/architecture/routing-objectives" >}}). The
`graphormer_weights/` pickles are the output of the
[Graphormer service]({{< relref "/docs/running/graphormer" >}}); the ordering must match the
graph's edge order (the [weight contract]({{< relref "/docs/architecture/weight-contract" >}})).

## Graphormer models (`graphormer/app/models/`)

```
graphormer/app/models/
├── abakan/
│   ├── checkpoint_best.pt
│   └── checkpoint_last.pt
└── omsk/
    ├── checkpoint_best.pt
    └── checkpoint_last.pt
```

One trained checkpoint per city — loaded to produce the per-edge weights.

## What breaks when something is missing

- **Backend won't start** → a graph, embedding, or weight file is absent or renamed under
  `backend/app/data/`. Check the traceback for the exact path.
- **A routing `type` is missing from the response** → its `*.pkl` is not in
  `data/weights_{city}/` (or `data/graphormer_weights/`).
- **Graphormer `/get_weights` fails** → the checkpoint under
  `graphormer/app/models/{city}/` is missing.

> The datasets themselves are for **research use only**. To incorporate the data in your own
> study, send a request to the address in the
> [repository README](https://github.com/vlzm/TransTTE).
