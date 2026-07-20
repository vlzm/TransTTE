---
title: "Results"
weight: 4
bookToc: true
math: true
---

# Results

## Comparison with baselines

TransTTE is compared against the three [baselines]({{< relref "/docs/research/related-work" >}})
(GBDT, MURAT, WDR) on both cities, reporting **MAE** and **RMSE** on train and test splits.
Lower is better; the **best test MAE per city is in bold**.

**Omsk**

| Model | Train MAE | Train RMSE | Test MAE | Test RMSE |
|-------|----------:|-----------:|---------:|----------:|
| GBDT | 403.921 | 582.011 | 408.644 | 573.559 |
| MURAT | 279.616 | 438.228 | 286.491 | 443.397 |
| WDR | 311.581 | 440.511 | 336.756 | 487.876 |
| **TransTTE** | 101.381 | 387.241 | **105.464** | 261.103 |

**Abakan**

| Model | Train MAE | Train RMSE | Test MAE | Test RMSE |
|-------|----------:|-----------:|---------:|----------:|
| GBDT | 244.119 | 449.250 | 248.862 | 399.534 |
| MURAT | 179.037 | 285.003 | 185.153 | 286.934 |
| WDR | 173.684 | 285.132 | 182.296 | 293.551 |
| **TransTTE** | 81.048 | 285.032 | **83.616** | 168.421 |

TransTTE achieves the best travel-time error on both datasets — on test **MAE** it beats
every baseline by a wide margin (≈ 105.5 on Omsk, ≈ 83.6 on Abakan), and it also leads on
test RMSE.

## Extra routing objectives: picturesqueness and historicity

Beyond estimating TTE for the shortest route, the framework also evaluates routes by
**picturesqueness** and **historicity**. Using the **OpenStreetMap API**, it parses the
location of historical, cultural, and natural objects, and turns their count into a
per-segment weight for the routing (Dijkstra) step:

```katex
W_i = \frac{1}{1 + C_r}
```

where \\(W_i\\) is the weight for the \\(i\\)-th road segment and \\(C_r\\) is the number
of objects within a radius \\(r\\) of that segment. A segment surrounded by many
points of interest gets a **smaller** weight, so the shortest-weight path is nudged toward
scenic or historical streets. In the running system each such objective is just another
edge-aligned weight list — see
[routing objectives]({{< relref "/docs/architecture/routing-objectives" >}}).

## Training efficiency

The authors reimplemented the Graphormer architecture to exploit the peculiar properties
of road trips. By **caching the spatial-encoding values** (the shared-across-layers bias
from the [Method]({{< relref "/docs/research/method" >}}) page), training was sped up by
**almost 10×**. The best configuration is **Graphormer-SLIM** (\\(L = 12\\), \\(d = 80\\))
with the **AdamW** optimizer; different TransTTE configurations train in **2.5–5 hours**,
faster than WDR (7 h) and MURAT (5.5 h). Full details are in
[Training]({{< relref "/docs/training" >}}).

## Takeaway

A graph transformer *can* work well for TTE: on real road networks TransTTE outperforms
strong segment-wise and whole-path baselines on travel-time error, while remaining
practical to train and flexible enough to support alternative routing objectives.
