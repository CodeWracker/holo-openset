"""Run the related-work search strings S1..S8 on open indexes (protocol C.1, open complement).

Scopus and ScienceDirect need an Elsevier key that we do not have. This script runs the
same strings, as declared translations, on two open indexes that need no key and no
identification, so that the survey also covers IEEE, Optica, SPIE, Elsevier and Wiley
venues that PubMed does not index:

* ``openalex``: ``/works?filter=title_and_abstract.search:<string>``; the ScienceDirect
  form of each string (plain words, no wildcards; OpenAlex stems words itself);
* ``s2``: Semantic Scholar ``/graph/v1/paper/search/bulk`` (title and abstract); the
  Scopus form of each string with AND as ``+`` and OR as ``|``, single-word wildcards
  kept, and the wildcards inside phrases (which this engine does not expand) replaced by
  the explicit forms (``"raw hologram" | "raw holograms"``...).

Crossref has no boolean search and is not used for the strings (only to check metadata).

Usage (run from outside the download folders, with ``python3 -I``)::

    python3 -I refs_open_search.py fetch {openalex,s2} S1 OUT_DIR   # OUT_DIR must be new or empty
    python3 -I refs_open_search.py to-ris {openalex,s2} OUT_DIR     # writes OUT_DIR/records.ris, .csv

Nothing identifying is sent: a generic User-Agent, no e-mail, no ``mailto``, no key.
Only the standard library is used. One request at a time, with a pause between requests.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

UA = "Mozilla/5.0 (X11; Linux x86_64)"
PAUSE_S = 3.0
MAX_RECORDS = 3000

# ScienceDirect forms, copied from sections/02-related.tex of the paper (S1-S8).
OPENALEX = {
    "S1": '("raw hologram" OR "reconstruction-free" OR "without reconstruction") AND hologram AND (classification OR recognition OR detection)',
    "S2": '("digital holography" OR "in-line holography" OR lensless OR "lens-free") AND ("deep learning" OR "neural network") AND (classification OR recognition)',
    "S3": '(hologram OR lensless OR "quantitative phase") AND ("open set" OR "novelty detection" OR "out-of-distribution" OR "unknown class" OR "anomaly detection")',
    "S4": 'microscopy AND ("open set" OR "novelty detection" OR "out-of-distribution") AND (cell OR bacteria OR particle OR microorganism)',
    "S5": '("learnable Fourier" OR "Fourier layer" OR "global filter" OR "spectral layer" OR "Fourier neural operator") AND (hologram OR diffraction OR lensless)',
    "S6": '("deep learning" OR "neural network") AND hologram AND (autofocus OR "twin image" OR "phase recovery" OR "phase retrieval")',
    "S7": '("field of view" OR "high-throughput" OR "wide-field") AND (lensless OR "digital holography") AND ("real-time" OR GPU OR computation)',
    "S8": '(hologram OR lensless) AND (simulation OR synthetic) AND ("sim-to-real" OR "domain gap" OR "domain adaptation" OR "partial coherence")',
}

# Scopus forms of 02-related.tex in Semantic Scholar syntax (see the module docstring).
S2 = {
    "S1": '("raw hologram" | "raw holograms" | "reconstruction-free" | "without reconstruction") + hologra* + (classif* | recogni* | detect*)',
    "S2": '("digital holography" | "digital holographic" | "in-line holography" | "in-line holographic" | "in-line hologram" | "in-line holograms" | lensless | "lens-free") + ("deep learning" | "neural network" | "neural networks") + (classif* | recogni*)',
    "S3": '(hologra* | lensless | "quantitative phase") + ("open set" | "novelty detection" | "out-of-distribution" | "unknown class" | "unknown classes" | "anomaly detection")',
    "S4": 'microscop* + ("open set" | "novelty detection" | "out-of-distribution") + (cell* | bacteri* | particle* | microorganism*)',
    "S5": '("learnable Fourier" | "Fourier layer" | "Fourier layers" | "global filter" | "spectral layer" | "Fourier neural operator") + (hologra* | diffraction | lensless)',
    "S6": '("deep learning" | "neural network" | "neural networks") + hologra* + (autofocus* | "twin image" | "phase recovery" | "phase retrieval")',
    "S7": '("field of view" | "high-throughput" | "wide-field") + (lensless | "digital holography" | "digital holographic") + ("real-time" | GPU | computation*)',
    "S8": '(hologra* | lensless) + (simulat* | synthetic) + ("sim-to-real" | "domain gap" | "domain adaptation" | "partial coherence")',
}

S2_FIELDS = "title,year,externalIds,venue,journal,abstract,authors,publicationDate,openAccessPdf"


def get_json(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < 3:
                time.sleep(15 * (attempt + 1))
                continue
            raise
    raise RuntimeError("unreachable")


def fetch(source: str, string: str, out: Path) -> int:
    if out.exists() and any(out.iterdir()):
        print(f"{out} is not empty; use a new folder", file=sys.stderr)
        return 1
    out.mkdir(parents=True, exist_ok=True)
    query = (OPENALEX if source == "openalex" else S2)[string]
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    urls, n, total, page = [], 0, None, 1
    if source == "openalex":
        cursor = "*"
        while cursor and n < MAX_RECORDS:
            params = {"filter": f"title_and_abstract.search:{query}", "per-page": "200", "cursor": cursor}
            url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
            d = get_json(url)
            urls.append(url)
            (out / f"page_{page:03d}.json").write_text(json.dumps(d), encoding="utf-8")
            total = d.get("meta", {}).get("count")
            res = d.get("results", [])
            n += len(res)
            cursor = d.get("meta", {}).get("next_cursor") if res else None
            page += 1
            time.sleep(PAUSE_S)
    else:
        token = None
        while n < MAX_RECORDS:
            params = {"query": query, "fields": S2_FIELDS}
            if token:
                params["token"] = token
            url = "https://api.semanticscholar.org/graph/v1/paper/search/bulk?" + urllib.parse.urlencode(params)
            d = get_json(url)
            urls.append(url)
            (out / f"page_{page:03d}.json").write_text(json.dumps(d), encoding="utf-8")
            total = d.get("total")
            n += len(d.get("data") or [])
            token = d.get("token")
            page += 1
            time.sleep(PAUSE_S)
            if not token:
                break
    prov = {"source": source, "string": string, "query": query, "started_utc": started,
            "finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "user_agent": UA, "requests": urls, "reported_total": total, "records_saved": n,
            "truncated_at": MAX_RECORDS if (total or 0) > n else None}
    (out / "query.json").write_text(json.dumps(prov, indent=1), encoding="utf-8")
    print(f"{source} {string}: total {total}, saved {n} -> {out}")
    return 0


def oa_abstract(inv) -> str:
    if not inv:
        return ""
    pos = {}
    for w, idx in inv.items():
        for i in idx:
            pos[i] = w
    return " ".join(pos[i] for i in sorted(pos))


def clean(v) -> str:
    return " ".join(str(v or "").replace("\r", " ").replace("\n", " ").split())


def records(source: str, folder: Path):
    for f in sorted(folder.glob("page_*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        if source == "openalex":
            for w in d.get("results", []):
                doi = (w.get("doi") or "").replace("https://doi.org/", "")
                src = ((w.get("primary_location") or {}).get("source") or {})
                ids = w.get("ids") or {}
                pmid = (ids.get("pmid") or "").rsplit("/", 1)[-1]
                yield {"id": w.get("id", ""), "title": clean(w.get("title")), "year": str(w.get("publication_year") or ""),
                       "venue": clean(src.get("display_name")), "doi": doi, "pmid": pmid,
                       "type": w.get("type", ""), "oa_url": ((w.get("open_access") or {}).get("oa_url") or ""),
                       "authors": [clean((a.get("author") or {}).get("display_name")) for a in w.get("authorships", [])],
                       "abstract": clean(oa_abstract(w.get("abstract_inverted_index")))}
        else:
            for p in d.get("data") or []:
                ext = p.get("externalIds") or {}
                yield {"id": p.get("paperId", ""), "title": clean(p.get("title")), "year": str(p.get("year") or ""),
                       "venue": clean(p.get("venue") or (p.get("journal") or {}).get("name")),
                       "doi": ext.get("DOI") or "", "pmid": str(ext.get("PubMed") or ""), "type": "",
                       "oa_url": ((p.get("openAccessPdf") or {}).get("url") or ""),
                       "authors": [clean(a.get("name")) for a in p.get("authors") or []],
                       "abstract": clean(p.get("abstract"))}


def to_ris(source: str, folder: Path) -> int:
    recs = list(records(source, folder))
    lines = []
    for r in recs:
        lines.append("TY  - JOUR")
        lines.append(f"TI  - {r['title']}")
        lines += [f"AU  - {a}" for a in r["authors"] if a]
        if r["year"]:
            lines.append(f"PY  - {r['year']}")
        if r["venue"]:
            lines.append(f"JO  - {r['venue']}")
        if r["doi"]:
            lines.append(f"DO  - {r['doi']}")
        if r["pmid"]:
            lines.append(f"AN  - PMID:{r['pmid']}")
        if r["abstract"]:
            lines.append(f"AB  - {r['abstract']}")
        lines.append(f"DB  - {source}")
        lines.append(f"UR  - {r['id']}")
        lines.append("ER  - ")
        lines.append("")
    (folder / "records.ris").write_text("\n".join(lines), encoding="utf-8")
    with (folder / "records.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["id", "title", "year", "venue", "doi", "pmid", "type", "oa_url", "abstract"])
        w.writeheader()
        for r in recs:
            w.writerow({k: r[k] for k in w.fieldnames})
    print(f"{folder}: {len(recs)} records -> records.ris, records.csv")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("source", choices=("openalex", "s2"))
    f.add_argument("string", choices=sorted(OPENALEX))
    f.add_argument("out", type=Path)
    t = sub.add_parser("to-ris")
    t.add_argument("source", choices=("openalex", "s2"))
    t.add_argument("folder", type=Path)
    a = ap.parse_args(argv)
    if a.cmd == "fetch":
        return fetch(a.source, a.string, a.out)
    return to_ris(a.source, a.folder)


if __name__ == "__main__":
    sys.exit(main())
