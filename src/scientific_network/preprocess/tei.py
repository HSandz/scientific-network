"""GROBID header parsing preserves explicit TEI author-to-affiliation nesting."""

import xml.etree.ElementTree as ET

NS = {"t": "http://www.tei-c.org/ns/1.0"}


def text(element) -> str:
    return " ".join(" ".join(element.itertext()).split()) if element is not None else ""


def parse_header(body: bytes) -> list[dict]:
    root = ET.fromstring(body)
    result = []
    for position, author in enumerate(root.findall(".//t:sourceDesc/t:biblStruct/t:analytic/t:author", NS), 1):
        name = author.find("t:persName", NS)
        if name is None:
            continue
        affiliations = []
        for affiliation in author.findall("t:affiliation", NS):
            institutions = [text(org) for org in affiliation.findall("t:orgName", NS)
                            if org.get("type") in {"institution", "laboratory"}]
            affiliations.append({"raw_text": text(affiliation), "institutions": institutions,
                "locator": f"//analytic/author[{position}]/affiliation[{len(affiliations) + 1}]"})
        result.append({"name": text(name), "position": position,
            "orcid": next((text(x) for x in author.findall("t:idno", NS) if (x.get("type") or "").lower() == "orcid"), None),
            "affiliations": affiliations})
    return result
