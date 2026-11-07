"""Synthetic checks for MICCAI 2024 Society and Springer reconciliation."""

from hashlib import sha256

import pytest

from scientific_network.collect.miccai_v2 import (
    parse_miccai2024_society_roster,
    reconcile_miccai2024_rosters,
)


def bibtex(record_id: str, title: str, authors: str, volume: int = 15001) -> str:
    return f"""@InProceedings{{{record_id},
      author = {{{authors}}},
      title = {{{{{title}}}}},
      booktitle = {{Medical Image Computing and Computer Assisted Intervention -- MICCAI 2024}},
      year = {{2024}},
      volume = {{LNCS {volume}}},
    }}"""


def society_page(records: list[tuple[str, str, str, int]]) -> bytes:
    cards = []
    for ordinal, (paper_id, title, authors, volume) in enumerate(records, start=1):
        cards.append(f"""<div class="posts-list-item"><ul><li>{title}</li>
        <li><a href="/miccai-2024/{ordinal:03d}-{paper_id}.html">Paper Information and Reviews</a>
        <pre>{bibtex(f'Key{ordinal}', title, authors, volume)}</pre></li></ul></div>""")
    return ("<html><body>" + "".join(cards) + "</body></html>").encode()


def parse(body: bytes, expected: int) -> list[dict]:
    url = "https://papers.miccai.org/miccai-2024/"
    return parse_miccai2024_society_roster(
        body,
        {"year": 2024, "expected_records": expected, "official_index": url},
        {"url": url, "sha256": sha256(body).hexdigest(),
         "retrieved_at": "2026-11-07T10:30:00+07:00"},
    )


def publisher(doi: str, title: str, authors: list[str], volume: int) -> dict:
    return {"doi": doi, "title": title, "authors": authors, "publisher_volume": volume}


def test_society_parser_preserves_full_byline_and_edition_record_ids():
    body = society_page([
        ("Paper1001", "Shared Title", "Author, Ada AND Writer, Bo", 15007),
        ("Paper1002", "Robust MRI Segmentation with Local Context", "Researcher, Cy", 15012),
    ])
    rows = parse(body, expected=2)

    assert [row["official_record_id"] for row in rows] == [
        "001-Paper1001", "002-Paper1002",
    ]
    assert rows[0]["authors"] == ["Author, Ada", "Writer, Bo"]
    assert rows[0]["publisher_volume"] == 15007
    assert all(row["status"] == "included" and row["track"] == "main" for row in rows)


@pytest.mark.parametrize("mutation", ["wrong_year", "wrong_volume", "duplicate_id", "count"])
def test_society_parser_rejects_edition_or_roster_contract_drift(mutation):
    body = society_page([
        ("Paper1001", "First Paper", "Author, Ada", 15001),
        ("Paper1002", "Second Paper", "Writer, Bo", 15002),
    ])
    if mutation == "wrong_year":
        body = body.replace(b"year = {2024}", b"year = {2023}", 1)
    elif mutation == "wrong_volume":
        body = body.replace(b"LNCS 15002", b"LNCS 14999", 1)
    elif mutation == "duplicate_id":
        body = body.replace(b"002-Paper1002", b"002-Paper1001")
    with pytest.raises(ValueError):
        parse(body, expected=1 if mutation == "count" else 2)


def test_reconciliation_matches_title_variant_with_byline_and_excludes_correction():
    body = society_page([
        ("Paper1001", "Shared Title", "Author, Ada AND Writer, Bo", 15007),
        ("Paper1002", "Robust MRI Segmentation with Local Context", "Researcher, Cy", 15002),
    ])
    society = parse(body, expected=2)
    springer = [
        publisher("10.1007/978-3-031-72104-5_1", "Shared Title", ["Ada Author", "Bo Writer"], 15007),
        publisher("10.1007/978-3-031-72069-7_1",
                  "Robust MRI Segmentation with Local Context Modeling", ["Cy Researcher"], 15002),
        publisher("10.1007/978-3-031-72104-5_75",
                  "Correction to: Shared Title", ["Ada Author", "Bo Writer"], 15007),
    ]

    result = reconcile_miccai2024_rosters(society, springer)

    assert result["exact_title_matches"] == 1
    assert result["unique_title_and_byline_matches"] == 1
    assert result["unresolved_society_records"] == 0
    assert result["publisher_only_records"] == 1
    assert result["publisher_only_corrections"] == 1
    assert result["correction_matches_a_society_original"] is True
    assert result["complete"] is True


def test_reconciliation_does_not_guess_when_variant_byline_does_not_match():
    body = society_page([
        ("Paper1001", "Robust MRI Segmentation with Local Context", "Researcher, Cy", 15001),
    ])
    society = parse(body, expected=1)
    springer = [publisher(
        "10.1007/978-3-031-72378-0_1",
        "Robust MRI Segmentation with Local Context Modeling", ["Other Person"], 15001,
    )]

    result = reconcile_miccai2024_rosters(society, springer)

    assert result["unresolved_society_records"] == 1
    assert result["complete"] is False
