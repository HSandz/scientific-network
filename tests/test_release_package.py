"""Local report rendering and package privacy on invented repositories."""

import base64
from hashlib import sha256
import json
from pathlib import Path
import subprocess
from zipfile import ZipFile

from bs4 import BeautifulSoup
import pytest

from scientific_network.reporting.release_package import (
    build_release_package, package_sources, permitted_source_path, print_html, render_html,
)


def git(root, *arguments):
    return subprocess.run(['git', '-C', str(root), *arguments], check=True, capture_output=True, text=True).stdout


@pytest.fixture
def repository(tmp_path):
    git(tmp_path, 'init')
    git(tmp_path, 'config', 'user.name', 'Synthetic package test')
    git(tmp_path, 'config', 'user.email', 'synthetic@example.invalid')
    report = tmp_path / 'reports/final-report/report.md'
    report.parent.mkdir(parents=True)
    report.write_text('# Invented report\n\n## 1. Invented section\n\nInvented text.\n')
    (tmp_path / 'README.md').write_text('Invented source')
    git(tmp_path, 'add', '.')
    git(tmp_path, 'commit', '-m', 'Invented fixture')
    return tmp_path, report


def test_html_embeds_images_and_fonts_checks_links_and_keeps_captions_with_figures(repository):
    pytest.importorskip('markdown', reason='optional report extra is required for HTML rendering')
    root, report = repository
    image = report.parent / 'figure.png'
    image.write_bytes(base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jXioAAAAASUVORK5CYII='))
    report.write_text('# Invented report\n\n## 1. Invented section\n\n'
                      '[Source](../../README.md) [Directory](./) [Section](#1-invented-section) '
                      '[External](https://example.invalid/not-fetched)\n\n'
                      '| Invented | Value |\n| --- | --- |\n| row | 2 |\n\n'
                      '![Invented figure](figure.png)\n\n*Figure 1. Invented caption.*\n\n'
                      '```python\nprint("invented")\n```\n')
    html, receipt = render_html(report, root)
    soup = BeautifulSoup(html, 'html.parser')
    assert soup.img['src'].startswith('data:image/png;base64,')
    assert soup.figure.figcaption.get_text(strip=True) == 'Figure 1. Invented caption.'
    assert soup.table is not None and soup.pre.code is not None
    assert receipt['image_count'] == receipt['raster_image_count'] == 1
    assert receipt['local_link_count'] == 3
    assert receipt['external_url_availability'] == 'not_tested'
    assert len(receipt['fonts']) == 3
    assert 'data:font/ttf;base64,' in html


@pytest.mark.parametrize('link,match', [
    ('[missing](missing.md)', 'missing or outside'),
    ('[outside](../../../outside.txt)', 'missing or outside'),
    ('[anchor](#no-such-heading)', 'unresolved internal anchor'),
    ('![remote](https://example.invalid/image.png)', 'images must be local'),
    ('[unsafe](javascript:alert(1))', 'unsupported report link scheme'),
])
def test_report_refuses_broken_or_unsafe_links(repository, link, match):
    pytest.importorskip('markdown', reason='optional report extra is required for HTML rendering')
    root, report = repository
    report.write_text('# Invented report\n\n' + link)
    with pytest.raises(ValueError, match=match):
        render_html(report, root)


def test_archive_uses_only_permitted_tracked_bytes_and_explicit_report_renders(repository):
    root, report = repository
    forbidden = ['.env', '.env.production', 'data/raw/source.json', 'data/interim/works.jsonl',
                 'data/processed/graph.json', 'models/model.bin', 'volumes/db.dat',
                 'neo4j-five-year-data/store', 'reports/runs/old/output.json',
                 'old.pdf', 'database.dump', 'other.zip', 'secret.key']
    for relative in forbidden + ['.env.example']:
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('Invented excluded material')
    (root / 'linked-source').symlink_to(root / 'README.md')
    git(root, 'add', '.')
    (root / 'untracked-source.txt').write_text('Invented untracked material')
    output = root / 'reports/runs/test/package'
    output.mkdir(parents=True)
    html = output / 'report.html'
    pdf = output / 'report.pdf'
    html.write_text('<h1>Invented report</h1>')
    pdf.write_bytes(b'Invented explicit render artifact')
    result = package_sources(root, report, html, pdf, output,
        {'local_links': [{'repository_path': 'README.md', 'kind': 'file'}], 'external_url_availability': 'not_tested'})
    with ZipFile(result['archive']) as archive:
        names = set(archive.namelist())
        assert names == {'README.md', '.env.example', 'reports/final-report/report.md',
                         'reports/final-report/report.html', 'reports/final-report/report.pdf', 'submission-manifest.json'}
        assert not names.intersection(forbidden)
        manifest = json.loads(archive.read('submission-manifest.json'))
        for member in manifest['members']:
            assert sha256(archive.read(member['path'])).hexdigest() == member['sha256']
    assert result['archive_sha256'] == sha256(Path(result['archive']).read_bytes()).hexdigest()
    assert result['source_commit'] == git(root, 'rev-parse', 'HEAD').strip()
    assert 'linked-source' in manifest['excluded_tracked_paths']


def test_package_refuses_local_links_that_would_disclose_excluded_data(repository):
    root, report = repository
    raw = root / 'data/raw/private.json'
    raw.parent.mkdir(parents=True)
    raw.write_text('Invented private source')
    output = root / 'reports/runs/test/package'
    output.mkdir(parents=True)
    html, pdf = output / 'report.html', output / 'report.pdf'
    html.write_text('Invented render')
    pdf.write_bytes(b'Invented PDF')
    with pytest.raises(ValueError, match='absent from the permitted tracked package'):
        package_sources(root, report, html, pdf, output,
                        {'local_links': [{'repository_path': 'data/raw/private.json', 'kind': 'file'}]})
    assert not (output / 'scientific-network-submission.zip').exists()


def test_existing_output_directory_is_never_replaced(repository):
    root, report = repository
    output = root / 'reports/runs/test/package'
    output.mkdir(parents=True)
    protected = output / 'keep.txt'
    protected.write_text('Keep this invented file')
    with pytest.raises(ValueError, match='refusing to overwrite'):
        build_release_package(report, output)
    assert protected.read_text() == 'Keep this invented file'


def test_private_source_filter_rejects_traversal_and_allows_env_example():
    assert permitted_source_path('.env.example')
    assert permitted_source_path('src/scientific_network/contracts.py')
    assert not permitted_source_path('../.env.example')
    assert not permitted_source_path('/etc/passwd')
    assert not permitted_source_path('project/.env.local')


def test_print_copy_retains_external_and_internal_links_without_workspace_annotations():
    html = '<a href="../../README.md"><code>README.md</code></a><a href="https://example.invalid">External</a><a href="#section">Section</a>'
    printed = BeautifulSoup(print_html(html), 'html.parser')
    assert printed.code.get_text() == 'README.md'
    assert [anchor['href'] for anchor in printed.find_all('a')] == ['https://example.invalid', '#section']
    assert '../../README.md' in html  # Portable source HTML remains unchanged.
