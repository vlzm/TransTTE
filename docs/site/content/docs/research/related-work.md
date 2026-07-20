---
title: "Related Work"
weight: 2
bookToc: true
---

# Related Work

## Two families of TTE methods

The paper divides existing TTE approaches into two categories, distinguished by *how much
of the route* they reason about:

1. **Segment-wise methods.** ETA is built by extracting and summing the traversal time of
   each individual segment of the path. Because each segment is treated on its own, these
   models **do not capture global properties of the path** — the way segments interact,
   the overall shape of the route, or path-level context.
2. **Whole-path methods.** ETA is computed from the trip path taken *as a whole*. Results
   from this class define the mainstream of current TTE research, and it is the family
   TransTTE belongs to.

TransTTE pushes the whole-path idea further by using a **graph transformer**
([Graphormer]({{< relref "/docs/research/method" >}})), so that a route's global
structure is available to the model through self-attention rather than being flattened
into a per-segment sum.

## Baselines

To verify the effectiveness of the proposed model, the paper reimplements three baselines
spanning classic and more sophisticated pipelines. They reappear in the
[Results]({{< relref "/docs/research/results" >}}) comparison.

| Baseline | What it is |
|----------|-----------|
| **GBDT** | Gradient-boosted decision trees — a strong classic tabular baseline. |
| **MURAT** | Produces unsupervised node representations with **DeepWalk** and applies **residual feed-forward** blocks to predict travel time and distance. |
| **WDR** | Combines a **generalized linear model (GLM)** with an **LSTM** to compute travel time. |

The next page, [Method]({{< relref "/docs/research/method" >}}), describes the TransTTE
model that is compared against these baselines.
