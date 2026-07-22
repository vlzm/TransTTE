---
title: "API"
weight: 1
bookToc: true
---

# API Reference

TransTTE exposes two HTTP services. In normal operation they do **not** call each other
live — the Graphormer service writes per-edge weights to pickles once, and the backend
reads them. See the [weight-handoff contract]({{< relref
"/docs/architecture/weight-contract" >}}). The endpoints below are what a client (the map
UI, or your own script) actually talks to.

Both services are FastAPI apps that bind to `0.0.0.0:80` regardless of what the Dockerfile
`EXPOSE`s or `settings.py` names — see [Data & Model Assets]({{< relref
"/docs/running/data-assets" >}}).

---

## Backend service

Source:
[`backend/app/app.py`](https://github.com/vlzm/TransTTE/blob/main/backend/app/app.py).

### `GET /`

Returns the interactive map UI (`index.html`) as HTML. No parameters.

### `POST /get_path`

Route between two points and return one alternative per [routing
objective]({{< relref "/docs/architecture/routing-objectives" >}}).

**Request body** (`application/json`) — coordinates are always `(lat, lon)`:

```json
{
  "start_lat": 55.7809453,
  "start_lon": 37.6373427,
  "end_lat":   55.6217188,
  "end_lon":   37.49859
}
```

| Field | Type | Meaning |
|--|--|--|
| `start_lat`, `start_lon` | float | Origin latitude / longitude |
| `end_lat`, `end_lon` | float | Destination latitude / longitude |

Every coordinate must be in `0..180` (validated) and both endpoints must fall inside the
**same** city bounding box — Abakan or Omsk. The city is chosen by `check_town`; the
request does not name it.

**Response** (`application/json`) — a **list**, one object per weight variant loaded for
the resolved city:

```json
[
  {
    "path": [[55.7809, 37.6373], [55.7791, 37.6350], "…"],
    "eta": 842,
    "type": "dist"
  },
  {
    "path": [["…"]],
    "eta": 910,
    "type": "graphormer_weights"
  }
]
```

| Field | Type | Meaning |
|--|--|--|
| `path` | list of `[lat, lon]` | Ordered node coordinates of the route (last node trimmed) |
| `eta` | number | Estimated travel time in **seconds** |
| `type` | string | The weight variant / objective this route optimises (`dist`, `green`, `hist`, …, or `graphormer_weights`) |

How `eta` is produced depends on the variant — a neural net for the Abakan non-Graphormer
variants, a weighted sum of edge weights for everything else. See [Two ETA
Paths]({{< relref "/docs/architecture/eta-paths" >}}). (For Omsk the summed value is
divided by 10 before being returned.)

**Errors**

| Status | Cause |
|--|--|
| `400` | A coordinate is outside `0..180`, or the endpoints are not both inside one supported city |

---

## Graphormer service

Source:
[`graphormer/app/app.py`](https://github.com/vlzm/TransTTE/blob/main/graphormer/app/app.py).
GPU service — expensive, normally run once to produce the weight pickles the backend
consumes.

### `GET /`

Health check. Returns `{"ping": "pong"}`.

### `POST /get_weights`

Returns one travel-time weight per edge, for both city road graphs. **No request body.**

**Response** (`application/json`):

```json
{
  "abakan": [12.4, 8.1, 33.0, "…"],
  "omsk":   [5.2, 19.7, "…"]
}
```

| Field | Type | Meaning |
|--|--|--|
| `abakan` | list of float | One weight per edge of the Abakan graph, **in graph edge order** |
| `omsk` | list of float | One weight per edge of the Omsk graph, in graph edge order |

The ordering is load-bearing: the position of a weight in the list *is* its edge
identity. Never reorder weights or edges independently — see the [weight-handoff
contract]({{< relref "/docs/architecture/weight-contract" >}}).

**Example call**

```python
import requests

r = requests.post(
    "http://0.0.0.0:80/get_weights",
    headers={"Content-Type": "application/json"},
)
weights = r.json()          # {"abakan": [...], "omsk": [...]}
```
