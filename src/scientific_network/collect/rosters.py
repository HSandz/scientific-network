"""Official source-family adapters. Section boundaries determine track eligibility."""

import re
from urllib.parse import urljoin, urlsplit, urlencode

from bs4 import BeautifulSoup

VERSION = "official-roster-families-v2"


def parse_roster(body: bytes, edition: dict, source: dict) -> list[dict]:
    soup = BeautifulSoup(body, "html.parser")
    family, year = edition["adapter"], edition["year"]
    for marker in edition.get("required_markers", [str(year)]):
        if marker.casefold() not in soup.get_text(" ", strip=True).casefold():
            raise ValueError(f"source does not identify expected edition marker: {marker}")
    entries = []
    if family == "pmlr":
        volume = edition["volume"]
        for item in soup.select("div.paper"):
            link = item.find("a", href=lambda h: h and re.search(rf"/v{volume}/[^/]+\.html$", h))
            heading = item.find_previous("h3")
            section = heading.get_text(" ", strip=True).lower() if heading else ""
            track = "nonresearch" if section in {"preface", "open problems"} else "main"
            entries.append((item, link, item.select_one(".title"), item.select_one(".authors"), track))
    elif family == "mlsys":
        for item in soup.select(".paper-content"):
            link = item.find("a", href=lambda h: h and f"/{year}/hash/" in h)
            entries.append((item, link, link, item.select_one(".paper-authors"), "main"))
    elif family == "acl":
        collection = edition["collection"]
        for link in soup.find_all("a", href=re.compile(rf"^/{re.escape(collection)}\.\d+/$")):
            if not link.find_parent("strong"):
                continue
            item = link.find_parent("span", class_="d-block")
            if item is None:
                raise ValueError("ACL byline layout changed")
            authors = [a.get_text(" ", strip=True) for a in item.select('a[href^="/people/"]')]
            entries.append((item, link, link, authors, "main"))
    elif family == "ijcai":
        for item in soup.select(".paper_wrapper"):
            heading = item.find_previous(["h2", "h3"])
            section = heading.get_text(" ", strip=True) if heading else ""
            track = "main" if section == "Main Track" else "nonresearch" if section else "unknown"
            link = item.select_one("a.title")
            authors = [a.get_text(" ", strip=True) for a in item.select(".authors a")]
            entries.append((item, link, link, authors, track))
    elif family == "rss":
        for item in soup.select("tr"):
            link = item.find("a", href=re.compile(r"^p\d+\.html$"))
            if link:
                entries.append((item, link, link, item.find("i"), "main"))
    elif family == "kr":
        for item in soup.select('div[class*="paperinfo"]'):
            link = item.find("a", href=re.compile(rf"^/{year}/\d+/$"))
            if link:
                heading = item.find_previous(["h2", "h3"])
                track = "main" if heading and heading.get_text(" ", strip=True) == "Main Track" else "unknown"
                authors = [a.get_text(" ", strip=True) for a in item.select("ol li")]
                entries.append((item.parent, link, link, authors, track))
    elif family == "aamas":
        for link in soup.find_all("a", href=re.compile(r"^\.\./pdfs/p\d+\.pdf$")):
            item = link.find_parent("p")
            heading = item.find_previous(["b", "strong"])
            section = " ".join(heading.get_text(" ", strip=True).split()) if heading else ""
            track = "main" if section.startswith("Session ") and not any(
                word in section for word in ("Blue Sky", "Innovative Applications")) else "nonresearch"
            byline = item.find("font", face="Times New Roman")
            authors = [" ".join(str(n).split()) for n in byline.children
                       if isinstance(n, str) and str(n).strip()] if byline else []
            entries.append((item, link, link, authors, track))
    elif family == "miccai":
        for link in soup.find_all("a", href=re.compile(rf"^/{year}/papers/\d+-Paper\d+\.html$")):
            entries.append((link.parent, link, link, [], "main"))
    elif family == "cvf":
        for item in soup.select("dt.ptitle"):
            link = item.find("a", href=True)
            names = item.find_next_sibling("dd")
            authors = [a.get_text(" ", strip=True) for a in names.find_all("a")] if names else []
            entries.append((item, link, link, authors, "main"))
    else:
        raise ValueError(f"unsupported official adapter: {family}")
    rows = []
    for item, link, title_element, author_element, track in entries:
        if link is None or title_element is None:
            raise ValueError("official paper missing title or record link")
        url = urljoin(edition["official_index"], link["href"])
        title = title_element.get_text(" ", strip=True)
        authors = author_element if isinstance(author_element, list) else [
            n.strip() for n in (author_element.get_text(" ", strip=True) if author_element else "").split(",") if n.strip()]
        identifier = urlsplit(url).path.rstrip("/").rsplit("/", 1)[-1].removesuffix(".html").removesuffix(".pdf")
        if "-Abstract" in identifier:
            identifier = identifier.split("-Abstract")[0]
        status, reason = "review", "unknown_track"
        if track in edition["include_tracks"]:
            status, reason = "included", "official_main_track"
        elif track in edition["exclude_tracks"]:
            status, reason = "excluded", "excluded_track"
        if re.search(r"\b(preface|withdrawn|retracted|editorial)\b", title, re.I):
            status, reason = "excluded", "nonresearch_record"
        if family == "acl" and identifier.endswith(".0"):
            status, reason = "excluded", "volume_front_matter"
        if not title or (not authors and family != "miccai"):
            status, reason = "review", "missing_title_or_byline"
        if family == "miccai" and status == "included":
            reason = "official_accepted_title_byline_pending_detail_after_split"
        pdf = item.find("a", href=lambda h: h and h.endswith(".pdf") and "supp" not in h.lower())
        rows.append(dict(paper_id=f"paper:{edition['venue_id'].split(':')[1]}:{year}:{identifier}",
            official_record_id=identifier, venue_id=edition["venue_id"], year=year,
            title=title, authors=authors, raw_authors=", ".join(authors), official_url=url,
            pdf_url=urljoin(url, pdf["href"]) if pdf else None, openreview_url=None,
            track=track, status=status, reason=reason, source_url=source["url"] + (("?" + urlencode(source["params"])) if source.get("params") else ""),
            source_sha256=source["sha256"], retrieved_at=source["retrieved_at"],
            source_locator=f"a[href='{link['href']}']", parser_version=VERSION))
    unique = {}
    for row in rows:
        previous = unique.get(row["paper_id"])
        if previous is not None and previous != row:
            raise ValueError("conflicting duplicate official record; reconcile roster")
        unique[row["paper_id"]] = row
    if not unique:
        raise ValueError("empty roster; reconcile official layout")
    # Exact repeated DOM entries are presentations of one official record, not
    # alternate versions. Differing titles, bylines, tracks or evidence still fail.
    return list(unique.values())
