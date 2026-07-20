---
title: "Problem Formulation"
weight: 1
bookToc: true
math: true
---

# Problem Formulation

## The TTE task

The paper states the task compactly:

> **Task.** Given an origin, a destination, and a departure time, our goal is to estimate
> the trip duration using the set of historical trip dataset \\(X\\) and the underlying
> road network \\(G\\).

So a single prediction consumes three inputs and produces one number:

| Input | Meaning |
|-------|---------|
| **Origin** | Start location of the trip |
| **Destination** | End location of the trip |
| **Departure time** | When the trip begins (carries the temporal/traffic context) |

```katex
\text{origin},\ \text{destination},\ \text{departure time}
\;\longrightarrow\;
\hat{t}\ \text{(estimated duration)}
```

## The two given structures

The estimate is grounded in two things the model is allowed to use:

- **Road network \\(G\\).** The city road graph — nodes and directed edges (road
  segments) with their topology and per-segment features. TransTTE supports two cities,
  **Abakan** and **Omsk**, which differ in scale and topology (see
  [Datasets]({{< relref "/docs/datasets" >}})).
- **Historical trip dataset \\(X\\).** Real trips collected over a one-month period
  starting **December 1, 2020**, used to learn the mapping from a path (in \\(G\\)) to a
  duration. The raw trips are noisy, so they are filtered by rebuild count, minimum and
  maximum length, and total trip time before training.

## Two targets

Each dataset actually carries **two** target values per trip:

- **Real travel time** — the quantity studied in this paper (the "TTE" target).
- **Real trip length** — an alternative target, available for other studies.

TransTTE is trained and evaluated on the **travel-time** target. The next page,
[Related Work]({{< relref "/docs/research/related-work" >}}), positions this task against
prior TTE approaches.
