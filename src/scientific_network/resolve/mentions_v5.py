"""Paper authorship mention decisions, distinct from historical v4 correction.

No fuzzy name-only merges. Names validate a position; stable provider IDs or a
paper-specific checksum-valid raw ORCID supply identity. Profile ORCID arrays
only quarantine, never select a paper identity. Decisions carry contradictions.
"""

from collections import Counter, defaultdict
from hashlib import sha256
import json
import re
import unicodedata

from scientific_network.collect.acquire import name_tokens, names_compatible
from scientific_network.collect.openalex_release import normalize_doi, title_similarity
from scientific_network.resolve.release import _roster_evidence, _work_evidence, short_id
from scientific_network.resolve.release_identity import collect_identity_evidence, valid_orcid

METHOD = "paper-mention-identity-v5.2"


def ordered_tokens(name):
    text = unicodedata.normalize("NFKD", name or "").casefold()
    return re.findall(r"[^\W_]+", "".join(c for c in text if not unicodedata.combining(c)))


def positional_name(official, raw):
    """Normalize scripts/diacritics/token order; initials require equal token counts.

    This is position compatibility only, never a canonical identity crosswalk.
    Full alternate spellings are deliberately abstained on.
    """
    if not isinstance(official, str) or not isinstance(raw, str):
        return None
    if names_compatible(official, raw):
        return "exact"
    a, b = name_tokens(official), name_tokens(raw)
    if not a or len(a) != len(b):
        return None
    # Match complete tokens first so initials cannot steal a complete anchor.
    common = Counter(a) & Counter(b)
    exact = sum(n for token, n in common.items() if len(token) > 1)
    left, right = list((Counter(a)-common).elements()), list((Counter(b)-common).elements())
    if not exact or not left:
        return None
    for token in sorted(left, key=lambda t: (-len(t), t)):
        choices = [x for x in right if (len(token)==1 and x.startswith(token)) or (len(x)==1 and token.startswith(x))]
        if not choices:
            return None
        right.remove(sorted(choices)[0])
    return "initials" if not right else None


def anchored_middle_expansion(official, raw, canonical):
    """Only alongside direct raw ORCID: preserve full tokens/order and endpoints."""
    if not isinstance(raw, str) or not isinstance(canonical, str) or not names_compatible(official, canonical):
        return False
    a, b = ordered_tokens(official), ordered_tokens(raw)
    if len(a) < 2 or not len(a) < len(b) <= len(a)+3 or a[0] != b[0] or a[-1] != b[-1]:
        return False
    if any(len(t) < 2 for t in a+b):
        return False
    it = iter(b)
    return all(any(x == t for x in it) for t in a)


def _digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def work_rejection(row):
    if row["match"]["status"] != "matched":
        return "work_not_matched"
    oa = row.get("openalex") or {}
    if not re.fullmatch(r"W\d+", short_id(oa.get("id")) or ""):
        return "work_identifier_missing_or_invalid"
    if not normalize_doi(row.get("doi")) or normalize_doi(row["doi"]) != normalize_doi(oa.get("doi")):
        return "work_doi_disagreement"
    if len(row["roster"]["authors"]) != len(oa.get("authorships") or []):
        return "work_author_count_disagreement"
    if title_similarity(row["roster"]["title"], oa.get("title")) < .9:
        return "work_title_disagreement"
    return None


def resolve_mentions(rows, baseline=None):
    """One deterministic decision per official mention, including unmatched works.

    ``baseline`` is a frozen GraphArtifact used only to avoid creating an ORCID
    identity already claimed by a different uncorroborated provider identity.
    It supplies no labels and cannot override contradictory source evidence.
    """
    if len({r["paper_id"] for r in rows}) != len(rows):
        raise ValueError("duplicate paper IDs in mention source")
    identity = collect_identity_evidence(rows)  # same full-source policy as release.py/v4
    blocked = dict(identity["withheld"])
    raw_by_id, raw_groups, malformed_ids = defaultdict(set), defaultdict(list), set()
    raw_anchors, provider_names = set(), defaultdict(set)
    for row in rows:
        if row["match"]["status"] != "matched":
            continue
        source_ids = [short_id((a.get("author") or {}).get("id")) for a in row["openalex"]["authorships"]]
        for i, a in enumerate(row["openalex"]["authorships"]):
            aid = short_id((a.get("author") or {}).get("id"))
            raw = a.get("raw_orcid")
            orcid = valid_orcid(raw)
            if aid and not work_rejection(row) and i<len(row["roster"]["authors"]) and positional_name(row["roster"]["authors"][i],a.get("raw_author_name")):
                provider_names[aid].add(row["roster"]["authors"][i])
            if raw and not orcid and aid:
                malformed_ids.add(aid)
            if orcid:
                if aid:
                    raw_by_id[aid].add(orcid)
                if not work_rejection(row) and i < len(row["roster"]["authors"]):
                    raw_groups[orcid].append((row["paper_id"], i, aid, row["roster"]["authors"][i]))
                    official_name = row["roster"]["authors"][i]
                    author = a.get("author") or {}
                    if (not aid or source_ids.count(aid)==1) and (
                            positional_name(official_name,a.get("raw_author_name")) or
                            anchored_middle_expansion(official_name,a.get("raw_author_name"),author.get("display_name"))):
                        raw_anchors.add((row["paper_id"], i))
    for aid, values in raw_by_id.items():
        if len(values | identity["orcids"].get(aid, set())) > 1:
            blocked[aid] = "author_id_conflicting_paper_or_profile_orcids"
    for aid in malformed_ids:
        blocked[aid] = "author_id_malformed_paper_orcid"
    name_inconsistencies = {aid for aid,names in provider_names.items()
                            if any(not positional_name(a,b) for a in names for b in names)}
    for aid in sorted(name_inconsistencies):
        blocked.setdefault(aid,"author_id_incompatible_name_variants")
    baseline_claims = defaultdict(set)
    if baseline:
        for n in baseline.nodes:
            if n.label == "Researcher" and valid_orcid(n.properties.get("orcid")):
                baseline_claims[valid_orcid(n.properties["orcid"])].add(n.id)
    raw_targets, raw_conflicts, aliases = {}, {}, {}
    provider_raw_mentions=defaultdict(list)
    for orcid,group in raw_groups.items():
        for paper,index,aid,name in group:
            if aid:
                provider_raw_mentions[aid].append((orcid,name))
    ambiguous_accounts=set()
    for aid,group in provider_raw_mentions.items():
        if any(left!=right and (positional_name(a,b) or anchored_middle_expansion(a,b,a)
                                or anchored_middle_expansion(b,a,b))
               for left,a in group for right,b in group):
            ambiguous_accounts.update(orcid for orcid,name in group)
    for orcid, group in sorted(raw_groups.items()):
        if orcid in ambiguous_accounts:
            raw_conflicts[orcid]="multiple_paper_orcid_accounts_identity_uncertain"
            continue
        names = [g[3] for g in group]
        same_paper = Counter(g[0] for g in group)
        if any(n > 1 for n in same_paper.values()):
            raw_conflicts[orcid] = "raw_orcid_repeated_in_paper"
            continue
        if any(not positional_name(a, b) for a in names for b in names):
            raw_conflicts[orcid] = "raw_orcid_incompatible_names"
            continue
        safe_ids = {g[2] for g in group if g[2] and re.fullmatch(r"A\d+",g[2]) and g[2] not in blocked and (g[0],g[1]) in raw_anchors}
        supported = {"researcher:openalex:"+a for a in safe_ids}
        if baseline_claims[orcid] - supported:
            raw_conflicts[orcid] = "raw_orcid_existing_identity_requires_crosswalk"
            continue
        target = (next(iter(supported)) if len(supported)==1 else "researcher:orcid:"+orcid)
        raw_targets[orcid] = target
        # Crosswalk only independent raw ORCID records, never observed-array aliases.
        if len(safe_ids)>1:
            aliases.update({aid: target for aid in safe_ids})
    decisions = []
    for row in sorted(rows, key=lambda r: r["paper_id"]):
        paper, official = row["paper_id"], row["roster"]["authors"]
        oa = row.get("openalex") or {}
        authorships = oa.get("authorships") or []
        ids = [short_id((a.get("author") or {}).get("id")) for a in authorships]
        repeated = {a for a,n in Counter(ids).items() if a and n>1}
        incompatible = sum(not positional_name(n,a.get("raw_author_name"))
                           for n,a in zip(official,authorships))
        damaged = incompatible>1 or bool(repeated)
        for index, name in enumerate(official):
            a = authorships[index] if index<len(authorships) else {}
            author = a.get("author") or {}
            aid, raw_orcid = short_id(author.get("id")), valid_orcid(a.get("raw_orcid"))
            raw_name = a.get("raw_author_name")
            kind = positional_name(name,raw_name)
            expansion = bool(raw_orcid and anchored_middle_expansion(name,raw_name,author.get("display_name")))
            roster_ev = _roster_evidence(row)
            evidence = [{"evidence_id": roster_ev.id, "raw_sha256": roster_ev.raw_sha256,
                         "source_url": str(roster_ev.source_url), "retrieved_at": roster_ev.retrieved_at.isoformat(),
                         "source_locator": roster_ev.source_locator, "field": f"official_byline[{index}]"}]
            if oa:
                ev = _work_evidence(row)
                evidence.append({"evidence_id": ev.id, "raw_sha256": ev.raw_sha256,
                                 "source_url": str(ev.source_url) if re.fullmatch(r"W\d+",short_id(oa.get("id")) or "") else oa["source"].get("url","https://api.openalex.org/works"),
                                 "retrieved_at": ev.retrieved_at.isoformat(),
                                 "source_locator": ev.source_locator,
                                 "field": f"authorships[{index}]" if index<len(authorships) else "authorships",
                                 "requested_authorship_position_present": index<len(authorships),
                                 "work_id": oa.get("id")})
            indicators = []
            if aid in blocked:
                indicators.append(blocked[aid])
            if aid in repeated:
                indicators.append("provider_id_repeated_in_paper")
            if raw_orcid and valid_orcid(author.get("orcid")) not in {None,raw_orcid}:
                indicators.append("paper_raw_orcid_disagrees_with_profile_selection")
            if damaged:
                indicators.append("damaged_provider_byline")
            reason, state, canonical = work_rejection(row), "ambiguous", None
            if reason:
                state = "unresolved" if reason == "work_not_matched" else "ambiguous"
            elif aid in repeated:
                reason = "provider_id_repeated_in_paper"
            elif a.get("raw_orcid") and not raw_orcid:
                reason = "malformed_paper_raw_orcid"
            elif aid and not re.fullmatch(r"A\d+",aid):
                reason = "provider_author_identifier_wrong_type"
            elif not kind and not expansion:
                reason = "raw_name_incompatible" if raw_name else "raw_name_missing"
            elif damaged and (kind != "exact" or
                    sum(names_compatible(name, n) for n in official) != 1 or
                    sum(names_compatible(name, x.get("raw_author_name") or "") for x in authorships) != 1):
                reason = "position_not_unique_on_damaged_byline"
            elif kind == "initials" and (sum(bool(positional_name(name,x.get("raw_author_name"))) for x in authorships)!=1 or
                    sum(bool(positional_name(n,raw_name)) for n in official)!=1):
                reason = "initials_position_not_unique"
            elif raw_orcid in raw_conflicts:
                reason = raw_conflicts[raw_orcid]
            elif raw_orcid and raw_orcid in raw_targets:
                canonical, state, reason = raw_targets[raw_orcid], "resolved", "paper_raw_orcid_name_anchored"
            elif aid in blocked:
                reason = blocked[aid]
            elif not aid:
                state, reason = "unresolved", "no_provider_id_or_paper_raw_orcid"
            elif kind:
                canonical, state = aliases.get(aid,"researcher:openalex:"+aid), "resolved"
                reason = "unique_raw_position_recovered" if damaged else "provider_id_raw_name_position"
            else:
                reason = "insufficient_identity_evidence"
            decision = {
                "mention_id": "mention:"+_digest([paper,index+1])[:24],
                "paper_id": paper,"author_position": index+1,"official_name": name,
                "venue_id": row["venue_id"],"year": row["year"],
                "source_author_id": aid,"source_work_id": short_id(oa.get("id")),
                "was_v4_global_identity_withheld": aid in identity["withheld"],
                "raw_author_name": raw_name,"canonical_display_name": author.get("display_name"),
                "paper_raw_orcid": raw_orcid,"raw_orcid_source_value": a.get("raw_orcid"),
                "profile_orcid": author.get("orcid"),"profile_observed_orcids": author.get("observed_orcids"),
                "canonical_researcher_id": canonical,"resolution_state": state,
                "matching_method": kind or ("raw_orcid_middle_expansion" if expansion else None),
                "method_version": METHOD,"decision_reason": reason,
                "conflict_indicators": sorted(indicators),"review_required": state != "resolved",
                "supporting_evidence": evidence,
                "identity_conflict_record_id": "provider-conflict:"+aid if aid in blocked else None,
                "contradicting_evidence": [{"indicator": indicator,
                    "source_author_id": aid,"field": "author.orcid+author.observed_orcids+raw_orcid",
                    "all_normalized_provider_orcids": sorted(identity["orcids"].get(aid,set()) | raw_by_id.get(aid,set())),
                    "source_record": evidence[-1]} for indicator in sorted(indicators)],
                "evidence_scope": "cached_work_authorship_and_official_byline_not_independent_owner_verification",
            }
            decision["decision_id"] = "identity-decision:"+_digest(decision)[:24]
            decisions.append(decision)
    canonical_positions = defaultdict(list)
    for d in decisions:
        if d["resolution_state"]=="resolved":
            canonical_positions[d["paper_id"],d["canonical_researcher_id"]].append(d)
    for group in canonical_positions.values():
        if len(group)>1:
            for d in group:
                d.update({"resolution_state":"ambiguous","canonical_researcher_id":None,
                          "decision_reason":"canonical_id_repeated_in_paper","review_required":True})
                d["conflict_indicators"].append("canonical_id_repeated_in_paper")
                d["conflict_indicators"].sort()
                d.pop("decision_id")
                d["decision_id"]="identity-decision:"+_digest(d)[:24]
    return decisions, {"shared_identity_counts": identity["counts"],
                       "provider_withholding": dict(sorted(blocked.items())),
                       "corroborated_provider_crosswalks": dict(sorted(aliases.items())),
                       "paper_raw_orcid_conflicts": dict(sorted(raw_conflicts.items())),
                       "incompatible_provider_names": {a:sorted(provider_names[a]) for a in sorted(name_inconsistencies)},
                       "provider_conflict_records": {"provider-conflict:"+a:{"author_id":a,"reason":why,
                           "normalized_orcids":sorted(identity["orcids"].get(a,set()) | raw_by_id.get(a,set())),
                           "compatible_position_official_names":sorted(provider_names.get(a,set())),
                           "source_review_key":a} for a,why in sorted(blocked.items())},
                       "profile_evidence_review": identity["review"]}
