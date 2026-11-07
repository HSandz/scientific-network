"""Synthetic source-contract tests for MICCAI roster parsing."""

from hashlib import sha256

import pytest

from scientific_network.collect.miccai_v1 import parse_miccai_roster


def source(body: bytes, url: str) -> dict:
    return {"url": url, "sha256": sha256(body).hexdigest(),
            "retrieved_at": "2026-11-07T09:00:00+07:00"}


def test_miccai_2021_and_2023_acceptance_lists_require_contiguous_unique_ids():
    cases = [
        (2021, "https://miccai2021.org/openaccess/paperlinks/",
         b"""<h2>List of Papers</h2><ul>
         <li><a href="2021/09/01/001-Paper1001.html">First paper</a></li>
         <li><a href="2021/09/01/002-Paper1002.html">Second paper</a></li>
         </ul>"""),
        (2023, "https://conferences.miccai.org/2023/papers/",
         b"""<h2>List of Papers</h2><ul>
         <li><a href="/2023/papers/001-Paper2001.html">First paper</a></li>
         <li><a href="/2023/papers/002-Paper2002.html">Second paper</a></li>
         </ul>"""),
    ]
    for year, url, body in cases:
        edition = {"venue_id": "venue:miccai", "year": year,
                   "format": "accepted_list", "expected_records": 2,
                   "official_index": url}
        rows = parse_miccai_roster(body, edition, source(body, url))
        assert [row["official_record_id"] for row in rows] == [
            "001-Paper1001" if year == 2021 else "001-Paper2001",
            "002-Paper1002" if year == 2021 else "002-Paper2002",
        ]
        assert all(row["status"] == "included" and row["track"] == "main" for row in rows)
        assert all(row["authors"] == [] for row in rows)


@pytest.mark.parametrize("links", [
    '<a href="/2023/papers/001-Paper2001.html">One</a><a href="/2023/papers/003-Paper2003.html">Three</a>',
    '<a href="/2023/papers/001-Paper2001.html">One</a><a href="/2023/papers/001-Paper2002.html">Two</a>',
])
def test_miccai_acceptance_list_rejects_gaps_and_duplicate_positions(links):
    body = f"<h2>List of Papers</h2>{links}".encode()
    url = "https://conferences.miccai.org/2023/papers/"
    edition = {"venue_id": "venue:miccai", "year": 2023,
               "format": "accepted_list", "expected_records": 2,
               "official_index": url}
    with pytest.raises(ValueError, match="sequence"):
        parse_miccai_roster(body, edition, source(body, url))


def bibtex_record(number: str, paper_id: str, title: str, authors: str, volume: int) -> str:
    return f"""<div class="posts-list-item"><ul><li><span class="posts-list-item-name">{title}
    <li>{authors}</li><li><a href="/miccai-2025/{number}-{paper_id}.html">Paper Information and Reviews</a>
    <div class="bibref"><pre>@InProceedings{{Key{number},
      author = {{{authors.replace(', ', ' AND ')}}},
      title = {{{{{title}}}}},
      booktitle = {{Medical Image Computing and Computer Assisted Intervention -- MICCAI 2025}},
      year = {{2025}},
      volume = {{LNCS {volume}}},
    }}</pre></div></li></ul></div>"""


def test_miccai_2025_bibtex_roster_binds_title_authors_year_and_volume():
    body = ("<html>" + bibtex_record("0001", "Paper1001", "First paper", "A. Author, B. Author", 15960)
            + bibtex_record("0002", "Paper1002", "Second paper", "C. Author", 15975) + "</html>").encode()
    url = "https://papers.miccai.org/miccai-2025/"
    edition = {"venue_id": "venue:miccai", "year": 2025,
               "format": "bibtex_list", "expected_records": 2,
               "official_index": url}
    rows = parse_miccai_roster(body, edition, source(body, url))
    assert [row["official_record_id"] for row in rows] == [
        "0001-Paper1001", "0002-Paper1002"]
    assert rows[0]["authors"] == ["A. Author", "B. Author"]
    assert all(row["status"] == "included" and row["track"] == "main" for row in rows)


def test_miccai_2025_rejects_title_or_source_hash_mismatch():
    body = ("<html>" + bibtex_record("0001", "Paper1001", "Visible title", "A. Author", 15960)
            + "</html>").encode()
    url = "https://papers.miccai.org/miccai-2025/"
    edition = {"venue_id": "venue:miccai", "year": 2025,
               "format": "bibtex_list", "expected_records": 1,
               "official_index": url}
    altered = body.replace(b"Visible title", b"A different display name", 1)
    with pytest.raises(ValueError, match="title"):
        parse_miccai_roster(altered, edition, source(altered, url))
    with pytest.raises(ValueError, match="hash"):
        parse_miccai_roster(body, edition, {**source(body, url), "sha256": "0" * 64})
