"""
Arizona Datacenter Heat Analysis v2 - Motor analítico / pipeline completo

Ponto de entrada único do projeto. Rode sempre:

    python main.py

Ordem de execução:
  1. analysis_v2.py         — motor analítico: modelo DiD + results_v2.json
  2. generate_report_v2.py  — relatório PDF (LST absoluta 2025)
  3. generate_heatmap_v2.py — mapa de calor PNG (Landsat LST)
  4. generate_background.py — imagem RGB de fundo para o frontend
"""

import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))

# O motor analítico é o núcleo do projeto, então é importado e chamado
# em processo (não como subprocesso), é ele que dá sentido ao resto.
import analysis_v2


def run_analise():
    """Roda o motor analítico: o modelo Diferenças-em-Diferenças (DiD).

    Lê os CSVs do GEE, calcula o IHI, ajusta o modelo, decompõe a anomalia
    térmica e exporta data/results_v2.json (consumido pelo frontend).
    """
    print("\n" + "=" * 60)
    print("  [1/4] Motor analítico — modelo DiD (analysis_v2.py)")
    print("=" * 60)
    analysis_v2.main()


def run_artefatos():
    """Gera os artefatos visuais a partir dos dados do GEE.

    Cada script roda isolado (subprocesso) porque usa matplotlib/rasterio e
    grava arquivos pesados; assim a falha de um é reportada com seu código
    de saída sem derrubar o processo principal antes da hora.
    """
    scripts = [
        ("[2/4] Relatório PDF", BASE / "generate_report_v2.py"),
        ("[3/4] Mapa de calor", BASE / "generate_heatmap_v2.py"),
        ("[4/4] Fundo RGB",     BASE / "generate_background.py"),
    ]
    for rotulo, script in scripts:
        print("\n" + "=" * 60)
        print(f"  {rotulo} — {script.name}")
        print("=" * 60)
        result = subprocess.run([sys.executable, str(script)], check=False)
        if result.returncode != 0:
            print(f"\n[ERRO] {script.name} falhou (código {result.returncode})")
            sys.exit(result.returncode)


def main():
    run_analise()
    run_artefatos()

    print("\n" + "=" * 60)
    print("  Pipeline v2 concluído.")
    print("  Modelo    : arizona-heat-analysis/data/results_v2.json")
    print("  Relatório : arizona-heat-analysis/data/relatorio_v2.pdf")
    print("  Frontend  : cd frontend_v2 && python -m http.server 8766")
    print("=" * 60)


if __name__ == "__main__":
    main()
