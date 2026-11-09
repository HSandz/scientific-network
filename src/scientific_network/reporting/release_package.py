"""Render the local release report and package permitted tracked source files.

Run with ``python -m scientific_network.reporting.release_package --help``.
Nothing is published, staged, committed, or written beside the source report.
"""

from __future__ import annotations

import argparse
import base64
from hashlib import sha256
import json
import mimetypes
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
from tempfile import TemporaryDirectory
import unicodedata
from urllib.parse import unquote, urlsplit
from zipfile import ZIP_DEFLATED, ZipFile

from bs4 import BeautifulSoup


MIN_PAGES = 10
FONT_DIRECTORY = Path("/usr/share/fonts/truetype/dejavu")
FONT_FILES = {"regular": "DejaVuSans.ttf", "bold": "DejaVuSans-Bold.ttf", "mono": "DejaVuSansMono.ttf"}
CSS = """
@page { size: A4; margin: 17mm 16mm 18mm; }
* { box-sizing: border-box; }
html { color-scheme: light; }
body { font-family: 'Report Sans', sans-serif; font-size: 10.2pt; line-height: 1.46; color: #17212b; margin: 0; }
h1 { font-size: 23pt; line-height: 1.2; margin: 0 0 12mm; color: #132f49; }
h2 { break-before: page; page-break-before: always; font-size: 16pt; line-height: 1.25; margin: 0 0 6mm; color: #132f49; }
h3 { font-size: 12pt; margin: 6mm 0 3mm; }
h1, h2, h3, h4 { break-after: avoid; page-break-after: avoid; }
p, li { orphans: 3; widows: 3; }
p { margin: 0 0 3.2mm; }
a { color: #17496e; text-decoration: underline; overflow-wrap: anywhere; }
strong { font-weight: 700; }
table { border-collapse: collapse; width: 100%; margin: 4mm 0; font-size: 8.7pt; line-height: 1.34; }
thead { display: table-header-group; }
th, td { border: .2mm solid #c4cbd1; padding: 1.7mm 2mm; vertical-align: top; overflow-wrap: anywhere; }
th { background: #eaf0f4; font-weight: 700; text-align: left; }
tr { break-inside: avoid; page-break-inside: avoid; }
code, pre { font-family: 'Report Mono', monospace; font-size: 8.5pt; }
code { overflow-wrap: anywhere; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; border: .2mm solid #c4cbd1; padding: 3mm; background: #f5f7f8; }
pre code { white-space: inherit; }
figure { break-inside: avoid; page-break-inside: avoid; margin: 5mm 0 6mm; }
img { display: block; max-width: 100%; width: auto; max-height: 120mm; margin: 0 auto 2mm; object-fit: contain; }
figcaption { font-size: 9pt; line-height: 1.36; color: #344552; }
figcaption p { margin: 0; }
blockquote { border-left: 1mm solid #c4cbd1; margin-left: 0; padding-left: 4mm; }
@media screen { body { max-width: 180mm; margin: 12mm auto; padding: 6mm; } h2 { margin-top: 12mm; } }
"""


def _digest(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _run(arguments: list[str], *, cwd: Path | None = None, timeout: int = 90) -> str:
    try:
        result = subprocess.run(arguments, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=True)
    except (OSError, subprocess.SubprocessError) as exc:
        raise ValueError(f"local report command failed: {arguments[0]} ({type(exc).__name__})") from exc
    return result.stdout


def _repo_root(report: Path) -> Path:
    return Path(_run(["git", "-C", str(report.parent), "rev-parse", "--show-toplevel"]).strip()).resolve()


def _local_target(url: str, report: Path, root: Path) -> Path | None:
    parts = urlsplit(url)
    if parts.scheme or parts.netloc:
        if parts.scheme in {"http", "https", "mailto", "tel", "data"}:
            return None
        raise ValueError(f"unsupported report link scheme: {parts.scheme}")
    if not parts.path:
        return None
    # Root-relative report links refer to the repository root, not the host FS.
    target = root / unquote(parts.path).lstrip("/") if parts.path.startswith("/") else report.parent / unquote(parts.path)
    if _has_symlink(target, root):
        raise ValueError(f"report local link must not use a symlink: {url}")
    target = target.resolve()
    if not target.is_relative_to(root) or not target.exists():
        raise ValueError(f"report local link is missing or outside the repository: {url}")
    return target


def _has_symlink(path: Path, root: Path) -> bool:
    if path.is_symlink():
        return True
    return any(parent.is_symlink() for parent in path.parents if parent != root and parent.is_relative_to(root))


def render_html(report: Path, root: Path) -> tuple[str, dict]:
    """Render tables/code and embed local images/fonts after checking local links."""
    try:
        import markdown
    except ImportError as exc:
        raise ValueError("report rendering requires the optional report dependency group (--extra report)") from exc
    source = report.read_text(encoding="utf-8")
    if "\ufffd" in source:
        raise ValueError("report source contains a replacement glyph")
    document = markdown.markdown(source, extensions=["tables", "fenced_code", "toc"], output_format="html")
    soup = BeautifulSoup(document, "html.parser")
    ids = {element["id"] for element in soup.find_all(id=True)}
    local_links = []
    external_links = set()
    images = []
    raster_count = 0
    for element in soup.find_all(["a", "img"]):
        attribute = "src" if element.name == "img" else "href"
        url = element.get(attribute, "")
        if not url:
            raise ValueError(f"report {element.name} has no {attribute}")
        target = _local_target(url, report, root)
        if target is None:
            if element.name == "img":
                raise ValueError("report images must be local repository files")
            if url.startswith("#") and unquote(url[1:]) not in ids:
                raise ValueError(f"report has an unresolved internal anchor: {url}")
            if urlsplit(url).scheme in {"http", "https"}:
                external_links.add(url)
            continue
        relative = target.relative_to(root).as_posix()
        local_links.append({"url": url, "repository_path": relative, "kind": "directory" if target.is_dir() else "file"})
        if element.name == "img":
            mime = mimetypes.guess_type(target.name)[0]
            if not target.is_file() or not mime or not mime.startswith("image/"):
                raise ValueError(f"report image is not a supported image file: {url}")
            raw = target.read_bytes()
            element["src"] = f"data:{mime};base64,{base64.b64encode(raw).decode('ascii')}"
            images.append({"repository_path": relative, "sha256": sha256(raw).hexdigest(), "media_type": mime})
            raster_count += mime != "image/svg+xml"
        elif url.startswith("/"):
            # Packaged report.html occupies the same directory as report.md.
            import os
            parts = urlsplit(url)
            element["href"] = os.path.relpath(target, report.parent) + ("#" + parts.fragment if parts.fragment else "")
    for image in list(soup.find_all("img")):
        paragraph = image.parent
        if paragraph.name != "p" or len(paragraph.find_all("img")) != 1:
            continue
        caption = paragraph.find_next_sibling()
        figure = soup.new_tag("figure")
        paragraph.wrap(figure)
        if caption and caption.name == "p" and re.match(r"Figure\s+\d+[.:]", caption.get_text(" ", strip=True)):
            figcaption = soup.new_tag("figcaption")
            caption.wrap(figcaption)
            figure.append(figcaption.extract())
    fonts = []
    font_css = []
    for kind, filename in FONT_FILES.items():
        path = FONT_DIRECTORY / filename
        if not path.is_file():
            raise ValueError(f"required report font is unavailable: {path}")
        family = "Report Mono" if kind == "mono" else "Report Sans"
        weight = 700 if kind == "bold" else 400
        encoded = base64.b64encode(path.read_bytes()).decode("ascii")
        font_css.append(f"@font-face {{ font-family: '{family}'; font-weight: {weight}; src: url(data:font/ttf;base64,{encoded}) format('truetype'); }}")
        fonts.append({"name": filename, "sha256": _digest(path)})
    title = soup.h1.get_text(" ", strip=True) if soup.h1 else "AI Research Network report"
    from html import escape
    result = f'<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><title>{escape(title)}</title><style>{"".join(font_css)}{CSS}</style></head><body><main>{soup}</main></body></html>\n'
    return result, {
        "headings": [heading.get_text(" ", strip=True) for heading in soup.find_all(["h1", "h2"])],
        "local_links": local_links, "local_link_count": len(local_links), "images": images,
        "image_count": len(images), "raster_image_count": raster_count, "fonts": fonts,
        "external_url_count": len(external_links), "external_url_availability": "not_tested",
    }


def permitted_source_path(relative: str) -> bool:
    """Apply explicit privacy exclusions even if an unsafe file was tracked."""
    path = PurePosixPath(relative)
    if path.is_absolute() or ".." in path.parts:
        return False
    lowered = tuple(part.lower() for part in path.parts)
    if any(part.startswith(".env") and part != ".env.example" for part in lowered):
        return False
    if lowered[:2] in {("data", "raw"), ("data", "interim"), ("data", "processed"), ("reports", "runs")}:
        return False
    private_dirs = {"models", "volumes", ".volumes", ".venv", "node_modules", "__pycache__", ".git"}
    if any(part in private_dirs or part.startswith(("neo4j-data", "neo4j-logs", "neo4j-five-year-data", "neo4j-five-year-logs")) for part in lowered):
        return False
    return path.suffix.lower() not in {".pdf", ".dump", ".backup", ".zip", ".tar", ".gz", ".tgz", ".7z", ".rar", ".db", ".sqlite", ".sqlite3", ".pem", ".key"}


def print_html(html: str) -> str:
    """Keep repository references visible without nonportable PDF file links."""
    soup = BeautifulSoup(html, "html.parser")
    for anchor in list(soup.find_all("a", href=True)):
        url = anchor["href"]
        if not url.startswith("#") and not urlsplit(url).scheme:
            anchor.unwrap()
    return str(soup)


def package_sources(root: Path, report: Path, html_path: Path, pdf_path: Path, output_dir: Path,
                    validation: dict) -> dict:
    """Package tracked working-tree bytes and explicit render artifacts only."""
    tracked = _run(["git", "ls-files", "-z"], cwd=root).split("\0")
    members = {}
    excluded = []
    for relative in sorted(set(tracked) - {""}):
        path = root / relative
        if not permitted_source_path(relative) or _has_symlink(path, root) or not path.is_file() or not path.resolve().is_relative_to(root):
            excluded.append(relative)
            continue
        members[relative] = path
    report_member = report.relative_to(root).as_posix()
    if report_member not in members:
        raise ValueError("release report must be a permitted tracked source file")
    parent = PurePosixPath(report_member).parent
    for path in (html_path, pdf_path):
        member = (parent / ("report" + path.suffix)).as_posix()
        if member in members:
            raise ValueError(f"rendered artifact would replace a tracked source member: {member}")
        members[member] = path
    for link in validation["local_links"]:
        path = link["repository_path"]
        included = path in members if link["kind"] == "file" else any(member.startswith(path.rstrip("/") + "/") for member in members)
        if not included:
            raise ValueError(f"report local link is absent from the permitted tracked package: {path}")
    manifest = {
        "package_kind": "local_course_submission_draft", "source_commit": _run(["git", "rev-parse", "HEAD"], cwd=root).strip(),
        "source_bytes": "tracked_working_tree_files", "report_source": report_member,
        "report_source_sha256": _digest(report), "render_validation": validation,
        "member_count": len(members), "members": [{"path": name, "sha256": _digest(path), "size_bytes": path.stat().st_size} for name, path in sorted(members.items())],
        "excluded_tracked_paths": excluded, "manifest_member": "submission-manifest.json",
        "limitations": ["Tracked working-tree bytes may differ from source_commit; member hashes identify the actual packaged files.",
                        "External URL availability was not tested. This local package is not a publication or submission."],
    }
    manifest_path = output_dir / "submission-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    archive = output_dir / "scientific-network-submission.zip"
    with ZipFile(archive, "x", compression=ZIP_DEFLATED, compresslevel=6) as zipped:
        for name, path in sorted(members.items()):
            raw = path.read_bytes()
            item = next(item for item in manifest["members"] if item["path"] == name)
            if sha256(raw).hexdigest() != item["sha256"]:
                raise ValueError(f"tracked source changed during packaging: {name}")
            zipped.writestr(name, raw)
        zipped.write(manifest_path, "submission-manifest.json")
    return {"archive": str(archive), "archive_sha256": _digest(archive), "manifest": str(manifest_path),
            "manifest_sha256": _digest(manifest_path), "source_commit": manifest["source_commit"],
            "member_count": len(members) + 1}


def build_release_package(report: Path, output_dir: Path, browser: str = "google-chrome") -> dict:
    report = report.absolute()
    root = _repo_root(report)
    if _has_symlink(report, root) or not report.is_file() or not report.resolve().is_relative_to(root):
        raise ValueError("report must be a regular file inside the repository")
    output_dir = output_dir.absolute()
    if output_dir.exists() or output_dir.is_symlink():
        raise ValueError("refusing to overwrite a report package output directory")
    for command in (browser, "pdfinfo", "pdftotext", "pdfimages"):
        if not shutil.which(command):
            raise ValueError(f"required local report tool is unavailable: {command}")
    report_sha = _digest(report)
    html, validation = render_html(report, root)
    output_dir.mkdir(parents=True, exist_ok=False)
    html_path = output_dir / "report.html"
    pdf_path = output_dir / "report.pdf"
    html_path.write_text(html, encoding="utf-8")
    with TemporaryDirectory(prefix="scientific-network-report-chrome-") as profile:
        print_path = Path(profile) / "print.html"
        print_path.write_text(print_html(html), encoding="utf-8")
        _run([browser, "--headless", "--no-sandbox", "--disable-gpu", "--no-pdf-header-footer",
              "--disable-dev-shm-usage", f"--user-data-dir={profile}", f"--print-to-pdf={pdf_path}", print_path.as_uri()])
    info = _run(["pdfinfo", str(pdf_path)])
    pages = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
    if not pages or int(pages[1]) < MIN_PAGES:
        raise ValueError(f"rendered report requires at least {MIN_PAGES} pages; measured {pages[1] if pages else 'unknown'}")
    if "A4" not in info:
        raise ValueError("rendered report is not A4")
    text = _run(["pdftotext", "-layout", str(pdf_path), "-"])
    if not text.strip() or "\ufffd" in text:
        raise ValueError("rendered PDF has empty text or replacement glyphs")
    normalized = " ".join(unicodedata.normalize("NFKC", text).split())
    absent = [heading for heading in validation["headings"] if " ".join(unicodedata.normalize("NFKC", heading).split()) not in normalized]
    if absent:
        raise ValueError(f"rendered PDF omits section headings: {absent}")
    image_listing = _run(["pdfimages", "-list", str(pdf_path)])
    image_count = sum(len(parts) > 2 and parts[0].isdigit() and parts[2] == "image" for line in image_listing.splitlines() if (parts := line.split()))
    if image_count < validation["raster_image_count"]:
        raise ValueError("rendered PDF is missing report raster figures")
    annotation_status = "not_run_mutool_unavailable"
    if shutil.which("mutool"):
        annotations = _run(["mutool", "show", str(pdf_path), "pages/*/Annots/*"])
        if re.search(r"file:|/S\s*/(?:GoToR|Launch)", annotations, re.IGNORECASE):
            raise ValueError("shared PDF contains a nonportable local-file annotation")
        annotation_status = "passed_no_local_file_annotations"
    if _digest(report) != report_sha:
        raise ValueError("report source changed during rendering; use a new output version")
    validation.update(page_count=int(pages[1]), page_format="A4", section_headings_verified=len(validation["headings"]),
                      pdf_raster_image_count=image_count, replacement_glyphs=0, text_extraction="passed",
                      pdf_repository_references="plain_text", html_repository_references="portable_relative_links",
                      pdf_local_file_annotation_check=annotation_status)
    result = package_sources(root, report, html_path, pdf_path, output_dir, validation)
    result.update(report_html=str(html_path), report_pdf=str(pdf_path), page_count=int(pages[1]),
                  image_count=validation["image_count"], section_headings_verified=len(validation["headings"]),
                  external_url_availability="not_tested")
    (output_dir / "package-receipt.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--browser", default="google-chrome")
    args = parser.parse_args(argv)
    try:
        result = build_release_package(args.report, args.output_dir, args.browser)
    except (OSError, ValueError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
