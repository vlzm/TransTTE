---
title: "Graphormer Service"
weight: 1
bookToc: true
---

# Graphormer Service

The Graphormer service (`graphormer/`) is the **GPU side** of the pipeline. It loads a
trained Graphormer checkpoint per city and produces exactly one travel-time weight for
every edge of that city's road graph. This is the expensive step, and it is normally run
**once** — the results are cached as pickle files that the [backend]({{< relref
"/docs/architecture/backend-service" >}}) reads at startup.

Source:
[`graphormer/app/app.py`](https://github.com/vlzm/TransTTE/blob/main/graphormer/app/app.py).

## The endpoint

```text
POST /get_weights        →  {"abakan": [w0, w1, ...], "omsk": [w0, w1, ...]}
```

The response is a JSON object with one key per city. Each value is a **flat list of
floats** — one weight per edge, in graph edge order. There is no request body. A
`GET /` returns `{"ping": "pong"}` as a liveness check.

## Two ways to get the weights

Like the backend, `app.py` has a `preloaded_weights` switch at module load time:

- **`preloaded_weights = True`** (default) — read
  `weights_abakan.pickle` and `weights_omsk.pickle` from the service's `weights/`
  directory and coerce every entry to `float`. No model, no GPU needed to serve.
- **`preloaded_weights = False`** — rebuild everything from scratch: load the raw
  edge/node tables, construct the city graph objects, load the checkpoints
  (`models/{city}/checkpoint_last.pt`), and run the fairseq eval iterator to predict a
  weight per edge. This is what you run to *regenerate* the pickles.

## How weights are computed (the `else` branch)

The recompute path wires together the offline evaluation machinery documented under
[Training]({{< relref "/docs/training" >}}):

1. Build the road graph as a PyG dataset (`full_geo_Abakan` in
   [`data_class.py`](https://github.com/vlzm/TransTTE/blob/main/graphormer/app/data_class.py),
   used for both cities).
2. Prepare the fairseq task, config, and model from the checkpoint
   (`prepare_eval_model`, `prepare_task` in
   [`evaluate_points.py`](https://github.com/vlzm/TransTTE/blob/main/graphormer/app/evaluate_points.py)).
3. Run inference to emit one predicted travel time per edge, in the same order as the
   graph's edges.

That ordering is not decorative — it is the contract the backend depends on. See the
[weight-handoff contract]({{< relref "/docs/architecture/weight-contract" >}}).

## Running it

Build and run the container, then call the endpoint from Python — see
[Running → Graphormer]({{< relref "/docs/running/graphormer" >}}). The checkpoints are
large binary assets that live outside git; see
[Data & Model Assets]({{< relref "/docs/running/data-assets" >}}).
