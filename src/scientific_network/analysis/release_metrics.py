"""D040 release-specific descriptive metrics over the frozen graph.

These measures describe accepted graph support. Topic measures remain provisional
because the release topic labels have not received independent human review.
"""

from collections import Counter, defaultdict

from scientific_network.contracts import GraphArtifact, Relation


SECTORS = ("academia", "industry", "government", "nonprofit", "unknown")
YEARS = tuple(range(2021, 2026))


def _round(value: float) -> float:
    return round(float(value), 12)


def _paper_record(paper_id: str, nodes: dict, paper_venues: dict, venues: dict) -> dict:
    paper = nodes[paper_id]
    properties = paper.properties
    venue_id = paper_venues.get(paper_id)
    return {
        "paper_id": paper_id,
        "title": paper.name,
        "year": properties.get("year"),
        "venue": venues[venue_id].name if venue_id in venues else venue_id,
        "doi": properties.get("doi"),
        "official_url": properties.get("official_url"),
        "openalex_id": properties.get("openalex_id"),
    }


def _core_paper_support(edge, evidence_by_id: dict, core_papers: set[str]) -> set[str]:
    support = set()
    for evidence_id in edge.evidence_ids:
        evidence = evidence_by_id.get(evidence_id)
        if evidence is not None:
            support.update(evidence.support_paper_ids)
    return support & core_papers


def compute_release_metrics(graph: GraphArtifact, projections: dict, config: dict) -> dict:
    """Compute release report metrics from accepted core graph records."""
    nodes = {node.id: node for node in graph.nodes}
    papers = {
        node.id: node
        for node in graph.nodes
        if node.label.value == "Paper" and node.properties.get("is_core") is True
        and node.properties.get("year") in YEARS
    }
    core_papers = set(papers)
    researchers = {node.id: node for node in graph.nodes if node.label.value == "Researcher"}
    organizations = {node.id: node for node in graph.nodes if node.label.value == "Organization"}
    topics = {node.id: node for node in graph.nodes if node.label.value == "Topic"}
    venues = {node.id: node for node in graph.nodes if node.label.value == "Venue"}
    evidence_by_id = {record.id: record for record in graph.evidence}

    paper_venues = {}
    authors_by_paper = defaultdict(set)
    topics_by_paper = defaultdict(set)
    citations = []
    coauthorships = []
    organization_collaborations = []
    organization_topic_edges = []
    for edge in graph.edges:
        if edge.relation == Relation.PUBLISHED_IN and edge.source_id in core_papers:
            paper_venues[edge.source_id] = edge.target_id
        elif edge.relation == Relation.AUTHORED and edge.target_id in core_papers:
            if edge.source_id in researchers:
                authors_by_paper[edge.target_id].add(edge.source_id)
        elif edge.relation == Relation.HAS_TOPIC and edge.source_id in core_papers:
            if edge.target_id in topics:
                topics_by_paper[edge.source_id].add(edge.target_id)
        elif edge.relation == Relation.CITES and edge.source_id in core_papers and edge.target_id in core_papers:
            citations.append(edge)
        elif edge.relation == Relation.COAUTHORED_WITH:
            coauthorships.append(edge)
        elif edge.relation == Relation.COLLABORATED_WITH:
            organization_collaborations.append(edge)
        elif edge.relation == Relation.CONTRIBUTES_TO_TOPIC:
            organization_topic_edges.append(edge)

    paper_rows = {
        paper_id: _paper_record(paper_id, nodes, paper_venues, venues)
        for paper_id in papers
    }
    annual_researchers = defaultdict(set)
    annual_papers = Counter()
    for paper_id, paper in papers.items():
        year = paper.properties["year"]
        annual_papers[year] += 1
        annual_researchers[year].update(authors_by_paper.get(paper_id, ()))

    first_pair_year = {}
    for edge in coauthorships:
        support_papers = _core_paper_support(edge, evidence_by_id, core_papers)
        support_years = [papers[paper_id].properties["year"] for paper_id in support_papers]
        if support_years:
            pair = tuple(sorted((edge.source_id, edge.target_id)))
            first_pair_year[pair] = min(support_years)
    new_pairs_by_year = Counter(first_pair_year.values())
    annual = [
        {
            "year": year,
            "paper_count": annual_papers[year],
            "active_researcher_count": len(annual_researchers[year]),
            "new_collaboration_pair_count": new_pairs_by_year[year],
        }
        for year in YEARS
    ]

    # Count sector/country mixing as distinct organization-pair × core-paper
    # supports, using the derived R8 evidence ledger rather than aggregate R2 edges.
    sector_matrix = {(row, col): 0 for row in SECTORS for col in SECTORS}
    country_counts = Counter()
    sector_topic_pair_papers = defaultdict(set)
    for edge in organization_collaborations:
        left, right = organizations.get(edge.source_id), organizations.get(edge.target_id)
        if left is None or right is None:
            continue
        support_papers = _core_paper_support(edge, evidence_by_id, core_papers)
        left_sector = left.properties.get("sector", "unknown")
        right_sector = right.properties.get("sector", "unknown")
        left_sector = left_sector if left_sector in SECTORS else "unknown"
        right_sector = right_sector if right_sector in SECTORS else "unknown"
        sector_matrix[left_sector, right_sector] += len(support_papers)
        if left_sector != right_sector:
            sector_matrix[right_sector, left_sector] += len(support_papers)
        left_country = left.properties.get("country_code") or "UNKNOWN"
        right_country = right.properties.get("country_code") or "UNKNOWN"
        # A same-country institution pair is domestic. A cross-country pair
        # contributes to each direction so the table is an undirected symmetric
        # mixing matrix; this prevents un-oriented country tuples double counting
        # only one matrix cell while preserving their support.
        if str(left_country).upper() == str(right_country).upper():
            country_pair = (str(left_country).upper(), str(right_country).upper())
            country_counts[country_pair] += len(support_papers)
        else:
            first = tuple(sorted((str(left_country).upper(), str(right_country).upper())))
            second = (first[1], first[0])
            country_counts[first] += len(support_papers)
            country_counts[second] += len(support_papers)

        if {left_sector, right_sector} == {"academia", "industry"}:
            for paper_id in support_papers:
                for topic_id in topics_by_paper.get(paper_id, ()):
                    key = (edge.source_id, edge.target_id, topic_id)
                    sector_topic_pair_papers[key].add(paper_id)

    sector_mixing = {
        "categories": list(SECTORS),
        "counting_rule": "distinct accepted COLLABORATED_WITH organization-pair by core-paper supports; symmetric matrix",
        "matrix": [
            {"row_sector": row, "column_sector": col, "pair_paper_support_count": sector_matrix[row, col]}
            for row in SECTORS for col in SECTORS
        ],
    }
    country_pairs = [
        {"country_a": pair[0], "country_b": pair[1], "pair_paper_support_count": count}
        for pair, count in sorted(country_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    # Topic shares are fractional across labels. Keep the all-paper coverage
    # denominator beside the labeled-paper denominator.
    topic_slices = defaultdict(lambda: {"papers": set(), "labeled_papers": set(), "raw": Counter(), "fractional": Counter()})
    for paper_id, paper in papers.items():
        year = paper.properties["year"]
        venue_id = paper_venues.get(paper_id)
        if not venue_id:
            continue
        key = (year, venue_id)
        topic_slices[key]["papers"].add(paper_id)
        paper_topics = sorted(topics_by_paper.get(paper_id, ()))
        if paper_topics:
            topic_slices[key]["labeled_papers"].add(paper_id)
            fraction = 1.0 / len(paper_topics)
            for topic_id in paper_topics:
                topic_slices[key]["raw"][topic_id] += 1
                topic_slices[key]["fractional"][topic_id] += fraction
    topic_shares = []
    for (year, venue_id), values in sorted(topic_slices.items()):
        labeled_count = len(values["labeled_papers"])
        all_count = len(values["papers"])
        for topic_id in sorted(values["fractional"]):
            topic_shares.append({
                "year": year,
                "venue": venues[venue_id].name if venue_id in venues else venue_id,
                "venue_id": venue_id,
                "topic_id": topic_id,
                "topic": topics[topic_id].name,
                "paper_count": values["raw"][topic_id],
                "fractional_paper_count": _round(values["fractional"][topic_id]),
                "labeled_paper_count": labeled_count,
                "all_core_paper_count": all_count,
                "topic_label_coverage": _round(labeled_count / all_count) if all_count else 0.0,
                "share_of_fractional_topic_mass": _round(values["fractional"][topic_id] / labeled_count) if labeled_count else 0.0,
            })

    # Organization portfolios use the schema's fractional allocation across
    # labels and distinct paper-supported organizations.
    organizations_by_paper = defaultdict(set)
    for observation in graph.affiliation_observations:
        if observation.paper_id in core_papers and observation.organization_id in organizations:
            organizations_by_paper[observation.paper_id].add(observation.organization_id)
    organization_topic_papers = defaultdict(set)
    organization_fractional = Counter()
    organization_fractional_denominator = Counter()
    organization_paper_denominator = defaultdict(set)
    for paper_id in core_papers:
        paper_topics = topics_by_paper.get(paper_id, set())
        paper_orgs = organizations_by_paper.get(paper_id, set())
        if not paper_topics or not paper_orgs:
            continue
        fraction = 1.0 / (len(paper_topics) * len(paper_orgs))
        for organization_id in paper_orgs:
            organization_paper_denominator[organization_id].add(paper_id)
            organization_fractional_denominator[organization_id] += 1.0 / len(paper_orgs)
            for topic_id in paper_topics:
                organization_topic_papers[organization_id, topic_id].add(paper_id)
                organization_fractional[organization_id, topic_id] += fraction
    organization_topic_profiles = []
    organization_topic_candidates = []
    for edge in organization_topic_edges:
        organization = organizations.get(edge.source_id)
        topic = topics.get(edge.target_id)
        if organization is None or topic is None:
            continue
        support_papers = _core_paper_support(edge, evidence_by_id, core_papers)
        declared_support = edge.properties.get("support_count")
        if declared_support != len(support_papers):
            raise ValueError(f"R10 support count disagrees with evidence for edge {edge.edge_id}")
        denominator = len(organization_paper_denominator[organization.id])
        profile = {
            "organization_id": organization.id,
            "organization": organization.name,
            "sector": organization.properties.get("sector", "unknown"),
            "topic_id": topic.id,
            "topic": topic.name,
            "supported_paper_count": len(support_papers),
            "organization_labeled_paper_denominator": denominator,
            "fractional_portfolio_denominator": _round(organization_fractional_denominator[organization.id]),
            "fractional_topic_portfolio_share": _round(
                organization_fractional[organization.id, topic.id]
                / organization_fractional_denominator[organization.id]
            ) if organization_fractional_denominator[organization.id] else 0.0,
        }
        organization_topic_profiles.append(profile)
        organization_topic_candidates.append({
            **profile,
            "supporting_papers": [paper_rows[paper_id] for paper_id in sorted(support_papers)[:5]],
        })
    organization_topic_profiles.sort(
        key=lambda item: (-item["supported_paper_count"], item["topic_id"], item["organization_id"])
    )
    organization_topic_candidates.sort(
        key=lambda item: (-item["supported_paper_count"], item["topic_id"], item["organization_id"])
    )

    academia_industry_pairs = []
    for (left_id, right_id, topic_id), support_papers in sector_topic_pair_papers.items():
        left, right = organizations[left_id], organizations[right_id]
        if left.properties.get("sector") == "industry":
            left, right = right, left
            left_id, right_id = right_id, left_id
        academia_industry_pairs.append({
            "academia_organization_id": left_id,
            "academia_organization": left.name,
            "industry_organization_id": right_id,
            "industry_organization": right.name,
            "topic_id": topic_id,
            "topic": topics[topic_id].name,
            "supported_paper_count": len(support_papers),
            "supporting_papers": [paper_rows[paper_id] for paper_id in sorted(support_papers)[:5]],
        })
    academia_industry_pairs.sort(
        key=lambda item: (-item["supported_paper_count"], item["topic_id"], item["academia_organization_id"], item["industry_organization_id"])
    )

    # In-scope citation influence is descriptive only: no age/exposure correction.
    in_degree = Counter(edge.target_id for edge in citations)
    pagerank = projections.get("core_citations", {}).get("centrality_scores", {}).get("pagerank", {})
    cited_records = []
    for paper_id in core_papers:
        cited_records.append({
            **paper_rows[paper_id],
            "in_degree": in_degree[paper_id],
            "pagerank": _round(pagerank.get(paper_id, 0.0)),
        })
    top_by_indegree = sorted(cited_records, key=lambda row: (-row["in_degree"], -row["pagerank"], row["paper_id"]))[:25]
    top_by_pagerank = sorted(cited_records, key=lambda row: (-row["pagerank"], -row["in_degree"], row["paper_id"]))[:25]

    # Community-topic profiles use the first frozen seed/resolution in config;
    # this is a descriptive slice, while all configured runs remain in projections.
    community_runs = projections.get("researcher_collaboration", {}).get("communities", [])
    seeds = config["communities"]["seeds"]
    resolutions = config["communities"]["resolutions"]
    selected_run = next((run for run in community_runs if run["seed"] == seeds[0] and run["resolution"] == float(resolutions[0])), None)
    if selected_run is None and community_runs:
        selected_run = community_runs[0]
    researcher_community = {}
    community_members = []
    if selected_run is not None:
        raw_groups = selected_run.get("communities", [])
        for index, members in enumerate(raw_groups):
            community_id = f"community:{index:05d}"
            community_members.append((community_id, members))
            for researcher_id in members:
                researcher_community[researcher_id] = community_id
    papers_by_community = defaultdict(set)
    for paper_id, authors in authors_by_paper.items():
        for researcher_id in authors:
            community_id = researcher_community.get(researcher_id)
            if community_id is not None:
                papers_by_community[community_id].add(paper_id)
    community_profiles = {}
    for community_id, members in community_members:
        paper_ids = papers_by_community[community_id]
        topic_paper_counts = Counter()
        topic_fractional = Counter()
        labeled_papers = set()
        for paper_id in paper_ids:
            paper_topics = topics_by_paper.get(paper_id, set())
            if not paper_topics:
                continue
            labeled_papers.add(paper_id)
            fraction = 1.0 / len(paper_topics)
            for topic_id in paper_topics:
                topic_paper_counts[topic_id] += 1
                topic_fractional[topic_id] += fraction
        top_topics = [
            {
                "topic_id": topic_id,
                "topic": topics[topic_id].name,
                "paper_count": topic_paper_counts[topic_id],
                "fractional_paper_count": _round(topic_fractional[topic_id]),
                "share_of_fractional_topic_mass": _round(topic_fractional[topic_id] / len(labeled_papers)) if labeled_papers else 0.0,
            }
            for topic_id in sorted(topic_fractional, key=lambda key: (-topic_fractional[key], key))[:5]
        ]
        community_profiles[community_id] = {
            "community_id": community_id,
            "member_count": len(members),
            "paper_count": len(paper_ids),
            "topic_labeled_paper_count": len(labeled_papers),
            "top_topics": top_topics,
        }
    selected_community_profiles = sorted(
        community_profiles.values(), key=lambda item: (-item["member_count"], item["community_id"])
    )[:20]
    researcher_nodes_by_score = projections.get("researcher_collaboration", {}).get("top_betweenness", [])
    bridge_researchers = []
    for item in researcher_nodes_by_score[:25]:
        researcher = researchers.get(item["node_id"])
        community_id = researcher_community.get(item["node_id"])
        profile = community_profiles.get(community_id)
        bridge_researchers.append({
            "researcher_id": item["node_id"],
            "researcher": researcher.name if researcher else item["node_id"],
            "betweenness": item["score"],
            "community_id": community_id,
            "community_member_count": profile["member_count"] if profile else None,
            "community_top_topics": profile["top_topics"] if profile else [],
        })

    degree = {researcher_id: 0 for researcher_id in researchers}
    for edge in coauthorships:
        if edge.source_id in degree and edge.target_id in degree:
            degree[edge.source_id] += 1
            degree[edge.target_id] += 1
    degree_frequency = Counter(degree.values())
    degree_ccdf = []
    at_least = len(degree)
    for value in range(max(degree_frequency, default=0) + 1):
        if value:
            at_least -= degree_frequency[value - 1]
        degree_ccdf.append({
            "degree": value,
            "researcher_count_at_least": at_least,
            "fraction_at_least": _round(at_least / len(degree)) if degree else 0.0,
        })

    component_sizes = projections.get("researcher_collaboration", {}).get("weak_or_undirected_component_sizes", [])
    return {
        "method_version": "d040-release-metrics-v1",
        "evidence_scope": "accepted core graph records; all topic results use inferred labels awaiting independent human review",
        "annual_counts": {
            "year_scope": list(YEARS),
            "new_collaboration_rule": "one accepted COAUTHORED_WITH pair counted in its earliest supported core-paper year",
            "rows": annual,
        },
        "researcher_degree_ccdf": {
            "projection": "Researcher–COAUTHORED_WITH–Researcher",
            "node_denominator": len(researchers),
            "includes_isolates": True,
            "rows": degree_ccdf,
        },
        "researcher_component_sizes": {
            "projection": "Researcher–COAUTHORED_WITH–Researcher",
            "component_count": len(component_sizes),
            "sizes_descending": component_sizes,
        },
        "sector_mixing": sector_mixing,
        "country_pair_collaborations": {
            "counting_rule": "distinct accepted COLLABORATED_WITH organization-pair by core-paper supports; unknown country retained",
            "rows": country_pairs,
        },
        "topic_shares_by_year_venue": {
            "counting_rule": "each labeled paper contributes 1/k to each of its k accepted inferred topic labels; shares normalize over labeled papers",
            "rows": topic_shares,
        },
        "cited_papers": {
            "projection": "directed core-paper CITES core-paper; current acquired in-scope snapshot",
            "ranking_limitation": "raw in-degree and PageRank are not exposure-time normalized",
            "top_by_in_degree": top_by_indegree,
            "top_by_pagerank": top_by_pagerank,
        },
        "bridge_researchers": {
            "projection": "Researcher–COAUTHORED_WITH–Researcher",
            "betweenness_method": "configured approximate NetworkX betweenness with inverse positive fractional strength distance",
            "community_topic_partition": {
                "algorithm": selected_run.get("algorithm") if selected_run else None,
                "seed": selected_run.get("seed") if selected_run else None,
                "resolution": selected_run.get("resolution") if selected_run else None,
                "topic_rule": "deduplicate papers within each community; fraction each topic-labeled paper across its accepted inferred labels",
            },
            "top_researchers": bridge_researchers,
            "community_topic_profiles_top_20_by_size": selected_community_profiles,
        },
        "academia_industry_topic_pair_candidates": academia_industry_pairs[:50],
        "organization_topic_profiles": organization_topic_profiles,
        "organization_topic_comparison_candidates": organization_topic_candidates[:50],
    }
