#!/usr/bin/env python3
"""
report_sast.py — Relatório SAST completo com análises estatísticas.

Lê todos os relatórios brutos gerados pelas 4 ferramentas SAST e produz:
  - reports/sast/report_detailed.csv   (1 linha por finding)
  - reports/sast/report_summary.csv    (totais por código analisado)
  - reports/sast/report_stats.csv      (estatísticas agregadas)
  - reports/sast/report.json           (estrutura hierárquica)
  - reports/sast/report.html           (relatório navegável com análises)

Uso: python3 scripts/report_sast.py
"""
from __future__ import annotations
import json, csv, re, sys, html, statistics
from pathlib import Path
from collections import defaultdict, Counter
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
SAST_DIR = ROOT / "reports" / "sast"

PATTERN = re.compile(
    r"^(?P<caso>caso\d+_[a-z]+)_(?P<ia>chatgpt|gemini|claude)_(?P<lang>python|java|javascript|typescript)$"
)

N_CASOS = 5
N_IAS = 3
N_LANGS = 4


# ============================================================================
# Parsers
# ============================================================================

def parse_bandit(path):
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return [{"_parse_error": f"Bandit parse error in {path.name}: {e}"}]
    findings = []
    for r in data.get("results", []):
        cwe_info = r.get("issue_cwe", {})
        findings.append({
            "tool": "bandit",
            "rule_id": r.get("test_id", ""),
            "rule_name": r.get("test_name", ""),
            "severity": (r.get("issue_severity") or "").upper(),
            "confidence": (r.get("issue_confidence") or "").upper(),
            "message": r.get("issue_text", ""),
            "file": r.get("filename", ""),
            "line": r.get("line_number", ""),
            "code_snippet": (r.get("code") or "").strip()[:300],
            "cwe": f"CWE-{cwe_info.get('id', '')}" if cwe_info.get("id") else "",
            "owasp": "",
            "more_info": r.get("more_info", ""),
        })
    return findings


def parse_semgrep(path):
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return [{"_parse_error": f"Semgrep parse error in {path.name}: {e}"}]
    findings = []
    for r in data.get("results", []):
        extra = r.get("extra", {})
        meta = extra.get("metadata", {})
        cwe = meta.get("cwe", [])
        if isinstance(cwe, list):
            cwe = "; ".join(cwe)
        owasp = meta.get("owasp", [])
        if isinstance(owasp, list):
            owasp = "; ".join(owasp)
        findings.append({
            "tool": "semgrep",
            "rule_id": r.get("check_id", ""),
            "rule_name": r.get("check_id", "").split(".")[-1] if r.get("check_id") else "",
            "severity": (extra.get("severity") or "").upper(),
            "confidence": (meta.get("confidence") or "").upper(),
            "message": extra.get("message", "").strip(),
            "file": r.get("path", ""),
            "line": r.get("start", {}).get("line", ""),
            "code_snippet": (extra.get("lines") or "").strip()[:300],
            "cwe": cwe,
            "owasp": owasp,
            "more_info": meta.get("source", "") or meta.get("shortlink", ""),
        })
    return findings


def parse_eslint(path):
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return [{"_parse_error": f"ESLint parse error in {path.name}: {e}"}]
    findings = []
    sev_map = {2: "ERROR", 1: "WARNING", 0: "INFO"}
    for file_entry in data:
        file_path = file_entry.get("filePath", "")
        for m in file_entry.get("messages", []):
            findings.append({
                "tool": "eslint",
                "rule_id": m.get("ruleId", "") or "",
                "rule_name": (m.get("ruleId", "") or "").split("/")[-1],
                "severity": sev_map.get(m.get("severity", 0), "INFO"),
                "confidence": "",
                "message": m.get("message", ""),
                "file": file_path,
                "line": m.get("line", ""),
                "code_snippet": "",
                "cwe": "",
                "owasp": "",
                "more_info": "",
            })
    return findings


def parse_spotbugs(path):
    try:
        root = ET.parse(path).getroot()
    except Exception as e:
        return [{"_parse_error": f"SpotBugs parse error in {path.name}: {e}"}]
    findings = []
    sev_map = {"1": "HIGH", "2": "MEDIUM", "3": "LOW"}
    for bi in root.iter("BugInstance"):
        bug_type = bi.get("type", "")
        priority = bi.get("priority", "3")
        category = bi.get("category", "")
        source_line = bi.find(".//SourceLine")
        file_name = source_line.get("sourcepath", "") if source_line is not None else ""
        start_line = source_line.get("start", "") if source_line is not None else ""
        short_msg = bi.find("ShortMessage")
        long_msg = bi.find("LongMessage")
        msg_text = ""
        if long_msg is not None and long_msg.text:
            msg_text = long_msg.text.strip()
        elif short_msg is not None and short_msg.text:
            msg_text = short_msg.text.strip()
        findings.append({
            "tool": "spotbugs",
            "rule_id": bug_type,
            "rule_name": bug_type,
            "severity": sev_map.get(priority, "LOW"),
            "confidence": "",
            "message": msg_text,
            "file": file_name,
            "line": start_line,
            "code_snippet": "",
            "cwe": f"CWE-{bi.get('cweid')}" if bi.get("cweid") else "",
            "owasp": "",
            "more_info": category,
        })
    return findings


TOOL_CONFIG = [
    ("bandit",   "*.json", parse_bandit),
    ("semgrep",  "*.json", parse_semgrep),
    ("eslint",   "*.json", parse_eslint),
    ("spotbugs", "*.xml",  parse_spotbugs),
]


def collect_all_findings():
    all_findings = []
    combos_analisados = set()
    for tool_name, glob, parser in TOOL_CONFIG:
        tool_dir = SAST_DIR / tool_name
        if not tool_dir.exists():
            continue
        for f in sorted(tool_dir.glob(glob)):
            stem = f.stem
            m = PATTERN.match(stem)
            if not m:
                continue
            combos_analisados.add((m["caso"], m["ia"], m["lang"]))
            findings = parser(f)
            for fd in findings:
                if "_parse_error" in fd:
                    print(f"  AVISO: {fd['_parse_error']}", file=sys.stderr)
                    continue
                fd["caso"] = m["caso"]
                fd["ia"] = m["ia"]
                fd["linguagem"] = m["lang"]
                all_findings.append(fd)
    return all_findings, combos_analisados


# ============================================================================
# Estatísticas
# ============================================================================

def stats_from(values):
    if not values:
        return {"count": 0, "sum": 0, "mean": 0.0, "median": 0.0,
                "stdev": 0.0, "min": 0, "max": 0, "zero_rate": 0.0}
    n = len(values)
    return {
        "count": n,
        "sum": sum(values),
        "mean": round(statistics.mean(values), 2),
        "median": round(statistics.median(values), 2),
        "stdev": round(statistics.stdev(values), 2) if n > 1 else 0.0,
        "min": min(values),
        "max": max(values),
        "zero_rate": round(100 * sum(1 for v in values if v == 0) / n, 1),
    }


def build_per_combo_totals(findings, all_combos):
    result = {}
    for combo in all_combos:
        result[combo] = {
            "total": 0, "by_severity": Counter(), "by_tool": Counter(),
            "by_cwe": Counter(), "by_rule": Counter(),
        }
    for f in findings:
        combo = (f["caso"], f["ia"], f["linguagem"])
        if combo not in result:
            result[combo] = {
                "total": 0, "by_severity": Counter(), "by_tool": Counter(),
                "by_cwe": Counter(), "by_rule": Counter(),
            }
        result[combo]["total"] += 1
        result[combo]["by_severity"][f["severity"]] += 1
        result[combo]["by_tool"][f["tool"]] += 1
        result[combo]["by_rule"][f["rule_id"]] += 1
        if f.get("cwe"):
            for c in str(f["cwe"]).split(";"):
                c = c.strip()
                if c.startswith("CWE-"):
                    result[combo]["by_cwe"][c.split(":")[0]] += 1
    return result


def aggregate_by_dimension(per_combo, dim):
    idx = {"caso": 0, "ia": 1, "linguagem": 2}[dim]
    grouped = defaultdict(list)
    for combo, data in per_combo.items():
        grouped[combo[idx]].append(data["total"])
    return {k: stats_from(v) for k, v in grouped.items()}


def aggregate_by_two(per_combo, dim1, dim2):
    idx_map = {"caso": 0, "ia": 1, "linguagem": 2}
    i1, i2 = idx_map[dim1], idx_map[dim2]
    grouped = defaultdict(list)
    for combo, data in per_combo.items():
        grouped[(combo[i1], combo[i2])].append(data["total"])
    return {k: stats_from(v) for k, v in grouped.items()}


def severity_aggregate(per_combo, dim):
    idx = {"caso": 0, "ia": 1, "linguagem": 2}[dim]
    gh, gm, gl = defaultdict(list), defaultdict(list), defaultdict(list)
    for combo, data in per_combo.items():
        key = combo[idx]
        sev = data["by_severity"]
        gh[key].append(sev.get("HIGH", 0) + sev.get("ERROR", 0))
        gm[key].append(sev.get("MEDIUM", 0) + sev.get("WARNING", 0))
        gl[key].append(sev.get("LOW", 0) + sev.get("INFO", 0))
    result = {}
    for key in set(list(gh.keys()) + list(gm.keys()) + list(gl.keys())):
        result[key] = {"high": stats_from(gh[key]), "medium": stats_from(gm[key]), "low": stats_from(gl[key])}
    return result


def cwe_by_dimension(findings, dim):
    result = defaultdict(Counter)
    for f in findings:
        if not f.get("cwe"):
            continue
        key = f[dim]
        for c in str(f["cwe"]).split(";"):
            c = c.strip()
            if c.startswith("CWE-"):
                result[key][c.split(":")[0]] += 1
    return result


# ============================================================================
# Conclusões automáticas
# ============================================================================

def gerar_conclusoes(per_combo, findings):
    conclusoes = []
    stats_by_ia = aggregate_by_dimension(per_combo, "ia")
    stats_by_lang = aggregate_by_dimension(per_combo, "linguagem")
    stats_by_caso = aggregate_by_dimension(per_combo, "caso")

    if stats_by_ia:
        ranked = sorted(stats_by_ia.items(), key=lambda x: x[1]["mean"])
        best, worst = ranked[0], ranked[-1]
        if best[0] != worst[0]:
            conclusoes.append({
                "tipo": "IA com menor média geral",
                "texto": f"Considerando todas as combinações analisadas, a IA '{best[0]}' apresentou a menor média de findings SAST por código ({best[1]['mean']}; mediana {best[1]['median']}, desvio padrão {best[1]['stdev']}). A IA com maior média foi '{worst[0]}' ({worst[1]['mean']} findings em média).",
                "nota": "Menos findings não necessariamente significa código mais seguro. Veja notas metodológicas."
            })

    if stats_by_lang:
        ranked = sorted(stats_by_lang.items(), key=lambda x: x[1]["mean"])
        conclusoes.append({
            "tipo": "Linguagem com menor média de findings",
            "texto": f"Por linguagem, '{ranked[0][0]}' teve a menor média ({ranked[0][1]['mean']} findings/código) e '{ranked[-1][0]}' a maior ({ranked[-1][1]['mean']} findings/código).",
            "nota": "Comparações entre linguagens são limitadas porque cada uma é analisada por ferramentas com cobertura diferente (Bandit ~67 regras, SpotBugs ~140, ESLint segurança 16, Semgrep 1000+). Mais regras tende a produzir mais findings, não necessariamente código pior."
        })

    if stats_by_caso:
        ranked = sorted(stats_by_caso.items(), key=lambda x: -x[1]["mean"])
        conclusoes.append({
            "tipo": "Caso de teste mais 'difícil'",
            "texto": f"O caso que produziu mais findings em média foi '{ranked[0][0]}' ({ranked[0][1]['mean']} achados por código). O caso com menos findings foi '{ranked[-1][0]}' ({ranked[-1][1]['mean']} achados).",
            "nota": "Casos diferentes têm superfícies de ataque diferentes — essa variação é esperada e indica que casos com mais ações sensíveis (upload, render HTML, etc.) tendem a gerar mais findings."
        })

    stats_ia_caso = aggregate_by_two(per_combo, "caso", "ia")
    casos = set(k[0] for k in stats_ia_caso.keys())
    for caso in sorted(casos):
        ia_in_caso = {k[1]: v for k, v in stats_ia_caso.items() if k[0] == caso}
        if len(ia_in_caso) >= 2:
            ranked = sorted(ia_in_caso.items(), key=lambda x: x[1]["mean"])
            conclusoes.append({
                "tipo": f"Melhor IA no {caso}",
                "texto": f"No '{caso}', a IA com menor média de findings foi '{ranked[0][0]}' ({ranked[0][1]['mean']} achados em {ranked[0][1]['count']} códigos analisados).",
                "nota": ""
            })

    cwe_per_ia = cwe_by_dimension(findings, "ia")
    for ia, cwes in cwe_per_ia.items():
        if cwes:
            top = cwes.most_common(3)
            top_str = ", ".join(f"{c} ({n} ocorrências)" for c, n in top)
            conclusoes.append({
                "tipo": f"Tipos de vulnerabilidade mais frequentes em '{ia}'",
                "texto": f"Para '{ia}', os CWEs mais frequentes foram: {top_str}.",
                "nota": ""
            })

    high_per_combo = []
    for combo, data in per_combo.items():
        h = data["by_severity"].get("HIGH", 0) + data["by_severity"].get("ERROR", 0)
        if h > 0:
            high_per_combo.append((combo, h))
    if high_per_combo:
        high_per_combo.sort(key=lambda x: -x[1])
        top_combo, top_high = high_per_combo[0]
        conclusoes.append({
            "tipo": "Combinação com mais findings High/Error",
            "texto": f"A combinação com mais findings de severidade HIGH/ERROR foi '{top_combo[0]} / {top_combo[1]} / {top_combo[2]}', com {top_high} achados nessa faixa.",
            "nota": ""
        })

    if stats_by_ia:
        zero_ranked = sorted(stats_by_ia.items(), key=lambda x: -x[1]["zero_rate"])
        if zero_ranked[0][1]["zero_rate"] > 0:
            ia_top, st = zero_ranked[0]
            conclusoes.append({
                "tipo": "Maior taxa de códigos sem findings",
                "texto": f"A IA '{ia_top}' teve a maior proporção de códigos sem qualquer finding SAST: {st['zero_rate']}% das combinações analisadas.",
                "nota": "Pode indicar tanto código mais seguro quanto código mais simples/abstrato que o SAST não consegue analisar profundamente."
            })

    return conclusoes


# ============================================================================
# Outputs CSV/JSON
# ============================================================================

DETAILED_FIELDS = [
    "caso", "ia", "linguagem", "tool", "severity", "confidence",
    "rule_id", "rule_name", "cwe", "owasp", "message",
    "file", "line", "code_snippet", "more_info"
]


def write_detailed_csv(findings, out):
    with out.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=DETAILED_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for f in sorted(findings, key=lambda x: (x["caso"], x["ia"], x["linguagem"], x["tool"], x["severity"])):
            writer.writerow(f)


def write_summary_csv(per_combo, out):
    all_tools, all_severities = set(), set()
    for data in per_combo.values():
        all_tools.update(data["by_tool"].keys())
        all_severities.update(data["by_severity"].keys())
    tools, severities = sorted(all_tools), sorted(all_severities)
    fields = ["caso", "ia", "linguagem", "total"] + [f"sev_{s}" for s in severities] + [f"tool_{t}" for t in tools]
    with out.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields)
        writer.writeheader()
        for combo, data in sorted(per_combo.items()):
            row = {"caso": combo[0], "ia": combo[1], "linguagem": combo[2], "total": data["total"]}
            for s in severities: row[f"sev_{s}"] = data["by_severity"].get(s, 0)
            for t in tools: row[f"tool_{t}"] = data["by_tool"].get(t, 0)
            writer.writerow(row)


def write_stats_csv(per_combo, out):
    rows = []
    for dim in ["ia", "linguagem", "caso"]:
        for key, st in aggregate_by_dimension(per_combo, dim).items():
            rows.append({"dimensao": dim, "valor": key, **st})
    for d1, d2 in [("ia", "linguagem"), ("ia", "caso"), ("linguagem", "caso")]:
        for (k1, k2), st in aggregate_by_two(per_combo, d1, d2).items():
            rows.append({"dimensao": f"{d1}_x_{d2}", "valor": f"{k1} × {k2}", **st})
    fields = ["dimensao", "valor", "count", "sum", "mean", "median", "stdev", "min", "max", "zero_rate"]
    with out.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(findings, out):
    structure = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for f in findings:
        structure[f["caso"]][f["ia"]][f["linguagem"]].append(
            {k: v for k, v in f.items() if k not in ("caso", "ia", "linguagem")}
        )
    out.write_text(json.dumps(structure, indent=2, ensure_ascii=False))


# ============================================================================
# HTML
# ============================================================================

CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       margin: 0; padding: 0; background: #f5f5f7; color: #1d1d1f; line-height: 1.5; }
header { background: linear-gradient(135deg, #1d1d1f 0%, #2c3e50 100%);
         color: white; padding: 28px 32px; }
header h1 { margin: 0; font-size: 26px; }
header p { margin: 8px 0 0; opacity: 0.85; font-size: 14px; }
nav.toc { background: white; padding: 16px 24px; border-bottom: 1px solid #e5e5e7;
          position: sticky; top: 0; z-index: 10; }
nav.toc a { display: inline-block; margin-right: 16px; color: #1565c0;
            text-decoration: none; font-size: 13px; }
nav.toc a:hover { text-decoration: underline; }
main { max-width: 1500px; margin: 0 auto; padding: 24px 32px; }
section { background: white; border-radius: 8px; padding: 24px 28px;
          margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
          scroll-margin-top: 60px; }
h2 { margin: 0 0 16px; font-size: 20px; border-bottom: 2px solid #e5e5e7;
     padding-bottom: 10px; }
h3 { margin: 20px 0 10px; font-size: 16px; color: #2c3e50; }
table { width: 100%; border-collapse: collapse; font-size: 13px; margin: 8px 0; }
th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #e5e5e7;
         vertical-align: top; }
th { background: #f5f5f7; font-weight: 600; }
tr:hover { background: #fafafa; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
              gap: 12px; margin-bottom: 16px; }
.stat-card { background: #f5f5f7; padding: 14px; border-radius: 6px; }
.stat-card .label { font-size: 11px; text-transform: uppercase; color: #666;
                    letter-spacing: 0.5px; }
.stat-card .value { font-size: 24px; font-weight: 600; margin-top: 4px; }
.sev-high, .sev-error { color: #d32f2f; font-weight: 600; }
.sev-medium, .sev-warning { color: #f57c00; font-weight: 600; }
.sev-low, .sev-info { color: #1976d2; font-weight: 600; }
.conclusao { background: #fffde7; border-left: 4px solid #fbc02d;
             padding: 14px 18px; margin: 12px 0; border-radius: 4px; }
.conclusao .titulo { font-weight: 600; font-size: 13px; color: #5d4037;
                     margin-bottom: 4px; text-transform: uppercase;
                     letter-spacing: 0.5px; }
.conclusao .texto { font-size: 14px; }
.conclusao .nota { font-size: 12px; color: #888; margin-top: 8px; font-style: italic; }
.warning-box { background: #fff3e0; border-left: 4px solid #ff9800;
               padding: 14px 18px; margin: 12px 0; border-radius: 4px; font-size: 13px; }
.method-box { background: #e3f2fd; border-left: 4px solid #1976d2;
              padding: 14px 18px; margin: 12px 0; border-radius: 4px; font-size: 13px; }
.badge { display: inline-block; padding: 2px 8px; border-radius: 10px;
         font-size: 11px; font-weight: 600; }
.badge-tool { background: #e3f2fd; color: #1565c0; }
.badge-cwe { background: #fce4ec; color: #c2185b; }
.code { font-family: "SF Mono", Menlo, Consolas, monospace; font-size: 11px;
        background: #f5f5f7; padding: 4px 6px; border-radius: 3px;
        white-space: pre-wrap; word-break: break-all; max-width: 380px; }
details { margin: 8px 0; }
details summary { cursor: pointer; padding: 10px 12px; background: #f5f5f7;
                  border-radius: 4px; font-weight: 600; }
details[open] summary { margin-bottom: 8px; }
.heatmap td { text-align: center; }
.heatmap .h0 { background: #f5f5f7; color: #666; }
.heatmap .h1 { background: #fff3e0; }
.heatmap .h2 { background: #ffe0b2; }
.heatmap .h3 { background: #ffcc80; }
.heatmap .h4 { background: #ffb74d; color: white; }
.heatmap .h5 { background: #ff9800; color: white; }
.heatmap .h6 { background: #f57c00; color: white; }
.rank-1 { background: #e8f5e9; }
.rank-2 { background: #fff8e1; }
.rank-3 { background: #ffebee; }
.empty { color: #999; font-style: italic; padding: 20px; text-align: center; }
"""


def heatmap_class(value, max_val):
    if max_val == 0 or value == 0:
        return "h0"
    ratio = value / max_val
    if ratio < 0.17: return "h1"
    if ratio < 0.34: return "h2"
    if ratio < 0.51: return "h3"
    if ratio < 0.68: return "h4"
    if ratio < 0.85: return "h5"
    return "h6"


def write_html(findings, per_combo, combos_analisados, out):
    def esc(s):
        return html.escape(str(s)) if s is not None else ""

    total_findings = len(findings)
    total_combos = len(combos_analisados)
    total_possible = N_CASOS * N_IAS * N_LANGS

    by_severity = Counter(f["severity"] for f in findings)
    by_ia = Counter(f["ia"] for f in findings)
    by_lang = Counter(f["linguagem"] for f in findings)

    stats_ia = aggregate_by_dimension(per_combo, "ia")
    stats_lang = aggregate_by_dimension(per_combo, "linguagem")
    stats_caso = aggregate_by_dimension(per_combo, "caso")
    stats_ia_lang = aggregate_by_two(per_combo, "ia", "linguagem")
    stats_ia_caso = aggregate_by_two(per_combo, "ia", "caso")
    stats_lang_caso = aggregate_by_two(per_combo, "linguagem", "caso")

    sev_by_ia = severity_aggregate(per_combo, "ia")
    sev_by_lang = severity_aggregate(per_combo, "linguagem")
    sev_by_caso = severity_aggregate(per_combo, "caso")

    cwe_per_ia = cwe_by_dimension(findings, "ia")
    cwe_per_lang = cwe_by_dimension(findings, "linguagem")
    cwe_per_caso = cwe_by_dimension(findings, "caso")

    conclusoes = gerar_conclusoes(per_combo, findings)

    p = []
    p.append(f"""<!DOCTYPE html>
<html lang="pt-br"><head><meta charset="UTF-8">
<title>Relatório SAST Completo — Comparativo LLMs</title>
<style>{CSS}</style></head><body>
<header>
  <h1>Relatório SAST Completo</h1>
  <p>Análise estatística e comparativa de vulnerabilidades em código gerado por LLMs</p>
  <p>{total_findings} findings totais · {total_combos}/{total_possible} combinações analisadas</p>
</header>
<nav class="toc">
  <a href="#visao-geral">1. Visão geral</a>
  <a href="#conclusoes">2. Conclusões</a>
  <a href="#stats-ia">3. Por IA</a>
  <a href="#stats-lang">4. Por linguagem</a>
  <a href="#stats-caso">5. Por caso</a>
  <a href="#cruzamentos">6. Cruzamentos</a>
  <a href="#severidades">7. Severidades</a>
  <a href="#cwes">8. CWEs</a>
  <a href="#detalhamento">9. Detalhamento</a>
  <a href="#notas">10. Notas metodológicas</a>
</nav>
<main>""")

    # 1. VISÃO GERAL
    p.append('<section id="visao-geral"><h2>1. Visão geral</h2><div class="stats-grid">')
    p.append(f'<div class="stat-card"><div class="label">Total findings</div><div class="value">{total_findings}</div></div>')
    p.append(f'<div class="stat-card"><div class="label">Combinações</div><div class="value">{total_combos}/{total_possible}</div></div>')
    for sev in ["HIGH", "ERROR", "MEDIUM", "WARNING", "LOW", "INFO"]:
        n = by_severity.get(sev, 0)
        if n:
            p.append(f'<div class="stat-card"><div class="label">{sev}</div><div class="value sev-{sev.lower()}">{n}</div></div>')
    p.append("</div>")
    p.append('<div class="method-box"><strong>Sobre este relatório:</strong> os números são contagens de findings (cada ocorrência reportada pelas ferramentas SAST). Veja "Notas metodológicas" ao final para interpretar corretamente.</div>')
    p.append("</section>")

    # 2. CONCLUSÕES
    p.append('<section id="conclusoes"><h2>2. Conclusões automáticas</h2>')
    p.append('<p style="font-size:13px;color:#666">Observações geradas automaticamente dos dados. Use com critério.</p>')
    if conclusoes:
        for c in conclusoes:
            p.append('<div class="conclusao">')
            p.append(f'<div class="titulo">{esc(c["tipo"])}</div>')
            p.append(f'<div class="texto">{esc(c["texto"])}</div>')
            if c.get("nota"):
                p.append(f'<div class="nota">⚠ {esc(c["nota"])}</div>')
            p.append('</div>')
    else:
        p.append('<div class="empty">Sem dados suficientes para conclusões.</div>')
    p.append("</section>")

    # 3. POR IA
    p.append('<section id="stats-ia"><h2>3. Estatísticas por IA</h2>')
    p.append('<p style="font-size:13px;color:#666">Cada linha agrega todas as combinações de caso × linguagem para essa IA.</p>')
    p.append('<table><thead><tr><th>IA</th><th class="num">Códigos</th><th class="num">Total</th><th class="num">Média</th><th class="num">Mediana</th><th class="num">Desvio</th><th class="num">Mín</th><th class="num">Máx</th><th class="num">% sem findings</th></tr></thead><tbody>')
    for i, (ia, st) in enumerate(sorted(stats_ia.items(), key=lambda x: x[1]["mean"])):
        rank_cls = f"rank-{i+1}" if i < 3 else ""
        p.append(f'<tr class="{rank_cls}"><td><strong>{esc(ia)}</strong></td><td class="num">{st["count"]}</td><td class="num">{st["sum"]}</td><td class="num">{st["mean"]}</td><td class="num">{st["median"]}</td><td class="num">{st["stdev"]}</td><td class="num">{st["min"]}</td><td class="num">{st["max"]}</td><td class="num">{st["zero_rate"]}%</td></tr>')
    p.append('</tbody></table><p style="font-size:12px;color:#888">Verde = menos findings (top 1), amarelo = posição 2, vermelho = mais findings (posição 3).</p></section>')

    # 4. POR LINGUAGEM
    p.append('<section id="stats-lang"><h2>4. Estatísticas por linguagem</h2>')
    p.append('<div class="warning-box">⚠ <strong>Aviso metodológico:</strong> linguagens diferentes têm ferramentas com cobertura diferente (Bandit ~67 regras, SpotBugs ~140, ESLint segurança 16, Semgrep 1000+). Não compare linguagens diretamente sem contextualizar.</div>')
    p.append('<table><thead><tr><th>Linguagem</th><th class="num">Códigos</th><th class="num">Total</th><th class="num">Média</th><th class="num">Mediana</th><th class="num">Desvio</th><th class="num">Mín</th><th class="num">Máx</th><th class="num">% sem findings</th></tr></thead><tbody>')
    for i, (lang, st) in enumerate(sorted(stats_lang.items(), key=lambda x: x[1]["mean"])):
        rank_cls = f"rank-{i+1}" if i < 3 else ""
        p.append(f'<tr class="{rank_cls}"><td><strong>{esc(lang)}</strong></td><td class="num">{st["count"]}</td><td class="num">{st["sum"]}</td><td class="num">{st["mean"]}</td><td class="num">{st["median"]}</td><td class="num">{st["stdev"]}</td><td class="num">{st["min"]}</td><td class="num">{st["max"]}</td><td class="num">{st["zero_rate"]}%</td></tr>')
    p.append('</tbody></table></section>')

    # 5. POR CASO
    p.append('<section id="stats-caso"><h2>5. Estatísticas por caso</h2>')
    p.append('<p style="font-size:13px;color:#666">Diferenças entre casos refletem complexidade e superfície de ataque distintas.</p>')
    p.append('<table><thead><tr><th>Caso</th><th class="num">Códigos</th><th class="num">Total</th><th class="num">Média</th><th class="num">Mediana</th><th class="num">Desvio</th><th class="num">Mín</th><th class="num">Máx</th><th class="num">% sem findings</th></tr></thead><tbody>')
    for caso, st in sorted(stats_caso.items(), key=lambda x: -x[1]["mean"]):
        p.append(f'<tr><td><strong>{esc(caso)}</strong></td><td class="num">{st["count"]}</td><td class="num">{st["sum"]}</td><td class="num">{st["mean"]}</td><td class="num">{st["median"]}</td><td class="num">{st["stdev"]}</td><td class="num">{st["min"]}</td><td class="num">{st["max"]}</td><td class="num">{st["zero_rate"]}%</td></tr>')
    p.append('</tbody></table></section>')

    # 6. CRUZAMENTOS (heatmaps)
    p.append('<section id="cruzamentos"><h2>6. Cruzamentos multidimensionais</h2>')

    def render_heatmap(title, matrix_data, row_label, col_label, row_means_dict):
        p.append(f'<h3>{title}</h3>')
        if not matrix_data:
            p.append('<div class="empty">Sem dados.</div>')
            return
        rows_set = sorted(set(k[0] for k in matrix_data.keys()))
        cols_set = sorted(set(k[1] for k in matrix_data.keys()))
        max_val = max((v["mean"] for v in matrix_data.values()), default=0)
        p.append(f'<table class="heatmap"><thead><tr><th>{row_label} \\ {col_label}</th>')
        for col in cols_set:
            p.append(f'<th>{esc(col)}</th>')
        p.append('<th>Média geral</th></tr></thead><tbody>')
        for row in rows_set:
            p.append(f'<tr><td><strong>{esc(row)}</strong></td>')
            for col in cols_set:
                st = matrix_data.get((row, col))
                if st:
                    cls = heatmap_class(st["mean"], max_val)
                    p.append(f'<td class="{cls}">{st["mean"]}<br><small>(n={st["count"]})</small></td>')
                else:
                    p.append('<td class="h0">—</td>')
            row_mean = row_means_dict.get(row, {}).get("mean", 0)
            p.append(f'<td><strong>{row_mean}</strong></td></tr>')
        p.append('</tbody></table>')

    render_heatmap("6.1 IA × Linguagem — média de findings por código", stats_ia_lang, "IA", "Linguagem", stats_ia)
    render_heatmap("6.2 IA × Caso — média de findings por código", stats_ia_caso, "IA", "Caso", stats_ia)
    render_heatmap("6.3 Linguagem × Caso — média de findings por código", stats_lang_caso, "Linguagem", "Caso", stats_lang)

    p.append('<p style="font-size:12px;color:#888;margin-top:8px">Cor: branco = 0, laranja claro = poucos, vermelho-escuro = muitos. n = códigos analisados.</p>')
    p.append("</section>")

    # 7. SEVERIDADES
    p.append('<section id="severidades"><h2>7. Análise por severidade</h2>')
    for titulo, dim_data in [("7.1 Severidade por IA", sev_by_ia),
                              ("7.2 Severidade por linguagem", sev_by_lang),
                              ("7.3 Severidade por caso", sev_by_caso)]:
        p.append(f'<h3>{titulo}</h3>')
        p.append('<table><thead><tr><th>Categoria</th><th class="num">HIGH/ERROR (média / total)</th><th class="num">MEDIUM/WARNING (média / total)</th><th class="num">LOW/INFO (média / total)</th></tr></thead><tbody>')
        for k, sevs in sorted(dim_data.items()):
            p.append(f'<tr><td><strong>{esc(k)}</strong></td><td class="num sev-high">{sevs["high"]["mean"]} / {sevs["high"]["sum"]}</td><td class="num sev-medium">{sevs["medium"]["mean"]} / {sevs["medium"]["sum"]}</td><td class="num sev-low">{sevs["low"]["mean"]} / {sevs["low"]["sum"]}</td></tr>')
        p.append('</tbody></table>')
    p.append("</section>")

    # 8. CWEs
    p.append('<section id="cwes"><h2>8. Análise por tipo de erro (CWE)</h2>')
    p.append('<p style="font-size:13px;color:#666">Common Weakness Enumeration — categorias padronizadas de vulnerabilidades.</p>')
    for titulo, dim_data in [("8.1 Top CWEs por IA", cwe_per_ia),
                              ("8.2 Top CWEs por linguagem", cwe_per_lang),
                              ("8.3 Top CWEs por caso", cwe_per_caso)]:
        p.append(f'<h3>{titulo}</h3>')
        p.append('<table><thead><tr><th>Categoria</th><th>Top 5 CWEs</th></tr></thead><tbody>')
        for k, cwes in sorted(dim_data.items()):
            top5 = cwes.most_common(5)
            top_str = " · ".join(f'<span class="badge badge-cwe">{esc(cwe)}</span> {n}' for cwe, n in top5) or "—"
            p.append(f'<tr><td><strong>{esc(k)}</strong></td><td>{top_str}</td></tr>')
        p.append('</tbody></table>')
    p.append("</section>")

    # 9. DETALHAMENTO
    p.append('<section id="detalhamento"><h2>9. Detalhamento por combinação</h2>')
    p.append('<p style="font-size:13px;color:#666">Clique para ver todos os findings detectados em cada combinação.</p>')
    by_combo = defaultdict(list)
    for f in findings:
        by_combo[(f["caso"], f["ia"], f["linguagem"])].append(f)
    for combo in sorted(combos_analisados):
        caso, ia, lang = combo
        fs = by_combo.get(combo, [])
        sev_counts = Counter(f["severity"] for f in fs)
        sev_summary = ", ".join(f"{s}: {n}" for s, n in sev_counts.most_common()) or "sem findings"
        p.append('<details>')
        p.append(f'<summary>{esc(caso)} → {esc(ia)} / {esc(lang)} — <strong>{len(fs)} findings</strong> ({sev_summary})</summary>')
        if fs:
            p.append('<table><thead><tr><th>Ferramenta</th><th>Severidade</th><th>Regra</th><th>Arquivo:Linha</th><th>Mensagem</th><th>CWE</th><th>Código</th></tr></thead><tbody>')
            for f in sorted(fs, key=lambda x: (x["tool"], x["severity"], str(x["line"]))):
                sev_class = f"sev-{f['severity'].lower()}" if f["severity"] else ""
                file_name = Path(str(f["file"])).name if f["file"] else ""
                code_html = f'<div class="code">{esc(f["code_snippet"])}</div>' if f.get("code_snippet") else ""
                p.append(
                    f'<tr><td><span class="badge badge-tool">{esc(f["tool"])}</span></td>'
                    f'<td class="{sev_class}">{esc(f["severity"])}</td>'
                    f'<td><code>{esc(f["rule_id"])}</code></td>'
                    f'<td>{esc(file_name)}:{esc(f["line"])}</td>'
                    f'<td>{esc(f["message"][:300])}</td>'
                    f'<td>{esc(f.get("cwe", ""))}</td>'
                    f'<td>{code_html}</td></tr>'
                )
            p.append('</tbody></table>')
        else:
            p.append('<div class="empty">Sem findings reportados nesta combinação.</div>')
        p.append('</details>')
    p.append('</section>')

    # 10. NOTAS METODOLÓGICAS
    p.append('<section id="notas"><h2>10. Notas metodológicas</h2>')
    p.append("""<div class="method-box">
<h3 style="margin-top:0">Como interpretar este relatório</h3>
<p><strong>1. Menor número de findings ≠ código mais seguro.</strong>
Pode significar: (a) código realmente mais seguro, (b) menos código (cobertura
funcional menor), (c) padrões não detectados por análise estática, (d) uso de
abstrações que escondem vulnerabilidades.</p>

<p><strong>2. Comparações entre linguagens são limitadas.</strong>
Bandit tem ~67 regras para Python; SpotBugs com find-sec-bugs tem ~140
detectores para Java; ESLint com plugins de segurança tem 16 regras explícitas;
Semgrep tem 1000+. Mais regras tende a produzir mais findings, não código pior.</p>

<p><strong>3. Comparações entre IAs dentro da mesma linguagem são mais válidas.</strong>
Como a mesma ferramenta analisa todos os códigos da mesma linguagem, comparar
ChatGPT × Gemini × Claude em Python (por ex) é metodologicamente sólido. Esta
é a comparação principal do relatório.</p>

<p><strong>4. Tamanho da amostra é pequeno.</strong>
São 20 amostras por IA (5 casos × 4 linguagens). Diferenças menores que 1–2
findings na média podem ser ruído. Desvios padrão altos indicam comportamento
inconsistente da IA.</p>

<p><strong>5. Severidade é definida pela ferramenta, não pelo impacto real.</strong>
Um HIGH do Bandit pode ser menos sério na prática que um MEDIUM do Semgrep,
dependendo do contexto. Use o CWE para entender a natureza da vulnerabilidade.</p>

<p><strong>6. DAST complementa SAST.</strong>
Este relatório cobre apenas análise estática. Vulnerabilidades dinâmicas
(configuração, runtime, autenticação) requerem o relatório DAST e o
relatório combinado.</p>
</div>""")
    p.append("""<h3>Glossário</h3>
<table>
<tr><th>Termo</th><th>Significado</th></tr>
<tr><td>Finding</td><td>Uma ocorrência reportada por uma ferramenta SAST. Pode ser vulnerabilidade real ou falso positivo.</td></tr>
<tr><td>CWE</td><td>Common Weakness Enumeration — categoria padronizada (ex: CWE-89 = SQL Injection).</td></tr>
<tr><td>Severidade</td><td>Classificação da ferramenta (HIGH/MEDIUM/LOW). Cada ferramenta usa critérios próprios.</td></tr>
<tr><td>Média</td><td>Total de findings ÷ nº de códigos analisados.</td></tr>
<tr><td>Desvio padrão</td><td>Mede consistência. Baixo = estável; alto = variável entre códigos.</td></tr>
<tr><td>Taxa de zero findings</td><td>% de códigos sem nenhum finding.</td></tr>
</table>""")
    p.append('</section></main></body></html>')

    out.write_text("\n".join(p), encoding="utf-8")


# ============================================================================
# Main
# ============================================================================

def main():
    if not SAST_DIR.exists():
        print(f"Diretório não existe: {SAST_DIR}")
        sys.exit(0)

    print("Coletando findings dos relatórios SAST...")
    findings, combos_analisados = collect_all_findings()
    print(f"  Total: {len(findings)} findings em {len(combos_analisados)} combinações")

    print("Calculando estatísticas...")
    per_combo = build_per_combo_totals(findings, combos_analisados)

    detailed_csv = SAST_DIR / "report_detailed.csv"
    summary_csv  = SAST_DIR / "report_summary.csv"
    stats_csv    = SAST_DIR / "report_stats.csv"
    json_out     = SAST_DIR / "report.json"
    html_out     = SAST_DIR / "report.html"

    print(f"Gerando {detailed_csv.name}...")
    write_detailed_csv(findings, detailed_csv)
    print(f"Gerando {summary_csv.name}...")
    write_summary_csv(per_combo, summary_csv)
    print(f"Gerando {stats_csv.name}...")
    write_stats_csv(per_combo, stats_csv)
    print(f"Gerando {json_out.name}...")
    write_json(findings, json_out)
    print(f"Gerando {html_out.name}...")
    write_html(findings, per_combo, combos_analisados, html_out)

    print()
    print("Relatórios gerados:")
    print(f"  {detailed_csv}")
    print(f"  {summary_csv}")
    print(f"  {stats_csv}")
    print(f"  {json_out}")
    print(f"  {html_out}")
    print()
    print(f"Para abrir: xdg-open {html_out}")


if __name__ == "__main__":
    main()