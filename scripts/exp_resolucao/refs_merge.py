"""Merge and de-duplicate the .RIS exports of the related-work survey (protocol C.1).

Usage:
    python3 -I scripts/exp_resolucao/refs_merge.py REFS_DIR [--out OUT_DIR] [--year-from 2020]

REFS_DIR is the survey folder (``referencias/c``). Every ``*.ris`` file under
``REFS_DIR/pubmed``, ``REFS_DIR/scopus`` and ``REFS_DIR/sciencedirect`` is read
(sub-folders included). The database is the first folder under REFS_DIR; the
search string (S1..S8) is taken from the first ``S<digit>`` token found in the
file's path relative to that folder (``pubmed/S3/records.ris``,
``scopus/S3.ris``, ``sciencedirect/S3_2020.ris`` ...); a file with no such token
is counted under ``?``. Drop the Scopus and ScienceDirect exports there with the
string in the file name and run the script again. Export each string once,
WITHOUT the year filter: the script counts the works from ``--year-from`` on
itself (an extra export with the filter would only be merged as duplicates, but
it would inflate the per-database record counts).

Two records are the same work when they share a normalised DOI, a PMID, or a
normalised title (lower case, accents and punctuation removed); the grouping is
transitive (union-find). Outputs, in OUT_DIR (default REFS_DIR/merged):

* ``merged.csv``  one row per work: key, title, year, journal, doi, pmid,
  databases, strings, number of records, and the screening columns
  (decision, reason, access, notes) carried over from a previous
  ``screening.csv`` in OUT_DIR when the key matches;
* ``merged.ris``  one RIS record per work (the most complete one);
* ``counts.json`` and a printed table: records per database and string, with
  and without the year filter, and works after de-duplication.

Only the standard library is used; nothing is fetched from the network.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

DATABASES = ("pubmed", "scopus", "sciencedirect")
SCREEN_COLS = ("decision", "reason", "access", "notes")


def parse_ris(text: str) -> list[dict[str, list[str]]]:
    """Return a list of records, each a dict tag -> list of values."""
    recs, cur, last = [], None, None
    for raw in text.splitlines():
        line = raw.rstrip("\r\n").lstrip("﻿")
        m = re.match(r"^([A-Z][A-Z0-9])  -\s?(.*)$", line)
        if m:
            tag, val = m.group(1), m.group(2).strip()
            if tag == "TY":
                cur = defaultdict(list)
                recs.append(cur)
            if cur is None:
                continue
            if tag == "ER":
                cur, last = None, None
                continue
            cur[tag].append(val)
            last = tag
        elif cur is not None and last and line.strip():
            cur[last][-1] += " " + line.strip()
    return [dict(r) for r in recs]


def norm_doi(v: str) -> str:
    v = v.strip().lower()
    v = re.sub(r"^(https?://)?(dx\.)?doi\.org/", "", v)
    v = re.sub(r"^doi:\s*", "", v)
    return v.rstrip(".")


def norm_title(v: str) -> str:
    v = unicodedata.normalize("NFKD", v)
    v = "".join(c for c in v if not unicodedata.combining(c)).lower()
    v = re.sub(r"<[^>]+>", " ", v)
    v = re.sub(r"[^a-z0-9]+", " ", v)
    return " ".join(v.split())


def first(rec, *tags):
    for t in tags:
        if rec.get(t):
            return rec[t][0]
    return ""


def record_keys(rec) -> dict[str, str]:
    doi = ""
    for t in ("DO", "DI"):
        for v in rec.get(t, []):
            doi = norm_doi(v)
            break
        if doi:
            break
    if not doi:
        for v in rec.get("UR", []) + rec.get("L2", []):
            m = re.search(r"doi\.org/(10\.\S+)", v)
            if m:
                doi = norm_doi(m.group(1))
                break
    pmid = ""
    for t in ("AN", "C2", "N1", "M2"):
        for v in rec.get(t, []):
            m = re.search(r"PMID[:\s]*(\d+)", v, re.I)
            if m:
                pmid = m.group(1)
                break
        if pmid:
            break
    if not pmid and first(rec, "DB").lower() == "pubmed":
        m = re.search(r"(\d+)", first(rec, "AN"))
        pmid = m.group(1) if m else ""
    title = norm_title(first(rec, "TI", "T1", "CT"))
    year = ""
    m = re.search(r"(19|20)\d\d", first(rec, "PY", "Y1", "DA"))
    if m:
        year = m.group(0)
    return {"doi": doi, "pmid": pmid, "title": title, "year": year}


def string_of(path: Path) -> str:
    m = re.search(r"(?<![A-Za-z0-9])S([1-9])(?![0-9])", str(path))
    return f"S{m.group(1)}" if m else "?"


class UF:
    def __init__(self, n):
        self.p = list(range(n))

    def find(self, i):
        while self.p[i] != i:
            self.p[i] = self.p[self.p[i]]
            i = self.p[i]
        return i

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self.p[max(ra, rb)] = min(ra, rb)


def to_ris(rec) -> str:
    lines = [f"TY  - {first(rec, 'TY') or 'JOUR'}"]
    for tag, vals in rec.items():
        if tag == "TY":
            continue
        lines += [f"{tag}  - {v}" for v in vals]
    lines.append("ER  - ")
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("refs_dir", type=Path)
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--year-from", type=int, default=2020)
    a = ap.parse_args(argv)
    out = a.out or a.refs_dir / "merged"
    out.mkdir(parents=True, exist_ok=True)

    items = []  # (db, string, file, rec, keys)
    for db in DATABASES:
        base = a.refs_dir / db
        if not base.is_dir():
            continue
        for f in sorted(base.rglob("*.ris")):
            text = f.read_text(encoding="utf-8", errors="replace")
            s = string_of(f.relative_to(base))
            for rec in parse_ris(text):
                items.append((db, s, str(f.relative_to(a.refs_dir)), rec, record_keys(rec)))
    if not items:
        print("no .ris records found under", a.refs_dir, file=sys.stderr)
        return 1

    uf = UF(len(items))
    seen: dict[tuple[str, str], int] = {}
    for i, (_, _, _, _, k) in enumerate(items):
        for kind in ("doi", "pmid", "title"):
            v = k[kind]
            if kind == "title" and len(v) < 20:  # too short to be a safe key
                continue
            if v:
                j = seen.setdefault((kind, v), i)
                if j != i:
                    uf.union(i, j)
    groups: dict[int, list[int]] = defaultdict(list)
    for i in range(len(items)):
        groups[uf.find(i)].append(i)

    prev = {}
    scr = out / "screening.csv"
    if scr.exists():
        with scr.open(newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                for kind in ("doi", "pmid", "title_norm"):
                    if row.get(kind):
                        prev[(kind, row[kind])] = row

    rows, ris_out = [], []
    for g in sorted(groups.values(), key=lambda g: g[0]):
        best = max(g, key=lambda i: (bool(items[i][4]["doi"]), sum(len(v) for v in items[i][3].values())))
        db, s, f, rec, k = items[best]
        doi = next((items[i][4]["doi"] for i in g if items[i][4]["doi"]), "")
        pmid = next((items[i][4]["pmid"] for i in g if items[i][4]["pmid"]), "")
        year = next((items[i][4]["year"] for i in g if items[i][4]["year"]), "")
        key = f"doi:{doi}" if doi else (f"pmid:{pmid}" if pmid else f"title:{k['title'][:60]}")
        row = {
            "key": key,
            "title": first(rec, "TI", "T1", "CT"),
            "year": year,
            "journal": first(rec, "JO", "T2", "JF", "J2", "BT"),
            "doi": doi,
            "pmid": pmid,
            "title_norm": k["title"],
            "databases": ";".join(sorted({items[i][0] for i in g})),
            "strings": ";".join(sorted({items[i][1] for i in g})),
            "n_records": len(g),
        }
        old = prev.get(("doi", doi)) or prev.get(("pmid", pmid)) or prev.get(("title_norm", k["title"])) or {}
        for c in SCREEN_COLS:
            row[c] = old.get(c, "")
        rows.append(row)
        ris_out.append(to_ris(rec))

    cols = ["key", "title", "year", "journal", "doi", "pmid", "databases", "strings", "n_records",
            *SCREEN_COLS, "title_norm"]
    with (out / "merged.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    (out / "merged.ris").write_text("\n\n".join(ris_out) + "\n", encoding="utf-8")

    # counts: records per (db, string), all years and from --year-from; works after de-dup.
    def yr_ok(y):
        return y.isdigit() and int(y) >= a.year_from

    counts = {"year_from": a.year_from, "records": {}, "works": {}}
    for db, s, _, _, k in items:
        c = counts["records"].setdefault(db, {}).setdefault(s, {"all": 0, "from_year": 0})
        c["all"] += 1
        c["from_year"] += yr_ok(k["year"])
    per_string = defaultdict(lambda: {"all": 0, "from_year": 0})
    for r in rows:
        for s in r["strings"].split(";"):
            per_string[s]["all"] += 1
            per_string[s]["from_year"] += yr_ok(r["year"])
    counts["works"] = {
        "total": len(rows),
        "total_from_year": sum(yr_ok(r["year"]) for r in rows),
        "records_total": len(items),
        "per_string_after_dedup": dict(sorted(per_string.items())),
    }
    (out / "counts.json").write_text(json.dumps(counts, indent=1), encoding="utf-8")

    print(f"{'database':<14}{'string':<7}{'records':>8}{'>=' + str(a.year_from):>8}")
    for db, d in counts["records"].items():
        for s, c in sorted(d.items()):
            print(f"{db:<14}{s:<7}{c['all']:>8}{c['from_year']:>8}")
    w_ = counts["works"]
    print(f"records read: {w_['records_total']}; distinct works: {w_['total']} "
          f"({w_['total_from_year']} from {a.year_from})")
    print("written:", out / "merged.csv", out / "merged.ris", out / "counts.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
