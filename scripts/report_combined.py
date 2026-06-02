#!/usr/bin/env python3
"""
report_combined.py — Relatório unificado SAST + DAST.

Cruza os achados das análises estática (SAST: Bandit/Semgrep/ESLint/SpotBugs)
e dinâmica (DAST: OWASP ZAP) numa visão única para análise comparativa.

Pré-requisitos:
  Antes de rodar este script, gere os relatórios de cada modalidade:
    python3 scripts/report_sast.py
    python3 scripts/report_dast.py

Saídas:
  reports/combined/report.html         — relatório interativo unificado
  reports/combined/report.csv          — visão matricial (caso/ia/linguagem × métricas)
  reports/combined/report.json         — estrutura hierárquica completa
  reports/combined/cwe_overlap.csv     — CWEs em comum entre SAST e DAST

Uso: python3 scripts/report_combined.py
"""
from __future__ import annotations
import json
import csv
import sys
import html
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parent.parent
SAST_REPORT  = ROOT / "reports" / "sast" / "report.json"
DAST_REPORT  = ROOT / "reports" / "dast" / "report.json"
OUT_DIR      = ROOT / "reports" / "combined"

# ============================================================================
# Modelo de dados
# ============================================================================
# Para cada (caso, ia, linguagem) construímos um "registro unificado" com:
#   - sast: { tools: {bandit, semgrep, eslint, spotbugs}, sev_counts, findings[] }
#   - dast: { scans: {baseline, full}, risk_counts, alerts[] }
#   - cross: { cwes_sast, cwes_dast, cwes_comuns }

def normalize_severity(sev_raw: str, source: str) -> str:
    """Normaliza severidades de fontes diferentes para uma escala única."""
    s = (sev_raw or "").upper()
    # SAST
    if s in ("HIGH", "ERROR"):  return "HIGH"
    if s in ("MEDIUM", "WARNING"):  return "MEDIUM"
    if s in ("LOW", "INFO", "INFORMATIONAL"):
        return "LOW" if source == "sast" else "INFORMATIONAL" if s == "INFORMATIONAL" else "LOW"
    return "UNKNOWN"

def extract_cwes(value) -> set[str]:
    """Aceita string ou lista, devolve set de CWE-XXX."""
    out = set()
    if not value:
        return out
    if isinstance(value, list):
        items = value
    else:
        items = str(value).split(";")
    for it in items:
        it = str(it).strip()
        if not it:
            continue
        # Pode vir como "CWE-89" ou "CWE-89: SQL Injection"
        if it.upper().startswith("CWE-"):
            cwe_id = it.split(":")[0].strip().upper()
        elif it.isdigit():
            cwe_id = f"CWE-{it}"
        else:
            continue
        out.add(cwe_id)
    return out


def load_sast() -> dict:
    """Lê reports/sast/report.json gerado pelo report_sast.py."""
    if not SAST_REPORT.exists():
        print(f"AVISO: {SAST_REPORT} não existe. Rode antes: python3 scripts/report_sast.py", file=sys.stderr)
        return {}
    return json.loads(SAST_REPORT.read_text())


def load_dast() -> dict:
    """Lê reports/dast/report.json gerado pelo report_dast.py."""
    if not DAST_REPORT.exists():
        print(f"AVISO: {DAST_REPORT} não existe. Rode antes: python3 scripts/report_dast.py", file=sys.stderr)
        return {}
    return json.loads(DAST_REPORT.read_text())


def build_unified(sast_data: dict, dast_data: dict) -> dict:
    """Constroi { caso: { ia: { linguagem: {sast:..., dast:..., cross:...} } } }"""
    unified = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
        "sast": {"total": 0, "by_tool": Counter(), "by_severity": Counter(),
                 "by_rule": Counter(), "by_cwe": Counter(), "findings": []},
        "dast": {"total": 0, "by_scan": Counter(), "by_risk": Counter(),
                 "by_alert": Counter(), "by_cwe": Counter(), "alerts": []},
        "cross": {"cwes_sast": set(), "cwes_dast": set(), "cwes_intersect": set()},
    })))

    # SAST: {caso: {ia: {linguagem: [findings]}}}
    for caso, ias in sast_data.items():
        for ia, langs in ias.items():
            for lang, findings in langs.items():
                bucket = unified[caso][ia][lang]["sast"]
                for f in findings:
                    bucket["total"] += 1
                    bucket["by_tool"][f.get("tool", "?")] += 1
                    sev = normalize_severity(f.get("severity"), "sast")
                    bucket["by_severity"][sev] += 1
                    bucket["by_rule"][f.get("rule_id", "?")] += 1
                    for cwe in extract_cwes(f.get("cwe")):
                        bucket["by_cwe"][cwe] += 1
                        unified[caso][ia][lang]["cross"]["cwes_sast"].add(cwe)
                    bucket["findings"].append(f)

    # DAST: {caso: {ia: {"linguagem__scan": [alerts]}}}
    for caso, ias in dast_data.items():
        for ia, lang_scan_dict in ias.items():
            for lang_scan, alerts in lang_scan_dict.items():
                # "python__full" -> ("python", "full")
                if "__" in lang_scan:
                    lang, scan = lang_scan.rsplit("__", 1)
                else:
                    lang, scan = lang_scan, "?"
                bucket = unified[caso][ia][lang]["dast"]
                for a in alerts:
                    bucket["total"] += 1
                    bucket["by_scan"][scan] += 1
                    risk = normalize_severity(a.get("risk"), "dast")
                    bucket["by_risk"][risk] += 1
                    bucket["by_alert"][a.get("alert_name", "?")] += 1
                    cwe_id = a.get("cwe_id")
                    if cwe_id:
                        cwe_str = f"CWE-{cwe_id}"
                        bucket["by_cwe"][cwe_str] += 1
                        unified[caso][ia][lang]["cross"]["cwes_dast"].add(cwe_str)
                    bucket["alerts"].append(a)

    # Calcula intersecção SAST ∩ DAST de CWEs
    for caso, ias in unified.items():
        for ia, langs in ias.items():
            for lang, data in langs.items():
                data["cross"]["cwes_intersect"] = (
                    data["cross"]["cwes_sast"] & data["cross"]["cwes_dast"]
                )

    return unified


# ============================================================================
# Saídas
# ============================================================================

def write_matrix_csv(unified: dict, out: Path):
    """Visão matricial: cada linha = combinação caso/ia/linguagem com métricas."""
    fields = [
        "caso", "ia", "linguagem",
        "sast_total", "sast_high", "sast_medium", "sast_low",
        "sast_bandit", "sast_semgrep", "sast_eslint", "sast_spotbugs",
        "sast_cwes_distintos",
        "dast_total", "dast_high", "dast_medium", "dast_low", "dast_informational",
        "dast_cwes_distintos",
        "cwes_em_comum_sast_dast",
    ]
    with out.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields)
        writer.writeheader()
        for caso in sorted(unified.keys()):
            for ia in sorted(unified[caso].keys()):
                for lang in sorted(unified[caso][ia].keys()):
                    d = unified[caso][ia][lang]
                    row = {
                        "caso": caso, "ia": ia, "linguagem": lang,
                        "sast_total": d["sast"]["total"],
                        "sast_high": d["sast"]["by_severity"].get("HIGH", 0),
                        "sast_medium": d["sast"]["by_severity"].get("MEDIUM", 0),
                        "sast_low": d["sast"]["by_severity"].get("LOW", 0),
                        "sast_bandit": d["sast"]["by_tool"].get("bandit", 0),
                        "sast_semgrep": d["sast"]["by_tool"].get("semgrep", 0),
                        "sast_eslint": d["sast"]["by_tool"].get("eslint", 0),
                        "sast_spotbugs": d["sast"]["by_tool"].get("spotbugs", 0),
                        "sast_cwes_distintos": len(d["cross"]["cwes_sast"]),
                        "dast_total": d["dast"]["total"],
                        "dast_high": d["dast"]["by_risk"].get("HIGH", 0),
                        "dast_medium": d["dast"]["by_risk"].get("MEDIUM", 0),
                        "dast_low": d["dast"]["by_risk"].get("LOW", 0),
                        "dast_informational": d["dast"]["by_risk"].get("INFORMATIONAL", 0),
                        "dast_cwes_distintos": len(d["cross"]["cwes_dast"]),
                        "cwes_em_comum_sast_dast": "; ".join(sorted(d["cross"]["cwes_intersect"])),
                    }
                    writer.writerow(row)


def write_cwe_overlap_csv(unified: dict, out: Path):
    """Mostra para cada combinação quais CWEs foram detectados por SAST, DAST ou ambos."""
    fields = ["caso", "ia", "linguagem", "cwe", "detectado_por_sast", "detectado_por_dast", "em_comum"]
    rows = []
    for caso in sorted(unified.keys()):
        for ia in sorted(unified[caso].keys()):
            for lang in sorted(unified[caso][ia].keys()):
                d = unified[caso][ia][lang]
                all_cwes = d["cross"]["cwes_sast"] | d["cross"]["cwes_dast"]
                for cwe in sorted(all_cwes):
                    in_sast = cwe in d["cross"]["cwes_sast"]
                    in_dast = cwe in d["cross"]["cwes_dast"]
                    rows.append({
                        "caso": caso, "ia": ia, "linguagem": lang, "cwe": cwe,
                        "detectado_por_sast": "sim" if in_sast else "não",
                        "detectado_por_dast": "sim" if in_dast else "não",
                        "em_comum": "sim" if (in_sast and in_dast) else "não",
                    })
    with out.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json_combined(unified: dict, out: Path):
    """Estrutura completa em JSON. Converte sets em listas."""
    def normalize(obj):
        if isinstance(obj, set):
            return sorted(obj)
        if isinstance(obj, Counter):
            return dict(obj)
        if isinstance(obj, dict):
            return {k: normalize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [normalize(v) for v in obj]
        return obj
    out.write_text(json.dumps(normalize(unified), indent=2, ensure_ascii=False))


# ============================================================================
# HTML
# ============================================================================

def write_html_combined(unified: dict, out: Path):
    def esc(s):
        return html.escape(str(s)) if s is not None else ""

    # Estatísticas globais
    total_sast = sum(d["sast"]["total"] for c in unified.values() for i in c.values() for d in i.values())
    total_dast = sum(d["dast"]["total"] for c in unified.values() for i in c.values() for d in i.values())
    combos_with_both = sum(
        1 for c in unified.values() for i in c.values() for d in i.values()
        if d["sast"]["total"] > 0 and d["dast"]["total"] > 0
    )
    cwes_overlap_total = set()
    for c in unified.values():
        for i in c.values():
            for d in i.values():
                cwes_overlap_total |= d["cross"]["cwes_intersect"]

    # Por IA
    by_ia = defaultdict(lambda: {"sast": 0, "dast": 0})
    for caso in unified.values():
        for ia, langs in caso.items():
            for d in langs.values():
                by_ia[ia]["sast"] += d["sast"]["total"]
                by_ia[ia]["dast"] += d["dast"]["total"]

    # Por linguagem
    by_lang = defaultdict(lambda: {"sast": 0, "dast": 0})
    for caso in unified.values():
        for ia in caso.values():
            for lang, d in ia.items():
                by_lang[lang]["sast"] += d["sast"]["total"]
                by_lang[lang]["dast"] += d["dast"]["total"]

    # Por caso
    by_caso = defaultdict(lambda: {"sast": 0, "dast": 0})
    for caso, ias in unified.items():
        for ia in ias.values():
            for d in ia.values():
                by_caso[caso]["sast"] += d["sast"]["total"]
                by_caso[caso]["dast"] += d["dast"]["total"]

    parts = []
    parts.append("""<!DOCTYPE html>
<html lang="pt-br">
<head>
<meta charset="UTF-8">
<title>Relatório Combinado SAST + DAST — Comparativo LLMs</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
         margin: 0; padding: 0; background: #f5f5f7; color: #1d1d1f; }
  header { background: linear-gradient(135deg, #1d1d1f 0%, #6a1b9a 100%);
           color: white; padding: 28px 32px; }
  header h1 { margin: 0; font-size: 26px; }
  header p { margin: 8px 0 0; opacity: 0.9; font-size: 14px; }
  main { max-width: 1500px; margin: 0 auto; padding: 24px 32px; }
  section { background: white; border-radius: 8px; padding: 20px 24px;
            margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }
  h2 { margin: 0 0 16px; font-size: 19px; border-bottom: 2px solid #e5e5e7;
       padding-bottom: 8px; }
  h3 { margin: 16px 0 8px; font-size: 15px; color: #555; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #e5e5e7;
           vertical-align: top; }
  th { background: #f5f5f7; font-weight: 600; }
  tr:hover { background: #fafafa; }
  td.num { text-align: right; font-variant-numeric: tabular-nums; }
  .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 12px; }
  .stat-card { background: #f5f5f7; padding: 16px; border-radius: 6px;
               border-left: 4px solid #ccc; }
  .stat-card.sast { border-left-color: #1976d2; }
  .stat-card.dast { border-left-color: #6a1b9a; }
  .stat-card.cross { border-left-color: #2e7d32; }
  .stat-card .label { font-size: 11px; text-transform: uppercase; color: #666;
                      letter-spacing: 0.5px; }
  .stat-card .value { font-size: 28px; font-weight: 600; margin-top: 4px; }
  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px;
           font-size: 11px; font-weight: 600; }
  .badge-sast { background: #e3f2fd; color: #1565c0; }
  .badge-dast { background: #ede7f6; color: #6a1b9a; }
  .badge-cwe { background: #fce4ec; color: #c2185b; }
  .badge-cross { background: #e8f5e9; color: #2e7d32; }
  details { margin: 8px 0; }
  details summary { cursor: pointer; padding: 10px 12px; background: #f5f5f7;
                    border-radius: 4px; font-weight: 600; }
  details[open] summary { margin-bottom: 8px; }
  .grid-2col { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  @media (max-width: 800px) { .grid-2col { grid-template-columns: 1fr; } }
  .empty { color: #999; font-style: italic; padding: 20px; text-align: center; }
  .nota { font-size: 12px; color: #666; font-style: italic; margin-top: 8px; }
  .legend { display: flex; gap: 16px; flex-wrap: wrap; margin-bottom: 12px;
            font-size: 12px; }
  .legend-item { display: flex; align-items: center; gap: 6px; }
  .legend-color { width: 12px; height: 12px; border-radius: 2px; }
</style>
</head>
<body>
<header>
  <h1>Relatório Combinado SAST + DAST</h1>
""")
    parts.append(f'  <p>Comparativo de Vulnerabilidades em Código Gerado por LLMs · {total_sast} achados estáticos + {total_dast} alertas dinâmicos</p>')
    parts.append("</header><main>")

    # === 1. Visão geral ===
    parts.append('<section><h2>1. Visão geral combinada</h2><div class="stats-grid">')
    parts.append(f'<div class="stat-card sast"><div class="label">SAST · achados estáticos</div><div class="value">{total_sast}</div></div>')
    parts.append(f'<div class="stat-card dast"><div class="label">DAST · alertas dinâmicos</div><div class="value">{total_dast}</div></div>')
    parts.append(f'<div class="stat-card cross"><div class="label">Combinações analisadas em ambas modalidades</div><div class="value">{combos_with_both}</div></div>')
    parts.append(f'<div class="stat-card cross"><div class="label">CWEs detectados em ambos SAST e DAST</div><div class="value">{len(cwes_overlap_total)}</div></div>')
    parts.append("</div>")
    parts.append('<p class="nota">SAST = análise estática (Bandit, Semgrep, ESLint, SpotBugs). DAST = análise dinâmica (OWASP ZAP).</p>')
    parts.append("</section>")

    # === 2. Comparação por IA ===
    parts.append('<section><h2>2. Comparação por IA</h2>')
    parts.append('<div class="legend">')
    parts.append('<div class="legend-item"><span class="legend-color" style="background:#1976d2"></span>SAST</div>')
    parts.append('<div class="legend-item"><span class="legend-color" style="background:#6a1b9a"></span>DAST</div>')
    parts.append('</div>')
    parts.append('<table><thead><tr><th>IA</th><th class="num">SAST</th><th class="num">DAST</th><th class="num">Total</th></tr></thead><tbody>')
    for ia in sorted(by_ia.keys()):
        s = by_ia[ia]["sast"]; d = by_ia[ia]["dast"]
        parts.append(f'<tr><td><strong>{esc(ia)}</strong></td><td class="num"><span class="badge badge-sast">{s}</span></td><td class="num"><span class="badge badge-dast">{d}</span></td><td class="num"><strong>{s+d}</strong></td></tr>')
    parts.append("</tbody></table></section>")

    # === 3. Comparação por linguagem ===
    parts.append('<section><h2>3. Comparação por linguagem</h2>')
    parts.append('<table><thead><tr><th>Linguagem</th><th class="num">SAST</th><th class="num">DAST</th><th class="num">Total</th></tr></thead><tbody>')
    for lang in sorted(by_lang.keys()):
        s = by_lang[lang]["sast"]; d = by_lang[lang]["dast"]
        parts.append(f'<tr><td><strong>{esc(lang)}</strong></td><td class="num"><span class="badge badge-sast">{s}</span></td><td class="num"><span class="badge badge-dast">{d}</span></td><td class="num"><strong>{s+d}</strong></td></tr>')
    parts.append("</tbody></table></section>")

    # === 4. Comparação por caso ===
    parts.append('<section><h2>4. Comparação por caso de teste</h2>')
    parts.append('<table><thead><tr><th>Caso</th><th class="num">SAST</th><th class="num">DAST</th><th class="num">Total</th></tr></thead><tbody>')
    for caso in sorted(by_caso.keys()):
        s = by_caso[caso]["sast"]; d = by_caso[caso]["dast"]
        parts.append(f'<tr><td><strong>{esc(caso)}</strong></td><td class="num"><span class="badge badge-sast">{s}</span></td><td class="num"><span class="badge badge-dast">{d}</span></td><td class="num"><strong>{s+d}</strong></td></tr>')
    parts.append("</tbody></table></section>")

    # === 5. Matriz IA × Linguagem (SAST + DAST lado a lado) ===
    parts.append('<section><h2>5. Matriz IA × Linguagem</h2>')
    parts.append('<p class="nota">Cada célula mostra: <strong>SAST + DAST = Total</strong></p>')
    matrix = defaultdict(lambda: defaultdict(lambda: {"sast": 0, "dast": 0}))
    for caso in unified.values():
        for ia, langs in caso.items():
            for lang, d in langs.items():
                matrix[ia][lang]["sast"] += d["sast"]["total"]
                matrix[ia][lang]["dast"] += d["dast"]["total"]
    ias = sorted(by_ia.keys())
    langs = sorted(by_lang.keys())
    if ias and langs:
        parts.append("<table><thead><tr><th>IA \\ Linguagem</th>")
        for lang in langs:
            parts.append(f"<th>{esc(lang)}</th>")
        parts.append("<th>Total</th></tr></thead><tbody>")
        for ia in ias:
            row_sast = sum(matrix[ia][l]["sast"] for l in langs)
            row_dast = sum(matrix[ia][l]["dast"] for l in langs)
            parts.append(f"<tr><td><strong>{esc(ia)}</strong></td>")
            for lang in langs:
                s = matrix[ia][lang]["sast"]; d = matrix[ia][lang]["dast"]
                parts.append(f'<td class="num">{s} + {d} = <strong>{s+d}</strong></td>')
            parts.append(f'<td class="num">{row_sast} + {row_dast} = <strong>{row_sast+row_dast}</strong></td></tr>')
        parts.append("</tbody></table>")
    parts.append("</section>")

    # === 6. CWEs cruzados ===
    parts.append('<section><h2>6. CWEs detectados em ambas modalidades</h2>')
    parts.append('<p class="nota">CWEs encontrados por SAST <em>E</em> DAST para a mesma combinação (caso/ia/linguagem). Indicam vulnerabilidades reais confirmadas por dois métodos independentes.</p>')

    cross_rows = []
    for caso, ias in sorted(unified.items()):
        for ia, langs in sorted(ias.items()):
            for lang, d in sorted(langs.items()):
                if d["cross"]["cwes_intersect"]:
                    cross_rows.append((caso, ia, lang, d["cross"]["cwes_intersect"]))
    if cross_rows:
        parts.append('<table><thead><tr><th>Caso</th><th>IA</th><th>Linguagem</th><th>CWEs em comum</th></tr></thead><tbody>')
        for caso, ia, lang, cwes in cross_rows:
            cwe_badges = " ".join(f'<span class="badge badge-cwe">{esc(c)}</span>' for c in sorted(cwes))
            parts.append(f"<tr><td>{esc(caso)}</td><td>{esc(ia)}</td><td>{esc(lang)}</td><td>{cwe_badges}</td></tr>")
        parts.append("</tbody></table>")
    else:
        parts.append('<div class="empty">Nenhum CWE foi detectado simultaneamente por SAST e DAST nas combinações analisadas.</div>')
    parts.append("</section>")

    # === 7. Detalhamento por combinação ===
    parts.append('<section><h2>7. Detalhamento por combinação (caso × IA × linguagem)</h2>')
    parts.append('<p class="nota">Clique em cada combinação para expandir e ver SAST e DAST lado a lado.</p>')

    for caso in sorted(unified.keys()):
        for ia in sorted(unified[caso].keys()):
            for lang in sorted(unified[caso][ia].keys()):
                d = unified[caso][ia][lang]
                sast_total = d["sast"]["total"]
                dast_total = d["dast"]["total"]
                if sast_total == 0 and dast_total == 0:
                    continue

                parts.append('<details>')
                cwes_inter = d["cross"]["cwes_intersect"]
                cross_label = f' · <span class="badge badge-cross">{len(cwes_inter)} CWE(s) em comum</span>' if cwes_inter else ""
                parts.append(
                    f'<summary>{esc(caso)} · {esc(ia)} · {esc(lang)} — '
                    f'<span class="badge badge-sast">SAST: {sast_total}</span> '
                    f'<span class="badge badge-dast">DAST: {dast_total}</span>'
                    f'{cross_label}</summary>'
                )
                parts.append('<div class="grid-2col">')

                # --- Coluna SAST ---
                parts.append('<div>')
                parts.append(f'<h3 style="color:#1565c0">SAST · {sast_total} achados</h3>')
                if sast_total > 0:
                    sev = d["sast"]["by_severity"]
                    parts.append('<table><thead><tr><th>Severidade</th><th class="num">Qtd</th></tr></thead><tbody>')
                    for s in ["HIGH", "MEDIUM", "LOW"]:
                        if sev.get(s, 0):
                            parts.append(f'<tr><td>{s}</td><td class="num">{sev[s]}</td></tr>')
                    parts.append("</tbody></table>")
                    # Por ferramenta
                    parts.append('<table><thead><tr><th>Ferramenta</th><th class="num">Qtd</th></tr></thead><tbody>')
                    for tool, n in d["sast"]["by_tool"].most_common():
                        parts.append(f'<tr><td><span class="badge badge-sast">{esc(tool)}</span></td><td class="num">{n}</td></tr>')
                    parts.append("</tbody></table>")
                    # Top regras
                    top_rules = d["sast"]["by_rule"].most_common(5)
                    if top_rules:
                        parts.append('<table><thead><tr><th>Top regras</th><th class="num">Qtd</th></tr></thead><tbody>')
                        for rule, n in top_rules:
                            parts.append(f'<tr><td><code>{esc(rule)}</code></td><td class="num">{n}</td></tr>')
                        parts.append("</tbody></table>")
                else:
                    parts.append('<div class="empty">Sem achados SAST.</div>')
                parts.append('</div>')

                # --- Coluna DAST ---
                parts.append('<div>')
                parts.append(f'<h3 style="color:#6a1b9a">DAST · {dast_total} alertas</h3>')
                if dast_total > 0:
                    risk = d["dast"]["by_risk"]
                    parts.append('<table><thead><tr><th>Risco</th><th class="num">Qtd</th></tr></thead><tbody>')
                    for r in ["HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]:
                        if risk.get(r, 0):
                            parts.append(f'<tr><td>{r}</td><td class="num">{risk[r]}</td></tr>')
                    parts.append("</tbody></table>")
                    # Top alertas
                    top_alerts = d["dast"]["by_alert"].most_common(5)
                    if top_alerts:
                        parts.append('<table><thead><tr><th>Top alertas</th><th class="num">Qtd</th></tr></thead><tbody>')
                        for alert_name, n in top_alerts:
                            parts.append(f'<tr><td>{esc(alert_name[:80])}</td><td class="num">{n}</td></tr>')
                        parts.append("</tbody></table>")
                else:
                    parts.append('<div class="empty">Sem alertas DAST.</div>')
                parts.append('</div>')

                parts.append('</div>')  # grid-2col

                # --- CWEs em comum ---
                if cwes_inter:
                    parts.append('<h3 style="color:#2e7d32">CWEs detectados por SAST e DAST</h3>')
                    parts.append('<div>')
                    for cwe in sorted(cwes_inter):
                        parts.append(f'<span class="badge badge-cross">{esc(cwe)}</span> ')
                    parts.append('</div>')

                parts.append('</details>')

    parts.append("</section>")

    if not unified:
        parts.append('<section><div class="empty">Sem dados. Rode primeiro: <code>python3 scripts/report_sast.py</code> e <code>python3 scripts/report_dast.py</code></div></section>')

    parts.append("</main></body></html>")
    out.write_text("\n".join(parts), encoding="utf-8")


# ============================================================================
# Main
# ============================================================================

def main():
    print("Carregando relatórios SAST e DAST...")
    sast_data = load_sast()
    dast_data = load_dast()

    if not sast_data and not dast_data:
        print("Nenhum relatório encontrado. Rode antes:", file=sys.stderr)
        print("  python3 scripts/report_sast.py", file=sys.stderr)
        print("  python3 scripts/report_dast.py", file=sys.stderr)
        sys.exit(1)

    print(f"  SAST: {sum(len(langs) for ias in sast_data.values() for langs in ias.values())} combinações")
    print(f"  DAST: {sum(len(langs) for ias in dast_data.values() for langs in ias.values())} execuções de scan")

    print("Cruzando dados...")
    unified = build_unified(sast_data, dast_data)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    matrix_csv = OUT_DIR / "report.csv"
    overlap_csv = OUT_DIR / "cwe_overlap.csv"
    json_out = OUT_DIR / "report.json"
    html_out = OUT_DIR / "report.html"

    print(f"Gerando {matrix_csv.name}...")
    write_matrix_csv(unified, matrix_csv)

    print(f"Gerando {overlap_csv.name}...")
    write_cwe_overlap_csv(unified, overlap_csv)

    print(f"Gerando {json_out.name}...")
    write_json_combined(unified, json_out)

    print(f"Gerando {html_out.name}...")
    write_html_combined(unified, html_out)

    print()
    print("Relatórios combinados gerados:")
    print(f"  {matrix_csv}")
    print(f"  {overlap_csv}")
    print(f"  {json_out}")
    print(f"  {html_out}")
    print()
    print(f"Para abrir o HTML: xdg-open {html_out}")


if __name__ == "__main__":
    main()