---
title: "TransTTE"
type: docs
---

# TransTTE

**Transformer-based travel time estimation.** TransTTE is the official implementation
of the PKDD'22 paper *"Logistics, Graphs, and Transformers: Towards improving Travel
Time Estimation"*. It treats a city road network as a graph and uses a
[Graphormer]({{< relref "/docs/research/method" >}})-based transformer to predict how
long a trip takes — reaching competitive performance against classic segment-wise and
whole-path baselines on the travel-time metric.

<picture>
  <source srcset="images/transtte_pipeline_bl.png" media="(prefers-color-scheme: dark)">
  <img src="images/transtte_pipeline_wh.png" alt="TransTTE pipeline" style="max-width:100%;">
</picture>

The project ships as a **two-service pipeline**: a GPU *Graphormer* service that emits a
travel-time weight for every road-graph edge, and a CPU *backend + map UI* that turns
those weights into routes and ETAs. See the
[Architecture]({{< relref "/docs/architecture" >}}) section for the full picture.

## Quick links

- 📄 **Paper** — [arXiv:2207.05835](https://arxiv.org/abs/2207.05835)
- 💻 **Code** — [github.com/vlzm/TransTTE](https://github.com/vlzm/TransTTE)
- 🌍 **Live demo** — [vlzm.github.io/TransTTE/demo](https://vlzm.github.io/TransTTE/demo/)

## Where to go next

| I want to… | Start here |
|------------|-----------|
| Understand the problem and the model | [Introduction]({{< relref "/docs/introduction" >}}) → [Research]({{< relref "/docs/research" >}}) |
| See how the services fit together | [Architecture]({{< relref "/docs/architecture" >}}) |
| Know what data the model uses | [Datasets]({{< relref "/docs/datasets" >}}) |
| Reproduce or fine-tune the model | [Training]({{< relref "/docs/training" >}}) |
| Run the demo locally | [Running]({{< relref "/docs/running" >}}) |
| Look up an endpoint or a term | [Reference]({{< relref "/docs/reference" >}}) |
