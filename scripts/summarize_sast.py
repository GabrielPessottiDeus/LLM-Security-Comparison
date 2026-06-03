"""
summarize_sast.py

Agrega todos os relatórios JSON gerados pelos SAST (Bandit, Semgrep, ESLint,
SpotBugs XML) numa tabela comparativa CSV + Markdown.

Saída:
  reports/sast/summary.csv
  reports/sast/summary.md

Uso: python3 scripts/summarize_sast.py
"""
from __future__ import annotations
import json
import csv
import re
import os
import sys
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SAST_DIR = ROOT / "reports" / "sast"


def parse_bandit(path: Path) -> dict:
    """Bandit JSON: results[] com 'issue_severity' (LOW/MEDIUM/HIGH)."""
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return {"erro": str(e), "total": 0, "high": 0, "medium": 0, "low": 0}
    sev = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    for r in data.get("results", []):
        s = (r.get("issue_severity") or "").upper()
        if s in sev:
            sev[s] += 1
    return {
        "total":  sum(sev.values()),
        "high":   sev["HIGH"],
        "medium": sev["MEDIUM"],
        "low":    sev["LOW"],
    }

def parse_semgrep(path: Path) -> dict:
    """Semgrep JSON: results[] com extra.severity (ERROR/WARNING/INFO)."""
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return {"erro": str(e), "total": 0, "high": 0, "medium": 0, "low": 0}
    sev = {"ERROR": 0, "WARNING": 0, "INFO": 0}
    for r in data.get("results", []):
        s = (r.get("extra", {}).get("severity") or "").upper()
        if s in sev:
            sev[s] += 1
    return {
        "total":  sum(sev.values()),
        "high":   sev["ERROR"],
        "medium": sev["WARNING"],
        "low":    sev["INFO"],
    }

def parse_eslint(path: Path) -> dict:
    """ESLint JSON: array de arquivos, cada um com messages[] com severity (1=warn, 2=error)."""
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return {"erro": str(e), "total": 0, "high": 0, "medium": 0, "low": 0}
    errors = warns = 0
    for f in data:
        for m in f.get("messages", []):
            if m.get("severity") == 2:
                errors += 1
            elif m.get("severity") == 1:
                warns += 1
    return {
        "total":  errors + warns,
        "high":   errors,
        "medium": warns,
        "low":    0,
    }

def parse_spotbugs(path: Path) -> dict:
    """SpotBugs XML: BugInstance com atributo 'priority' (1=high, 2=medium, 3=low)."""
    try:
        root = ET.parse(path).getroot()
    except Exception as e:
        return {"erro": str(e), "total": 0, "high": 0, "medium": 0, "low": 0}
    sev = {"1": 0, "2": 0, "3": 0}
    for bi in root.iter("BugInstance"):
        p = bi.get("priority", "3")
        if p in sev:
            sev[p] += 1
    return {
        "total":  sum(sev.values()),
        "high":   sev["1"],
        "medium": sev["2"],
        "low":    sev["3"],
    }


TOOL_CONFIG = [
    ("bandit",   "*.json", parse_bandit),
    ("semgrep",  "*.json", parse_semgrep),
    ("eslint",   "*.json", parse_eslint),
    ("spotbugs", "*.xml",  parse_spotbugs),
]

PATTERN = re.compile(r"^(?P<caso>caso\d+_[a-z]+)_(?P<ia>chatgpt|gemini|claude)_(?P<lang>python|java|javascript|typescript)$")

def collect() -> list[dict]:
    rows = []
    for tool, glob, parser in TOOL_CONFIG:
        tool_dir = SAST_DIR / tool
        if not tool_dir.exists():
            continue
        for f in sorted(tool_dir.glob(glob)):
            stem = f.stem
            m = PATTERN.match(stem)
            if not m:
                continue
            stats = parser(f)
            rows.append({
                "caso": m["caso"],
                "ia": m["ia"],
                "linguagem": m["lang"],
                "ferramenta": tool,
                "total": stats.get("total", 0),
                "high": stats.get("high", 0),
                "medium": stats.get("medium", 0),
                "low": stats.get("low", 0),
                "arquivo": str(f.relative_to(ROOT)),
            })
    return rows


def write_csv(rows, out: Path):
    if not rows:
        out.write_text("(sem dados)\n")
        return
    with out.open("w", newline="") as fp:
        w = csv.DictWriter(fp, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

def write_md(rows, out: Path):
    if not rows:
        out.write_text("(sem dados)\n")
        return
    lines = [
        "# Resumo SAST",
        "",
        "| Caso | IA | Linguagem | Ferramenta | Total | High | Medium | Low |",
        "|------|-----|-----------|------------|-------|------|--------|-----|",
    ]
    rows_sorted = sorted(rows, key=lambda r: (r["caso"], r["ia"], r["linguagem"], r["ferramenta"]))
    for r in rows_sorted:
        lines.append(
            f"| {r['caso']} | {r['ia']} | {r['linguagem']} | {r['ferramenta']} | "
            f"{r['total']} | {r['high']} | {r['medium']} | {r['low']} |"
        )

    from collections import defaultdict
    agg = defaultdict(lambda: {"total": 0, "high": 0, "medium": 0, "low": 0})
    for r in rows:
        key = (r["caso"], r["ia"], r["linguagem"])
        for k in ("total", "high", "medium", "low"):
            agg[key][k] += r[k]

    lines += [
        "",
        "## Agregado (somando todas as ferramentas)",
        "",
        "| Caso | IA | Linguagem | Total | High | Medium | Low |",
        "|------|-----|-----------|-------|------|--------|-----|",
    ]
    for (caso, ia, lang), v in sorted(agg.items()):
        lines.append(
            f"| {caso} | {ia} | {lang} | {v['total']} | {v['high']} | {v['medium']} | {v['low']} |"
        )
    out.write_text("\n".join(lines) + "\n")

def main():
    if not SAST_DIR.exists():
        print(f"Diretório não existe ainda: {SAST_DIR}")
        sys.exit(0)
    rows = collect()
    csv_out = SAST_DIR / "summary.csv"
    md_out  = SAST_DIR / "summary.md"
    write_csv(rows, csv_out)
    write_md(rows, md_out)
    print(f"OK. {len(rows)} relatórios processados.")
    print(f"  {csv_out}")
    print(f"  {md_out}")

if __name__ == "__main__":
    main()
