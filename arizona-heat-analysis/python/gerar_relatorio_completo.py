"""
Gera um PDF com TUDO que foi realizado na sessão de trabalho sobre o projeto
arizona-heat-analysis: execução do pipeline V2, correções de conformidade
(C1–C5), implementação dos requisitos de FED e WD, entregáveis e verificações.

Saída: data/relatorio_completo_v2.pdf

Reutiliza a infraestrutura de layout (classe Page e paleta) de
gerar_relatorio_alteracoes.py.
"""

import json
import sys
from datetime import date
from pathlib import Path

from matplotlib.patches import Rectangle
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).parent))
import config
from gerar_relatorio_alteracoes import (
    Page, DARK, ACCENT, GREEN, AMBER, RED, GREY, TXT, LEFT, RIGHT,
)


def _model():
    try:
        d = json.load(open(config.RESULTS_JSON_V2, encoding="utf-8"))
        dec = d.get("decomposicao", [{}])[0]
        return {
            "ok": True,
            "n": d.get("n_obs"), "r2": d.get("r2"),
            "total": dec.get("total_anomalia"),
            "op": d.get("coeficientes", {}).get("operacao"),
            "p": d.get("coeficientes", {}).get("operacao_pval"),
        }
    except Exception:
        return {"ok": False}


def main():
    m = _model()
    hoje = date.today().strftime("%d/%m/%Y")
    out = str(Path(config.RESULTS_DIR) / "relatorio_completo_v2.pdf")
    footer = f"Relatório de trabalho · {hoje}"

    with PdfPages(out) as pdf:
        st = {"p": None}

        def new_page(title=None):
            if st["p"]:
                st["p"].close()
            st["p"] = Page(pdf, footer)
            if title:
                st["p"].band(title)

        def section(title):
            """Banda de seção com quebra de página se faltar espaço."""
            p = st["p"]
            if p.space_left() < 0.14:
                new_page()
                p = st["p"]
            p.gap(0.004)
            p.band(title)

        def block(title, body, files=None):
            p = st["p"]
            if p.space_left() < 0.16:
                new_page("(continuação)")
                p = st["p"]
            p.para(title, size=10.5, bold=True, color=DARK)
            p.para(body, size=9.3)
            if files:
                p.para("Arquivos: " + files, size=8.5, color=GREY)
            p.gap(0.006)

        # ───────────────────────── PÁGINA 1 ─────────────────────────
        p = Page(pdf, footer)
        st["p"] = p
        p.ax.add_patch(Rectangle((0, 0.905), 1, 0.095, facecolor=DARK,
                                 edgecolor="none", transform=p.ax.transAxes))
        p.ax.add_patch(Rectangle((0, 0.902), 1, 0.004, facecolor=ACCENT,
                                 edgecolor="none", transform=p.ax.transAxes))
        p.ax.text(LEFT, 0.965, "RELATÓRIO DE TRABALHO", color="white",
                  fontsize=20, fontweight="bold", va="center", transform=p.ax.transAxes)
        p.ax.text(LEFT, 0.928, "Tudo que foi realizado no projeto arizona-heat-analysis  ·  "
                  "Global Solution 2026  ·  FIAP", color="#cfd8e3", fontsize=9.5,
                  va="center", transform=p.ax.transAxes)
        p.y = 0.875

        p.para(f"Projeto: arizona-heat-analysis (pipeline V2 + frontend_v2)   |   "
               f"Data: {hoje}   |   Grupo: João Thees (RM572829), Caio Viana "
               f"(RM570634), Miguel Menezes (RM573825).", size=9, color=GREY)
        p.gap(0.004)
        p.para("Este relatório consolida toda a sessão de trabalho: execução do "
               "pipeline de dados V2, correção dos bloqueadores apontados no "
               "Relatório de Conformidade FED + WD, e a implementação completa dos "
               "requisitos inegociáveis das duas disciplinas. As constatações foram "
               "verificadas empiricamente (HTTP local, validação de JSON, contagem "
               "de landmarks/aria/@media e checagem de sintaxe JS).", size=9.5)
        p.gap(0.008)

        # Sumário em tabela
        p.band("Sumário do que foi feito")
        rows = [
            ("Pipeline V2", "Baixados os GeoTIFFs do Drive; main.py gerou relatório PDF, "
             "heatmap real e fundo RGB.", GREEN),
            ("Correções C1–C5", "Caminhos, JSON inválido (NaN), imagens no Git, IDs do "
             "geojson; C5 já existia.", GREEN),
            ("Front-End Design", "Semântica, acessibilidade WCAG AA, componentes, "
             "responsividade, narrativa de missão, moodboard, integrantes.", GREEN),
            ("Web Development", "Telemetria em tempo real (setInterval), BOM, formulário "
             "validado, Manual de Interatividade.", GREEN),
            ("Documentação", "Dois PDFs: relatório de alterações e este relatório "
             "completo (scripts reaproveitáveis).", GREEN),
        ]
        for t, d, c in rows:
            y0 = p.y
            p.ax.add_patch(Rectangle((LEFT + 0.012, y0 - 0.004), 0.022, 0.022,
                           facecolor=c, edgecolor="none", transform=p.ax.transAxes))
            p.ax.text(LEFT + 0.05, y0, t, fontsize=9.5, fontweight="bold",
                      color=DARK, va="top", transform=p.ax.transAxes)
            import textwrap
            lines = textwrap.wrap(d, 74) or [""]
            for i, ch in enumerate(lines):
                p.ax.text(LEFT + 0.05, y0 - 0.018 - i * 0.016, ch, fontsize=9,
                          color=TXT, va="top", transform=p.ax.transAxes)
            p.y = y0 - 0.018 - len(lines) * 0.016 - 0.006

        p.gap(0.006)
        if m["ok"]:
            p.para(f"Estado do modelo: results_v2.json VÁLIDO — n={m['n']} obs, "
                   f"R²={m['r2']}, anomalia total CyrusOne={m['total']} K.",
                   size=8.8, color=GREY)

        # ──────────────── 1. PIPELINE V2 ────────────────
        new_page("1. Pipeline de dados V2 executado")
        st["p"].para("O pipeline transforma os dados do Google Earth Engine em "
                     "relatório, mapa de calor e fundo do mapa.", size=9.3, color=GREY)
        st["p"].gap(0.004)
        block("Download dos GeoTIFFs (Drive)",
              "Os arquivos pesados (delta_lst_v2.tif, lst_ops_v2.tif, rgb_background.tif, "
              "20–60 MB cada) não vêm no repositório; foram baixados do Drive e colocados "
              "em data/gee_exports_v2/, conforme o README.",
              "data/gee_exports_v2/*.tif")
        block("Execução de main.py",
              "Rodou em sequência: generate_report_v2.py (relatório PDF), "
              "generate_heatmap_v2.py (heatmap real a partir do TIF, range −0,75 a "
              "+2,88 K) e generate_background.py (fundo RGB Sentinel/Landsat).",
              "data/relatorio_v2.pdf, data/heatmap_v2.png, data/rgb_background.png")
        block("Resultado do relatório (LST 2025, zona sítio, 79 cenas/site)",
              "Datacenter 310,19 K (37,04 °C); Área verde 306,37 K (33,22 °C); "
              "diferença +3,82 K (+6,88 °F) — datacenter mais quente, coerente com a "
              "pesquisa de referência de Phoenix.")

        # ──────────────── 2. CORREÇÕES C1–C5 ────────────────
        new_page("2. Correções de conformidade (C1–C5)")
        block("C1 · Caminhos ../data",
              "README corrigido para servir a partir da raiz arizona-heat-analysis "
              "(não de frontend_v2). Antes, dava 404 em todos os dados; agora todos os "
              "endpoints retornam 200.", "README.md")
        block("C2 · results_v2.json inválido (NaN)",
              "Alinhadas as chaves de config.SITES aos IDs reais (cyrusone/area_verde), "
              "adicionado sanitizador NaN→null e allow_nan=False; forçado UTF-8 no stdout. "
              "JSON agora válido, 0 NaN, decomposição com número real.",
              "python/config.py, python/analysis_v2.py, data/results_v2.json")
        block("C3 · Imagens do mapa no Git",
              "Versionados os 2 PNGs leves que o frontend renderiza (~10 MB) via negação "
              "no .gitignore, mantendo os *.tif pesados ignorados. Mapa passa a renderizar "
              "ao clonar do GitHub.", ".gitignore (raiz e do subprojeto)")
        block("C4 · sites.geojson e IDs",
              "Reescrito o geojson com os polígonos cyrusone (DC) e area_verde; IDs e "
              "cores unificados em config.py, chartsV2.js, mainV2.js e results_v2.json.",
              "data/sites.geojson, python/config.py, frontend_v2/js/mainV2.js")
        block("C5 · Repositório",
              "Verificado: existe UM repositório com remote no GitHub "
              "(Joao-Thees/Global-Solution). O achado do relatório estava desatualizado — "
              "nenhuma ação necessária.")

        # ──────────────── 3. FRONT-END DESIGN ────────────────
        new_page("3. Front-End Design (FED) — requisitos inegociáveis")
        block("HTML semântico",
              "indexV2.html reescrito com header, nav, main, aside, section (×8) e footer; "
              "fim do 'div soup'; hierarquia de títulos h1→h2→h3.")
        block("Acessibilidade (WCAG AA)",
              "Contraste mínimo AA (tokens --text-muted/--text-dim), 40 aria-*/role, "
              "<label for> em todos os campos, skip link, foco visível e "
              "prefers-reduced-motion. 0 estilos inline no HTML.")
        block("Componentes que o edital cita",
              "Alerta crítico, tabela de telemetria, botões e formulário — todos "
              "estilizados por classe no CSS.")
        block("Narrativa espacial / usuário e tarefa",
              "UI reposicionada como painel de observação orbital. Usuário: Analista de "
              "Observação da Terra; tarefa crítica: detectar excesso térmico do datacenter "
              "e emitir alerta.")
        block("Entregáveis",
              "integrantes.txt (3 integrantes com RM), moodboard com análise crítica de "
              "referências, e documentação FED no README.",
              "integrantes.txt, frontend_v2/assets/moodboard.html, README.md")

        # ──────────────── 4. WEB DEVELOPMENT ────────────────
        new_page("4. Web Development (WD) — requisitos inegociáveis")
        block("Telemetria em tempo real (BOM)",
              "Novo telemetryV2.js: setInterval simula a chegada de leituras LST do "
              "satélite a cada 2,5 s, atualiza a tabela e alterna o estado seguro→alerta.",
              "frontend_v2/js/telemetryV2.js")
        block("Alerta de emergência",
              "Quando o Δ (Datacenter − Área verde) ultrapassa o limiar, mostra banner "
              "vermelho (role=alert, aria-live) sobre o mapa e dispara window.alert único "
              "por episódio.")
        block("Controles e BOM",
              "Botões: forçar varredura, reconectar (setTimeout), armar/desarmar (confirm). "
              "Estado da conexão via navigator.onLine + eventos online/offline.")
        block("Formulário com validação",
              "Configuração do limiar de alerta com validação numérica (0–20 °C), "
              "mensagem de erro e aria-invalid.")
        block("Manual de Interatividade",
              "Seção no README descrevendo onde clicar e o que acontece na tela.",
              "README.md")

        # ──────────────── 5. VERIFICAÇÕES ────────────────
        new_page("5. Verificações realizadas e estado final")
        st["p"].para("Checagens empíricas executadas durante o trabalho:", size=9.3,
                     color=GREY)
        st["p"].gap(0.004)
        checks = [
            "Endpoints HTTP (servidor local 8766): indexV2.html, CSS, JS, JSON, PNGs, "
            "geojson e moodboard retornam 200.",
            "results_v2.json válido por json.load, com 0 ocorrências de NaN.",
            "Coerência de IDs (cyrusone/area_verde) nos 5 arquivos: config, geojson, "
            "chartsV2.js, mainV2.js e results_v2.json.",
            "Estrutura HTML: header/nav/main/aside/section/footer presentes; 40 aria-*; "
            "label for nos campos; skip link.",
            "Responsividade: 4 blocos @media; sintaxe dos 3 arquivos JS sem erros "
            "(node --check).",
        ]
        for c in checks:
            st["p"].para("• " + c, size=9.2, indent=0.0)
            st["p"].gap(0.002)

        section("Ressalva analítica (não é bug)")
        if m["ok"]:
            st["p"].para(f"O coeficiente da operação dos servidores é {m['op']} K com "
                         f"p-valor {m['p']:.3g} (acima de 0,05). O modelo DiD acusa "
                         "multicolinearidade (poucos sites/zonas). O sinal é o esperado, "
                         "mas o efeito não é estatisticamente significativo — vale como "
                         "apoio, não como prova isolada. A diferença bruta de LST de 2025 "
                         "permanece válida.", size=9.3)

        # ──────────────── 6. ARQUIVOS ────────────────
        new_page("6. Arquivos alterados e criados")
        st["p"].para("Alterados", size=10, bold=True, color=DARK)
        for f in ["README.md", "frontend_v2/indexV2.html", "frontend_v2/css/styleV2.css",
                  "frontend_v2/js/mainV2.js", "data/sites.geojson", "data/results_v2.json",
                  "python/config.py", "python/analysis_v2.py", ".gitignore (raiz e subprojeto)"]:
            st["p"].para("• " + f, size=9, indent=0.0); st["p"].gap(0.001)
        st["p"].gap(0.006)
        st["p"].para("Criados", size=10, bold=True, color=DARK)
        for f in ["frontend_v2/js/telemetryV2.js", "frontend_v2/assets/moodboard.html",
                  "integrantes.txt", "python/gerar_relatorio_alteracoes.py",
                  "python/gerar_relatorio_completo.py",
                  "data/relatorio_alteracoes_v2.pdf", "data/relatorio_completo_v2.pdf"]:
            st["p"].para("• " + f, size=9, indent=0.0); st["p"].gap(0.001)
        st["p"].gap(0.006)
        st["p"].para("Saídas do pipeline (regeneráveis)", size=10, bold=True, color=DARK)
        for f in ["data/relatorio_v2.pdf", "data/heatmap_v2.png (versionado)",
                  "data/rgb_background.png (versionado)", "data/heatmap_bounds_v2.json",
                  "data/rgb_bounds.json"]:
            st["p"].para("• " + f, size=9, indent=0.0); st["p"].gap(0.001)

        st["p"].close()

    print(f"[OK] Relatório completo salvo: {out}")
    return out


if __name__ == "__main__":
    main()
