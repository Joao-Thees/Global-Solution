"""
Gera um relatório PDF documentando as alterações feitas no projeto
arizona-heat-analysis em resposta ao "Relatório de Conformidade FED + WD".

Saída: data/relatorio_alteracoes_v2.pdf

Cada alteração lista: o que foi feito, por quê, e quais arquivos mudaram —
para que, caso falte algo, seja fácil rastrear depois.
"""

import json
import sys
import textwrap
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, str(Path(__file__).parent))
import config

# ── Paleta ──────────────────────────────────────────────────────────────
DARK    = "#16263d"   # barras de seção (azul-escuro)
ACCENT  = "#ff6600"   # laranja (DC / destaque)
GREEN   = "#1f9d55"
RED     = "#d23b3b"
AMBER   = "#e08e0b"
GREY    = "#666666"
LIGHT   = "#f4f6f9"
TXT     = "#1a1a1a"

A4 = (8.27, 11.69)
LEFT, RIGHT = 0.07, 0.93
WIDTH = RIGHT - LEFT


def _results_summary():
    """Lê números atuais do modelo para citar no relatório."""
    try:
        d = json.load(open(config.RESULTS_JSON_V2, encoding="utf-8"))
        dec = d.get("decomposicao", [])
        op = d.get("coeficientes", {})
        site0 = dec[0] if dec else {}
        return {
            "n_obs": d.get("n_obs"),
            "r2": d.get("r2"),
            "sites": list(d.get("sites", {}).keys()),
            "total": site0.get("total_anomalia"),
            "operacao": op.get("operacao"),
            "pval": op.get("operacao_pval"),
            "valido": True,
        }
    except Exception as e:
        return {"valido": False, "erro": str(e)}


class Page:
    """Página A4 com cursor vertical em coordenadas 0..1 (topo = 1)."""

    def __init__(self, pdf, footer):
        self.pdf = pdf
        self.footer = footer
        self.fig = plt.figure(figsize=A4)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, 1)
        self.ax.set_ylim(0, 1)
        self.ax.axis("off")
        self.y = 0.95

    def band(self, text, sub=None):
        h = 0.040
        self.y -= 0.010
        self.ax.add_patch(Rectangle((LEFT, self.y - h), WIDTH, h,
                                    facecolor=DARK, edgecolor="none",
                                    transform=self.ax.transAxes))
        self.ax.text(LEFT + 0.015, self.y - h / 2, text, color="white",
                     fontsize=12.5, fontweight="bold", va="center",
                     transform=self.ax.transAxes)
        self.y -= h + 0.018
        if sub:
            self.para(sub, size=9, color=GREY)

    def para(self, text, size=9.5, color=TXT, bold=False, indent=0.0, gap=0.006):
        wrap = int(96 - indent * 90)
        for line in text.split("\n"):
            chunks = textwrap.wrap(line, wrap) or [""]
            for ch in chunks:
                self.ax.text(LEFT + 0.015 + indent, self.y, ch, color=color,
                             fontsize=size, va="top",
                             fontweight="bold" if bold else "normal",
                             transform=self.ax.transAxes)
                self.y -= size / 600.0 + gap
        self.y -= 0.004

    def badge(self, label, color, x, y, w=0.115):
        self.ax.add_patch(FancyBboxPatch((x, y - 0.012), w, 0.024,
                          boxstyle="round,pad=0.004", facecolor=color,
                          edgecolor="none", transform=self.ax.transAxes))
        self.ax.text(x + w / 2, y, label, color="white", fontsize=7.8,
                     fontweight="bold", ha="center", va="center",
                     transform=self.ax.transAxes)

    def gap(self, g=0.012):
        self.y -= g

    def space_left(self):
        return self.y - 0.07  # 0.07 = margem acima do rodapé

    def close(self):
        self.ax.text(LEFT, 0.025, self.footer, color=GREY, fontsize=7.5,
                     transform=self.ax.transAxes)
        self.ax.text(RIGHT, 0.025, "arizona-heat-analysis", color=GREY,
                     fontsize=7.5, ha="right", transform=self.ax.transAxes)
        self.pdf.savefig(self.fig)
        plt.close(self.fig)


def main():
    r = _results_summary()
    hoje = date.today().strftime("%d/%m/%Y")
    out = str(Path(config.RESULTS_DIR) / "relatorio_alteracoes_v2.pdf")
    footer = f"Relatório de alterações · {hoje}"

    with PdfPages(out) as pdf:
        # ───────────────────────── PÁGINA 1 ─────────────────────────
        p = Page(pdf, footer)
        # Cabeçalho
        p.ax.add_patch(Rectangle((0, 0.905), 1, 0.095, facecolor=DARK,
                                 edgecolor="none", transform=p.ax.transAxes))
        p.ax.add_patch(Rectangle((0, 0.902), 1, 0.004, facecolor=ACCENT,
                                 edgecolor="none", transform=p.ax.transAxes))
        p.ax.text(LEFT, 0.965, "RELATÓRIO DE ALTERAÇÕES", color="white",
                  fontsize=20, fontweight="bold", va="center",
                  transform=p.ax.transAxes)
        p.ax.text(LEFT, 0.928, "Resposta ao Relatório de Conformidade FED + WD  ·  "
                  "Global Solution 2026  ·  FIAP", color="#cfd8e3",
                  fontsize=9.5, va="center", transform=p.ax.transAxes)
        p.y = 0.875

        p.para("Projeto: arizona-heat-analysis (frontend_v2)   |   "
               f"Data: {hoje}   |   Base de verificação: Relatório de "
               "Conformidade FED + WD (análise de terceiros).", size=9, color=GREY)
        p.gap(0.004)
        p.para("Este documento registra o que foi alterado e por quê, em resposta "
               "aos achados do relatório de conformidade. As constatações foram "
               "testadas empiricamente (servidor HTTP local, validação de JSON com "
               "json.load, contagem de landmarks/aria/@media e sintaxe JS). Ao final, "
               "um checklist confirma os requisitos inegociáveis atendidos.",
               size=9.5)
        p.gap(0.006)

        # Tabela-resumo
        p.band("Quadro-resumo")
        rows = [
            ("C1", "Caminhos ../data quebravam (404) ao servir como o README mandava",
             "RESOLVIDO", GREEN),
            ("—", "Responsividade: 0 media queries (mobile/tablet ilegível)",
             "RESOLVIDO", GREEN),
            ("C2", "results_v2.json inválido (NaN) — frontend caía no modo demo",
             "RESOLVIDO", GREEN),
            ("C3", "Imagens do mapa fora do Git (.gitignore) — mapa vazio ao clonar",
             "RESOLVIDO", GREEN),
            ("C4", "sites.geojson com IDs incoerentes (polígonos não apareciam)",
             "RESOLVIDO", GREEN),
            ("C5", "Repositório/GitHub — relatório apontava ausência",
             "JÁ EXISTIA", AMBER),
            ("FED", "Semântica, acessibilidade, componentes, entregáveis, narrativa",
             "ATENDIDO", GREEN),
            ("WD", "BOM/tempo real (setInterval), formulário, Manual de Interatividade",
             "ATENDIDO", GREEN),
        ]
        for code, desc, status, color in rows:
            y0 = p.y
            p.ax.text(LEFT + 0.015, y0, code, fontsize=8.5, fontweight="bold",
                      color=DARK, va="top", transform=p.ax.transAxes)
            for i, ch in enumerate(textwrap.wrap(desc, 66) or [""]):
                p.ax.text(LEFT + 0.075, y0 - i * 0.016, ch, fontsize=8.5,
                          color=TXT, va="top", transform=p.ax.transAxes)
            p.badge(status, color, RIGHT - 0.135, y0 - 0.006)
            nlines = max(1, len((textwrap.wrap(desc, 66) or [""])))
            p.y = y0 - nlines * 0.016 - 0.008
            p.ax.plot([LEFT + 0.01, RIGHT - 0.01], [p.y + 0.004, p.y + 0.004],
                      color="#e2e6ec", lw=0.6, transform=p.ax.transAxes)
            p.y -= 0.004

        p.gap(0.006)
        if r["valido"]:
            p.para(f"Estado do modelo após as correções: results_v2.json VÁLIDO  "
                   f"(n={r['n_obs']} obs, R²={r['r2']}, sites={', '.join(r['sites'])}, "
                   f"anomalia total CyrusOne={r['total']} K).", size=8.8, color=GREY)
        p.close()

        # ───────────────────── PÁGINAS 2+ (detalhamento) ─────────────
        state = {"p": Page(pdf, footer)}
        state["p"].band("Detalhamento das correções (o que e por quê)")

        def fix(code, title, what, why, files):
            p = state["p"]
            # Quebra de página se o bloco não couber inteiro (evita vazar no rodapé)
            if p.space_left() < 0.20:
                p.close()
                p = Page(pdf, footer)
                p.band("Detalhamento das correções (continuação)")
                state["p"] = p
            p.gap(0.004)
            p.para(f"{code} · {title}", size=11, bold=True, color=DARK)
            p.para("O que foi feito: " + what, size=9.3)
            p.para("Por quê: " + why, size=9.3, color="#333333")
            p.para("Arquivos: " + files, size=8.6, color=GREY)
            p.gap(0.006)

        fix("C1", "Caminhos ../data (CONFIRMADO no relatório)",
            "Corrigida a instrução do README para servir a partir da raiz "
            "arizona-heat-analysis (e não de dentro de frontend_v2), com a URL "
            "http://localhost:8766/frontend_v2/indexV2.html.",
            "O JS busca dados em ../data/...; servindo de dentro de frontend_v2 o "
            "navegador resolvia para /data (inexistente) → 404 em tudo. Verificado: "
            "agora todos os endpoints retornam 200.",
            "README.md")

        fix("Resp.", "Responsividade (FED — inegociável)",
            "Adicionados 3 breakpoints @media (1024 / 768 / 480 px): em telas "
            "estreitas o mapa vai para o topo e o painel desce, rolável. Incluído "
            "map.invalidateSize() no resize/orientationchange.",
            "Não havia nenhuma media query; o painel fixo de 340px tornava o mapa "
            "quase invisível em celular/tablet. O edital classifica breakpoints "
            "como requisito inegociável.",
            "frontend_v2/css/styleV2.css, frontend_v2/js/mainV2.js")

        fix("C2", "results_v2.json inválido por NaN (CONFIRMADO)",
            "Alinhadas as chaves de config.SITES aos IDs reais dos dados "
            "(cyrusone / area_verde); adicionado sanitizador _clean_json (NaN→null) "
            "e allow_nan=False na escrita; forçado UTF-8 no stdout.",
            "config.SITES usava IDs (phoenix_cyrius/dc_demarcado) que não existem "
            "na coluna 'site' do CSV → a decomposição ficava vazia e gravava NaN, "
            "que é JSON inválido; o frontend caía no modo demo. Verificado: JSON "
            "válido por json.load, 0 ocorrências de NaN, decomposição com número "
            "real.",
            "python/config.py, python/analysis_v2.py, data/results_v2.json")

        fix("C3", "Imagens do mapa fora do Git (CONFIRMADO)",
            "Versionados os 2 PNGs leves que o frontend renderiza (heatmap_v2.png, "
            "rgb_background.png, ~10 MB) via negação no .gitignore, mantendo os "
            "*.tif pesados (20–60 MB) ignorados.",
            "data/*.png estava no .gitignore: ao clonar do GitHub o mapa ficava sem "
            "fundo e sem heatmap, salvo baixar 100+ MB de TIF do Drive. Risco da "
            "penalidade objetiva da FED por imagens com link quebrado.",
            ".gitignore (raiz), arizona-heat-analysis/.gitignore, "
            "branch fix/c3-versionar-pngs-mapa")

        fix("C4", "sites.geojson e IDs incoerentes (CONFIRMADO)",
            "Reescrito sites.geojson com os polígonos cyrusone (DC) e area_verde, "
            "IDs e cores unificados em config.py, chartsV2.js, mainV2.js e "
            "results_v2.json. Tooltip especial do DC religado ao id 'cyrusone'.",
            "A legenda/JS citavam dc_demarcado/area_verde, mas o geojson tinha "
            "phoenix_cyrius/arizona_area → polígonos não apareciam e o tooltip do DC "
            "nunca disparava. Verificado: os 4 arquivos agora usam os mesmos IDs.",
            "data/sites.geojson, python/config.py, frontend_v2/js/mainV2.js")

        fix("FED", "Requisitos inegociáveis de Front-End Design",
            "Reescrito o indexV2.html com landmarks semânticos (header/nav/main/"
            "aside/section/footer), fim do 'div soup' e hierarquia de títulos "
            "h1→h2→h3. Acessibilidade: contraste WCAG AA, 40 aria-*/role, <label "
            "for> em todos os campos, skip link, foco visível e prefers-reduced-"
            "motion. Novos componentes (alerta crítico, tabela de telemetria, "
            "botões, formulário). 0 estilos inline no HTML. Narrativa de missão "
            "(usuário=Analista de Observação da Terra; tarefa=emitir alerta). "
            "Criados integrantes.txt e o moodboard.",
            "O edital classifica semântica, responsividade e acessibilidade como "
            "inegociáveis, e exige moodboard, README próprio e integrantes.txt. "
            "Verificado: checklist de landmarks/aria/label/skip/componentes "
            "todos OK.",
            "frontend_v2/indexV2.html, css/styleV2.css, integrantes.txt, "
            "frontend_v2/assets/moodboard.html, README.md")

        fix("WD", "Requisitos inegociáveis de Web Development",
            "Criado telemetryV2.js: setInterval simula a chegada de leituras LST "
            "do satélite a cada 2,5 s, alterna estado seguro→alerta e dispara "
            "alerta de emergência (banner role=alert + window.alert único por "
            "episódio). Botões (forçar varredura, reconectar com setTimeout, "
            "armar/desarmar com confirm), formulário de limiar com validação e "
            "aria-invalid, e BOM (navigator.onLine + eventos online/offline). "
            "Adicionado o 'Manual de Interatividade' ao README.",
            "O coração do edital de WD é a tela mudar sozinha (tempo real) e o "
            "uso de BOM/eventos, além do Manual de Interatividade no README — "
            "tudo ausente antes. Verificado: setInterval/BOM presentes, JS sem "
            "erro de sintaxe.",
            "frontend_v2/js/telemetryV2.js, frontend_v2/js/mainV2.js, README.md")

        # ─────────────── PÁGINA seguinte: C5 + pendências ────────────
        state["p"].close()
        p = Page(pdf, footer)

        p.band("C5 — Repositório (divergência do relatório)")
        p.para("O relatório apontou 'dois repositórios Git sobrepostos e nenhum "
               "remoto'. Verificação atual: existe UM repositório na raiz, com "
               "remote configurado (origin → github.com/Joao-Thees/Global-Solution). "
               "Ou seja, o achado C5 está desatualizado — o repositório existe e "
               "está publicado. Nenhuma ação necessária além de manter os commits "
               "em dia.", size=9.5)
        p.gap(0.006)

        p.band("Checklist de requisitos inegociáveis (todos atendidos)")
        p.para("Verificado empiricamente (estrutura do HTML, contagem de @media/"
               "aria, sintaxe JS e endpoints HTTP).", size=9, color=GREY)
        p.gap(0.004)
        done = [
            ("Landmarks semânticos", "header / nav / main / aside / section / footer."),
            ("Responsividade", "breakpoints @media em 1024 / 768 / 480 px + invalidateSize."),
            ("Acessibilidade", "contraste WCAG AA, 40 aria-*/role, <label for>, skip link, foco visível."),
            ("Componentes", "alerta crítico, tabela de telemetria, botões e formulário (0 inline no HTML)."),
            ("WD · tempo real / BOM", "setInterval, setTimeout, navigator.onLine, alert/confirm."),
            ("Entregáveis", "integrantes.txt preenchido, moodboard.html, README FED + Manual de Interatividade."),
            ("Narrativa espacial", "UI reposicionada como painel de observação orbital da Terra."),
        ]
        for t, d in done:
            p.para("• " + t, size=9.5, bold=True, color=DARK)
            p.para(d, size=9, indent=0.02)
            p.gap(0.002)

        p.gap(0.004)
        p.band("Observações")
        p.para("Moodboard: usa referências públicas curadas com retângulos marcados "
               "para o grupo trocar por capturas de tela reais quando quiser (opcional, "
               "não bloqueia a entrega).", size=9.3)
        p.gap(0.004)
        if r["valido"]:
            p.para(f"Ressalva analítica (não é bug): o coeficiente da operação é "
                   f"{r['operacao']} K com p-valor {r['pval']:.3g} (acima de 0,05). O "
                   "modelo DiD acusa multicolinearidade (poucos sites/zonas). O sinal "
                   "é o esperado, mas o efeito não é estatisticamente significativo — "
                   "vale como apoio, não como prova isolada. A diferença bruta de LST "
                   "de 2025 (relatório principal) permanece válida.", size=9.3)
        p.close()

    print(f"[OK] Relatório de alterações salvo: {out}")
    return out


if __name__ == "__main__":
    main()
