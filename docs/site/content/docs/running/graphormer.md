---
title: "Graphormer"
weight: 2
bookToc: true
---

# Running Graphormer

The Graphormer service is the **GPU side**: it loads a trained checkpoint per city and
produces one travel-time weight per road-graph edge, served at `POST /get_weights`. This is
expensive and normally run **once** — the backend then consumes the cached result. See
[Graphormer Service]({{< relref "/docs/architecture/graphormer-service" >}}) for the
internals.

> This service needs a **GPU** and the trained checkpoints under
> `graphormer/app/models/{abakan,omsk}/`. Get them from
> [Data Assets]({{< relref "/docs/running/data-assets" >}}) first.

## Build and run (Docker)

Docker is the recommended path — the dependency stack (torch 1.9.1+cu111,
torch-geometric 1.7.2, dgl 0.7.2, and a source build of fairseq) is finicky to reproduce by
hand. The [`Dockerfile`](https://github.com/vlzm/TransTTE/blob/main/graphormer/Dockerfile)
installs the pinned packages and runs
[`install.sh`](https://github.com/vlzm/TransTTE/blob/main/graphormer/app/install.sh),
which clones and source-builds **fairseq** into `graphormer_repo/`.

```bash
cd graphormer
docker build . -t graphormer
docker run --rm -it -p 80:80 graphormer
```

Despite the `EXPOSE 3006` in the `Dockerfile`, `app/app.py` binds to **port 80** (see the
[port gotcha]({{< relref "/docs/running" >}})) — so map `-p 80:80`.

## Fetch the per-edge weights

Once the container is up, request the weights. The endpoint takes **no body** and returns a
dict of flat float lists, one entry per edge, keyed by city:

```python
import requests
r = requests.post(
    "http://0.0.0.0:80/get_weights",
    headers={"Content-Type": "application/json"},
)
weights_dict = r.json()      # {'abakan': [...], 'omsk': [...]}
```

To use these in routing, the lists are pickled and dropped into the backend's
`data/graphormer_weights/` directory as `weights_abakan.pickle` / `weights_omsk.pickle`.
The **order of the list must match the graph's edge order** — this is the
[weight contract]({{< relref "/docs/architecture/weight-contract" >}}), the one invariant
that fails silently if broken.

## Notes

- The default serving path uses cached pickles (`preloaded_weights = True`); recomputing
  from the model is the `else` branch. You only need to run this service when regenerating
  weights.
- The evaluation iterator that turns a checkpoint into edge weights lives in
  [`evaluate_points.py`](https://github.com/vlzm/TransTTE/blob/main/graphormer/app/evaluate_points.py)
  — see [Training]({{< relref "/docs/training" >}}).
