# Final-exam network analysis: S1-S3 and trend metrics

Graph `enriched-cb371912e308` (file SHA-256 `37ee8c59d8245d45...`), config `analysis-final-exam-v1` (declared before any real-graph result; two dated changes, see the config). Every number below was measured by `research-network final-analysis` from the graph file; nothing is a planned target. Enrichment-derived labels (topics, methods, tasks, datasets, Wikidata/Wikipedia links) are AI-assessed, not human annotation, and the evaluation figures that describe them cover sampling error only. Reproduce with `uv run research-network final-analysis all --config configs/analysis-final-exam-v1.yaml --graph data/processed/enriched-graph-v3/graph.json --output reports/final-exam/analysis` (the stage `report` regenerates this file).

Runtimes (wall clock, one process each, 12 GB machine, `neo4j-enriched` stopped): sanity 0 s, smallworld 1084 s, ranking 198 s, communities 157 s, trends 12 s, report 1 s; peak resident memory of any run 1502 MB.

## Networks and the v4 sanity check

N1 = researcher co-authorship (COAUTHORED_WITH, weight = fractional weight), N2 = organization collaboration (COLLABORATED_WITH, fractional weight), N3 = paper citation (CITES, directed, core papers), N4 = the full enriched graph as one undirected simple graph (all labels, all relations, unweighted). N1-N3 are rebuilt from the v4 layer inside the graph file (parent-only organizations added by enrichment are excluded from N2).

| Network | Nodes | Edges | Largest (weak) component |
|---|---|---|---|
| N1 | 32189 | 80482 | 20776 |
| N2 | 2047 | 13031 | 1932 |
| N3 | 13617 | 7308 | 3899 |
| N4 | 50144 | 241767 | 50144 |

Sanity check against the frozen v4 analysis (`reports/release-v4/analysis.json`): 20 overlapping figures (nodes, edges, isolates, max degree, largest component, component count, strength sum) compared; all match. The first attempt differed for N2 (2,312 nodes against 2,047): it had included the 265 parent-only organizations that enrichment added; restricting N2 to the v4 layer removed the difference. Details: `sanity-v4.json`.

## S1 Small world (largest connected component)

| Network | n (LCC) | m (LCC) | mean degree | L (exact) | diameter | C (avg local) | transitivity |
|---|---|---|---|---|---|---|---|
| N1 | 20776 | 61991 | 5.97 | 8.807 | 28 | 0.8102 | 0.4257 |
| N2 | 1932 | 13016 | 13.47 | 3.253 | 8 | 0.4984 | 0.1950 |
| N4 | 50144 | 241767 | 9.64 | 3.361 | 10 | 0.5419 | 0.0121 |

Baselines: 20 replicates of each kind, same n and m (mean ± sd over replicates). σ = (C/C_rand)/(L/L_rand) from the means; the minimum is over the 20 replicates.

| Network | Baseline | L_rand | C_rand | σ (means) | min σ over replicates | L / L_rand | baseline L |
|---|---|---|---|---|---|---|---|
| N1 | Erdos-Renyi G(n,m) | 5.767 ± 0.002 | 0.00029 ± 0.00004 | 1853.6 | 1503.5 | 1.53 | exact |
| N1 | degree-preserving rewiring | 5.153 ± 0.003 | 0.00073 ± 0.00009 | 650.3 | 497.5 | 1.71 | exact |
| N2 | Erdos-Renyi G(n,m) | 3.185 ± 0.001 | 0.00693 ± 0.00029 | 70.4 | 65.9 | 1.02 | exact |
| N2 | degree-preserving rewiring | 3.004 ± 0.007 | 0.12042 ± 0.00316 | 3.8 | 3.7 | 1.08 | exact |
| N4 | Erdos-Renyi G(n,m) | 5.024 ± 0.004 | 0.00020 ± 0.00002 | 4037.4 | 3320.8 | 0.67 | seeded pivot sample (2000 sources per replicate) |
| N4 | degree-preserving rewiring | 3.300 ± 0.008 | 0.04107 ± 0.00030 | 13.0 | 12.8 | 1.02 | seeded pivot sample (2000 sources per replicate) |

| Network | ω (approximate, analytic ring lattice) | σ > 1 in all 40 replicates | L / L_rand ≤ 2.0 for both | Verdict (declared rule) |
|---|---|---|---|---|
| N1 | -0.73 | True | True | small world holds for N1 under the declared rule |
| N2 | 0.23 | True | True | small world holds for N2 under the declared rule |
| N4 | 0.42 | True | True | small world holds for N4 under the declared rule |

Reading: the declared rule holds for all three networks. For N1 it holds with room to spare on clustering (C is about 1,112 to 2,831 times the random value) but only moderately on path length: L is 1.53 to 1.71 times the random value and the diameter is 28, and ω = -0.73 leans toward a lattice-like structure; N1 is a clustered, long-path co-authorship graph that satisfies the declared bound, not a textbook small world. N2's L is 2% to 8% above the random baseline; N4's is 2% above the rewired baseline and 33% below the Erdos-Renyi one. ω uses analytic ring-lattice formulas (an approximation, not a simulated lattice). The N4 baseline L is a seeded 2,000-pivot sample per replicate (the exact BFS on 40 replicates of a 50k-node graph was not run); the real graph's L is exact everywhere. N4 includes paper, topic and venue nodes, so its clustering mixes bipartite structure with the collaboration graphs and its transitivity (0.012) is far below its average local clustering because of hub nodes.

Evolution of the cumulative network (largest component of the network built from papers up to and including the year; the 2025 row equals the full network, checked: edges 80,482 and 13,031):

| Network | Year | nodes with edges | edges | LCC nodes | L | diameter | C |
|---|---|---|---|---|---|---|---|
| N1 | 2021 | 6233 | 12599 | 345 | 6.499 | 16 | 0.8222 |
| N1 | 2022 | 10917 | 23329 | 3004 | 10.945 | 32 | 0.8141 |
| N1 | 2023 | 15787 | 36327 | 7996 | 11.060 | 34 | 0.8068 |
| N1 | 2024 | 22339 | 53774 | 12963 | 9.535 | 30 | 0.8057 |
| N1 | 2025 | 31775 | 80482 | 20776 | 8.807 | 28 | 0.8073 |
| N2 | 2021 | 810 | 2650 | 771 | 3.794 | 11 | 0.4743 |
| N2 | 2022 | 1118 | 4712 | 1080 | 3.504 | 8 | 0.4783 |
| N2 | 2023 | 1390 | 6911 | 1341 | 3.363 | 7 | 0.4838 |
| N2 | 2024 | 1661 | 9403 | 1624 | 3.301 | 8 | 0.4911 |
| N2 | 2025 | 1957 | 13031 | 1932 | 3.253 | 8 | 0.4936 |

N1's L rises from 6.5 to 11.1 while the largest component grows from 345 to 8,000 nodes, then falls back to 8.8 as new papers join the components: path length is not monotone in time; C is stable near 0.81. N4 is not evolved yearly.

Degree distribution and heavy-tail fit (`powerlaw`, discrete; likelihood-ratio tests of the power law against each alternative, R > 0 favours the power law):

| Network | nodes (deg ≥ 1) | xmin | alpha | tail nodes | vs lognormal | vs exponential | vs truncated power law | power-law claim allowed |
|---|---|---|---|---|---|---|---|---|
| N1 | 31775 | 4 | 2.83 | 18683 | R=-13.74, p=6.15e-43: alternative favoured | R=7.59, p=3.19e-14: power law favoured | R=-12.78, p=0: alternative favoured | False |
| N2 | 1957 | 8 | 1.99 | 742 | R=-4.55, p=5.29e-06: alternative favoured | R=3.34, p=0.000831: power law favoured | R=-5.63, p=1.07e-14: alternative favoured | False |
| N4 | 50144 | 67 | 2.14 | 290 | R=-0.25, p=0.805: indistinguishable | R=3.61, p=0.000311: power law favoured | R=-0.76, p=0.402: indistinguishable | True |

N1 and N2: the lognormal and the truncated power law fit significantly better than the pure power law, so **no power-law claim**; the tails are heavy (they beat the exponential) but not scale-free by this test. N4: the power law is favoured over the exponential and indistinguishable from lognormal and truncated power law, so the declared rule allows a power-law tail claim for degrees ≥ xmin = 67 only (290 nodes); no goodness-of-fit bootstrap was run, so even this is weak evidence.

Figures: `smallworld/path-length-histograms.svg` (share of node pairs at each shortest-path length in each network's largest component), `smallworld/degree-distributions.svg` (degree CCDF on log-log axes; the dotted line is the fitted xmin), `smallworld/evolution.svg` (L and C of the cumulative network by year).

## S2 Ranking

PageRank damping 0.85; N1 and N2 weighted by fractional weight, N3 directed (citing → cited, so score flows to cited papers), N4 unweighted. Full score tables: `ranking/scores-N*.csv.gz`; top-20 tables with name, score, rank, degree and community: `ranking/ranking-N*.json`.

**N1 top 10 by PageRank**

| Rank | Name | PageRank | Degree | Community |
|---|---|---|---|---|
| 1 | Shirui Pan | 0.00039 | 88 | 14 |
| 2 | Dongxiao He | 0.00032 | 58 | 14 |
| 3 | Zheng-Jun Zha | 0.00032 | 65 | 10 |
| 4 | Shu‐Tao Xia | 0.00031 | 64 | 2 |
| 5 | Xinwang Liu | 0.00031 | 65 | 56 |
| 6 | Chengjie Wang | 0.00031 | 90 | 0 |
| 7 | Bo An | 0.00031 | 48 | 18 |
| 8 | Min-Ling Zhang | 0.00030 | 38 | 18 |
| 9 | Lizhuang Ma | 0.00030 | 80 | 0 |
| 10 | Jianye Hao | 0.00028 | 71 | 27 |

**N2 top 10 by PageRank**

| Rank | Name | PageRank | Degree | Community |
|---|---|---|---|---|
| 1 | Zhejiang University | 0.01451 | 220 | 4 |
| 2 | Tsinghua University | 0.01171 | 222 | 2 |
| 3 | Chinese Academy of Sciences | 0.01073 | 257 | 5 |
| 4 | Peking University | 0.01014 | 187 | 2 |
| 5 | Tencent (China) | 0.00964 | 156 | 2 |
| 6 | Shanghai Jiao Tong University | 0.00903 | 175 | 2 |
| 7 | University of Chinese Academy of Sciences | 0.00852 | 206 | 5 |
| 8 | National University of Singapore | 0.00818 | 196 | 6 |
| 9 | University of Science and Technology of China | 0.00817 | 159 | 2 |
| 10 | Centre National de la Recherche Scientifique | 0.00786 | 246 | 0 |

**N3 top 10 by PageRank**

| Rank | Name | PageRank | Degree | Community |
|---|---|---|---|---|
| 1 | Boundary Proposal Network for Two-stage Natural Language Video Localization | 0.00250 | 10 |  |
| 2 | Ref-NMS: Breaking Proposal Bottlenecks in Two-Stage Referring Expression Grounding | 0.00247 | 9 |  |
| 3 | Turbocharging Treewidth-Bounded Bayesian Network Structure Learning | 0.00226 | 6 |  |
| 4 | SAT-based Decision Tree Learning for Large Data Sets | 0.00223 | 8 |  |
| 5 | Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting | 0.00194 | 51 |  |
| 6 | Context-Aware Graph Convolution Network for Target Re-identification | 0.00175 | 5 |  |
| 7 | BSN++: Complementary Boundary Regressor with Scale-Balanced Relation Modeling for Temporal Action Proposal Generation | 0.00164 | 5 |  |
| 8 | Incomplete Multi-View Multi-Label Learning via Label-Guided Masked View- and Category-Aware Transformers | 0.00133 | 9 |  |
| 9 | DICNet: Deep Instance-Level Contrastive Network for Double Incomplete Multi-View Multi-Label Classification | 0.00132 | 9 |  |
| 10 | T2I-Adapter: Learning Adapters to Dig Out More Controllable Ability for Text-to-Image Diffusion Models | 0.00125 | 21 |  |

**N4 top 5 by PageRank within each node label** (the whole-graph rank is in the JSON)

- Researcher: Shirui Pan (0.00020); Chengjie Wang (0.00017); Lizhuang Ma (0.00016); Ying Yu Tai (0.00016); Jianye Hao (0.00015)
- Organization: Zhejiang University (0.00216); Chinese Academy of Sciences (0.00208); Tsinghua University (0.00177); Peking University (0.00157); University of Chinese Academy of Sciences (0.00156)
- Paper: Informer: Beyond Efficient Transformer for Long Sequence Tim (0.00010); T2I-Adapter: Learning Adapters to Dig Out More Controllable  (0.00005); Beyond Low-frequency Information in Graph Convolutional Netw (0.00005); Masked Label Prediction: Unified Message Passing Model for S (0.00005); Time-Series Representation Learning via Temporal and Context (0.00005)
- Topic: Representation learning (0.00873); Multimodal learning (0.00457); Reinforcement learning (0.00377); Efficient machine learning systems (0.00373); Graph machine learning (0.00354)
- Method: graph neural networks (0.00055); contrastive learning (0.00033); diffusion models (0.00028); Transformer (0.00028); reinforcement learning (0.00027)
- Task: image classification (0.00020); semantic segmentation (0.00017); object detection (0.00016); node classification (0.00011); link prediction (0.00009)
- Dataset: ImageNet (0.00028); CIFAR-10 (0.00024); CIFAR-100 (0.00016); nuScenes (0.00011); MS-COCO (0.00009)

PageRank against the other measures (Spearman correlation over all nodes; top-20 overlap):

| Network | Measure | Spearman ρ | top-20 overlap |
|---|---|---|---|
| N1 | degree | 0.413 | 16 |
| N1 | strength | 0.648 | 10 |
| N1 | betweenness | 0.669 | 9 |
| N1 | eigenvector | -0.175 | 0 |
| N2 | degree | 0.781 | 18 |
| N2 | strength | 0.901 | 17 |
| N2 | betweenness | 0.783 | 15 |
| N2 | eigenvector | 0.485 | 17 |
| N3 | degree | 0.676 | 3 |
| N3 | strength | 0.676 | 3 |
| N3 | betweenness | n/a | n/a |
| N3 | eigenvector | n/a | n/a |
| N4 | degree | 0.954 | 19 |
| N4 | strength | 0.954 | 19 |
| N4 | betweenness | n/a | n/a |
| N4 | eigenvector | 0.449 | 19 |

Betweenness: N2 exact (igraph, Brandes); N1 exact as well, because the probe estimated 96 s, within the 30-minute limit, so no source sample was needed (took 87 s). Betweenness is not computed for N3 and N4, and eigenvector centrality is not computed for N3 (the citation graph is almost acyclic). Eigenvector centrality is meaningful only on a connected graph; on N1 (2,936 components) the leading eigenvector concentrates on one dense cluster, which explains ρ ≈ -0.18 and zero top-20 overlap there.

Robustness: PageRank on the full network against the strict-evidence network (edges with support_count ≥ 2 only, same node set):

| Network | edges | edges kept | share kept | Spearman ρ of PageRank | top-20 overlap |
|---|---|---|---|---|---|
| N1 | 80482 | 6260 | 0.078 | 0.542 | 7 |
| N2 | 13031 | 3397 | 0.261 | 0.797 | 19 |

Only a minority of N1 edges rest on two or more shared papers, so the strict ranking is a different, much sparser view: N1's top 20 changes a lot, N2's barely.

**Personalized PageRank** (N4, restart uniform over the papers of the subject; the subject's own papers are left out of the Paper list): precomputed for 16 topics, 30 methods, 30 tasks, 30 datasets (topics: the 16 leaf topics that have papers; the 4 parent topics carry no HAS_TOPIC edges; methods, tasks, datasets: the 30 with most papers each) in `ranking/personalized-pagerank.json`; `scientific_network.analysis.fx_cli.personalized_summary` computes it for any subject. Examples:

- Topic **Representation learning** (3195 papers): researchers Min-Ling Zhang; Chengjie Wang; Shu‐Tao Xia; Lizhuang Ma; organizations Zhejiang University; Chinese Academy of Sciences; Peking University
- Method **graph neural networks** (296 papers): researchers Shirui Pan; Dongxiao He; Di Jin; Chuan Shi; organizations Zhejiang University; Chinese Academy of Sciences; Peking University
- Dataset **ImageNet** (155 papers): researchers Bo Yuan; Leo Yu Zhang; Chang Xu; Shengshan Hu; organizations Chinese Academy of Sciences; Zhejiang University; Peking University

## S3 Communities, key individuals and groups

**N1 Leiden (modularity objective)**

| Resolution | Seed | Communities | Modularity Q (whole graph) | Communities in LCC | Q in LCC | Singletons | Largest |
|---|---|---|---|---|---|---|---|
| 0.8 | 17 | 3019 | 0.9546 | 84 | 0.9339 | 414 | 679 |
| 0.8 | 42 | 3018 | 0.9544 | 83 | 0.9336 | 414 | 753 |
| 0.8 | 101 | 3017 | 0.9545 | 82 | 0.9336 | 414 | 794 |
| 1.0 | 17 | 3029 | 0.9546 | 94 | 0.9344 | 414 | 616 |
| 1.0 | 42 | 3029 | 0.9546 | 94 | 0.9345 | 414 | 618 |
| 1.0 | 101 | 3028 | 0.9545 | 93 | 0.9345 | 414 | 580 |
| 1.2 | 17 | 3040 | 0.9546 | 105 | 0.9349 | 414 | 592 |
| 1.2 | 42 | 3040 | 0.9546 | 105 | 0.9348 | 414 | 622 |
| 1.2 | 101 | 3035 | 0.9547 | 100 | 0.9349 | 414 | 587 |

| Resolution | NMI across seeds (mean of 3 pairs) | min | Louvain communities | Louvain Q | NMI Leiden-Louvain (seed 17) |
|---|---|---|---|---|---|
| 0.8 | 0.933 | 0.927 | 3013 | 0.9530 | 0.921 |
| 1.0 | 0.947 | 0.943 | 3026 | 0.9532 | 0.927 |
| 1.2 | 0.957 | 0.954 | 3040 | 0.9531 | 0.934 |

Hierarchy (level 1 = Leiden at resolution 0.25 on the graph contracted by the level-0 headline partition: resolution 1.0, seed 17): 3029 level-0 communities → 2973 level-1 communities.

**N2 Leiden (modularity objective)**

| Resolution | Seed | Communities | Modularity Q (whole graph) | Communities in LCC | Q in LCC | Singletons | Largest |
|---|---|---|---|---|---|---|---|
| 0.8 | 17 | 120 | 0.4384 | 19 | 0.4370 | 90 | 621 |
| 0.8 | 42 | 118 | 0.4271 | 17 | 0.4256 | 90 | 549 |
| 0.8 | 101 | 118 | 0.4370 | 17 | 0.4356 | 90 | 468 |
| 1.0 | 17 | 117 | 0.4412 | 16 | 0.4399 | 90 | 520 |
| 1.0 | 42 | 118 | 0.4398 | 17 | 0.4385 | 90 | 525 |
| 1.0 | 101 | 122 | 0.4406 | 21 | 0.4393 | 90 | 580 |
| 1.2 | 17 | 118 | 0.4358 | 17 | 0.4347 | 90 | 336 |
| 1.2 | 42 | 119 | 0.4341 | 18 | 0.4330 | 90 | 318 |
| 1.2 | 101 | 119 | 0.4345 | 18 | 0.4333 | 90 | 318 |

| Resolution | NMI across seeds (mean of 3 pairs) | min | Louvain communities | Louvain Q | NMI Leiden-Louvain (seed 17) |
|---|---|---|---|---|---|
| 0.8 | 0.799 | 0.757 | 113 | 0.4235 | 0.725 |
| 1.0 | 0.759 | 0.739 | 119 | 0.4299 | 0.674 |
| 1.2 | 0.849 | 0.812 | 117 | 0.4216 | 0.674 |

Hierarchy (level 1 = Leiden at resolution 0.25 on the graph contracted by the level-0 headline partition: resolution 1.0, seed 17): 117 level-0 communities → 105 level-1 communities.


Whole-graph modularity on N1 is inflated: N1 has 2,936 connected components (414 isolates), and each small component is its own community. The LCC columns are the informative ones. Level 1: the original rule (resolution 1.0) merged nothing, so it was changed to 0.25 (dated change in the config) and run once. On N1 level 1 barely coarsens (most communities are tiny separate components); on N2 it collapses the connected core into one community of 1,837 of 2,047 organizations, so for N2 the 0.8/1.2 partitions are the more useful alternative levels.

**Largest N1 communities** (c-TF-IDF labels over member papers; hubs = highest PageRank in the community; brokers = highest participation coefficient / betweenness; names are researchers). Full tables: `communities/communities-N1.csv`.

| Community | Members | Top topic | Top methods | Hub | Broker (participation) | Broker (betweenness) |
|---|---|---|---|---|---|---|
| 0 | 616 | Computer vision | 2D CNN; 3DMM; GAN inversion; Experience Replay; semantic augmentation | Chengjie Wang | Jun Liu | Chengjie Wang |
| 1 | 553 | Multi-agent systems | Method of Equal Shares; Proportional Approval Voting; Thiele rules; mo | Warut Suksompong | Paul W. Goldberg | Hau Chan |
| 2 | 416 | Natural language processing and language models | contrastive loss function; Machine Unlearning; autoregressive model; a | Shu‐Tao Xia | Huaidong Zhang | Shu‐Tao Xia |
| 3 | 406 | Natural language processing and language models | Generative Adversarial Imitation Learning; mutual information learning | Yanghua Xiao | Weihua Luo | Xintao Wang |
| 4 | 396 | Computer vision | iterative algorithm; self-supervised contrastive learning; ranking los | Zhenguang Liu | Yaxiong Wang | Shouling Ji |
| 5 | 371 | Multimodal learning | interaction module; vision foundation models; BART; adaptive weighting | Xian‐Sheng Hua | Tong Lü | Shih‐Fu Chang |

**Largest N2 communities** (organizations)

| Community | Members | Top topic | Hub | Broker (participation) | Broker (betweenness) |
|---|---|---|---|---|---|
| 0 | 520 | Planning and reasoning | Centre National de la Recherche Scientifique | King Abdullah University of Science and Technology | Centre National de la Recherche Scientifique |
| 1 | 397 | Reinforcement learning | Carnegie Mellon University | Mohamed bin Zayed University of Artificial Intelligence | Google (United States) |
| 2 | 254 | Multimodal learning | Tsinghua University | Baidu (China) | Tencent (China) |
| 3 | 140 | Trustworthy machine learning | Xidian University | Singapore Management University | Xidian University |
| 4 | 133 | Multimodal learning | Zhejiang University | Nanjing University of Posts and Telecommunications | Zhejiang University |

Community labels are c-TF-IDF terms; generated titles belong to M3 (specification 6.2) and were not produced. Labels from rare terms (a few papers) are characteristic of c-TF-IDF and should be read with the member count.

**Rising researchers** (rule: 2024-2025 paper share at least 2.0 times the 2021-2023 share, at least 3 recent and 4 total papers; 484 researchers qualify, 147 of them new entrants with no 2021-2023 paper). Top 10 by recent papers:

| Researcher | 2024-25 papers | 2021-23 papers | share ratio | N1 community |
|---|---|---|---|---|
| Dongxiao He | 22 | 7 | 2.832 | 14 |
| Qingfu Zhang | 12 | 1 | 10.812 | 29 |
| Jingcai Guo | 12 | 2 | 5.406 | 24 |
| Songcan Chen | 12 | 5 | 2.162 | 18 |
| Xingcheng Fu | 11 | 2 | 4.956 | 15 |
| Mang Ye | 11 | 3 | 3.304 | 25 |
| Jiancheng Lv | 11 | 4 | 2.478 | 12 |
| Stan Ziqing Li | 11 | 4 | 2.478 | 56 |
| Qingyun Sun | 10 | 2 | 4.505 | 15 |
| Jiantao Zhou | 10 | 2 | 4.505 | 36 |

**Groups, by kind.** The application must state which kind a group is:

- *Organizations* (2047; 1462 flagged Wikipedia-notable, meaning a Wikidata match with an English Wikipedia page): largest by papers: Chinese Academy of Sciences (576); Zhejiang University (570); Tsinghua University (485); Peking University (442); University of Chinese Academy of Sciences (436).
- *Labs* (organization-anchored N1 communities: at least 10 members and one organization affiliating at least 40% of them; an approximation, not a verified research group): 124 found, e.g. University of Science and Technology of China (329 members, 50%); Institute of Computing Technology (54 members, 65%); Korea University (44 members, 48%); Politecnico di Milano (44 members, 57%); Korea University (43 members, 54%).
- *Leiden communities* of N1 and N2: tables above and `communities/communities-N*.csv` (117 N1 and 11 N2 communities with at least 20 members).
- *Parent organizations* (roll-up along PART_OF only; MEMBER_OF is not used; parents whose name contains "ministry" are skipped): 783 PART_OF edges, 48 skipped as ministry parents (a rule on the Wikidata class label would have flagged 78, including Tsinghua University and US federal departments; the name rule was declared before any roll-up), 378 parents with at least one child. Largest by papers: State Council of the People's Republic of China (33 units, 650 papers); Chinese Academy of Sciences (28 units, 626 papers); Zhejiang University (1 units, 570 papers); Tsinghua University (3 units, 490 papers); Peking University (2 units, 442 papers). Parents are not all universities: government bodies such as the State Council of the People's Republic of China appear as parents of research institutes; the 30 edges that only the class-label rule would flag (US federal departments, Tsinghua University and others) stay in.

Figure: `communities/community-sizes.svg` (rank-size plot of the headline communities; many tiny components produce the long tail).

## Trend metrics (specification 5.4)

Per subject and year: paper count, share of that year's 13,617-paper corpus (2,240 / 1,997 / 2,217 / 3,121 / 4,042 papers in 2021-2025), compound annual growth of the share 2021→2025, least-squares slope of the share with its p-value, year-over-year change, and class. Classes (declared in the config): emerging = at most 2 papers in 2021-2022 and at least 8 in 2024-2025; rising = positive slope with p ≤ 0.10, recent share at least 1.5 times the base share and at least 3 base papers; declining = negative slope with p ≤ 0.10, ratio ≤ 2/3 and at least 10 base papers; insufficient data below 15 papers in total; everything else stable. The classes are descriptive; no multiple-testing correction was applied.

| Subject kind | Subjects | rising | emerging | declining | stable | insufficient data (<15 papers) |
|---|---|---|---|---|---|---|
| Topic | 16 | 1 | 0 | 1 | 14 | 0 |
| Method | 954 | 5 | 21 | 11 | 53 | 864 |
| Task | 679 | 4 | 7 | 4 | 37 | 627 |
| Dataset | 371 | 2 | 1 | 5 | 18 | 345 |

**Topics** (base = papers 2021-2022, recent = papers 2024-2025)

- rising: Multimodal learning (367 → 1108)
- emerging: none
- declining: Probabilistic and Bayesian learning (66 → 69)

**Methods** (base = papers 2021-2022, recent = papers 2024-2025)

- rising: Large Language Models (LLMs) (7 → 126); U-Net (4 → 22); Graph Contrastive Learning (6 → 20); Federated Learning (6 → 18); Answer Set Programming (3 → 11)
- emerging: diffusion models (0 → 140); CLIP (2 → 66); Mamba (1 → 27); 3D Gaussian Splatting (0 → 24); GPT-4 (0 → 23)
- declining: deep neural networks (40 → 43); convolutional neural networks (39 → 32); graph convolutional network (31 → 28); adversarial training (27 → 27); generative adversarial networks (38 → 24)

**Tasks** (base = papers 2021-2022, recent = papers 2024-2025)

- rising: Medical Image Segmentation (7 → 25); Visual Question Answering (5 → 22); Out-of-Distribution Detection (3 → 15); language modeling (3 → 11)
- emerging: multi-view clustering (1 → 27); image editing (1 → 14); Deepfake Detection (2 → 13); image restoration (0 → 13); node classification tasks (2 → 11)
- declining: link prediction (24 → 18); image captioning (13 → 6); person re-identification (14 → 6); text classification (23 → 6)

**Datasets** (base = papers 2021-2022, recent = papers 2024-2025)

- rising: nuScenes (4 → 44); DomainNet (3 → 11)
- emerging: S3DIS (2 → 12)
- declining: ImageNet (70 → 56); CIFAR-10 (68 → 47); MNIST (26 → 16); MuJoCo (13 → 9); UCF101 (10 → 7)

Group interest (`trends/group-interest.csv`: 9165 group-subject rows for 192 organizations with at least 30 papers and 89 N1 communities with at least 50 members; topics, methods and tasks; datasets are skipped because coverage is too thin). Example, organizations with the highest revealed comparative advantage (RCA = the group's share of papers in the topic divided by the corpus share) on topics with at least 5 of the group's papers (this filter only trims the table below, not the CSV):

| Organization | Topic | group papers in topic | RCA | first active year |
|---|---|---|---|---|
| Guangdong University of Technology | Causal inference | 13 | 19.45 | 2021 |
| Huazhong Agricultural University | Optimization and learning theory | 8 | 11.50 | 2021 |
| Columbia University | Causal inference | 8 | 9.07 | 2021 |
| University of Amsterdam | Multi-agent systems | 7 | 8.24 | 2021 |
| Saarland University | Planning and reasoning | 22 | 8.05 | 2021 |
| Mohamed bin Zayed University of Artificial Intelligence | Causal inference | 6 | 8.02 | 2022 |
| Technical University of Munich | Multi-agent systems | 8 | 7.77 | 2021 |
| Université d'Artois | Planning and reasoning | 15 | 7.62 | 2021 |

Figure: `trends/topic-shares.svg` (share of each year's papers by topic; non-stable topics are labelled).

**Caveats that apply to every trend number**

- Only two venues (AAAI and IJCAI) are covered, so a trend is a trend in these proceedings, not in the field.
- Venue size changes from 2,240 papers in 2021 to 4,042 in 2025; shares correct for it, raw counts do not.
- Topic labels come from an embedding classifier with known limits; the topic evaluation is human_review_pending / AI-assessed.
- Method, task and dataset labels exist for only part of the papers (about 40%, 28% and 12%); a share is a share of all papers, so low coverage lowers every share.
- All enrichment quality figures (entity, relation and linking precision) are AI-assessed, not human annotation; Wilson intervals cover sampling error only.

## What was not done

- A simulated lattice baseline for ω (an analytic ring lattice is used and labelled approximate).
- Exact baseline path lengths on N4 (a 2,000-pivot sample is used; the real graph's L is exact).
- A goodness-of-fit bootstrap for the power-law fit.
- Betweenness on N3 and N4, eigenvector centrality on N3, and group interest for datasets.
- Generated community titles (M3).
- Any human validation of community labels, rising-researcher lists or trend classes.
- Personalized PageRank for the 4 parent topics (no HAS_TOPIC papers).

