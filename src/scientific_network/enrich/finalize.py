"""Combine surface-form merging and Wikipedia/Wikidata links into the final entity nodes (E2 steps 3-5)."""

from collections import defaultdict

from scientific_network.enrich.entities import aggregate_entities, entity_id


def qid_groups(pre_nodes: list[dict], links: dict[str, dict]) -> dict[tuple[str, str], tuple[str, str]]:
    """Map every key of nodes that link to the same (type, QID) onto the smallest key of the group."""
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for node in pre_nodes:
        link = links.get(node["id"])
        if link and link.get("linked") and link.get("wikibase_item"):
            groups[(node["type"], link["wikibase_item"])].append(node)
    mapping = {}
    for (entity_type, _qid), members in groups.items():
        if len(members) < 2:
            continue
        representative = min(min(m["keys"]) for m in members)
        for member in members:
            for key in member["keys"]:
                if key != representative:
                    mapping[(entity_type, key)] = (entity_type, representative)
    return mapping


def finalize_entities(mentions: list[dict], embedding_merge: dict, pre_nodes: list[dict], links: dict[str, dict], *,
                      min_papers: int, enrichment_version: str) -> dict:
    """Return graph nodes, the (type, key) -> node ID lookup and counts after the QID merge."""
    combined = dict(embedding_merge)
    for source, target in qid_groups(pre_nodes, links).items():
        combined[source] = target
    # a key mapped by the embedding merge may also be a QID source: resolve chains once
    for source, target in list(combined.items()):
        combined[source] = combined.get(target, target)
    aggregated = aggregate_entities(mentions, combined, min_papers=min_papers)
    pre_by_key = {(n["type"], k): n for n in pre_nodes for k in n["keys"]}
    nodes, lookup = [], {}
    for item in aggregated["nodes"]:
        link = None
        for key in item["keys"]:
            pre = pre_by_key.get((item["type"], key))
            if pre and links.get(pre["id"], {}).get("linked"):
                link = links[pre["id"]]
                break
        linked = bool(link)
        node_id = f"{item['type'].lower()}:{link['wikibase_item']}" if linked else entity_id(item["type"], item["key"])
        props = {"key": item["key"], "paper_count": item["paper_count"], "linked": linked, "surfaces": item["surfaces"],
                 "enrichment_version": enrichment_version, "is_core": False, "layer": "enrichment"}
        if linked:
            props.update({"wikidata_qid": link["wikibase_item"], "wikipedia_title": link["wikipedia_title"],
                          "wikipedia_url": link["wikipedia_url"], "wikipedia_revision_id": link["revision_id"],
                          "link_score": link["link_score"]})
        nodes.append({"id": node_id, "label": item["type"], "name": item["name"], "properties": props})
        for key in item["keys"]:
            lookup[(item["type"], key)] = node_id
    ids = [n["id"] for n in nodes]
    if len(ids) != len(set(ids)):
        raise ValueError("node ID collision after the QID merge")
    return {"nodes": nodes, "lookup": lookup, "below_threshold": aggregated["below_threshold"], "groups": aggregated["groups"]}
