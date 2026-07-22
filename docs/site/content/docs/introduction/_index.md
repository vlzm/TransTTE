---
title: "Introduction"
weight: 1
bookToc: true
---

# Introduction

## The problem

As ground transport keeps growing in cities, traffic management becomes more complex and
less predictable for drivers. To handle that trend it is important to estimate the
quantities that describe traffic dynamics accurately. One of the most important is the
**estimated time of arrival (ETA)** — the expected time expenditure for a trip between
two locations — and, closely related, **travel time estimation (TTE)**.

TTE is especially hard for cars because of the limitations imposed by the road-network
structure: the time to traverse a route is not just the sum of independent segments — it
depends on how those segments connect, on turns, intersections, and the global shape of
the path. These spatial aspects of the road, combined with the temporal dynamics of
traffic, call for dedicated **spatio-temporal methods**.

## The idea: transformers on road graphs

TransTTE frames a city road network as a **graph** and applies a transformer designed
for graphs — [Graphormer](https://arxiv.org/abs/2106.05234) — to reason about the trip
path *as a whole* rather than segment by segment. This lets the model capture global
structural properties of a route that segment-wise methods miss. The
[Research]({{< relref "/docs/research" >}}) section works through the formulation, the
baselines, and the model in detail.

## Contributions

The paper makes three contributions:

1. **The TransTTE model** — a transformer architecture that exploits spatio-temporal
   dependencies for TTE and reaches competitive performance versus several baselines
   (GBDT, MURAT, WDR).
2. **A new dataset** for the city of **Omsk**, released alongside the existing Abakan
   data (see [Datasets]({{< relref "/docs/datasets" >}})).
3. **A web service** built on TransTTE for demonstration — the map UI you can try live.

## Links

- 📄 Paper — [arXiv:2207.05835](https://arxiv.org/abs/2207.05835) (PKDD'22)
- 💻 Code — [github.com/vlzm/TransTTE](https://github.com/vlzm/TransTTE)
- 🌍 Live demo — [transtte.online](http://transtte.online)

> **Authors.** Natalia Semenova, Vadim Porvatov, Vladislav Tishin, Artyom Sosedka,
> Vladislav Zamkovoy (Sberbank · AIRI · MISIS).
