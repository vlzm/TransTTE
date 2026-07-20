---
title: "Routing Objectives"
weight: 5
bookToc: true
math: true
---

# Routing Objectives

A single `POST /get_path` call returns **several routes**, one per *objective*. An
objective is nothing more than a per-edge weight list: change what the weights mean and you
change what "shortest" optimizes for — fastest, shortest distance, greenest, most
historic, and so on.

## Where they come from

The backend loads every objective for a city from a directory at startup:

```python
for weight in sorted((BASE / 'data/weights_abakan').iterdir()):
    if '.pkl' in weight.name:
        weights_dict_abakan[weight.name.split('.')[0]] = pickle.load(fd)
```

So the **file name (minus extension) becomes the `type`** in the response, and `sorted()`
fixes the order. The objectives shipped in the demo data are, for example:

| City | Files | Objectives (`type`) |
|--|--|--|
| Abakan | `data/weights_abakan/*.pkl` | `1dist`, `2dist_green_abakan`, `3hist_abakan` |
| Omsk | `data/weights_omsk/*.pkl` | `dist_omsk`, `green_omsk`, `hist_omsk` |

On top of these, the `graphormer_weights` variant (from
[`data/graphormer_weights/`]({{< relref "/docs/architecture/weight-contract" >}})) is
appended in code, so it always appears too.

## What the objectives mean

- **dist** — shortest physical distance.
- **green** — prefer routes with more greenery / parks.
- **hist** (historicity) and **beauty / picturesqueness** — prefer routes past more
  points of interest.

The paper builds the picturesqueness and historicity objectives from OpenStreetMap: for a
road segment, it counts the number of relevant objects \\(C_r\\) within a radius \\(r\\) and
assigns the segment a weight

```katex
W_i = \frac{1}{1 + C_r}
```

so segments richer in nearby objects get a *lower* weight and are preferred by the
shortest-path search. See [Research → Results]({{< relref "/docs/research/results" >}}) for
the picturesqueness/historicity evaluation.

## Adding a new objective

There is **no code change**. Drop a new edge-aligned `*.pkl` (one weight per edge, in graph
edge order) into `data/weights_{city}/`, restart the backend, and it appears automatically
as a new `type` in the `/get_path` response.

The only rule is the [weight-handoff contract]({{< relref
"/docs/architecture/weight-contract" >}}): the list length and order must match the city
graph's edges exactly, or the routes will be silently wrong. Note also that for Abakan the
non-Graphormer variants use the [neural ETA]({{< relref "/docs/architecture/eta-paths" >}}),
while Omsk variants use the weighted sum — so a new Abakan objective changes the route but
still gets its ETA from `FFNet`.
