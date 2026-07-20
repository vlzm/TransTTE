---
title: "Backend"
weight: 1
bookToc: true
---

# Running the Backend

The backend is the **CPU service + web UI**. It loads the precomputed edge weights and the
road graphs, answers `POST /get_path`, and serves the map at `GET /`. See
[Backend Service]({{< relref "/docs/architecture/backend-service" >}}) for what it does
internally.

> Make sure the [data assets]({{< relref "/docs/running/data-assets" >}}) are in
> `backend/app/data/` first — the backend loads graphs, embeddings, and weight pickles at
> startup and will fail on a missing file.

## Run it directly (Python)

The backend is a plain FastAPI app; the entrypoint is
[`start.sh`](https://github.com/Vloods/TransTTE_demo/blob/main/backend/start.sh), which just
runs the app:

```bash
cd backend

# install deps (pick one)
pip install -r requirements.txt      # or: poetry install

./start.sh                           # exec python3 app/app.py
```

`app/app.py` binds `uvicorn` to **host `0.0.0.0`, port `80`** (hardcoded — see the
[port gotcha]({{< relref "/docs/running" >}})). Then open:

```
http://127.0.0.1:80/
```

> Port 80 is privileged on most systems, so `start.sh` may need `sudo` (or edit the
> `uvicorn.run(...)` line in `app/app.py` to a high port like 8000 for local testing).

## Dependencies

Backend requirements ([`requirements.txt`](https://github.com/Vloods/TransTTE_demo/blob/main/backend/requirements.txt)):

```
fastapi~=0.67.0
pydantic~=1.8.2
uvicorn~=0.14.0
pandas~=1.3.1
sklearn~=0.0
python-igraph~=0.9.6
loguru~=0.5.3
```

The neural-ETA variants also need **PyTorch** (`torch==1.9.1+cu111`) to load
`SimpleTTE.pth`. Omsk and the `graphormer_weights` variant use the weighted-sum ETA path
and do not require the neural net — see
[Two ETA Paths]({{< relref "/docs/architecture/eta-paths" >}}).

## Smoke-testing

With the server up, request a route (coordinates are always `lat, lon`):

```python
import requests
r = requests.post(
    "http://127.0.0.1:80/get_path",
    json={"start_lat": 53.72, "start_lon": 91.44,
          "end_lat": 53.71, "end_lon": 91.47},
)
print(r.json())   # one route + ETA per weight variant (`type`)
```

See the [API reference]({{< relref "/docs/reference/api" >}}) for the full request/response
shapes. The city (Abakan vs. Omsk) is chosen automatically by bounding box, so use
coordinates inside one of the two cities.
