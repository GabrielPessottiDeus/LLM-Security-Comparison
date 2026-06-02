#!/usr/bin/env python3
"""
generate_pdfs.py — Gera PDFs executivos dos relatórios SAST, DAST e combinado.

Diferença em relação ao HTML:
  - PDF é uma versão "executiva": estatísticas, conclusões, cruzamentos e tabelas
  - Detalhamento finding-por-finding fica APENAS no HTML/CSV (caso contrário o PDF
    teria 200-500 páginas)
  - PDFs gerados:
      reports/sast/report.pdf
      reports/dast/report.pdf
      reports/combined/report.pdf

Pré-requisitos:
  - Rodar antes: report_sast.py, report_dast.py, report_combined.py
  - Instalar WeasyPrint: pip install weasyprint --break-system-packages
  - No Fedora pode precisar: sudo dnf install -y pango cairo

Uso:
  python3 scripts/generate_pdfs.py             # gera os 3 PDFs
  python3 scripts/generate_pdfs.py sast        # gera só o SAST
  python3 scripts/generate_pdfs.py dast        # gera só o DAST
  python3 scripts/generate_pdfs.py combined    # gera só o combinado
"""
from __future__ import annotations
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Verifica dependência
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
except ImportError:
    print("ERRO: WeasyPrint não está instalado.", file=sys.stderr)
    print("Instale com: pip install weasyprint --break-system-packages", file=sys.stderr)
    print("No Fedora, se houver erro de libs do sistema: sudo dnf install -y pango cairo", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# CSS específico para impressão em PDF
# ============================================================================
PRINT_CSS = """
@page {
    size: A4;
    margin: 2cm 1.5cm;
    @top-right {
        content: "Comparativo LLMs · Segurança";
        font-size: 9pt;
        color: #666;
    }
    @bottom-right {
        content: counter(page) " / " counter(pages);
        font-size: 9pt;
        color: #666;
    }
    @bottom-left {
        content: string(report-title);
        font-size: 9pt;
        color: #666;
    }
}

@page :first {
    @top-right { content: none; }
    @bottom-right { content: none; }
    @bottom-left { content: none; }
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
    color: #1d1d1f;
    line-height: 1.4;
    font-size: 10pt;
}

/* Capa do relatório */
.capa {
    page-break-after: always;
    text-align: center;
    padding-top: 5cm;
}
.capa h1 {
    font-size: 28pt;
    margin: 0 0 12pt;
    color: #1d1d1f;
}
.capa h2 {
    font-size: 16pt;
    margin: 0 0 40pt;
    color: #666;
    font-weight: normal;
    border: none;
}
.capa .meta {
    margin-top: 60pt;
    font-size: 11pt;
    color: #666;
}
.capa .stats-line {
    margin: 8pt 0;
    font-size: 12pt;
    color: #1d1d1f;
}

/* Esconde elementos não-imprimíveis */
nav.toc, .empty, details summary { display: none; }
details { display: block; }
details > *:not(summary) { display: block; }

/* Quebras de página */
section {
    page-break-inside: avoid;
    margin-bottom: 16pt;
    break-inside: avoid;
}
section.page-break {
    page-break-before: always;
}
table { page-break-inside: auto; }
tr { page-break-inside: avoid; page-break-after: auto; }

/* Cabeçalhos */
header {
    string-set: report-title content();
    background: linear-gradient(135deg, #1d1d1f 0%, #2c3e50 100%);
    color: white;
    padding: 24pt 18pt;
    margin-bottom: 18pt;
}
header h1 { margin: 0; font-size: 22pt; }
header p { margin: 6pt 0 0; font-size: 10pt; opacity: 0.9; }

h2 {
    font-size: 16pt;
    border-bottom: 2pt solid #e5e5e7;
    padding-bottom: 6pt;
    margin: 18pt 0 10pt;
    color: #1d1d1f;
}
h3 {
    font-size: 13pt;
    margin: 14pt 0 6pt;
    color: #2c3e50;
}

/* Tabelas */
table {
    width: 100%;
    border-collapse: collapse;
    font-size: 9pt;
    margin: 6pt 0 10pt;
}
th, td {
    padding: 5pt 7pt;
    text-align: left;
    border-bottom: 1pt solid #e5e5e7;
    vertical-align: top;
}
th { background: #f5f5f7; font-weight: 600; }
td.num { text-align: right; font-variant-numeric: tabular-nums; }

/* Cards de estatísticas */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8pt;
    margin: 8pt 0 12pt;
}
.stat-card {
    background: #f5f5f7;
    padding: 8pt 10pt;
    border-radius: 4pt;
    border-left: 3pt solid #ccc;
}
.stat-card .label {
    font-size: 7pt;
    text-transform: uppercase;
    color: #666;
    letter-spacing: 0.3pt;
    font-weight: 600;
}
.stat-card .value {
    font-size: 18pt;
    font-weight: 700;
    margin-top: 2pt;
}
.stat-card.high { border-left-color: #d32f2f; }
.stat-card.medium { border-left-color: #f57c00; }
.stat-card.low { border-left-color: #1976d2; }
.stat-card.info { border-left-color: #757575; }

/* Severidades / riscos */
.sev-high, .risk-high, .sev-error { color: #d32f2f; font-weight: 600; }
.sev-medium, .risk-medium, .sev-warning { color: #f57c00; font-weight: 600; }
.sev-low, .risk-low, .sev-info { color: #1976d2; font-weight: 600; }
.risk-informational { color: #757575; }

/* Caixas de conclusão e notas */
.conclusao {
    background: #fffde7;
    border-left: 3pt solid #fbc02d;
    padding: 8pt 12pt;
    margin: 6pt 0;
    page-break-inside: avoid;
}
.conclusao .titulo {
    font-weight: 700;
    font-size: 9pt;
    color: #5d4037;
    margin-bottom: 3pt;
    text-transform: uppercase;
}
.conclusao .texto { font-size: 10pt; }
.conclusao .nota { font-size: 8pt; color: #888; margin-top: 4pt; font-style: italic; }

.warning-box {
    background: #fff3e0;
    border-left: 3pt solid #ff9800;
    padding: 8pt 12pt;
    margin: 8pt 0;
    font-size: 9pt;
}
.method-box {
    background: #e3f2fd;
    border-left: 3pt solid #1976d2;
    padding: 8pt 12pt;
    margin: 8pt 0;
    font-size: 9pt;
}
.method-box h3 { margin-top: 0; font-size: 11pt; }

/* Badges */
.badge {
    display: inline-block;
    padding: 1pt 6pt;
    border-radius: 8pt;
    font-size: 8pt;
    font-weight: 600;
}
.badge-tool { background: #e3f2fd; color: #1565c0; }
.badge-cwe { background: #fce4ec; color: #c2185b; }
.badge-scan { background: #ede7f6; color: #6a1b9a; }
.badge-cross { background: #e8f5e9; color: #2e7d32; }
.badge-infra { background: #eceff1; color: #455a64; }

/* Heatmap */
.heatmap td { text-align: center; font-size: 8pt; }
.heatmap .h0 { background: #f5f5f7; color: #666; }
.heatmap .h1 { background: #fff3e0; }
.heatmap .h2 { background: #ffe0b2; }
.heatmap .h3 { background: #ffcc80; }
.heatmap .h4 { background: #ffb74d; color: white; }
.heatmap .h5 { background: #ff9800; color: white; }
.heatmap .h6 { background: #f57c00; color: white; }

/* Rankings */
.rank-1 { background: #e8f5e9; }
.rank-2 { background: #fff8e1; }
.rank-3 { background: #ffebee; }

/* Esconde a seção de detalhamento (muito longa pra PDF) */
section#detalhamento { display: none; }
section#detalhamento * { display: none; }

/* Cores de cabeçalho diferentes por relatório */
header.dast {
    background: linear-gradient(135deg, #6a1b9a 0%, #4a148c 100%);
}
header.combined {
    background: linear-gradient(135deg, #1d1d1f 0%, #6a1b9a 100%);
}

/* Pequenos ajustes em rodapé/notas */
p { margin: 4pt 0; }
small { font-size: 8pt; color: #888; }
code { background: #f5f5f7; padding: 1pt 4pt; border-radius: 2pt; font-size: 8pt; }
.url-cell { font-size: 7pt; word-break: break-all; }
"""


# ============================================================================
# Geração
# ============================================================================

def add_cover_page(html_content: str, title: str, subtitle: str, report_type: str) -> str:
    """Injeta uma capa antes do conteúdo principal."""
    from datetime import datetime
    data_hoje = datetime.now().strftime("%d de %B de %Y")

    cover = f"""
<div class="capa">
    <h1>{title}</h1>
    <h2>{subtitle}</h2>
    <div class="meta">
        <div class="stats-line"><strong>Comparativo de Vulnerabilidades</strong></div>
        <div class="stats-line">Código gerado por ChatGPT × Gemini × Claude</div>
        <div class="stats-line">5 casos de teste × 4 linguagens</div>
        <br>
        <div>Gerado em {data_hoje}</div>
    </div>
</div>
"""

    # Injeta o body — adiciona classe no header para colorir conforme o tipo
    if "<body>" in html_content:
        html_content = html_content.replace("<body>", "<body>" + cover, 1)

    # Marca o header com a classe correta para CSS
    if report_type in ("dast", "combined"):
        html_content = html_content.replace("<header>", f'<header class="{report_type}">', 1)

    return html_content


def generate_pdf(html_path: Path, pdf_path: Path, title: str, subtitle: str, report_type: str):
    """Lê HTML, ajusta para impressão, gera PDF."""
    if not html_path.exists():
        print(f"  AVISO: HTML não existe: {html_path}", file=sys.stderr)
        print(f"  Rode primeiro: python3 scripts/report_{report_type}.py", file=sys.stderr)
        return False

    html_content = html_path.read_text(encoding="utf-8")

    # Remove tag <style> existente do HTML (vamos usar nosso CSS de impressão)
    import re
    html_content = re.sub(r"<style>.*?</style>", "", html_content, flags=re.DOTALL)

    # Adiciona capa
    html_content = add_cover_page(html_content, title, subtitle, report_type)

    print(f"  Renderizando PDF (pode demorar alguns segundos)...")
    font_config = FontConfiguration()
    HTML(string=html_content, base_url=str(html_path.parent)).write_pdf(
        str(pdf_path),
        stylesheets=[CSS(string=PRINT_CSS, font_config=font_config)],
        font_config=font_config,
    )
    size_kb = pdf_path.stat().st_size // 1024
    print(f"  ✓ Gerado: {pdf_path} ({size_kb} KB)")
    return True


# ============================================================================
# Main
# ============================================================================

REPORTS = {
    "sast": {
        "html": ROOT / "reports" / "sast" / "report.html",
        "pdf":  ROOT / "reports" / "sast" / "report.pdf",
        "title": "Relatório SAST",
        "subtitle": "Análise Estática de Vulnerabilidades em Código Gerado por LLMs",
        "type": "sast",
    },
    "dast": {
        "html": ROOT / "reports" / "dast" / "report.html",
        "pdf":  ROOT / "reports" / "dast" / "report.pdf",
        "title": "Relatório DAST",
        "subtitle": "Análise Dinâmica (OWASP ZAP) de Vulnerabilidades em Apps Geradas por LLMs",
        "type": "dast",
    },
    "combined": {
        "html": ROOT / "reports" / "combined" / "report.html",
        "pdf":  ROOT / "reports" / "combined" / "report.pdf",
        "title": "Relatório Combinado",
        "subtitle": "Visão Integrada SAST + DAST",
        "type": "combined",
    },
}


def main():
    args = sys.argv[1:]
    if not args:
        targets = list(REPORTS.keys())
    else:
        targets = []
        for arg in args:
            if arg not in REPORTS:
                print(f"ERRO: '{arg}' não é um relatório válido. Opções: sast, dast, combined", file=sys.stderr)
                sys.exit(1)
            targets.append(arg)

    print(f"Gerando PDFs: {', '.join(targets)}")
    print()

    sucessos, falhas = 0, 0
    for name in targets:
        cfg = REPORTS[name]
        print(f"[{name.upper()}]")
        if generate_pdf(cfg["html"], cfg["pdf"], cfg["title"], cfg["subtitle"], cfg["type"]):
            sucessos += 1
        else:
            falhas += 1
        print()

    print(f"Concluído: {sucessos} sucesso(s), {falhas} falha(s).")
    if sucessos > 0:
        print()
        print("PDFs gerados:")
        for name in targets:
            cfg = REPORTS[name]
            if cfg["pdf"].exists():
                print(f"  {cfg['pdf']}")


if __name__ == "__main__":
    main()