"""Fetch primary sources into ``data/raw`` and write ``data/MANIFEST.yaml``.

Every source is described by a :class:`Source` record.  Sources served by hosts that
accept non-browser clients are downloaded here when missing (or when ``--refresh`` is
given).  Two hosts, ``downloads.regulations.gov`` and ``edap.epa.gov``, reject
non-browser clients; the corresponding files were retrieved once through a browser
session and are kept in the repository.  For those the script verifies presence and
records the checksum.  The manifest records, for every file, the source organization,
URL, retrieval date, SHA-256 checksum, licence or terms of use, and the exact query
parameters or export settings used.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import sys
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
MANIFEST = ROOT / "data" / "MANIFEST.yaml"

US_GOV = "United States Government work; public domain (17 U.S.C. 105)"
EIA_TERMS = "U.S. Energy Information Administration; public domain, see https://www.eia.gov/about/copyrights_reuse.php"
CROSSREF_TERMS = "Crossref REST API metadata; CC0 (https://www.crossref.org/documentation/retrieve-metadata/rest-api/rest-api-metadata-license-information/)"


@dataclass(frozen=True)
class Source:
    path: str
    url: str
    organization: str
    description: str
    license: str = US_GOV
    method: str = "http"
    retrieved: str = "2026-11-24"
    query: dict[str, str] = field(default_factory=dict)
    curl_options: str = ""


def fr_xml(doc: str, date: str, description: str) -> Source:
    y, m, d = date.split("-")
    return Source(
        path=f"federal_register/{doc}.xml",
        url=f"https://www.federalregister.gov/documents/full_text/xml/{y}/{m}/{d}/{doc}.xml",
        organization="Office of the Federal Register",
        description=description,
    )


SOURCES: list[Source] = [
    Source(
        "federal_register_api/2026-21155.json",
        "https://www.federalregister.gov/api/v1/documents/2026-21155.json",
        "Office of the Federal Register",
        "Federal Register API record for the proposed rule (comment deadline, docket, document ID)",
        retrieved="2026-11-23",
    ),
    Source(
        "federal_register_api/2026-06275.json",
        "https://www.federalregister.gov/api/v1/documents/2026-06275.json",
        "Office of the Federal Register",
        "Federal Register API record for the Set 2 final rule",
        retrieved="2026-11-23",
    ),
    Source(
        "federal_register/2026-21155.pdf",
        "https://www.govinfo.gov/content/pkg/FR-2026-10-16/pdf/2026-21155.pdf",
        "Government Publishing Office",
        "Proposed rule, 91 FR 65699 (Oct. 16, 2026), official PDF",
    ),
    fr_xml("2026-21155", "2026-10-16", "Proposed rule, 91 FR 65699, full-text XML"),
    Source(
        "federal_register/2026-06275.pdf",
        "https://www.govinfo.gov/content/pkg/FR-2026-04-01/pdf/2026-06275.pdf",
        "Government Publishing Office",
        "Set 2 final rule, 91 FR 16388 (Apr. 1, 2026), official PDF",
    ),
    fr_xml("2026-06275", "2026-04-01", "Set 2 final rule, 91 FR 16388, full-text XML"),
    fr_xml("2010-30296", "2010-12-09", "2011 RFS standards, 75 FR 76790"),
    fr_xml("2011-33451", "2012-01-09", "2012 RFS standards, 77 FR 1320"),
    fr_xml("2013-19557", "2013-08-15", "2013 RFS standards, 78 FR 49794"),
    fr_xml("2015-30893", "2015-12-14", "2014-2016 RFS standards, 80 FR 77420"),
    fr_xml("2016-28879", "2016-12-12", "2017 RFS standards, 81 FR 89746"),
    fr_xml("2017-26426", "2017-12-12", "2018 RFS standards, 82 FR 58486"),
    fr_xml("2018-26566", "2018-12-11", "2019 RFS standards, 83 FR 63704"),
    fr_xml("2020-00431", "2020-02-06", "2020 RFS standards, 85 FR 7016"),
    fr_xml("2022-12376", "2022-07-01", "2020-2022 RFS annual rules, 87 FR 39600"),
    fr_xml("2023-13462", "2023-07-12", "Set 1 rule (2023-2025 standards), 88 FR 44468"),
    fr_xml("2025-11128", "2025-06-17", "Set 2 proposed rule, 90 FR 25784"),
    fr_xml("2025-18111", "2025-09-18", "Set 2 supplemental proposal, 90 FR 45007"),
    fr_xml("2026-18132", "2026-09-04", "Extension of 2025 compliance reporting deadline, 91 FR 56780"),
    fr_xml("2021-26983", "2021-12-14", "Proposed denial of pending SRE petitions, 86 FR 70999"),
    fr_xml("2022-08686", "2022-04-25", "Notice of April 2022 denial of 36 SRE petitions, 87 FR 24300"),
    fr_xml("2022-08687", "2022-04-25", "Notice of April 2022 alternative compliance approach, 87 FR 24294"),
    fr_xml("2022-12359", "2022-06-08", "Notice of June 2022 denial of 69 SRE petitions, 87 FR 34873"),
    fr_xml("2022-12357", "2022-06-08", "Notice of June 2022 alternative compliance approach, 87 FR 34872"),
    fr_xml("2023-15401", "2023-07-20", "Notice of July 2023 denial of 26 SRE petitions, 88 FR 46795"),
    fr_xml("2025-16390", "2025-08-27", "Notice of August 2025 SRE decisions, 90 FR 41829"),
    fr_xml("2025-20440", "2025-11-20", "Notice of November 2025 SRE decisions, 90 FR 52385"),
    fr_xml("2026-15905", "2026-08-05", "Notice of August 3, 2026 SRE decisions, 91 FR 50532"),
    fr_xml("2026-17985", "2026-09-02", "Notice of August 31, 2026 SRE decisions, 91 FR 56444"),
    Source(
        "regulations_gov/EPA-HQ-OAR-2024-0505-0956.pdf",
        "https://downloads.regulations.gov/EPA-HQ-OAR-2024-0505-0956/content.pdf",
        "U.S. Environmental Protection Agency (docket EPA-HQ-OAR-2024-0505)",
        "Calculation of Co-Proposed Revised 2026 and 2027 RFS Percentage Standards (memorandum printed from spreadsheet)",
        method="browser",
    ),
    Source(
        "regulations_gov/EPA-HQ-OAR-2024-0505-0790.pdf",
        "https://downloads.regulations.gov/EPA-HQ-OAR-2024-0505-0790/content.pdf",
        "U.S. Environmental Protection Agency (docket EPA-HQ-OAR-2024-0505)",
        "Calculation of 2026 and 2027 RFS Percentage Standards Without SRE Reallocation Volumes",
        method="browser",
    ),
    Source(
        "regulations_gov/EPA-HQ-OAR-2024-0505-0789.pdf",
        "https://downloads.regulations.gov/EPA-HQ-OAR-2024-0505-0789/content.pdf",
        "U.S. Environmental Protection Agency (docket EPA-HQ-OAR-2024-0505)",
        "Calculation of Final 2026 and 2027 RFS Percentage Standards",
        method="browser",
    ),
    Source(
        "regulations_gov/EPA-HQ-OAR-2024-0505-0961.pdf",
        "https://downloads.regulations.gov/EPA-HQ-OAR-2024-0505-0961/content.pdf",
        "U.S. Environmental Protection Agency (docket EPA-HQ-OAR-2024-0505)",
        "Fuel Price Impacts for Reallocation of Additional 2025 SREs Proposed Rule (memorandum)",
        method="browser",
    ),
    Source(
        "regulations_gov/EPA-HQ-OAR-2024-0505-0954.pdf",
        "https://downloads.regulations.gov/EPA-HQ-OAR-2024-0505-0954/content.pdf",
        "U.S. Environmental Protection Agency (docket EPA-HQ-OAR-2024-0505)",
        "Proposed Regulations for Reallocation of Additional 2025 SREs Rule (amendatory text)",
        method="browser",
    ),
    Source(
        "regulations_gov/EPA-HQ-OAR-2024-0505-0953.pdf",
        "https://downloads.regulations.gov/EPA-HQ-OAR-2024-0505-0953/content.pdf",
        "U.S. Environmental Protection Agency (docket EPA-HQ-OAR-2024-0505)",
        "August 2025 Decisions on Petitions for RFS Small Refinery Exemptions (EPA-420-R-25-010), docket copy",
        method="browser",
    ),
    Source(
        "epa/420r26017.pdf",
        "https://www.epa.gov/system/files/documents/2026-08/420r26017.pdf",
        "U.S. Environmental Protection Agency",
        "August 31, 2026 Decisions on Petitions for RFS Small Refinery Exemptions (EPA-420-R-26-017)",
    ),
    Source(
        "epa/420r26004-2026-0803-rev.pdf",
        "https://www.epa.gov/system/files/documents/2026-08/420r26004-2026-0803-rev.pdf",
        "U.S. Environmental Protection Agency",
        "August 3, 2026 Decisions on Petitions for RFS Small Refinery Exemptions (EPA-420-R-26-004)",
    ),
    Source(
        "epa/420r25010.pdf",
        "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=P101HUDF.pdf",
        "U.S. Environmental Protection Agency (NEPIS)",
        "August 2025 Decisions on Petitions for RFS Small Refinery Exemptions (EPA-420-R-25-010)",
        curl_options="-L",
    ),
    Source(
        "epa/420r25013.pdf",
        "https://nepis.epa.gov/Exe/ZyPDF.cgi?Dockey=P101HUOJ.pdf",
        "U.S. Environmental Protection Agency (NEPIS)",
        "November 2025 Decisions on Petitions for RFS Small Refinery Exemptions (EPA-420-R-25-013)",
        curl_options="-L",
    ),
    Source(
        "epa/420r26011.pdf",
        "https://www.epa.gov/system/files/documents/2026-03/420r26011.pdf",
        "U.S. Environmental Protection Agency",
        "Set 2 Rule Regulatory Impact Analysis (EPA-420-R-26-011), March 2026",
    ),
    Source(
        "epa/set-2-detailed-fact-sheet.pdf",
        "https://www.epa.gov/system/files/documents/2026-03/set-2-detailed-fact-sheet.pdf",
        "U.S. Environmental Protection Agency",
        "Set 2 final rule detailed fact sheet",
    ),
    Source(
        "epa_dashboard/sre_table1_exempted_volumes.csv",
        "https://edap.epa.gov/public/single/?appid=73b2b6a5-70c6-4820-b3fa-186ac094f10d&sheet=7f64db2b-616a-493e-b9ea-8c3d8fc2ab6e&opt=noselections&select=clearall",
        "U.S. Environmental Protection Agency (RFS public data, Small Refinery Exemptions sheet)",
        "Table SRE-1: exempted volume of gasoline and diesel and exempted RVO by compliance year (dashboard last updated Nov. 19, 2026)",
        method="browser",
        query={"export": "Export Table button, CSV", "selections": "none"},
    ),
    Source(
        "epa_dashboard/sre_table2_petition_decisions.csv",
        "https://edap.epa.gov/public/single/?appid=73b2b6a5-70c6-4820-b3fa-186ac094f10d&sheet=7f64db2b-616a-493e-b9ea-8c3d8fc2ab6e&opt=noselections&select=clearall",
        "U.S. Environmental Protection Agency (RFS public data, Small Refinery Exemptions sheet)",
        "Table SRE-2: small refinery exemption petition decisions by compliance year",
        method="browser",
        query={"export": "Export Table button, CSV", "selections": "none"},
    ),
    Source(
        "epa_dashboard/sre_table3_petitions_since_2022.csv",
        "https://edap.epa.gov/public/single/?appid=73b2b6a5-70c6-4820-b3fa-186ac094f10d&sheet=7f64db2b-616a-493e-b9ea-8c3d8fc2ab6e&opt=noselections&select=clearall",
        "U.S. Environmental Protection Agency (RFS public data, Small Refinery Exemptions sheet)",
        "Table SRE-3: petitions submitted July 1, 2022 or later, with submission and decision dates",
        method="browser",
        query={"export": "Export Table button, CSV", "selections": "none"},
    ),
    Source(
        "epa_dashboard/rvo_table1_projected_vs_actual_volumes.csv",
        "https://edap.epa.gov/public/single/?appid=73b2b6a5-70c6-4820-b3fa-186ac094f10d&sheet=9fea8284-c3bc-45cb-8d99-8d91cff608e6&opt=currsel",
        "U.S. Environmental Protection Agency (RFS public data, Renewable Volume Obligations sheet)",
        "Table 1: projected versus actual volumes of gasoline and diesel reported by obligated parties (data current as of Nov. 10, 2026)",
        method="browser",
        query={"export": "Export Table button, CSV", "selections": "none"},
    ),
    Source(
        "epa_dashboard/rvo_table2_obligations_by_year.xlsx",
        "https://edap.epa.gov/public/single/?appid=73b2b6a5-70c6-4820-b3fa-186ac094f10d&sheet=9fea8284-c3bc-45cb-8d99-8d91cff608e6&opt=currsel",
        "U.S. Environmental Protection Agency (RFS public data, Renewable Volume Obligations sheet)",
        "Table 2: obligated party RVOs by year (projected volume obligation, reported obligation, prior-year deficit)",
        method="browser",
        query={
            "export": "table export icon, XLSX with formatting",
            "selections": "all compliance years (year filter cleared)",
        },
    ),
    Source(
        "epa_dashboard/rvo_table5_rins_retired_by_year.xlsx",
        "https://edap.epa.gov/public/single/?appid=73b2b6a5-70c6-4820-b3fa-186ac094f10d&sheet=9fea8284-c3bc-45cb-8d99-8d91cff608e6&opt=currsel",
        "U.S. Environmental Protection Agency (RFS public data, Renewable Volume Obligations sheet)",
        "Table 5: RINs used to demonstrate compliance by obligated parties, by category and year",
        method="browser",
        query={"export": "table export icon, XLSX with formatting", "selections": "none"},
    ),
    Source(
        "epa_dashboard/rvo_table6_deficits_by_year.xlsx",
        "https://edap.epa.gov/public/single/?appid=73b2b6a5-70c6-4820-b3fa-186ac094f10d&sheet=9fea8284-c3bc-45cb-8d99-8d91cff608e6&opt=currsel",
        "U.S. Environmental Protection Agency (RFS public data, Renewable Volume Obligations sheet)",
        "Table 6: total compliance deficits by RVO category and year",
        method="browser",
        query={"export": "table export icon, XLSX with formatting", "selections": "none"},
    ),
    Source(
        "ecfr/80.1405.xml",
        "https://www.ecfr.gov/api/versioner/v1/full/2026-11-20/title-40.xml?section=80.1405",
        "Office of the Federal Register (eCFR)",
        "40 CFR 80.1405 as of 2026-11-20 (standards table and percentage-standard equations)",
        query={"section": "80.1405", "date": "2026-11-20"},
        curl_options="--compressed",
    ),
    Source(
        "ecfr/80.1427.xml",
        "https://www.ecfr.gov/api/versioner/v1/full/2026-11-20/title-40.xml?section=80.1427",
        "Office of the Federal Register (eCFR)",
        "40 CFR 80.1427 as of 2026-11-20 (carryover RIN cap and deficit carryforward)",
        query={"section": "80.1427", "date": "2026-11-20"},
        curl_options="--compressed",
    ),
    Source(
        "ecfr/80.1451.xml",
        "https://www.ecfr.gov/api/versioner/v1/full/2026-11-20/title-40.xml?section=80.1451",
        "Office of the Federal Register (eCFR)",
        "40 CFR 80.1451 as of 2026-11-20 (compliance reporting deadlines)",
        query={"section": "80.1451", "date": "2026-11-20"},
        curl_options="--compressed",
    ),
    Source(
        "ecfr/versions_80.1405.json",
        "https://www.ecfr.gov/api/versioner/v1/versions/title-40.json?section=80.1405",
        "Office of the Federal Register (eCFR)",
        "Version history of 40 CFR 80.1405",
        query={"section": "80.1405"},
        curl_options="--compressed",
    ),
    Source(
        "eia/MGFUPUS2a.xls",
        "https://www.eia.gov/dnav/pet/hist_xls/MGFUPUS2a.xls",
        "U.S. Energy Information Administration",
        "U.S. product supplied of finished motor gasoline, annual (thousand barrels per day), series MGFUPUS2",
        license=EIA_TERMS,
    ),
    Source(
        "eia/MDIUPUS2a.xls",
        "https://www.eia.gov/dnav/pet/hist_xls/MDIUPUS2a.xls",
        "U.S. Energy Information Administration",
        "U.S. product supplied of distillate fuel oil, annual (thousand barrels per day), series MDIUPUS2",
        license=EIA_TERMS,
    ),
    Source(
        "crossref/10.1086_692071.json",
        "https://api.crossref.org/works/10.1086/692071",
        "Crossref",
        "Metadata for Knittel, Meiselman and Stock (2017)",
        license=CROSSREF_TERMS,
    ),
    Source(
        "crossref/10.1093_ajae_aax097.json",
        "https://api.crossref.org/works/10.1093/ajae/aax097",
        "Crossref",
        "Metadata for Lade, Lin Lawell and Smith (2018)",
        license=CROSSREF_TERMS,
    ),
    Source(
        "crossref/10.1002_aepp.70083.json",
        "https://api.crossref.org/works/10.1002/aepp.70083",
        "Crossref",
        "Metadata for Gerveni, Hubbs, Irwin and Stock (2026)",
        license=CROSSREF_TERMS,
    ),
]

# Secondary analysis used only as a cross-check; not redistributed, fetched on demand.
ON_DEMAND: list[Source] = [
    Source(
        "farmdoc/fdd111126.pdf",
        "https://farmdocdaily.illinois.edu/wp-content/uploads/2026/11/fdd111126.pdf",
        "farmdoc daily, University of Illinois",
        "Hubbs and Irwin (2026), farmdoc daily 16:204, secondary analysis used as cross-check only",
        license="Copyright University of Illinois Board of Trustees; not redistributed, fetched on demand",
    ),
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def download(src: Source, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(
        src.url,
        headers={
            "Accept-Encoding": "gzip" if "--compressed" in src.curl_options else "identity",
            "User-Agent": "rfsrealloc-fetch/1.0",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            import gzip

            data = gzip.decompress(data)
    dest.write_bytes(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--refresh", action="store_true", help="re-download http sources even if present")
    parser.add_argument("--on-demand", action="store_true", help="also fetch sources that are not redistributed")
    parser.add_argument("--verify", action="store_true", help="verify checksums against the existing manifest and exit")
    args = parser.parse_args(argv)

    if args.verify:
        manifest = yaml.safe_load(MANIFEST.read_text())
        bad = []
        for entry in manifest["files"]:
            p = RAW / entry["path"]
            if not p.exists() or sha256(p) != entry["sha256"]:
                bad.append(entry["path"])
        if bad:
            print("checksum mismatch or missing:", *bad, sep="\n  ")
            return 1
        print(f"verified {len(manifest['files'])} files")
        return 0

    sources = list(SOURCES) + (list(ON_DEMAND) if args.on_demand else [])
    entries = []
    today = dt.date.today().isoformat()
    for src in sources:
        dest = RAW / src.path
        retrieved = src.retrieved
        if src.method == "http" and (args.refresh or not dest.exists()):
            print("fetching", src.url)
            download(src, dest)
            retrieved = today
        if not dest.exists():
            print(f"missing {src.path}: retrieve through a browser from {src.url}", file=sys.stderr)
            return 1
        entries.append(
            {
                "path": src.path,
                "organization": src.organization,
                "description": src.description,
                "url": src.url,
                "retrieved": retrieved,
                "method": src.method if src.method == "http" else "browser (host rejects non-browser clients)",
                "query": src.query,
                "sha256": sha256(dest),
                "bytes": dest.stat().st_size,
                "license": src.license,
            }
        )
    manifest = {
        "generated": today,
        "note": (
            "Raw files are stored unmodified. Files marked 'browser' were retrieved through an "
            "interactive browser session because the host returns HTTP 403 to non-browser clients; "
            "their checksums are recorded here and verified by 'python scripts/fetch_data.py --verify'."
        ),
        "files": entries,
    }
    MANIFEST.write_text(yaml.safe_dump(manifest, sort_keys=False, allow_unicode=True))
    print(f"wrote {MANIFEST} with {len(entries)} entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
