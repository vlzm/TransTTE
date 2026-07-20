---
title: "ETA Paths"
weight: 4
bookToc: true
---

# Two ETA Paths

Once the backend has a route, it has to turn that route into an **estimated time of
arrival**. It does this in one of two ways, depending on the weight variant. Know which one
you are touching — they share no code.

`return_path` in
[`backend/app/app.py`](https://github.com/Vloods/TransTTE_demo/blob/main/backend/app/app.py)
picks the path per variant:

| Variant | ETA method | Where |
|--|--|--|
| Abakan non-Graphormer (`dist`, `green`, `hist`, …) | Neural ETA (`FFNet`) | `ETAInf.forward` |
| Abakan `graphormer_weights` | Weighted sum | `get_shortest_path_grph` |
| All Omsk variants (incl. `graphormer_weights`) | Weighted sum | `get_shortest_path_grph` |

## 1. Neural ETA — `FFNet`

For the Abakan non-Graphormer variants the ETA comes from a small feed-forward network,
**`FFNet`** (152 inputs → 128 → 1, ReLU), defined in
[`ml.py`](https://github.com/Vloods/TransTTE_demo/blob/main/backend/app/ml.py) and driven
by `ETAInf.forward` in
[`eta_inference.py`](https://github.com/Vloods/TransTTE_demo/blob/main/backend/app/eta_inference.py).
The 152-dimensional input vector is assembled per request from:

- **Route node embeddings** — the DeepGraphInfomax + GraphSAGE embeddings (`dgi_*` CSV),
  summed over the nodes of the route.
- **Geometry** — how far the requested endpoints sit from the snapped edges, and where
  along the first/last edge the trip actually starts and ends (perpendicular projection,
  haversine distances).
- **Weather** — the latest row of `meteoData.csv` (cloud, weather, temperature, wind
  speed, pressure), with a day/evening split and a one-hot wind-direction class.
- **Time of day / week** — one-hot hour-of-day bucket and a weekday/weekend flag.

The trained weights are `SimpleTTE.pth`. Here the **edge weights only shape the route**;
the ETA itself is predicted by the net, not read off the weights.

## 2. Weighted-sum ETA — `get_shortest_path_grph`

For every Omsk variant and for the `graphormer_weights` variant, the **weight *is* the
time**. `get_shortest_path_grph` in
[`dijkstra_inference.py`](https://github.com/Vloods/TransTTE_demo/blob/main/backend/app/dijkstra_inference.py)
routes with igraph and then sums the per-edge weights along the chosen path to get the ETA
directly — no separate model. (For Omsk the summed value is divided by 10 before being
returned, an empirical unit adjustment baked into `app.py`.)

This is the ETA path that consumes the Graphormer output end to end: the model predicts a
travel time per edge, and the route ETA is just the sum along the path — which is exactly
why the [weight-handoff contract]({{< relref "/docs/architecture/weight-contract" >}})
matters here.

## Why two paths at all

The neural ETA predates the Graphormer integration and was tuned on Abakan trip data with
rich weather/time features. The weighted-sum path is the natural fit once a model already
emits a per-edge travel time — the weights carry the estimate, so summing them is the whole
computation. Both coexist so the demo can show classic feature-based variants and the
Graphormer variant side by side.
