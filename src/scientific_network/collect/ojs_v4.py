"""Stop archive parsing at the first corroborated out-of-window issue.

V3 safely withheld AAAI because an older, nonstandard issue title appeared after
the verified 2020 boundary on the same archive page. Preserve its outputs/replay.
"""
from pathlib import Path

from scientific_network.collect.ojs import archive_entries, load_archive, parse_ojs, recover_ojs

VERSION = "five-year-official-rosters-v4"


def archive_entries_v4(body: bytes, journal: str, source: dict):
    return archive_entries(body, journal, source, stop_before_year=2021)


def load_archive_v4(cache, conference: dict, max_pages: int, sources=None):
    return load_archive(cache, conference, max_pages, sources, archive_parser=archive_entries_v4)


def parse_v4(body: bytes, edition: dict, source: dict):
    rows = parse_ojs(body, edition, source)
    for row in rows:
        row["parser_version"] = VERSION
    return rows


def recover_v4(config: Path, output: Path, cache: Path) -> dict:
    return recover_ojs(config, output, cache, method_version=VERSION,
                       archive_loader=load_archive_v4, roster_parser=parse_v4)
