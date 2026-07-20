---
title: "Method"
weight: 3
bookToc: true
math: true
---

# Method

## Why a transformer for graphs

The transformer architecture has become dominant in NLP and computer vision, yet on
graph-level prediction leaderboards it had *not* matched mainstream GNN variants. TransTTE
asks the question directly: **can a transformer perform well for graph representation
learning in the TTE task?** Its answer builds on **Graphormer** ([Ying et al., 2021](https://arxiv.org/abs/2106.05234)),
which injects graph structure into a standard transformer through a few structural
encodings. TransTTE adopts the two graph-oriented aspects below.

The repository implementation lives in
[`graphormer/app/graphormer_repo/graphormer/models/graphormer.py`](https://github.com/Vloods/TransTTE_demo/blob/main/graphormer/app/graphormer_repo/graphormer/models/graphormer.py).

## Centrality encoding

Each node is assigned two learnable real-valued embedding vectors according to its
**indegree** and **outdegree**, which are added to the node's input features to form the
layer-0 representation:

```katex
h_i^{(0)} = x_i + z^{-}_{\deg^{-}(v_i)} + z^{+}_{\deg^{+}(v_i)}
```

where \\(x_i\\) is the input feature of node \\(v_i\\), and
\\(z^{-}, z^{+} \in \mathbb{R}^{d}\\) are learnable embedding vectors indexed by the
indegree \\(\deg^{-}(v_i)\\) and outdegree \\(\deg^{+}(v_i)\\) respectively. This lets the
model know how "central" — how well connected — each intersection is.

## Spatial encoding

Along with centrality encoding, a **spatial encoding** captures the structural relation
between nodes via a function

```katex
\phi(v_i, v_j) : V \times V \rightarrow \mathbb{R}
```

that measures the spatial relation between nodes \\(v_i\\) and \\(v_j\\) of the road
network \\(G\\). The original choice for \\(\phi(v_i, v_j)\\) is the **shortest distance**
between the two nodes.

## Attention bias

The spatial encoding then enters the self-attention module as a learnable **bias term**,
so that structurally distant nodes are treated differently from nearby ones:

```katex
A_{ij} = \frac{(h_i W_Q)(h_j W_K)^{\top}}{\sqrt{d}} + b_{\phi(v_i, v_j)}
```

Here \\(A_{ij}\\) is the attention score between nodes \\(v_i\\) and \\(v_j\\),
\\(W_Q\\) and \\(W_K\\) are the query/key projections, \\(d\\) is the head dimension, and
\\(b_{\phi(v_i, v_j)}\\) is a **learnable scalar indexed by \\(\phi(v_i, v_j)\\)** that is
**shared across all layers**. Sharing the bias across layers is also what makes the
spatial encoding cacheable — the source of the training speedup discussed in
[Results]({{< relref "/docs/research/results" >}}) and
[Training]({{< relref "/docs/training" >}}).

## From the model to routing

At serving time the trained model produces one travel-time **weight per road-graph edge**.
Those weights are what the backend consumes to run shortest-path routing and report an
ETA — see the [weight-handoff contract]({{< relref "/docs/architecture/weight-contract" >}})
and the [Graphormer service]({{< relref "/docs/architecture/graphormer-service" >}}).
