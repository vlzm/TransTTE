---
title: "Glossary"
weight: 2
bookToc: true
---

# Glossary

Terms used across these docs, the paper, and the code, in one place.

**TTE — Travel Time Estimation.**
Predicting how long a trip along a road network will take. The task this project targets;
also the "T" in TransTTE. Given an origin, a destination, and a departure time, estimate
the trip duration. See [Problem Formulation]({{< relref
"/docs/research/problem-formulation" >}}).

**ETA — Estimated Time of Arrival.**
The predicted duration (in seconds) returned for a route. In this system the ETA is
computed one of two ways — a neural net or a weighted sum of edge weights. See [Two ETA
Paths]({{< relref "/docs/architecture/eta-paths" >}}).

**Road graph.**
The city's street network as a directed graph: nodes are junctions/points and edges are
road segments. Abakan ≈ 65.5k nodes / 340k edges; Omsk ≈ 232k nodes / 1.15M edges. See
[Datasets]({{< relref "/docs/datasets" >}}).

**Edge weight.**
A single number attached to a road-graph edge that the router treats as the cost of
traversing it. For the Graphormer variant the weight *is* the predicted travel time; for
other objectives it encodes a different cost (distance, greenery, safety, …). The list of
weights is **edge-aligned** — one weight per edge, in graph edge order.

**Weight variant / routing objective.**
One complete edge-aligned weight list optimising for a particular goal (`dist`, `green`,
`hist`, `safety`, `beauty`, `graphormer_weights`, …). Each variant becomes one `type` in
the `/get_path` response. Adding a variant is just dropping a new `*.pkl` into
`data/weights_{city}/`. See [Routing Objectives]({{< relref
"/docs/architecture/routing-objectives" >}}).

**Graphormer.**
A transformer architecture for graphs (Microsoft) that TransTTE builds on. It injects
graph structure into attention through centrality and spatial encodings rather than
treating the graph as a sequence. See [Method]({{< relref "/docs/research/method" >}}).

**Centrality encoding.**
A per-node term added to the node's input features based on its in-/out-degree, letting
the model weight nodes by how connected they are.

**Spatial encoding.**
A bias added to the attention score between two nodes based on the shortest-path distance
between them — how the model perceives graph topology. Caching this encoding gives the
~10× training speed-up. See [Method]({{< relref "/docs/research/method" >}}).

**Attention bias.**
The spatial-encoding term added to the raw query–key attention score, so structurally
close nodes attend to each other more strongly.

**FFNet.**
The small feed-forward network (152 inputs → 128 → 1) that produces the neural ETA for the
Abakan non-Graphormer variants, from route embeddings, weather, time-of-day and geometry
features. Weights are `SimpleTTE.pth`. See [Two ETA Paths]({{< relref
"/docs/architecture/eta-paths" >}}).

**Node embedding (DGI + GraphSAGE).**
A learned vector per node, trained offline with Deep Graph Infomax over GraphSAGE and
stored as the `dgi_*` CSVs. Summed along a route, these feed the FFNet ETA.

**BallTree.**
A spatial index (from scikit-learn) built over node coordinates with the **haversine**
metric. Used to snap an arbitrary request coordinate to its nearest graph node. See
[Backend Service]({{< relref "/docs/architecture/backend-service" >}}).

**Haversine.**
The great-circle distance formula for points on a sphere; the metric used both for the
BallTree and for geometry features. Note: several internal helpers take `(lon, lat)` order
even though the API uses `(lat, lon)`.

**igraph.**
The graph library whose `get_shortest_paths` does the actual routing. Despite the class
name `DijkstraPath`, no hand-rolled Dijkstra is involved.

**Weight-handoff contract.**
The convention that the Graphormer service and the backend communicate through pickled,
edge-ordered weight lists — not live HTTP — and that weights and edges must never be
reordered independently. See [The Weight Contract]({{< relref
"/docs/architecture/weight-contract" >}}).

**check_town.**
The bounding-box test that decides whether a `/get_path` request belongs to Abakan, Omsk,
or neither (→ HTTP 400).
