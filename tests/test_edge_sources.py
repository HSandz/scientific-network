import json
from hashlib import sha256
import pytest
from scientific_network.evaluation.edge_sources import raw_work


def test_raw_source_verification_retains_observed_arrays_and_refuses_projection(tmp_path):
    (tmp_path / 'objects').mkdir()
    work = {'id': 'https://openalex.org/W1', 'authorships': [{'author': {'id': 'https://openalex.org/A1',
           'orcid': None, 'observed_orcids': ['0000-0002-1825-0097', '0000-0001-5109-3700']}}], 'referenced_works': []}
    data = json.dumps({'results': [work]}).encode()
    h = sha256(data).hexdigest()
    (tmp_path / 'objects' / h).write_bytes(data)
    oa = {**work, 'source': {'raw_sha256': h, 'locator': 'results[0]@page1'}}
    assert raw_work(oa, tmp_path)[2]['authorships'][0]['author']['observed_orcids'] == work['authorships'][0]['author']['observed_orcids']
    oa['authorships'] = [{'author': {'id': 'https://openalex.org/A1', 'orcid': None}}]
    with pytest.raises(ValueError, match='authorship mismatch'):
        raw_work(oa, tmp_path)
