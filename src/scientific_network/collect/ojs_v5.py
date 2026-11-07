"""Literal, edition-specific AAAI main technical section variants.

The sections occur inside archive-verified Technical Tracks issues. Keep their
exact headings as evidence; other labels/years still abstain. V3/v4 are unchanged.
"""
from pathlib import Path

from scientific_network.collect.ojs import recover_ojs
from scientific_network.collect.ojs_v4 import load_archive_v4, parse_v4

VERSION = "five-year-official-rosters-v5"
MAIN_SECTION_VARIANTS = {
    2021: {
        "AAAI Technical Track Focus Area on Neuro-Symbolic AI",
        "AAAI Technical Track Focus Area on AI Responses to the COVID-19 Pandemic",
        "AAAI Technical Track Focus Area on AI for Conference Organization and Delivery",
    },
    2024: {"Intelligent Robots (ROB)"},
}


def parse_v5(body: bytes, edition: dict, source: dict) -> list[dict]:
    rows = parse_v4(body, edition, source)
    for row in rows:
        if (edition["journal"] == "AAAI" and edition["disposition"] == "collect"
                and row["reason"] == "unknown_track"
                and row["track_section"] in MAIN_SECTION_VARIANTS.get(edition["year"], set())):
            row.update(track="main", status="included", reason="official_main_technical_section_variant",
                       section_policy="D027_literal_edition_specific_main_technical_heading")
        row["parser_version"] = VERSION
    return rows


def recover_v5(config: Path, output: Path, cache: Path) -> dict:
    return recover_ojs(config, output, cache, method_version=VERSION,
                       archive_loader=load_archive_v4, roster_parser=parse_v5)
