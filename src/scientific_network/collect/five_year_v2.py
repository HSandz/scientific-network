"""Second roster revision; retain v1 semantics for replay and historical diagnostics."""
from pathlib import Path
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import pyarrow as pa
import pyarrow.parquet as pq

from scientific_network.collect.five_year import (
    edition_routes, parse_five_year, discover_five_year, _row,
)
from scientific_network.collect.rosters import parse_roster
from scientific_network.collect.storage import write_jsonl

VERSION = 'five-year-official-rosters-v2'


def routes_v2(body: bytes, conference: dict, year: int) -> list[dict]:
    routes = edition_routes(body, conference, year)
    if conference.get('adapter') == 'rss':
        soup = BeautifulSoup(body,'html.parser')
        for route in routes:
            match = re.search(r'Robotics: Science and Systems ([IVX]+)',route['catalog_locator'])
            if not match:
                raise ValueError('RSS catalog lacks explicit edition numeral/year corroboration')
            route['required_markers']=['Robotics: Science and Systems '+match[1]]
            route['catalog_verified_year']=year
    return routes


def parse_v2(body: bytes, edition: dict, source: dict) -> list[dict]:
    family,year=edition['adapter'],edition['year']
    soup=BeautifulSoup(body,'html.parser')
    if family=='rss':
        if edition.get('catalog_verified_year')!=year:
            raise ValueError('RSS year requires official catalog corroboration')
        return parse_roster(body,edition,source)
    if family=='ecva':
        rows=[]
        for item in soup.select('dt.ptitle'):
            link=item.find('a',href=re.compile(rf'papers/eccv_{year}/'))
            if not link:continue
            panel=item.find_parent('div',class_='accordion-content')
            button=panel.find_previous_sibling('button',class_='accordion') if panel else None
            if not button or button.get_text(' ',strip=True)!=f'ECCV {year} Papers':
                raise ValueError('ECVA edition accordion and paper URL disagree')
            author=item.find_next_sibling('dd')
            # Preserve literal printed names/markers; identity matching is a later stage.
            names=[n.strip() for n in author.get_text(' ',strip=True).split(',') if n.strip()] if author else []
            row=_row(link,names,'main',edition,source)
            links=author.find_next_sibling('dd') if author else None
            pdf=links.find('a',href=lambda h:h and h.endswith('.pdf') and 'supp' not in h) if links else None
            row['pdf_url']=urljoin(edition['official_index'],pdf['href']) if pdf else None
            row['source_locator']+=f';accordion[{year}]'
            rows.append(row)
    elif family=='kr':
        rows=[]
        allowed={'Main Track','Full Papers','Short Papers'}
        excluded={'Preface','Special Session on KR and Machine Learning',
                  'Special Session on KR and Robotics','Applications and Systems',
                  'KR in the Wild','Reasoning, Learning & Decision-Making Track',
                  'KR and Constraints','KR in Planning and Scheduling'}
        for item in soup.select('div[class*="paperinfo"]'):
            link=item.find('a',href=re.compile(rf'^/{year}/\d+/$'))
            if not link:continue
            heading=item.find_previous(['h2','h3'])
            text=heading.get_text(' ',strip=True) if heading else ''
            track='main' if text in allowed else 'nonresearch' if text in excluded else 'unknown'
            names=[a.get_text(' ',strip=True) for a in item.select('ol li')]
            row=_row(link,names,track,edition,source)
            row['track_section']=text
            rows.append(row)
    else:
        rows=parse_five_year(body,edition,source)
        if family=='neurips':
            # New 2025 position-paper track is outside the existing main research policy.
            by_url={urljoin(edition['official_index'],a['href']):a.find_parent('li')
                    for a in soup.find_all('a',href=re.compile(rf'/{year}/hash/[^/]+-Abstract'))}
            for row in rows:
                item=by_url[row['official_url']]
                if item.get('data-track')=='position_paper_track':
                    row.update(track='position_paper_track',status='excluded',reason='excluded_non_main_position_track')
    if not rows:raise ValueError('empty roster; reconcile official layout')
    if len({r['paper_id'] for r in rows})!=len(rows):
        raise ValueError('duplicate official records; reconcile before acceptance')
    for row in rows:row['parser_version']=VERSION
    return rows


def write_complete_manifest(path: Path, rows: list[dict]) -> None:
    """Keep canonical JSONL and a union-schema mirror; preserve the earlier mirror.

    Arrow infers columns from the first row, which omits KR-only track_section.
    Use a new filename so an existing lossy mirror is never replaced silently.
    """
    write_jsonl(path.with_suffix('.jsonl'), rows)
    keys = sorted({key for row in rows for key in row})
    normalized = [{key: row.get(key) for key in keys} for row in rows]
    complete = path.with_name(path.stem + '-complete.parquet')
    if complete.exists():
        if pq.read_table(complete).to_pylist() != normalized:
            raise ValueError(f'refusing to overwrite different complete table: {complete}')
    else:
        pq.write_table(pa.Table.from_pylist(normalized), complete)


def discover_v2(config: Path, output: Path, cache: Path) -> dict:
    return discover_five_year(config,output,cache,method_version=VERSION,
                             roster_parser=parse_v2,route_resolver=routes_v2,
                             manifest_table_writer=write_complete_manifest)
