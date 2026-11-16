"""Check static files/references; not a browser, privacy or rights audit."""
from html.parser import HTMLParser
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

from qa import read_json

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PRIVATE_PATH = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/]|file://|/Users/|/home/")


class References(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])


def check():
    errors = []
    for name in ("index.html", "app.js", "style.css", "review-data.json"):
        if not (SITE / name).is_file():
            errors.append(f"Missing site/{name}; run build_site.py after authoring")
    for path in SITE.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(SITE)
        if any(x in {"private", "raw", "__local_materials", "__pycache__"} for x in rel.parts):
            errors.append(f"Excluded directory inside site: {rel.as_posix()}")
        if path.suffix.lower() in {".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".gif", ".pdf", ".pyc"}:
            errors.append(f"Source/binary asset needs explicit release review: {rel.as_posix()}")
        if path.suffix.lower() == ".png" and rel.parts[:2] != ("assets", "screenshots"):
            errors.append(f"PNG allowed only as a manually reviewed page screenshot: {rel.as_posix()}")
        if path.suffix.lower() not in {".html", ".css", ".js", ".json", ".svg", ".txt", ".md"}:
            continue
        text = path.read_text(encoding="utf-8-sig")
        if PRIVATE_PATH.search(text):
            errors.append(f"Private path in site/{rel.as_posix()}")
        refs = []
        if path.suffix == ".html":
            parsed = References()
            parsed.feed(text)
            refs = parsed.links
            for ref in refs:
                if ref.startswith("#") and unquote(ref[1:]) not in parsed.ids:
                    errors.append(f"Missing anchor in {rel.as_posix()}: {ref}")
        elif path.suffix == ".css":
            refs = [x.strip(" '\"") for x in re.findall(r"url\(([^)]+)\)", text)]
        for ref in refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc or not url.path:
                continue
            if url.path.startswith("/"):
                errors.append(f"Root-relative link unsuitable for a project Pages site: {ref}")
                continue
            target = (path.parent / unquote(url.path)).resolve()
            if not target.is_relative_to(ROOT) or not target.exists():
                errors.append(f"Broken local reference in {rel.as_posix()}: {ref}")
    if (SITE / "review-data.json").is_file():
        data = read_json(SITE / "review-data.json")
        if data.get("release") != {"status": "pending_review", "geojson_features": 0}:
            errors.append("Release status differs from the current no-geometry review policy")
    if errors:
        print("Static checks failed:\n- " + "\n- ".join(errors), file=sys.stderr)
        return 1
    print("Static references and release exclusions pass. Browser behavior, factual accuracy and image rights still require review.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(check())
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"Site check failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
