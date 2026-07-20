---
title: "Documentation"
weight: 1
bookFlatSection: false
---

# TransTTE documentation

TransTTE is a transformer-based approach to **travel time estimation (TTE)** —
predicting how long a car trip will take on a real city road network. This
documentation covers four things:

- **[Research]({{< relref "/docs/research" >}})** — the problem, the related work, the
  Graphormer-based model, and the experimental results from the PKDD'22 paper.
- **[Architecture]({{< relref "/docs/architecture" >}})** — how the running system is
  built: a GPU model service and a CPU backend that share per-edge weights.
- **[Training]({{< relref "/docs/training" >}})** — how the model was trained (fairseq,
  Graphormer-SLIM, hardware) and how the datasets and features were prepared.
- **[Running]({{< relref "/docs/running" >}})** — how to build and run both services
  with Docker, and which data assets to download first.

Supporting material lives in **[Datasets]({{< relref "/docs/datasets" >}})** (the Abakan
and Omsk road networks) and the **[Reference]({{< relref "/docs/reference" >}})** (API
endpoints and a glossary).

New to the project? Read the **[Introduction]({{< relref "/docs/introduction" >}})**
first — it states the problem and summarizes the paper's contributions in a page.
