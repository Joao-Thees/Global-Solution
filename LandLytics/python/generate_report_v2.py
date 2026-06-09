"""
Arizona Datacenter Heat Analysis v2 - Relatório PDF (2025)
Compara LST absoluta (Landsat) entre:
  - CyrusOne Phoenix Datacenter (dc_demarcado)
  - Área Verde adjacente (area_verde)
Objetivo: corroborar achados de TechXplore/2026-05 sobre aquecimento
causado por datacenters em Phoenix, AZ.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages

sys.path.insert(0, str(Path(__file__).parent))
import config

ANO      = 2025
ZONA     = "sitio"
REF_URL  = "techxplore.com/news/2026-05-centers-nearby-temperatures-degrees-phoenix"


def carregar_dados():
    path = Path(config.DADOS_SAT_CSV_V2)
    if not path.exists():
        raise FileNotFoundError(f"CSV não encontrado: {path}")

    df = pd.read_csv(str(path))
    df = df[(df["year"] == ANO) & (df["zone"] == ZONA)].copy()

    if df.empty:
        anos = sorted(pd.read_csv(str(path))["year"].unique())
        raise ValueError(f"Sem dados para ano={ANO}, zone={ZONA}. Anos disponíveis: {anos}")

    return df


def calcular_stats(arr):
    arr = arr[~np.isnan(arr)]
    return {
        "n":       int(len(arr)),
        "media":   round(float(np.mean(arr)),   2),
        "mediana": round(float(np.median(arr)), 2),
        "desvio":  round(float(np.std(arr)),    2),
        "minimo":  round(float(np.min(arr)),    2),
        "maximo":  round(float(np.max(arr)),    2),
    }


def k_to_c(k):
    return round(k - 273.15, 2)


def k_to_f(k_diff):
    return round(k_diff * 9 / 5, 2)


def gerar_pdf(stats_dc, stats_verde, n_cenas):
    diferenca_k = round(stats_dc["media"] - stats_verde["media"], 2)
    diferenca_c = diferenca_k
    diferenca_f = k_to_f(diferenca_k)
    sinal       = "+" if diferenca_k >= 0 else ""

    out_path = str(Path(config.RESULTS_DIR) / "relatorio_v2.pdf")

    with PdfPages(out_path) as pdf:
        fig, ax = plt.subplots(figsize=(12, 9))
        ax.axis("off")
        ax.set_title(
            f"Impacto Térmico de Datacenter — Phoenix, AZ  |  {ANO}",
            fontsize=14, fontweight="bold", pad=20
        )

        linhas = [
            f"ANÁLISE DE TEMPERATURA SUPERFICIAL (LST) — LANDSAT / GEE",
            f"{'─' * 68}",
            f"Região       : Phoenix, Arizona",
            f"Fonte        : Landsat 8/9 via Google Earth Engine",
            f"Ano          : {ANO}   |   Zona: {ZONA}",
            f"Observações  : {n_cenas} cenas Landsat por site",
            f"{'─' * 68}",
            f"",
            f"LST MÉDIA ABSOLUTA (média das {n_cenas} cenas de {ANO})",
            f"",
            f"  CyrusOne Phoenix Datacenter",
            f"    {stats_dc['media']:.2f} K  =  {k_to_c(stats_dc['media']):.2f} °C",
            f"    Mediana: {stats_dc['mediana']:.2f} K  |  Desvio: ±{stats_dc['desvio']:.2f} K",
            f"    Min: {stats_dc['minimo']:.2f} K  |  Max: {stats_dc['maximo']:.2f} K",
            f"    n = {stats_dc['n']} observações",
            f"",
            f"  Área Verde Adjacente",
            f"    {stats_verde['media']:.2f} K  =  {k_to_c(stats_verde['media']):.2f} °C",
            f"    Mediana: {stats_verde['mediana']:.2f} K  |  Desvio: ±{stats_verde['desvio']:.2f} K",
            f"    Min: {stats_verde['minimo']:.2f} K  |  Max: {stats_verde['maximo']:.2f} K",
            f"    n = {stats_verde['n']} observações",
            f"",
            f"{'─' * 68}",
            f"",
            f"  DIFERENÇA (Datacenter − Área Verde)",
            f"    {sinal}{diferenca_k:.2f} K  =  {sinal}{diferenca_c:.2f} °C  =  {sinal}{diferenca_f:.2f} °F",
            f"",
            f"{'─' * 68}",
            f"",
            f"CONTEXTO — Pesquisa de referência:",
            f"  '{REF_URL}'",
            f"  Metodologia: sensores de temperatura do ar em veículos",
            f"               (junho–outubro 2025, quatro datacenters, Phoenix AZ)",
            f"  Achado:      +1.3 a +1.6°F (~+0.7 a +0.9°C) de temperatura",
            f"               do ar a jusante dos datacenters",
            f"",
            f"COMPARAÇÃO:",
        ]

        if diferenca_k > 0:
            linhas += [
                f"  Este estudo (LST de superfície via satélite) encontrou",
                f"  {sinal}{diferenca_c:.2f}°C ({sinal}{diferenca_f:.2f}°F) de diferença entre o",
                f"  datacenter e a área verde adjacente em {ANO}.",
                f"",
                f"  LST tende a superar a temperatura do ar, especialmente",
                f"  em superfícies impermeáveis como telhados de datacenters.",
                f"  O resultado é coerente com os achados da pesquisa de referência.",
            ]
        else:
            linhas += [
                f"  A diferença observada foi de {sinal}{diferenca_c:.2f}°C ({sinal}{diferenca_f:.2f}°F).",
                f"  Resultado negativo pode indicar cobertura vegetal reduzida",
                f"  na área verde ou período de medição fora do pico de calor.",
            ]

        texto = "\n".join(linhas)
        ax.text(
            0.03, 0.97, texto,
            transform=ax.transAxes,
            fontsize=9.5, verticalalignment="top", fontfamily="monospace",
            bbox=dict(boxstyle="round,pad=0.9", facecolor="#f5f7fa", alpha=0.9)
        )

        d = pdf.infodict()
        d["Title"]   = f"Arizona Heat Analysis v2 — LST {ANO}"
        d["Subject"] = "CyrusOne Phoenix: LST datacenter vs área verde"

        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)

    print(f"[OK] Relatório salvo: {out_path}")
    return out_path


def main():
    print("=" * 65)
    print(f"  Arizona Heat Analysis v2 — LST absoluta {ANO} (zona: {ZONA})")
    print("=" * 65)

    print(f"\n>> Carregando dados do GEE (ano={ANO}, zone={ZONA})...")
    df = carregar_dados()
    n_cenas = df[df["trat"] == "dc"]["lst"].count()
    print(f"   {len(df)} observações carregadas ({n_cenas} por site)")

    lst_dc    = df[df["trat"] == "dc"]["lst"].values
    lst_verde = df[df["trat"] != "dc"]["lst"].values

    stats_dc    = calcular_stats(lst_dc)
    stats_verde = calcular_stats(lst_verde)

    diferenca = round(stats_dc["media"] - stats_verde["media"], 2)
    print(f"\n   Datacenter  : {stats_dc['media']:.2f} K  ({k_to_c(stats_dc['media']):.2f} °C)")
    print(f"   Área Verde  : {stats_verde['media']:.2f} K  ({k_to_c(stats_verde['media']):.2f} °C)")
    print(f"   Diferença   : {diferenca:+.2f} K  ({k_to_f(diferenca):+.2f} °F)")

    print("\n>> Gerando PDF...")
    gerar_pdf(stats_dc, stats_verde, n_cenas)
    print(f"\n  Pronto. Abra: LandLytics/data/relatorio_v2.pdf")


if __name__ == "__main__":
    main()
