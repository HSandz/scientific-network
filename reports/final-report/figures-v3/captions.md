# Phase 6 figure captions

### Researcher collaboration degree CCDF

Projection: Researcher–COAUTHORED_WITH–Researcher. Filter: all accepted base graph edges. Counting: unique coauthor neighbors; denominator includes all resolved researchers, including isolates. Graph version: release-9d4a6fb20f63.

### Researcher collaboration component sizes

Projection: Researcher–COAUTHORED_WITH–Researcher. Filter: all accepted base graph edges. Counting: connected components over all resolved researchers, including isolates. Graph version: release-9d4a6fb20f63.

### Topic profiles of largest researcher communities

Projection: Researcher–COAUTHORED_WITH–Researcher, Louvain seed 17 and resolution 0.8. Filter: all accepted base graph edges; topics are inferred HAS_TOPIC labels. Counting: distinct papers per community, each fractionally allocated across its labels; top 12 communities are plotted, selected from the top 20 by membership. Only stored top-five topics per community are shown; grey means outside that stored profile, not zero support. Graph version: release-9d4a6fb20f63.

### Organization collaboration by sector

Projection: Organization–COLLABORATED_WITH–Organization. Filter: all accepted base R8 edges. Counting: distinct organization-pair by core-paper supports; the matrix is symmetric and includes unknown sector. Graph version: release-9d4a6fb20f63.

### Inferred topic portfolio trends, 2021–2025

Projection: core Paper–HAS_TOPIC–Topic. Filter: core papers in AAAI and IJCAI, 2021–2025; inferred labels remain pending review. Counting: each labeled paper contributes 1/k to each of k labels; shares normalize over labeled papers across both venues in each year. Lines show the eight largest topics by fractional mass. Graph version: release-9d4a6fb20f63.

### Most cited papers within the release corpus

Projection: directed core Paper–CITES–Paper, citing to cited. Filter: both endpoints are in-scope core papers. Counting: distinct in-scope citing papers (in-degree); citations outside the release corpus are excluded and older papers have more exposure time. Graph version: release-9d4a6fb20f63.
