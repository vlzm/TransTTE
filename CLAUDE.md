# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

TransTTE — transformer-based travel time estimation (PKDD'22 paper "Logistics, Graphs, and Transformers: Towards improving Travel Time Estimation"). Two datasets/cities are supported: **Abakan** and **Omsk**. Live demo: https://vlzm.github.io/TransTTE/demo/. Paper: https://arxiv.org/abs/2207.05835

The system is a two-service pipeline. A Graphormer model predicts a travel-time weight for every edge in a city road graph; the backend uses those per-edge weights to run shortest-path routing and serve a map UI.

## Two-service architecture

**`graphormer/`** — GPU service. Loads a trained Graphormer checkpoint per city and produces one travel-time weight per road-graph edge. Exposes `POST /get_weights` returning `{'abakan': [...], 'omsk': [...]}` (a flat list of floats, one per edge). This is expensive and normally run once; results are cached as pickles.

**`backend/`** — CPU service + web UI. Loads the precomputed edge weights and answers `POST /get_path` with `{start_lat, start_lon, end_lat, end_lon}`. It picks the city by bounding-box (`check_town` in [backend/app/app.py](backend/app/app.py)), snaps endpoints to the nearest graph nodes via a `BallTree` (haversine), runs igraph shortest-path over several weight variants, and returns a route + ETA for each. Serves the map at `GET /`.

### The weight-handoff contract (important)

The two services communicate through **pickled weight lists**, not live HTTP, in normal operation. Both `app.py` files have a `preloaded_weights = True` branch (uses cached pickles) and an `else` branch (recomputes from the model / calls the other service). The precomputed path is the default.

- Graphormer writes/serves `weights_abakan.pickle`, `weights_omsk.pickle`.
- Backend reads them from `backend/app/data/graphormer_weights/` as the `graphormer_weights` route variant.
- Backend also has non-Graphormer weight variants loaded from `backend/app/data/weights_abakan/` and `backend/app/data/weights_omsk/` (`*.pkl`), each keyed by filename → a separate routing objective (dist, green, hist, safety, beauty, etc.). Each becomes one entry in the `/get_path` response, tagged by `type`.

The ordering of a weights list must line up with graph edge order — do not reorder edges or weights independently.

## Two ETA paths in the backend

`return_path` in [backend/app/app.py](backend/app/app.py) computes ETA two different ways depending on the variant — know which you're touching:

1. **Neural ETA** (`ETAInf.forward`, [backend/app/eta_inference.py](backend/app/eta_inference.py)): a small feed-forward net `FFNet` (152 inputs, in [backend/app/ml.py](backend/app/ml.py)) that consumes route node embeddings + weather + time-of-day + geometry features. Used for the Abakan non-Graphormer variants.
2. **Weighted-sum ETA** (`get_shortest_path_grph`, [backend/app/dijkstra_inference.py](backend/app/dijkstra_inference.py)): sums the per-edge weights along the path (the weight *is* the time). Used for all Omsk variants and the `graphormer_weights` variant.

`DijkstraPath` despite its name uses igraph's `get_shortest_paths`, not a hand-rolled Dijkstra.

## Data dependencies (not in git)

Neither service runs without large binary assets that are gitignored / downloaded separately:

- Backend data → `backend/app/data/` (from https://disk.yandex.ru/d/NHj3ukteUGn-dA). Includes `SimpleTTE.pth` (FFNet weights), `dijkstra.pickle` / `graph_omsk.pkl` (igraph graphs), `clear_nodes*.pkl` (node coord tables), `meteoData.csv` (weather), node-embedding CSVs, and the `weights_*` pickles.
- Graphormer models → `graphormer/app/models/{abakan,omsk}/checkpoint_{best,last}.pt` (from https://disk.yandex.ru/d/rQCIJs_7Q7Li6g).

When a load fails, it's almost always a missing/renamed asset under `data/` or `models/`, not a code bug. File paths are hardcoded relative to each script's location.

## Running

Both services are intended to run via Docker (dependency pinning is finicky — Graphormer needs torch 1.9.1+cu111, torch-geometric 1.7.2, dgl 0.7.2, and a source build of fairseq).

Backend:
```
cd backend
docker build . -t visual
docker run --rm -it -p 80:80 visual        # then open http://127.0.0.1:80/
```

Graphormer:
```
cd graphormer
docker build . -t graphormer
docker run --rm -it -p 80:80 graphormer
# fetch per-edge weights:
#   r = requests.post('http://0.0.0.0:80/get_weights', headers={'Content-Type':'application/json'})
#   weights_dict = r.json()
```

Note: both `app.py` hardcode `uvicorn.run(app, host='0.0.0.0', port=80)`; the graphormer `Dockerfile` `EXPOSE`s 3006 and `backend/app/settings.py` names other ports — the actual bind is 80. `settings.py` (placeholder hostname + SSL cert paths) is not wired into the run call.

The Graphormer Docker build runs [graphormer/app/install.sh](graphormer/app/install.sh), which clones and source-builds fairseq into `graphormer_repo/`.

## Graphormer internals

[graphormer/app/graphormer_repo/](graphormer/app/graphormer_repo/) is a vendored/modified copy of Microsoft's Graphormer (built on fairseq tasks/criterions/models). City road graphs are registered as PyG datasets: `mydata_abakan.py`, `mydata_omsk.py` under `graphormer_repo/graphormer/data/pyg_datasets/`. [graphormer/app/data_class.py](graphormer/app/data_class.py) (`single_geo_Abakan`, `full_geo_Abakan`, `GraphormerPYGDataset_predict`, etc.) builds graph objects from raw edge/node tables. [graphormer/app/evaluate_points.py](graphormer/app/evaluate_points.py) wires the fairseq eval iterator to produce edge weights.

## Offline notebooks (research, not serving)

`preprocessing/` and `algorithms/` are Jupyter notebooks + scripts for building the datasets and training the auxiliary models — separate from the two serving apps and not needed to run the demo:

- `preprocessing/graph_preprocessing.ipynb`, `ETA_additional_features_processing.ipynb`, `gismeteo_parser.ipynb` — build road graphs and features.
- `algorithms/stellar_deepgraphinfomax-graphsage.ipynb` — trains the DeepGraphInfomax + GraphSAGE node embeddings (the `dgi_*` CSVs the backend consumes).
- `algorithms/inference_ETA.py`, `regression.ipynb` — the regression-based ETA baseline (uses TensorFlow/Keras, unlike the serving FFNet which is PyTorch).
- `algorithms/parse_weather.py`, `get_samples.py` — weather scraping and trip sampling.

## Conventions / gotchas

- No test suite, linter, or CI. The `if __name__ == "__main__"` blocks in `dijkstra_inference.py` and the `app.py` files are the closest thing to smoke tests.
- Lots of `print('1')`-style debug output and commented-out code paths are intentional/left in — don't treat them as the intended interface.
- Coordinates are always `(lat, lon)` in API bodies; several internal helpers take `(lon, lat)` (e.g. `haversine_np` in [backend/app/utils.py](backend/app/utils.py)). Check argument order when touching geometry.
- Adding a routing objective = dropping a new `*.pkl` (edge-aligned weight list) into `data/weights_{city}/`; it auto-appears as a `type` in `/get_path`. No code change needed.
