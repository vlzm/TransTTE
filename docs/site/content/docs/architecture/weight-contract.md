---
title: "Weight Contract"
weight: 3
bookToc: true
---

# Weight Handoff Contract

The Graphormer service and the backend communicate through **pickled weight lists**, not
live HTTP, in normal operation. This page describes that handoff and the single invariant
that makes it work.

## The artifacts

The Graphormer service writes (and can serve) two pickles:

```text
weights_abakan.pickle    # one float per edge of the Abakan road graph
weights_omsk.pickle      # one float per edge of the Omsk road graph
```

The backend reads them from
`backend/app/data/graphormer_weights/` and exposes them as the `graphormer_weights`
route variant. Each pickle is just a flat list of floats.

## The invariant: order == edge order

> **The i-th weight is the travel time of the i-th edge.** The order of a weights list
> must line up with the graph's edge order. Do **not** reorder edges or weights
> independently.

There is no key, no edge id, no coordinate embedded alongside each weight — position *is*
the join key. The backend applies the list directly to the graph's edge sequence
(`self.g.es["weight"] = list(weights)` in
[`dijkstra_inference.py`](https://github.com/vlzm/TransTTE/blob/main/backend/app/dijkstra_inference.py)),
so a mismatch produces **wrong routes and wrong ETAs with no error** — the worst kind of
bug, because everything still "works".

This is why the graph must be built the same way on both sides. The producing side and the
consuming side both derive edge order from the same raw graph tables; if you regenerate one
graph you must regenerate the weights that go with it.

## Non-Graphormer variants follow the same rule

The `graphormer_weights` variant is one of several. The other
[routing objectives]({{< relref "/docs/architecture/routing-objectives" >}}) —
`dist`, `green`, `hist`, … — are also edge-aligned weight lists, each in its own `*.pkl`
under `data/weights_{city}/`. They obey the identical contract: one weight per edge, in
edge order.

## The two load branches

Both `app.py` files gate this handoff behind `preloaded_weights`:

| | `preloaded_weights = True` (default) | `preloaded_weights = False` |
|--|--|--|
| Graphormer | serve the cached pickles | recompute weights from the checkpoint |
| Backend | load pickles from `data/graphormer_weights/` | `POST /get_path`-style call to the model service |

The precomputed path is the default because recomputing is a GPU job. See the
[Graphormer service]({{< relref "/docs/architecture/graphormer-service" >}}) for how the
pickles are produced.
