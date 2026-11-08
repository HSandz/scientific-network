"""Git normalization must not invalidate frozen, quoted Unicode CSV packets."""

import csv
from hashlib import sha256
from pathlib import Path
import subprocess


def test_git_staged_csv_preserves_exact_quoted_unicode_and_embedded_newlines(tmp_path):
    root = Path(__file__).resolve().parents[1]
    (tmp_path / '.gitattributes').write_bytes((root / '.gitattributes').read_bytes())
    subprocess.run(['git', 'init', '-q', str(tmp_path)], check=True)
    packet = tmp_path / 'packet.csv'
    rows = [{'id': 'edge:tên', 'context': 'says "NLP", đồ thị\r\nsecond line\nthird\u2028part'}]
    with packet.open('x', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['id', 'context'], lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)
    subprocess.run(['git', '-C', str(tmp_path), 'add', '.gitattributes', 'packet.csv'], check=True)
    staged = subprocess.run(['git', '-C', str(tmp_path), 'show', ':packet.csv'], check=True, capture_output=True).stdout
    assert sha256(staged).digest() == sha256(packet.read_bytes()).digest()
    with packet.open(newline='', encoding='utf-8') as stream:
        assert list(csv.DictReader(stream)) == rows
