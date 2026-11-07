"""Synthetic contract cases for the versioned IFAAMAS roster parser."""

import pytest

from scientific_network.collect.aamas import parse_aamas_roster, reconcile_aamas_2023


def edition(**changes):
    value = {
        "year": 2021,
        "official_index": "https://www.ifaamas.org/Proceedings/aamas2021/forms/contents.htm",
        "main_section": "Main Track",
        "expected_section_counts": {"Main Track": 1, "Blue Sky Ideas Track": 1},
        "expected_included": 1,
    }
    value.update(changes)
    return value


def page(main_title="AAMAS 2021"):
    return f"""<html><head><title>{main_title} Proceedings</title></head><body>
    <font><a name="blue"></a>Blue Sky Ideas Track</font>
    <p><a href="../pdfs/p2.pdf">A Blue Sky Paper</a>
       <font face="Times New Roman">Nora Paper<i> (Example Lab)</i></font></p>
    <font><a name="main"></a>Main Track</font>
    <p><a href="../pdfs/p1.pdf">A Main Paper</a>
       <font face="Times New Roman">Ada Author<i> (Example University)</i><br/>Bo Author<i> (Example Institute)</i></font></p>
    </body></html>""".encode("utf-8")


SOURCE = {
    "url": "https://www.ifaamas.org/Proceedings/aamas2021/forms/contents.htm",
    "sha256": "source-hash",
    "retrieved_at": "2026-11-07T00:00:00+00:00",
}


def test_parses_only_the_edition_bound_main_section_and_keeps_full_byline():
    rows = parse_aamas_roster(page(), edition(), SOURCE)
    included = [row for row in rows if row["status"] == "included"]
    assert len(rows) == 2
    assert included[0]["official_record_id"] == "p1"
    assert included[0]["authors"] == ["Ada Author", "Bo Author"]
    assert included[0]["track_section"] == "Main Track"
    assert sum(row["status"] == "excluded" for row in rows) == 1


@pytest.mark.parametrize("mutation", ["unknown_section", "duplicate_id", "missing_byline", "wrong_year"])
def test_rejects_unreconciled_ifaamas_toc(mutation):
    body = page()
    config = edition()
    if mutation == "unknown_section":
        body = body.replace(b"Main Track", b"Special Track")
    elif mutation == "duplicate_id":
        body = body.replace(
            b'<a href="../pdfs/p2.pdf">',
            b'<a href="../pdfs/p1.pdf">',
        )
    elif mutation == "missing_byline":
        body = body.replace(b'Nora Paper<i> (Example Lab)</i>', b'')
    else:
        body = page("AAMAS 2022")
    with pytest.raises(ValueError):
        parse_aamas_roster(body, config, SOURCE)


def test_aamas_2023_reconciliation_counts_only_exact_titles_and_reports_byline_differences():
    accepted = b"""<html><body>
    <h2>Main Track: Full Papers</h2>
    <p>Shared Title<br/><em>One Author and Two Author</em></p>
    <h2>Main Track: Extended Abstracts</h2>
    <p>An Extended Abstract<br/><em>Three Author</em></p>
    </body></html>"""
    contents = b"""<html><head><title>AAMAS 2023</title></head><body>
    <a name="1A"></a><font>Session 1A</font>
    <p><a href="../pdfs/p12.pdf">Shared Title</a>
       <font face="Times New Roman">One Author<i> (Lab)</i><br/>Two Author<i> (School)</i></font></p>
    </body></html>"""
    result = reconcile_aamas_2023(accepted, contents)
    assert result["official_full_papers_listed"] == 1
    assert result["accepted_extended_abstracts_listed"] == 1
    assert result["contents_pdf_records_observed"] == 1
    assert result["exact_normalized_title_joins_to_contents"] == 1
    assert result["accepted_titles_without_exact_contents_match"] == 0
    assert result["exact_byline_mismatches_among_matched_titles"] == 0
