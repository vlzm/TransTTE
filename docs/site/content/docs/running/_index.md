---
title: "Running"
weight: 6
bookCollapseSection: true
---

# Running

TransTTE runs as two independent services. In normal operation you only need the
**[backend]({{< relref "/docs/running/backend" >}})** — it serves the map UI and answers
routing requests using **precomputed** edge weights. The
**[Graphormer service]({{< relref "/docs/running/graphormer" >}})** is only needed to
(re)generate those weights, which is expensive and normally done once. See the
[architecture overview]({{< relref "/docs/architecture" >}}) for how the two connect.

Either way, **nothing runs without the large binary assets** (graphs, checkpoints,
embeddings, weight pickles) that are not in git — start with
[Data Assets]({{< relref "/docs/running/data-assets" >}}).

## Prerequisites

Dependency pinning is finicky, so the Graphormer service is meant to run via **Docker**.
Key package versions:

**Backend** (CPU + UI)

```
fastapi==0.67.0
pydantic==1.8.2
uvicorn==0.14.0
pandas==1.3.4
sklearn==0.0
python-igraph==0.9.6
loguru==0.5.3
torch==1.9.1+cu111
```

**Graphormer** (GPU)

```
torch==1.9.1+cu111
torch-scatter==2.0.9
torch-sparse==0.6.12
torch-geometric==1.7.2
dgl==0.7.2
lmdb==1.3.0
ogb==1.3.2
tensorboardX==2.4.1
rdkit-pypi==2021.9.3
igraph==0.9.10
numpy==1.20.3
```

The Graphormer service additionally source-builds
[fairseq](https://github.com/facebookresearch/fairseq) — handled by its Docker build.

## The port gotcha

Both services **hardcode** their bind in `app.py`:

```python
uvicorn.run(app, host='0.0.0.0', port=80)
```

So the actual listening port is always **80**, regardless of other numbers you may see:
the Graphormer `Dockerfile` `EXPOSE`s **3006**, and `backend/app/settings.py` names port
**9998** with placeholder SSL cert paths. Those settings (`Settings().port`, cert
files) sit in a **commented-out** `uvicorn.run` line and are **not wired into the actual
run**. Map port 80 when you `docker run`.

## Next

1. **[Data Assets]({{< relref "/docs/running/data-assets" >}})** — download and place the
   binary assets first.
2. **[Backend]({{< relref "/docs/running/backend" >}})** — run the CPU service + map UI.
3. **[Graphormer]({{< relref "/docs/running/graphormer" >}})** — build/run the GPU service
   and fetch fresh per-edge weights.
