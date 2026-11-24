"""Check every DOI in ``paper/references.bib`` against Crossref metadata.

For each entry with a ``doi`` field the resolved title, first author family name,
year and container title are compared with the BibTeX fields.  Entries without a DOI
(Federal Register documents, regulations, docket documents, agency reports) are
checked for the mandatory citation fields instead.  A mismatch fails the build.
"""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BIB = ROOT / "paper" / "references.bib"
CACHE = ROOT / "data" / "raw" / "crossref"


def parse_bib(text: str) -> list[dict[str, str]]:
    entries = []
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", text, flags=re.S):
        fields = {"type": m.group(1).lower(), "key": m.group(2).strip()}
        for fm in re.finditer(r"(\w+)\s*=\s*[{\"](.*?)[}\"]\s*,?\s*\n", m.group(3) + "\n", flags=re.S):
            fields[fm.group(1).lower()] = re.sub(r"\s+", " ", fm.group(2)).strip()
        entries.append(fields)
    return entries


def crossref(doi: str) -> dict[str, object]:
    cached = CACHE / (doi.replace("/", "_") + ".json")
    if cached.exists():
        return dict(json.loads(cached.read_text())["message"])
    req = urllib.request.Request(
        f"https://api.crossref.org/works/{doi}", headers={"User-Agent": "rfsrealloc-check-refs/1.0"}
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    CACHE.mkdir(parents=True, exist_ok=True)
    cached.write_text(json.dumps(data))
    return dict(data["message"])


def norm(s: str) -> str:
    s = re.sub(r"[{}\\]", "", s)
    s = s.replace("‐", "-").replace("–", "-")
    return re.sub(r"[^a-z0-9]+", " ", s.lower()).strip()


def main() -> int:
    entries = parse_bib(BIB.read_text())
    failures: list[str] = []
    for e in entries:
        if "doi" in e:
            try:
                msg = crossref(e["doi"])
            except Exception as exc:  # network or resolution failure
                failures.append(f"{e['key']}: DOI {e['doi']} could not be resolved ({exc})")
                continue
            title = norm(str(msg.get("title", [""])[0]))
            if norm(e.get("title", "")) != title:
                failures.append(
                    f"{e['key']}: title mismatch\n  bib: {e.get('title')}\n  doi: {msg.get('title', [''])[0]}"
                )
            authors = msg.get("author", [])
            fam = norm(str(authors[0].get("family", ""))) if isinstance(authors, list) and authors else ""
            if fam and fam not in norm(e.get("author", "")):
                failures.append(f"{e['key']}: first author {fam!r} not in bib author field")
            issued = msg.get("issued", {})
            year = str(issued.get("date-parts", [[None]])[0][0]) if isinstance(issued, dict) else ""
            pub_year = msg.get("published-print", {}) if isinstance(msg.get("published-print"), dict) else {}
            pyear = str(pub_year.get("date-parts", [[None]])[0][0]) if pub_year else ""
            if e.get("year") not in (year, pyear):
                failures.append(f"{e['key']}: year {e.get('year')} differs from Crossref {year}/{pyear}")
            container = norm(str(msg.get("container-title", [""])[0])) if msg.get("container-title") else ""
            if container and norm(e.get("journal", "")) != container:
                failures.append(
                    f"{e['key']}: journal mismatch\n  bib: {e.get('journal')}\n  doi: {msg.get('container-title', [''])[0]}"
                )
        else:
            needed = {
                "misc": ["title", "year"],
                "techreport": ["title", "institution", "year"],
                "article": ["title", "journal", "year"],
            }
            for f in needed.get(e["type"], ["title", "year"]):
                if f not in e:
                    failures.append(f"{e['key']}: missing field {f}")
            if e.get("fr_volume") and not e.get("fr_doc"):
                failures.append(f"{e['key']}: Federal Register entry lacks fr_doc")
    if failures:
        print("\n".join(failures))
        return 1
    print(f"checked {len(entries)} references")
    return 0


if __name__ == "__main__":
    sys.exit(main())
