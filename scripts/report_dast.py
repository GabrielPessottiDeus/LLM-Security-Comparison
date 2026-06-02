#!/usr/bin/env python3
"""
report_dast.py — Relatório DAST completo com análises estatísticas.
"""
from __future__ import annotations
import json, csv, re, sys, html, statistics
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parent.parent
DAST_DIR = ROOT / "reports" / "dast"

PATTERN = re.compile(
    r"^zap_(?P<scan>baseline|full)_caso(?P<num>\d+)_(?P<tag>.+?)_(?P<ts>\d{8}_\d{6})$"
)

RISK_MAP = {"0": "INFORMATIONAL", "1": "LOW", "2": "MEDIUM", "3": "HIGH"}
CONFIDENCE_MAP = {"0": "FALSE POSITIVE", "1": "LOW", "2": "MEDIUM", "3": "HIGH", "4": "CONFIRMED"}

N_CASOS = 5
N_IAS = 3
N_LANGS = 4

CASO_MAP = {
    "1": "caso01_auth", "2": "caso02_products", "3": "caso03_upload",
    "4": "caso04_comments", "5": "caso05_session",
}

INFRA_ALERT_IDS = {
    "10038", "10036", "10063", "10049", "10106", "10020", "10021", "10035",
    "10037", "10054", "10055", "10010", "10011", "10015", "10017", "10027",
    "10031", "10033", "10040", "10041", "10042", "10043", "10094", "10096", "10098",
}


def clean_html(s):
    if not s:
        return ""
    s = re.sub(r"<p>", "\n", s)
    s = re.sub(r"</p>", "", s)
    s = re.sub(r"<br\s*/?>", "\n", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\n\s*\n", "\n", s).strip()
    return s


def parse_zap(path):
    try:
        data = json.loads(path.read_text())
    except Exception as e:
        return ({"_parse_error": str(e)}, [])

    stem = path.stem
    m = PATTERN.match(stem)
    if not m:
        return ({}, [])

    tag = m["tag"]
    ia, lang = "", ""
    parts = tag.split("_")
    for i, pp in enumerate(parts):
        if pp in ("python", "java", "javascript", "typescript"):
            lang = pp
            ia = "_".join(parts[:i]) if i > 0 else ""
            break
    if not lang:
        ia = parts[0]
        lang = "_".join(parts[1:])

    meta = {
        "arquivo": path.name,
        "scan_tipo": m["scan"],
        "caso": CASO_MAP.get(m["num"], f"caso{m['num']}"),
        "ia": ia,
        "linguagem": lang,
        "timestamp": m["ts"],
    }

    alerts = []
    for site in data.get("site", []):
        site_name = site.get("@name", "")
        for alert in site.get("alerts", []):
            risk_code = str(alert.get("riskcode", ""))
            conf_code = str(alert.get("confidence", ""))
            plugin_id = alert.get("pluginid", "")
            is_infra = plugin_id in INFRA_ALERT_IDS
            instances = alert.get("instances", []) or [{}]
            for inst in instances:
                alerts.append({
                    "site": site_name,
                    "plugin_id": plugin_id,
                    "alert_ref": alert.get("alertRef", ""),
                    "alert_name": alert.get("alert", ""),
                    "risk_code": risk_code,
                    "risk": RISK_MAP.get(risk_code, "UNKNOWN"),
                    "confidence_code": conf_code,
                    "confidence": CONFIDENCE_MAP.get(conf_code, "UNKNOWN"),
                    "description": clean_html(alert.get("desc", ""))[:500],
                    "solution": clean_html(alert.get("solution", ""))[:500],
                    "cwe_id": alert.get("cweid", ""),
                    "wasc_id": alert.get("wascid", ""),
                    "url": inst.get("uri", ""),
                    "method": inst.get("method", ""),
                    "param": inst.get("param", ""),
                    "attack": (inst.get("attack") or "")[:200],
                    "evidence": (inst.get("evidence") or "")[:300],
                    "other_info": clean_html(inst.get("otherinfo", ""))[:300],
                    "is_infra": is_infra,
                })
    return meta, alerts


def collect_all():
    all_alerts = []
    scans_realizados = set()
    if not DAST_DIR.exists():
        return all_alerts, scans_realizados
    for f in sorted(DAST_DIR.glob("zap_*.json")):
        if f.name in ("report.json",):
            continue
        meta, alerts = parse_zap(f)
        if "_parse_error" in meta:
            print(f"  AVISO: falha em {f.name}: {meta['_parse_error']}", file=sys.stderr)
            continue
        if not meta:
            continue
        scans_realizados.add((meta["caso"], meta["ia"], meta["linguagem"], meta["scan_tipo"]))
        for a in alerts:
            a.update(meta)
            all_alerts.append(a)
    return all_alerts, scans_realizados


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


def build_per_scan_totals(alerts, scans_realizados):
    result = {}
    for combo in scans_realizados:
        result[combo] = {
            "total": 0, "total_real": 0, "total_infra": 0,
            "by_risk": Counter(), "by_risk_real": Counter(),
            "by_alert": Counter(), "by_cwe": Counter(),
        }
    for a in alerts:
        combo = (a["caso"], a["ia"], a["linguagem"], a["scan_tipo"])
        if combo not in result:
            result[combo] = {
                "total": 0, "total_real": 0, "total_infra": 0,
                "by_risk": Counter(), "by_risk_real": Counter(),
                "by_alert": Counter(), "by_cwe": Counter(),
            }
        result[combo]["total"] += 1
        result[combo]["by_risk"][a["risk"]] += 1
        result[combo]["by_alert"][a["alert_name"]] += 1
        if a["is_infra"]:
            result[combo]["total_infra"] += 1
        else:
            result[combo]["total_real"] += 1
            result[combo]["by_risk_real"][a["risk"]] += 1
        if a.get("cwe_id"):
            result[combo]["by_cwe"][f"CWE-{a['cwe_id']}"] += 1
    return result


def aggregate_by_dimension(per_scan, dim, use_real=False):
    idx = {"caso": 0, "ia": 1, "linguagem": 2, "scan_tipo": 3}[dim]
    grouped = defaultdict(list)
    field = "total_real" if use_real else "total"
    for combo, data in per_scan.items():
        grouped[combo[idx]].append(data[field])
    return {k: stats_from(v) for k, v in grouped.items()}


def aggregate_by_two(per_scan, dim1, dim2, use_real=False):
    idx_map = {"caso": 0, "ia": 1, "linguagem": 2, "scan_tipo": 3}
    i1, i2 = idx_map[dim1], idx_map[dim2]
    grouped = defaultdict(list)
    field = "total_real" if use_real else "total"
    for combo, data in per_scan.items():
        grouped[(combo[i1], combo[i2])].append(data[field])
    return {k: stats_from(v) for k, v in grouped.items()}


def risk_aggregate(per_scan, dim, use_real=False):
    idx = {"caso": 0, "ia": 1, "linguagem": 2, "scan_tipo": 3}[dim]
    gh, gm, gl, gi = defaultdict(list), defaultdict(list), defaultdict(list), defaultdict(list)
    field = "by_risk_real" if use_real else "by_risk"
    for combo, data in per_scan.items():
        key = combo[idx]
        risk = data[field]
        gh[key].append(risk.get("HIGH", 0))
        gm[key].append(risk.get("MEDIUM", 0))
        gl[key].append(risk.get("LOW", 0))
        gi[key].append(risk.get("INFORMATIONAL", 0))
    result = {}
    for key in set(list(gh.keys()) + list(gm.keys()) + list(gl.keys()) + list(gi.keys())):
        result[key] = {
            "high": stats_from(gh[key]),
            "medium": stats_from(gm[key]),
            "low": stats_from(gl[key]),
            "info": stats_from(gi[key]),
        }
    return result


def cwe_by_dimension(alerts, dim, only_real=False):
    result = defaultdict(Counter)
    for a in alerts:
        if only_real and a.get("is_infra"):
            continue
        if not a.get("cwe_id"):
            continue
        key = a[dim]
        result[key][f"CWE-{a['cwe_id']}"] += 1
    return result


def gerar_conclusoes(per_scan, alerts):
    conclusoes = []
    stats_by_ia = aggregate_by_dimension(per_scan, "ia")
    stats_by_ia_real = aggregate_by_dimension(per_scan, "ia", use_real=True)
    stats_by_lang_real = aggregate_by_dimension(per_scan, "linguagem", use_real=True)
    stats_by_caso = aggregate_by_dimension(per_scan, "caso")

    if stats_by_ia:
        ranked = sorted(stats_by_ia.items(), key=lambda x: x[1]["mean"])
        best, worst = ranked[0], ranked[-1]
        if best[0] != worst[0]:
            conclusoes.append({
                "tipo": "IA com menor média geral (incluindo infra)",
                "texto": f"Considerando todos os alertas DAST, a IA '{best[0]}' apresentou a menor média ({best[1]['mean']}; mediana {best[1]['median']}, desvio {best[1]['stdev']}). A IA '{worst[0]}' apresentou a maior ({worst[1]['mean']} alertas em média).",
                "nota": "Alertas de configuração de servidor (CSP, headers, HTTPS) tendem a aparecer em toda app — veja a próxima conclusão com filtro."
            })

    if stats_by_ia_real:
        ranked = sorted(stats_by_ia_real.items(), key=lambda x: x[1]["mean"])
        best, worst = ranked[0], ranked[-1]
        if best[0] != worst[0]:
            conclusoes.append({
                "tipo": "IA com menor média de alertas APLICACIONAIS",
                "texto": f"Excluindo alertas de configuração de servidor, a IA '{best[0]}' apresentou a menor média ({best[1]['mean']} alertas/scan). A pior foi '{worst[0]}' ({worst[1]['mean']}).",
                "nota": "Esta é a métrica mais útil para comparar a qualidade do código entre IAs, pois filtra ruído de configuração."
            })

    if stats_by_lang_real:
        ranked = sorted(stats_by_lang_real.items(), key=lambda x: x[1]["mean"])
        conclusoes.append({
            "tipo": "Linguagem com menor média de alertas aplicacionais",
            "texto": f"Por linguagem (excluindo infra), '{ranked[0][0]}' teve a menor média ({ranked[0][1]['mean']}) e '{ranked[-1][0]}' a maior ({ranked[-1][1]['mean']}).",
            "nota": "Diferenças entre linguagens refletem características do framework usado (Spring, Flask, Express) e como cada um trata requisições malformadas."
        })

    if stats_by_caso:
        ranked = sorted(stats_by_caso.items(), key=lambda x: -x[1]["mean"])
        conclusoes.append({
            "tipo": "Caso mais 'difícil' em runtime",
            "texto": f"O caso que produziu mais alertas DAST em média foi '{ranked[0][0]}' ({ranked[0][1]['mean']}). O mais 'limpo' foi '{ranked[-1][0]}' ({ranked[-1][1]['mean']}).",
            "nota": "Casos com mais endpoints expostos e mais superfície de ataque tendem a gerar mais alertas."
        })

    stats_ia_caso = aggregate_by_two(per_scan, "caso", "ia", use_real=True)
    casos = set(k[0] for k in stats_ia_caso.keys())
    for caso in sorted(casos):
        ia_in_caso = {k[1]: v for k, v in stats_ia_caso.items() if k[0] == caso}
        if len(ia_in_caso) >= 2:
            ranked = sorted(ia_in_caso.items(), key=lambda x: x[1]["mean"])
            conclusoes.append({
                "tipo": f"Melhor IA no {caso} (alertas aplicacionais)",
                "texto": f"No '{caso}', a IA com menor média de alertas aplicacionais foi '{ranked[0][0]}' ({ranked[0][1]['mean']} alertas em {ranked[0][1]['count']} scans).",
                "nota": ""
            })

    high_by_ia = defaultdict(int)
    for a in alerts:
        if a["risk"] == "HIGH":
            high_by_ia[a["ia"]] += 1
    if high_by_ia:
        ranked = sorted(high_by_ia.items(), key=lambda x: x[1])
        best_ia, best_count = ranked[0]
        worst_ia, worst_count = ranked[-1]
        if best_count != worst_count:
            conclusoes.append({
                "tipo": "IA com menos alertas HIGH",
                "texto": f"A IA '{best_ia}' teve menos alertas de risco HIGH ({best_count} no total). A IA '{worst_ia}' teve mais ({worst_count}).",
                "nota": "Alertas HIGH representam vulnerabilidades exploráveis identificadas pelo ZAP em tempo de execução."
            })

    cwe_per_ia = cwe_by_dimension(alerts, "ia", only_real=True)
    for ia, cwes in cwe_per_ia.items():
        if cwes:
            top = cwes.most_common(3)
            top_str = ", ".join(f"{c} ({n} instâncias)" for c, n in top)
            conclusoes.append({
                "tipo": f"Top CWEs aplicacionais em '{ia}'",
                "texto": f"Para '{ia}', as CWEs aplicacionais mais frequentes foram: {top_str}.",
                "nota": ""
            })

    high_per_combo = defaultdict(int)
    for a in alerts:
        if a["risk"] == "HIGH":
            high_per_combo[(a["caso"], a["ia"], a["linguagem"])] += 1
    if high_per_combo:
        top_combo, top_n = max(high_per_combo.items(), key=lambda x: x[1])
        conclusoes.append({
            "tipo": "Combinação com mais alertas HIGH",
            "texto": f"A combinação com mais alertas de risco HIGH foi '{top_combo[0]} / {top_combo[1]} / {top_combo[2]}', com {top_n} alertas.",
            "nota": ""
        })

    return conclusoes


DETAILED_FIELDS = [
    "caso", "ia", "linguagem", "scan_tipo", "risk", "confidence",
    "is_infra", "plugin_id", "alert_ref", "alert_name", "cwe_id", "wasc_id",
    "url", "method", "param", "attack", "evidence",
    "description", "solution", "other_info", "timestamp", "arquivo"
]


def write_detailed_csv(alerts, out):
    with out.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=DETAILED_FIELDS, extrasaction="ignore")
        writer.writeheader()
        for a in sorted(alerts, key=lambda x: (x["caso"], x["ia"], x["linguagem"], x["risk"])):
            row = dict(a)
            row["is_infra"] = "sim" if a.get("is_infra") else "não"
            writer.writerow(row)


def write_summary_csv(per_scan, out):
    fields = ["caso", "ia", "linguagem", "scan_tipo",
              "total", "total_real", "total_infra",
              "risk_HIGH", "risk_MEDIUM", "risk_LOW", "risk_INFORMATIONAL",
              "risk_HIGH_real", "risk_MEDIUM_real", "risk_LOW_real"]
    with out.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields)
        writer.writeheader()
        for combo, data in sorted(per_scan.items()):
            row = {
                "caso": combo[0], "ia": combo[1], "linguagem": combo[2], "scan_tipo": combo[3],
                "total": data["total"],
                "total_real": data["total_real"],
                "total_infra": data["total_infra"],
            }
            for r in ["HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]:
                row[f"risk_{r}"] = data["by_risk"].get(r, 0)
            for r in ["HIGH", "MEDIUM", "LOW"]:
                row[f"risk_{r}_real"] = data["by_risk_real"].get(r, 0)
            writer.writerow(row)


def write_stats_csv(per_scan, out):
    rows = []
    for dim in ["ia", "linguagem", "caso", "scan_tipo"]:
        for variant, use_real in [("total", False), ("total_aplicacional", True)]:
            for key, st in aggregate_by_dimension(per_scan, dim, use_real=use_real).items():
                rows.append({"dimensao": dim, "metrica": variant, "valor": key, **st})
    for d1, d2 in [("ia", "linguagem"), ("ia", "caso"), ("linguagem", "caso")]:
        for variant, use_real in [("total", False), ("total_aplicacional", True)]:
            for (k1, k2), st in aggregate_by_two(per_scan, d1, d2, use_real=use_real).items():
                rows.append({"dimensao": f"{d1}_x_{d2}", "metrica": variant, "valor": f"{k1} × {k2}", **st})
    fields = ["dimensao", "metrica", "valor", "count", "sum", "mean", "median", "stdev", "min", "max", "zero_rate"]
    with out.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(alerts, out):
    structure = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for a in alerts:
        key = f"{a['linguagem']}__{a['scan_tipo']}"
        structure[a["caso"]][a["ia"]][key].append(
            {k: v for k, v in a.items() if k not in ("caso", "ia", "linguagem", "scan_tipo")}
        )
    out.write_text(json.dumps(structure, indent=2, ensure_ascii=False))


CSS = """
* { box-sizing: border-box; }
body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
       margin: 0; padding: 0; background: #f5f5f7; color: #1d1d1f; line-height: 1.5; }
header { background: linear-gradient(135deg, #6a1b9a 0%, #4a148c 100%);
         color: white; padding: 28px 32px; }
header h1 { margin: 0; font-size: 26px; }
header p { margin: 8px 0 0; opacity: 0.9; font-size: 14px; }
nav.toc { background: white; padding: 16px 24px; border-bottom: 1px solid #e5e5e7;
          position: sticky; top: 0; z-index: 10; }
nav.toc a { display: inline-block; margin-right: 16px; color: #6a1b9a;
            text-decoration: none; font-size: 13px; }
nav.toc a:hover { text-decoration: underline; }
main { max-width: 1500px; margin: 0 auto; padding: 24px 32px; }
section { background: white; border-radius: 8px; padding: 24px 28px;
          margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);
          scroll-margin-top: 60px; }
h2 { margin: 0 0 16px; font-size: 20px; border-bottom: 2px solid #e5e5e7;
     padding-bottom: 10px; }
h3 { margin: 20px 0 10px; font-size: 16px; color: #4a148c; }
table { width: 100%; border-collapse: collapse; font-size: 13px; margin: 8px 0; }
th, td { padding: 8px 10px; text-align: left; border-bottom: 1px solid #e5e5e7;
         vertical-align: top; }
th { background: #f5f5f7; font-weight: 600; }
tr:hover { background: #fafafa; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
              gap: 12px; margin-bottom: 16px; }
.stat-card { background: #f5f5f7; padding: 14px; border-radius: 6px;
             border-left: 4px solid #ccc; }
.stat-card.high { border-left-color: #d32f2f; }
.stat-card.medium { border-left-color: #f57c00; }
.stat-card.low { border-left-color: #1976d2; }
.stat-card.info { border-left-color: #757575; }
.stat-card .label { font-size: 11px; text-transform: uppercase; color: #666;
                    letter-spacing: 0.5px; }
.stat-card .value { font-size: 24px; font-weight: 600; margin-top: 4px; }
.risk-high { color: #d32f2f; font-weight: 600; }
.risk-medium { color: #f57c00; font-weight: 600; }
.risk-low { color: #1976d2; font-weight: 600; }
.risk-informational { color: #757575; }
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
.badge-scan { background: #ede7f6; color: #6a1b9a; }
.badge-cwe { background: #fce4ec; color: #c2185b; }
.badge-infra { background: #eceff1; color: #455a64; font-weight: normal; }
.url-cell { font-family: monospace; font-size: 11px; word-break: break-all; max-width: 320px; }
details { margin: 8px 0; }
details summary { cursor: pointer; padding: 10px 12px; background: #f5f5f7;
                  border-radius: 4px; font-weight: 600; }
details[open] summary { margin-bottom: 8px; }
.heatmap td { text-align: center; }
.heatmap .h0 { background: #f5f5f7; color: #666; }
.heatmap .h1 { background: #f3e5f5; }
.heatmap .h2 { background: #e1bee7; }
.heatmap .h3 { background: #ce93d8; }
.heatmap .h4 { background: #ba68c8; color: white; }
.heatmap .h5 { background: #ab47bc; color: white; }
.heatmap .h6 { background: #8e24aa; color: white; }
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


def write_html(alerts, per_scan, scans_realizados, out):
    def esc(s):
        return html.escape(str(s)) if s is not None else ""

    total = len(alerts)
    total_real = sum(1 for a in alerts if not a.get("is_infra"))
    total_infra = total - total_real
    total_scans = len(scans_realizados)
    by_risk = Counter(a["risk"] for a in alerts)

    stats_ia = aggregate_by_dimension(per_scan, "ia")
    stats_ia_real = aggregate_by_dimension(per_scan, "ia", use_real=True)
    stats_lang = aggregate_by_dimension(per_scan, "linguagem")
    stats_lang_real = aggregate_by_dimension(per_scan, "linguagem", use_real=True)
    stats_caso = aggregate_by_dimension(per_scan, "caso")
    stats_caso_real = aggregate_by_dimension(per_scan, "caso", use_real=True)
    stats_ia_lang = aggregate_by_two(per_scan, "ia", "linguagem", use_real=True)
    stats_ia_caso = aggregate_by_two(per_scan, "ia", "caso", use_real=True)
    stats_lang_caso = aggregate_by_two(per_scan, "linguagem", "caso", use_real=True)

    risk_by_ia = risk_aggregate(per_scan, "ia")
    risk_by_lang = risk_aggregate(per_scan, "linguagem")
    risk_by_caso = risk_aggregate(per_scan, "caso")

    cwe_per_ia = cwe_by_dimension(alerts, "ia", only_real=True)
    cwe_per_lang = cwe_by_dimension(alerts, "linguagem", only_real=True)
    cwe_per_caso = cwe_by_dimension(alerts, "caso", only_real=True)

    conclusoes = gerar_conclusoes(per_scan, alerts)

    p = []
    p.append(f"""<!DOCTYPE html>
<html lang="pt-br"><head><meta charset="UTF-8">
<title>Relatório DAST Completo — Comparativo LLMs</title>
<style>{CSS}</style></head><body>
<header>
  <h1>Relatório DAST Completo (OWASP ZAP)</h1>
  <p>Análise estatística de vulnerabilidades em runtime nas apps geradas por LLMs</p>
  <p>{total} alertas ({total_real} aplicacionais + {total_infra} infra) · {total_scans} scans</p>
</header>
<nav class="toc">
  <a href="#visao-geral">1. Visão geral</a>
  <a href="#conclusoes">2. Conclusões</a>
  <a href="#stats-ia">3. Por IA</a>
  <a href="#stats-lang">4. Por linguagem</a>
  <a href="#stats-caso">5. Por caso</a>
  <a href="#cruzamentos">6. Cruzamentos</a>
  <a href="#riscos">7. Riscos</a>
  <a href="#cwes">8. CWEs</a>
  <a href="#detalhamento">9. Detalhamento</a>
  <a href="#notas">10. Notas metodológicas</a>
</nav>
<main>""")

    p.append('<section id="visao-geral"><h2>1. Visão geral</h2><div class="stats-grid">')
    p.append(f'<div class="stat-card"><div class="label">Total alertas</div><div class="value">{total}</div></div>')
    p.append(f'<div class="stat-card"><div class="label">Aplicacionais</div><div class="value">{total_real}</div></div>')
    p.append(f'<div class="stat-card"><div class="label">Infra / configuração</div><div class="value">{total_infra}</div></div>')
    p.append(f'<div class="stat-card"><div class="label">Scans realizados</div><div class="value">{total_scans}</div></div>')
    for risk in ["HIGH", "MEDIUM", "LOW", "INFORMATIONAL"]:
        n = by_risk.get(risk, 0)
        if n:
            p.append(f'<div class="stat-card {risk.lower()}"><div class="label">{risk}</div><div class="value risk-{risk.lower()}">{n}</div></div>')
    p.append("</div>")
    p.append("""<div class="method-box">
<strong>Alertas "aplicacionais" vs "infra":</strong> o ZAP detecta dois tipos:
<ul style="margin:8px 0">
<li><strong>Alertas de infra/configuração</strong>: aparecem em quase toda app com a mesma stack (CSP header ausente, server header expondo versão, falta de HTTPS, cookies sem flags). <em>Não diferenciam as IAs.</em></li>
<li><strong>Alertas aplicacionais</strong>: problemas específicos do código gerado (SQL injection, XSS, path traversal, exceções não tratadas). <em>Diferenciam as IAs.</em></li>
</ul>
Em comparações IA × IA, este relatório usa <strong>total aplicacional</strong> sempre que possível.
</div>""")
    p.append("</section>")

    p.append('<section id="conclusoes"><h2>2. Conclusões automáticas</h2>')
    if conclusoes:
        for c in conclusoes:
            p.append('<div class="conclusao">')
            p.append(f'<div class="titulo">{esc(c["tipo"])}</div>')
            p.append(f'<div class="texto">{esc(c["texto"])}</div>')
            if c.get("nota"):
                p.append(f'<div class="nota">⚠ {esc(c["nota"])}</div>')
            p.append('</div>')
    else:
        p.append('<div class="empty">Sem dados suficientes.</div>')
    p.append("</section>")

    p.append('<section id="stats-ia"><h2>3. Estatísticas por IA</h2>')
    p.append('<h3>3.1 Total bruto (incluindo alertas de infra)</h3>')
    p.append('<table><thead><tr><th>IA</th><th class="num">Scans</th><th class="num">Total</th><th class="num">Média</th><th class="num">Mediana</th><th class="num">Desvio</th><th class="num">Mín</th><th class="num">Máx</th></tr></thead><tbody>')
    for i, (ia, st) in enumerate(sorted(stats_ia.items(), key=lambda x: x[1]["mean"])):
        rank_cls = f"rank-{i+1}" if i < 3 else ""
        p.append(f'<tr class="{rank_cls}"><td><strong>{esc(ia)}</strong></td><td class="num">{st["count"]}</td><td class="num">{st["sum"]}</td><td class="num">{st["mean"]}</td><td class="num">{st["median"]}</td><td class="num">{st["stdev"]}</td><td class="num">{st["min"]}</td><td class="num">{st["max"]}</td></tr>')
    p.append('</tbody></table>')

    p.append('<h3>3.2 Apenas alertas aplicacionais (excluindo infra) — métrica mais útil</h3>')
    p.append('<table><thead><tr><th>IA</th><th class="num">Scans</th><th class="num">Total</th><th class="num">Média</th><th class="num">Mediana</th><th class="num">Desvio</th><th class="num">Mín</th><th class="num">Máx</th><th class="num">% sem alertas</th></tr></thead><tbody>')
    for i, (ia, st) in enumerate(sorted(stats_ia_real.items(), key=lambda x: x[1]["mean"])):
        rank_cls = f"rank-{i+1}" if i < 3 else ""
        p.append(f'<tr class="{rank_cls}"><td><strong>{esc(ia)}</strong></td><td class="num">{st["count"]}</td><td class="num">{st["sum"]}</td><td class="num">{st["mean"]}</td><td class="num">{st["median"]}</td><td class="num">{st["stdev"]}</td><td class="num">{st["min"]}</td><td class="num">{st["max"]}</td><td class="num">{st["zero_rate"]}%</td></tr>')
    p.append('</tbody></table></section>')

    p.append('<section id="stats-lang"><h2>4. Estatísticas por linguagem</h2>')
    p.append('<div class="warning-box">⚠ Diferenças entre linguagens em DAST refletem características do framework (Spring vs Flask vs Express).</div>')
    p.append('<h3>4.1 Total bruto</h3>')
    p.append('<table><thead><tr><th>Linguagem</th><th class="num">Scans</th><th class="num">Total</th><th class="num">Média</th><th class="num">Mediana</th><th class="num">Desvio</th><th class="num">Mín</th><th class="num">Máx</th></tr></thead><tbody>')
    for i, (lang, st) in enumerate(sorted(stats_lang.items(), key=lambda x: x[1]["mean"])):
        rank_cls = f"rank-{i+1}" if i < 3 else ""
        p.append(f'<tr class="{rank_cls}"><td><strong>{esc(lang)}</strong></td><td class="num">{st["count"]}</td><td class="num">{st["sum"]}</td><td class="num">{st["mean"]}</td><td class="num">{st["median"]}</td><td class="num">{st["stdev"]}</td><td class="num">{st["min"]}</td><td class="num">{st["max"]}</td></tr>')
    p.append('</tbody></table>')
    p.append('<h3>4.2 Apenas alertas aplicacionais</h3>')
    p.append('<table><thead><tr><th>Linguagem</th><th class="num">Scans</th><th class="num">Total</th><th class="num">Média</th><th class="num">Mediana</th><th class="num">Desvio</th><th class="num">Mín</th><th class="num">Máx</th><th class="num">% sem alertas</th></tr></thead><tbody>')
    for i, (lang, st) in enumerate(sorted(stats_lang_real.items(), key=lambda x: x[1]["mean"])):
        rank_cls = f"rank-{i+1}" if i < 3 else ""
        p.append(f'<tr class="{rank_cls}"><td><strong>{esc(lang)}</strong></td><td class="num">{st["count"]}</td><td class="num">{st["sum"]}</td><td class="num">{st["mean"]}</td><td class="num">{st["median"]}</td><td class="num">{st["stdev"]}</td><td class="num">{st["min"]}</td><td class="num">{st["max"]}</td><td class="num">{st["zero_rate"]}%</td></tr>')
    p.append('</tbody></table></section>')

    p.append('<section id="stats-caso"><h2>5. Estatísticas por caso</h2>')
    p.append('<h3>5.1 Total bruto</h3>')
    p.append('<table><thead><tr><th>Caso</th><th class="num">Scans</th><th class="num">Total</th><th class="num">Média</th><th class="num">Mediana</th><th class="num">Desvio</th><th class="num">Mín</th><th class="num">Máx</th></tr></thead><tbody>')
    for caso, st in sorted(stats_caso.items(), key=lambda x: -x[1]["mean"]):
        p.append(f'<tr><td><strong>{esc(caso)}</strong></td><td class="num">{st["count"]}</td><td class="num">{st["sum"]}</td><td class="num">{st["mean"]}</td><td class="num">{st["median"]}</td><td class="num">{st["stdev"]}</td><td class="num">{st["min"]}</td><td class="num">{st["max"]}</td></tr>')
    p.append('</tbody></table>')
    p.append('<h3>5.2 Apenas alertas aplicacionais</h3>')
    p.append('<table><thead><tr><th>Caso</th><th class="num">Scans</th><th class="num">Total</th><th class="num">Média</th><th class="num">Mediana</th><th class="num">Desvio</th><th class="num">Mín</th><th class="num">Máx</th><th class="num">% sem alertas</th></tr></thead><tbody>')
    for caso, st in sorted(stats_caso_real.items(), key=lambda x: -x[1]["mean"]):
        p.append(f'<tr><td><strong>{esc(caso)}</strong></td><td class="num">{st["count"]}</td><td class="num">{st["sum"]}</td><td class="num">{st["mean"]}</td><td class="num">{st["median"]}</td><td class="num">{st["stdev"]}</td><td class="num">{st["min"]}</td><td class="num">{st["max"]}</td><td class="num">{st["zero_rate"]}%</td></tr>')
    p.append('</tbody></table></section>')

    p.append('<section id="cruzamentos"><h2>6. Cruzamentos multidimensionais</h2>')
    p.append('<p style="font-size:13px;color:#666">Médias usam apenas alertas aplicacionais (excluindo infra).</p>')

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
        p.append('<th>Média</th></tr></thead><tbody>')
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

    render_heatmap("6.1 IA × Linguagem", stats_ia_lang, "IA", "Linguagem", stats_ia_real)
    render_heatmap("6.2 IA × Caso", stats_ia_caso, "IA", "Caso", stats_ia_real)
    render_heatmap("6.3 Linguagem × Caso", stats_lang_caso, "Linguagem", "Caso", stats_lang_real)

    p.append('<p style="font-size:12px;color:#888">Cor: branco = 0, roxo claro = poucos, roxo escuro = muitos. n = scans.</p>')
    p.append("</section>")

    p.append('<section id="riscos"><h2>7. Análise por risco</h2>')
    p.append('<p style="font-size:13px;color:#666">Médias por scan, todos os alertas (com infra).</p>')
    for titulo, dim_data in [("7.1 Risco por IA", risk_by_ia),
                              ("7.2 Risco por linguagem", risk_by_lang),
                              ("7.3 Risco por caso", risk_by_caso)]:
        p.append(f'<h3>{titulo}</h3>')
        p.append('<table><thead><tr><th>Categoria</th><th class="num">HIGH (méd/total)</th><th class="num">MEDIUM (méd/total)</th><th class="num">LOW (méd/total)</th><th class="num">INFO (méd/total)</th></tr></thead><tbody>')
        for k, risks in sorted(dim_data.items()):
            p.append(f'<tr><td><strong>{esc(k)}</strong></td>'
                     f'<td class="num risk-high">{risks["high"]["mean"]} / {risks["high"]["sum"]}</td>'
                     f'<td class="num risk-medium">{risks["medium"]["mean"]} / {risks["medium"]["sum"]}</td>'
                     f'<td class="num risk-low">{risks["low"]["mean"]} / {risks["low"]["sum"]}</td>'
                     f'<td class="num risk-informational">{risks["info"]["mean"]} / {risks["info"]["sum"]}</td></tr>')
        p.append('</tbody></table>')
    p.append("</section>")

    p.append('<section id="cwes"><h2>8. Análise por CWE</h2>')
    p.append('<p style="font-size:13px;color:#666">CWEs apenas em alertas aplicacionais.</p>')
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

    p.append('<section id="detalhamento"><h2>9. Detalhamento por scan</h2>')
    by_combo = defaultdict(list)
    for a in alerts:
        by_combo[(a["caso"], a["ia"], a["linguagem"], a["scan_tipo"])].append(a)

    for combo in sorted(scans_realizados):
        caso, ia, lang, scan = combo
        als = by_combo.get(combo, [])
        risk_counts = Counter(a["risk"] for a in als)
        risk_summary = ", ".join(f"{r}: {n}" for r, n in risk_counts.most_common()) or "sem alertas"
        n_real = sum(1 for a in als if not a.get("is_infra"))
        n_infra = len(als) - n_real
        p.append('<details>')
        p.append(f'<summary>{esc(caso)} → {esc(ia)} / {esc(lang)} <span class="badge badge-scan">{esc(scan)}</span> — <strong>{len(als)} alertas</strong> ({n_real} aplicacionais + {n_infra} infra)</summary>')
        if als:
            p.append('<table><thead><tr><th>Risco</th><th>Conf</th><th>Alerta</th><th>Tipo</th><th>URL</th><th>Método</th><th>Param</th><th>Evidência</th><th>CWE</th></tr></thead><tbody>')
            for a in sorted(als, key=lambda x: (-int(x["risk_code"] or 0), x["alert_name"])):
                risk_class = f"risk-{a['risk'].lower()}"
                infra_badge = '<span class="badge badge-infra">infra</span>' if a.get("is_infra") else ''
                p.append(
                    f'<tr><td class="{risk_class}">{esc(a["risk"])}</td>'
                    f'<td>{esc(a["confidence"])}</td>'
                    f'<td>{esc(a["alert_name"])}</td>'
                    f'<td>{infra_badge}</td>'
                    f'<td class="url-cell">{esc(a["url"])}</td>'
                    f'<td>{esc(a["method"])}</td>'
                    f'<td>{esc(a["param"])}</td>'
                    f'<td class="url-cell">{esc(a["evidence"])}</td>'
                    f'<td>{("CWE-" + esc(a["cwe_id"])) if a["cwe_id"] else ""}</td></tr>'
                )
            p.append('</tbody></table>')
        else:
            p.append('<div class="empty">Sem alertas.</div>')
        p.append('</details>')
    p.append('</section>')

    p.append('<section id="notas"><h2>10. Notas metodológicas</h2>')
    p.append("""<div class="method-box">
<h3 style="margin-top:0">Como interpretar este relatório</h3>
<p><strong>1. Alertas de infra vs aplicacionais.</strong> Alertas de configuração de servidor (CSP, headers, HTTPS) aparecem em toda app e <em>não diferenciam IAs</em>. Use sempre a métrica "aplicacional" para comparar IAs.</p>
<p><strong>2. Cada instância (URL atacada) conta como ocorrência.</strong> Se o ZAP atacou 10 URLs com mesmo problema, registramos 10 instâncias.</p>
<p><strong>3. DAST analisa apenas o que rodou.</strong> Apps que crasharam no startup não aparecem. Compare "scans realizados" com o total possível (60) para entender cobertura.</p>
<p><strong>4. Severidade definida pelo ZAP.</strong> INFORMATIONAL geralmente é informativo. HIGH = vulnerabilidades exploráveis em runtime.</p>
<p><strong>5. DAST complementa SAST.</strong> SAST detecta padrões inseguros no código; DAST detecta comportamento inseguro em runtime. Veja o relatório combinado para visão integrada.</p>
<p><strong>6. Comparações dentro do mesmo caso/linguagem são as mais válidas.</strong> Mesmo cenário e stack significam que diferenças refletem qualidade do código gerado.</p>
</div>""")
    p.append("""<h3>Glossário</h3>
<table>
<tr><th>Termo</th><th>Significado</th></tr>
<tr><td>Alerta</td><td>Problema detectado pelo ZAP em uma URL atacada. Cada URL é uma instância separada.</td></tr>
<tr><td>Alerta aplicacional</td><td>Relacionado ao código gerado (não a config padrão do servidor).</td></tr>
<tr><td>Alerta de infra</td><td>Relacionado a configuração de servidor/framework (CSP, headers, HTTPS).</td></tr>
<tr><td>Risco</td><td>HIGH / MEDIUM / LOW / INFORMATIONAL conforme classificação do ZAP.</td></tr>
<tr><td>Confiança</td><td>CONFIRMED > HIGH > MEDIUM > LOW > FALSE POSITIVE.</td></tr>
<tr><td>CWE</td><td>Categoria padronizada de vulnerabilidade (ex: CWE-79 = XSS).</td></tr>
<tr><td>Scan</td><td>Execução do ZAP contra uma app (caso × ia × linguagem × tipo).</td></tr>
<tr><td>Baseline scan</td><td>Scan rápido (~1min), analisa apenas respostas observadas.</td></tr>
<tr><td>Full scan</td><td>Scan completo (~15-30min), envia ataques ativos.</td></tr>
</table>""")
    p.append('</section></main></body></html>')

    out.write_text("\n".join(p), encoding="utf-8")


def main():
    if not DAST_DIR.exists():
        print(f"Diretório não existe: {DAST_DIR}")
        sys.exit(0)

    print("Coletando alertas dos relatórios DAST...")
    alerts, scans_realizados = collect_all()
    print(f"  Total: {len(alerts)} alertas em {len(scans_realizados)} scans")
    n_infra = sum(1 for a in alerts if a.get("is_infra"))
    print(f"  Aplicacionais: {len(alerts) - n_infra} · Infra/config: {n_infra}")

    print("Calculando estatísticas...")
    per_scan = build_per_scan_totals(alerts, scans_realizados)

    detailed_csv = DAST_DIR / "report_detailed.csv"
    summary_csv  = DAST_DIR / "report_summary.csv"
    stats_csv    = DAST_DIR / "report_stats.csv"
    json_out     = DAST_DIR / "report.json"
    html_out     = DAST_DIR / "report.html"

    print(f"Gerando {detailed_csv.name}...")
    write_detailed_csv(alerts, detailed_csv)
    print(f"Gerando {summary_csv.name}...")
    write_summary_csv(per_scan, summary_csv)
    print(f"Gerando {stats_csv.name}...")
    write_stats_csv(per_scan, stats_csv)
    print(f"Gerando {json_out.name}...")
    write_json(alerts, json_out)
    print(f"Gerando {html_out.name}...")
    write_html(alerts, per_scan, scans_realizados, html_out)

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