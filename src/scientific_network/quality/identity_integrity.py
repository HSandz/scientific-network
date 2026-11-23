"""Task2D structural bindings and source-object checks, never identity truth."""
import json
from pathlib import Path

from scientific_network.quality.identity_audit import file_hash


def load_candidates(path, freeze_sha256):
    binding = json.loads(Path(path).read_bytes())
    if binding['freeze_sha256'] != freeze_sha256:
        raise ValueError('candidate binding refers to another frozen sample')
    if set(binding['graphs']) != {'v4', 'candidate_v3', 'task2b'}:
        raise ValueError('exactly v4, candidate_v3 and task2b bindings required')
    result = {}
    for name, rec in binding['graphs'].items():
        p = Path(rec['path'])
        if file_hash(p) != rec['sha256']:
            raise ValueError(f'{name}: candidate graph hash mismatch')
        g = json.loads(p.read_bytes())
        if rec.get('graph_version', g['graph_version']) != g['graph_version']:
            raise ValueError(f'{name}: candidate graph version mismatch')
        people = {n['id'] for n in g['nodes'] if n['label'] == 'Researcher'}
        positions, clusters = {}, {}
        for e in g['edges']:
            if e['relation'] != 'AUTHORED':
                continue
            key = (e['target_id'], e['properties']['byline_position'])
            if key in positions or e['source_id'] not in people:
                raise ValueError(f'{name}: contradictory authorship assignment')
            positions[key] = e['source_id']
            clusters.setdefault(e['source_id'], []).append(list(key))
        from hashlib import sha256
        result[name] = dict(sha256=rec['sha256'], graph_version=g['graph_version'],
            positions=positions, people=people,
            cluster_hashes={cid:sha256(json.dumps(sorted(rows), separators=(',', ':')).encode()).hexdigest()
                            for cid, rows in clusters.items()})
    return result


def verify_crosswalk(crosswalk, unit, candidates):
    """Check a decision about this exact position, including an explicit rejection.

    Reviewer ownership is an assertion preserved separately; matching IDs or hashes
    only proves structural compatibility, never real-world person equivalence.
    """
    maps = crosswalk.candidate_assignments
    if maps is None or set(maps) != set(candidates):
        raise ValueError('v3 crosswalk requires every declared candidate; migrate legacy mapping explicitly')
    key = (unit['paper_id'], unit['author_position'])
    result = {}
    for name, claim in maps.items():
        g = candidates[name]
        if (claim.graph_sha256, claim.graph_version) != (g['sha256'], g['graph_version']):
            raise ValueError(f'{name}: crosswalk graph binding mismatch')
        predicted = g['positions'].get(key)
        if claim.predicted_canonical_id != predicted:
            raise ValueError(f'{name}: canonical ID does not match sampled paper/author position')
        if claim.accepted_canonical_ids and claim.accepted_canonical_ids != [predicted]:
            raise ValueError(f'{name}: unrelated canonical ID in case-specific crosswalk')
        if claim.cluster_sha256 != (g['cluster_hashes'].get(predicted) if predicted else None):
            raise ValueError(f'{name}: authorship cluster binding mismatch')
        if claim.ownership == 'supported' and (not predicted or claim.accepted_canonical_ids != [predicted]):
            raise ValueError(f'{name}: supported ownership requires assigned ID')
        if claim.ownership != 'supported' and claim.accepted_canonical_ids:
            raise ValueError(f'{name}: uncertain/rejected ownership cannot accept ID')
        if claim.ownership == 'unknown':
            result[name] = dict(status='unknown', accepted_canonical_ids=[], structural_compatibility=True)
        else:
            result[name] = dict(status='reviewer_asserted', accepted_canonical_ids=claim.accepted_canonical_ids,
                                structural_compatibility=True)
    return result


class EvidenceVerifier:
    """Explicit registry: exact metadata + preserved bytes; locator is separate.

    No network requests, domain-based independence inference or execution of source
    text. Registry records can represent original cache objects or later retrievals.
    """
    def __init__(self, records=()):
        self.records = {}
        for rec in records:
            key = (rec['sha256'], rec['url'], rec['retrieved_at'])
            if key in self.records and self.records[key] != rec:
                raise ValueError('contradictory source registry metadata')
            self.records[key] = rec

    def verify(self, evidence):
        e = evidence.model_dump() if hasattr(evidence, 'model_dump') else evidence
        key = (e['sha256'], e['url'], e['retrieved_at'])
        rec = self.records.get(key)
        flags = []
        if e['independence'] in ('construction', 'shared_upstream'):
            flags.append('shared_upstream')
        else:
            flags.append('independence_unknown')
        related = [r for r in self.records.values() if r['sha256'] == e['sha256'] and r['url'] == e['url']]
        if rec is None:
            flags += ['source_unavailable', 'locator_unverified']
            if related:
                flags.append('metadata_contradiction')
        else:
            if any(e.get(k) != rec[k] for k in ('source_owner', 'provenance') if k in rec):
                flags.append('metadata_contradiction')
            path = Path(rec['object_path'])
            if not path.is_file():
                flags.append('source_unavailable')
            elif file_hash(path) != e['sha256']:
                flags.append('hash_mismatch')
            else:
                flags.append('hash_verified')
            # Only an exact preserved locator/excerpt registry matches. This is
            # documentary verification, not semantic correctness of the claim.
            if rec.get('locators', {}).get(e['locator']) != e['excerpt']:
                flags.append('locator_unverified')
            else:
                flags.append('locator_registered')
        return dict(evidence_id=e['evidence_id'], flags=sorted(flags),
                    identity_truth='not_established', independence_claim=e['independence'])
