"""Strict independent-review contracts and blind local workspace generation.

No authentication is claimed: distribute A and B directories separately. Submitted
exports are immutable inputs to compilation; adjudication never rewrites them.
"""
import argparse
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from scientific_network.collect.storage import read_jsonl, write_json, write_jsonl
from scientific_network.quality.identity_audit import file_hash, unused


class Strict(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True, str_strip_whitespace=True)


class Evidence(Strict):
    evidence_id: str = Field(min_length=1)
    url: str
    retrieved_at: str
    sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    locator: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    source_owner: str = Field(min_length=1)
    provenance: str = Field(min_length=1)
    independence: Literal['independent', 'construction', 'shared_upstream', 'unknown']
    independence_rationale: str = Field(min_length=1)

    @field_validator('url')
    @classmethod
    def public_url(cls, value):
        from urllib.parse import urlsplit
        u = urlsplit(value)
        if u.scheme not in ('https', 'http') or not u.hostname or u.username or u.password:
            raise ValueError('public HTTP(S) URL required')
        return value

    @field_validator('retrieved_at')
    @classmethod
    def dated(cls, value):
        if datetime.fromisoformat(value.replace('Z', '+00:00')).utcoffset() is None:
            raise ValueError('timezone-aware date required')
        return value


class Review(Strict):
    unit_id: str = Field(min_length=1)
    reviewer: Literal['A', 'B']
    reviewer_identity: str = Field(min_length=1)
    reviewer_kind: Literal['human', 'ai']
    model: str | None = None
    run_id: str | None = None
    label: Literal['identity', 'unresolvable', 'unknown', 'same', 'different']
    reference_identity: str | None = None
    confidence: Literal['high', 'medium', 'low']
    notes: str = Field(min_length=1)
    evidence: list[Evidence]
    submitted_at: str

    _date = field_validator('submitted_at')(Evidence.dated.__func__)

    @model_validator(mode='after')
    def coherent(self):
        if self.reviewer_kind == 'ai' and (not self.model or not self.run_id):
            raise ValueError('AI review requires actual model/run metadata')
        if self.label == 'identity' and not self.reference_identity:
            raise ValueError('verified identity requires independent reference identity anchor')
        if self.label != 'identity' and self.reference_identity is not None:
            raise ValueError('only identity label has an identity anchor')
        if self.label != 'unknown' and not any(e.independence == 'independent' for e in self.evidence):
            raise ValueError('determinate label needs independent evidence')
        return self


class Submission(Strict):
    schema_version: Literal['identity-review-v2']
    freeze_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    reviewer: Literal['A', 'B']
    reviews: list[Review]

    @model_validator(mode='after')
    def isolated(self):
        if len({r.unit_id for r in self.reviews}) != len(self.reviews):
            raise ValueError('duplicate review')
        if any(r.reviewer != self.reviewer for r in self.reviews):
            raise ValueError('mixed reviewer file')
        if len({r.reviewer_identity for r in self.reviews}) > 1:
            raise ValueError('one actual reviewer per file')
        return self


class Crosswalk(Strict):
    reference_identity: str = Field(min_length=1)
    accepted_canonical_ids: list[str]
    complete: Literal[True]
    evidence: list[Evidence] = Field(min_length=1)
    rationale: str = Field(min_length=1)

    @model_validator(mode='after')
    def supported(self):
        if (len(set(self.accepted_canonical_ids)) != len(self.accepted_canonical_ids)
                or any(not i.strip() for i in self.accepted_canonical_ids)
                or not any(e.independence == 'independent' for e in self.evidence)):
            raise ValueError('unique canonical crosswalk requires independent support')
        return self


class Adjudication(Strict):
    unit_id: str = Field(min_length=1)
    review_a_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    review_b_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    adjudicator_identity: str = Field(min_length=1)
    adjudicator_kind: Literal['human', 'ai']
    model: str | None = None
    run_id: str | None = None
    resolution: Literal['consensus', 'adjudicated', 'unresolved']
    label: Literal['identity', 'unresolvable', 'unknown', 'same', 'different']
    reference_identity: str | None = None
    rationale: str = Field(min_length=1)
    evidence: list[Evidence]
    crosswalk: Crosswalk | None = None
    decided_at: str

    _date = field_validator('decided_at')(Evidence.dated.__func__)

    @model_validator(mode='after')
    def coherent(self):
        if self.adjudicator_kind == 'ai' and (not self.model or not self.run_id):
            raise ValueError('AI adjudication requires actual model/run metadata')
        if (self.resolution == 'unresolved') != (self.label == 'unknown'):
            raise ValueError('unresolved must preserve unknown')
        if self.label == 'identity':
            if not self.crosswalk or self.crosswalk.reference_identity != self.reference_identity:
                raise ValueError('identity requires completed matching crosswalk')
        elif self.crosswalk is not None or self.reference_identity is not None:
            raise ValueError('nonidentity labels cannot carry crosswalk')
        if self.label != 'unknown' and not any(e.independence == 'independent' for e in self.evidence):
            raise ValueError('adjudication requires independent evidence')
        return self


def verify_freeze(evaluation):
    freeze = json.loads((evaluation/'freeze.json').read_bytes())
    for name, digest in freeze['files'].items():
        if Path(name).name != name or file_hash(evaluation/name) != digest:
            raise ValueError('frozen artifact mismatch: '+name)
    return file_hash(evaluation/'freeze.json')


def units(evaluation):
    result = {}
    for category in ('assignment', 'diagnostic', 'pair'):
        for row in read_jsonl(evaluation/(category+'-sample.jsonl')):
            uid = row['unit_id']
            if uid not in result:
                result[uid] = dict(row, category=category, categories=[])
            result[uid]['categories'].append(category)
    return result


def validate_submission(value, evaluation):
    submission = Submission.model_validate(value)
    if submission.freeze_sha256 != verify_freeze(evaluation):
        raise ValueError('submission bound to another freeze')
    frame = units(evaluation)
    for r in submission.reviews:
        if r.unit_id not in frame:
            raise ValueError('review outside frozen membership')
        is_pair = frame[r.unit_id]['category'] == 'pair'
        if r.label != 'unknown' and ((r.label in ('same', 'different')) != is_pair):
            raise ValueError('label belongs to another case type')
    return submission


def compile_references(evaluation, a_path, b_path, decisions_path, output):
    """Compile only explicit consensus/adjudications; AI-only outputs stay separate."""
    unused(output)
    a = validate_submission(json.loads(a_path.read_bytes()), evaluation)
    b = validate_submission(json.loads(b_path.read_bytes()), evaluation)
    if (a.reviewer, b.reviewer) != ('A', 'B'):
        raise ValueError('separate A and B submissions required')
    aa, bb = ({r.unit_id: r for r in s.reviews} for s in (a,b))
    if {r.reviewer_identity for r in a.reviews} & {r.reviewer_identity for r in b.reviews}:
        raise ValueError('A/B must be different actual reviewers')
    hashes = (file_hash(a_path), file_hash(b_path))
    frame = units(evaluation)
    refs, ai, seen = [], [], set()
    canonical_owner, identity_crosswalk = {}, {}
    for row in read_jsonl(decisions_path):
        d = Adjudication.model_validate(row)
        if d.unit_id in seen: raise ValueError('duplicate adjudication')
        seen.add(d.unit_id)
        if d.unit_id not in aa or d.unit_id not in bb:
            raise ValueError('both reviews must be submitted before adjudication')
        if (d.review_a_sha256, d.review_b_sha256) != hashes:
            raise ValueError('original review hash mismatch')
        ra, rb = aa[d.unit_id], bb[d.unit_id]
        if d.resolution == 'consensus' and (ra.label, ra.reference_identity) != (rb.label, rb.reference_identity):
            raise ValueError('disagreement requires documented adjudication')
        if d.resolution == 'consensus' and (d.label, d.reference_identity) != (ra.label, ra.reference_identity):
            raise ValueError('consensus must match original reviews')
        if d.label != 'unknown' and ((d.label in ('same','different')) != (frame[d.unit_id]['category']=='pair')):
            raise ValueError('wrong adjudication case type')
        human = all(x == 'human' for x in (ra.reviewer_kind, rb.reviewer_kind, d.adjudicator_kind))
        if human and d.crosswalk:
            ids = frozenset(d.crosswalk.accepted_canonical_ids)
            if d.reference_identity in identity_crosswalk and identity_crosswalk[d.reference_identity] != ids:
                raise ValueError('inconsistent completed reference crosswalk')
            identity_crosswalk[d.reference_identity] = ids
            for cid in ids:
                if cid in canonical_owner and canonical_owner[cid] != d.reference_identity:
                    raise ValueError('canonical ID maps to conflicting reference people')
                canonical_owner[cid] = d.reference_identity
        record = {'unit_id': d.unit_id, 'label': d.label, 'reference_identity': d.reference_identity,
                  'accepted_canonical_ids': d.crosswalk.accepted_canonical_ids if d.crosswalk else [],
                  'crosswalk_complete': bool(d.crosswalk),
                  'evidence': [e.model_dump() for e in d.evidence],
                  'crosswalk_evidence': [e.model_dump() for e in d.crosswalk.evidence] if d.crosswalk else [],
                  'independence': 'independent' if human and d.label != 'unknown' else 'unknown',
                  'adjudication': 'complete' if d.label != 'unknown' else 'unresolved',
                  'reviewer_kind': 'human' if human else 'ai',
                  'original_review_sha256': list(hashes), 'decision': d.model_dump()}
        (refs if human else ai).append(record)
    write_jsonl(output/'references.jsonl', sorted(refs,key=lambda r:r['unit_id']))
    write_jsonl(output/'ai-assessments.jsonl', sorted(ai,key=lambda r:r['unit_id']))
    write_json(output/'manifest.json', {'freeze_sha256': verify_freeze(evaluation),
        'inputs': {str(p): file_hash(p) for p in (a_path,b_path,decisions_path)},
        'reference_n': len(refs), 'ai_n': len(ai), 'pending_n': len(frame)-len(seen),
        'outputs': {p.name:file_hash(p) for p in sorted(output.iterdir())}})


def prepare(evaluation, works_path, output, evidence_path=None, candidates_path=None):
    unused(output)
    if output.resolve().is_relative_to(evaluation.resolve()):
        raise ValueError('output must be outside frozen evaluation directory')
    digest = verify_freeze(evaluation)
    frame = units(evaluation)
    packets = {r['mention_id']:r for r in read_jsonl(evaluation/'evidence-packets.jsonl')}
    works = {r['paper_id']:r for r in read_jsonl(works_path)}
    leads = read_jsonl(evidence_path) if evidence_path else []
    def context(mid):
        p = packets[mid]; w = works[p['paper_id']]; r = w['roster']
        return {'mention_id': mid, 'paper_id': p['paper_id'], 'position': p['author_position'],
                'name': p['official_name'], 'title': r['title'], 'venue': w['venue_id'],
                'year': w['year'], 'doi': w['doi'], 'official_byline': r['authors'],
                'official_url': r.get('official_url') or r.get('url'), 'pdf_url': r.get('pdf_url'),
                'construction_evidence': [e for e in p['supporting_evidence'] if 'roster' in e['evidence_id']],
                'additional_sources': [{k:lead[k] for k in ('url','status','upstream_independence','locator') if k in lead} for lead in leads if mid in lead['mention_ids']]}
    cases = [dict(unit_id=uid, category=u['category'], categories=u['categories'],
                  mentions=[context(u[k]) for k in ('left','right')] if u['category']=='pair' else [context(uid)])
             for uid,u in sorted(frame.items())]
    predictions = {}
    if candidates_path:
        bindings = json.loads(candidates_path.read_bytes())
        if bindings['freeze_sha256'] != digest:
            raise ValueError('candidate bindings refer to another evaluation freeze')
        for name, record in bindings['graphs'].items():
            path = Path(record['path'])
            if file_hash(path) != record['sha256']:
                raise ValueError('candidate graph hash mismatch')
            graph = json.loads(path.read_bytes())
            positions = {(e['target_id'], e['properties']['byline_position']): e['source_id']
                         for e in graph['edges'] if e['relation'] == 'AUTHORED'}
            names = {n['id']: n['name'] for n in graph['nodes'] if n['label'] == 'Researcher'}
            predictions[name] = {mid: {'canonical_id': positions.get((p['paper_id'],p['author_position'])),
                'display_name': names.get(positions.get((p['paper_id'],p['author_position'])))} for mid,p in packets.items()}
            del graph
    assets = Path(__file__).with_name('identity_workspace')
    for role in ('A','B','adjudication'):
        root = output/role; root.mkdir(parents=True)
        bundle = {'schema_version':'identity-review-v2', 'reviewer':role, 'freeze_sha256':digest, 'cases':cases}
        if role == 'adjudication': bundle['candidate_predictions'] = predictions
        # Script-safe JSON. No candidate predictions, provider IDs, profile ORCIDs,
        # developer mechanisms, alternate records or other reviewer's answers.
        (root/'bundle.js').write_text('const BUNDLE = '+json.dumps(bundle,ensure_ascii=True).replace('<','\\u003c')+';\n')
        for name in ('index.html','app.js','style.css'):
            (root/name).write_bytes((assets/name).read_bytes())
    schema = {'submission':Submission.model_json_schema(), 'evidence':Evidence.model_json_schema(),
              'adjudication':Adjudication.model_json_schema(), 'crosswalk':Crosswalk.model_json_schema()}
    write_json(output/'schemas.json',schema)
    write_json(output/'manifest.json',{'freeze_sha256':digest, 'works_sha256':file_hash(works_path),
        'unique_cases':len(cases),'files':{str(p.relative_to(output)):file_hash(p) for p in sorted(output.rglob('*')) if p.is_file()}})


def main():
    p=argparse.ArgumentParser(description=__doc__); sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare'); a.add_argument('--works',type=Path,required=True); a.add_argument('--evidence',type=Path); a.add_argument('--candidates',type=Path)
    for name in ('prepare','validate','compile'):
        a = a if name=='prepare' else sub.add_parser(name)
        a.add_argument('--evaluation',type=Path,required=True)
        if name in ('prepare','compile'): a.add_argument('--output',type=Path,required=True)
        if name=='validate': a.add_argument('--submission',type=Path,required=True)
        if name=='compile':
            for arg in ('review-a','review-b','adjudications'): a.add_argument('--'+arg,type=Path,required=True)
    args=p.parse_args()
    if args.command=='prepare':prepare(args.evaluation,args.works,args.output,args.evidence,args.candidates)
    elif args.command=='validate':
        result=validate_submission(json.loads(args.submission.read_bytes()),args.evaluation)
        print(json.dumps({'reviewer':result.reviewer,'submitted':len(result.reviews)}))
    else:compile_references(args.evaluation,args.review_a,args.review_b,args.adjudications,args.output)

if __name__=='__main__':main()
