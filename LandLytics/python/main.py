"""
Arizona Datacenter Heat Analysis v2 - Motor analítico / pipeline completo

Ponto de entrada único do projeto. Rode sempre:

    python main.py

Ordem de execução:
  0. config do frontend     — escreve js/config.js com o token Mapbox (os.getenv)
  1. analysis_v2.py         — motor analítico: modelo DiD + results_v2.json
  2. generate_report_v2.py  — relatório PDF (LST absoluta 2025)
  3. generate_heatmap_v2.py — mapa de calor PNG (Landsat LST)
  4. generate_background.py — imagem RGB de fundo para o frontend

Segredo: defina a variável de ambiente MAPBOX_TOKEN antes de rodar (ver README).
"""

import json
import os
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent
sys.path.insert(0, str(BASE))


def run_frontend_config():
    """Gera frontend_v2/js/config.js com o token do Mapbox lido do ambiente.

    O token é um segredo: NÃO fica no código nem no versionamento. Ele é lido de
    uma variável de ambiente com os.getenv("MAPBOX_TOKEN"). Defina antes de rodar:

        PowerShell:  $env:MAPBOX_TOKEN = "pk...."
        Linux/Mac:   export MAPBOX_TOKEN="pk...."

    Em deploy, configure MAPBOX_TOKEN nas variáveis de ambiente da plataforma.
    O arquivo gerado (frontend_v2/js/config.js) está no .gitignore.
    """
    print("\n" + "=" * 60)
    print("  [config] Token do Mapbox -> frontend_v2/js/config.js")
    print("=" * 60)

    token = os.getenv("MAPBOX_TOKEN", "").strip()
    config_path = BASE.parent / "frontend_v2" / "js" / "config.js"

    if not token:
        print("[AVISO] MAPBOX_TOKEN não definida no ambiente.")
        print("        O mapa dos EUA (usa.html) não carrega até você definir o token.")
        print('        Ex. (PowerShell): $env:MAPBOX_TOKEN = "pk..."  e rode de novo.')
        return

    conteudo = (
        "// ARQUIVO GERADO por python/main.py a partir de os.getenv('MAPBOX_TOKEN').\n"
        "// NÃO versionar (está no .gitignore) e NÃO editar à mão.\n"
        "window.LANDLYTICS_CONFIG = {\n"
        f"  MAPBOX_TOKEN: {json.dumps(token)}\n"
        "};\n"
    )
    config_path.write_text(conteudo, encoding="utf-8")
    print(f"[OK] config.js gerado em {config_path}")


def run_analise():
    """Roda o motor analítico: o modelo Diferenças-em-Diferenças (DiD).

    Lê os CSVs do GEE, calcula o IHI, ajusta o modelo, decompõe a anomalia
    térmica e exporta data/results_v2.json (consumido pelo frontend).
    """
    print("\n" + "=" * 60)
    print("  [1/4] Motor analítico — modelo DiD (analysis_v2.py)")
    print("=" * 60)
    # import tardio: a geração do config.js do frontend não depende das libs
    # pesadas (pandas/statsmodels), então o import fica só onde é usado.
    import analysis_v2
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
    # gera o config.js do frontend (token Mapbox) primeiro: não depende dos
    # dados pesados, então roda mesmo sem os TIFs do GEE baixados.
    run_frontend_config()
    run_analise()
    run_artefatos()

    print("\n" + "=" * 60)
    print("  Pipeline v2 concluído.")
    print("  Modelo    : LandLytics/data/results_v2.json")
    print("  Relatório : LandLytics/data/relatorio_v2.pdf")
    print("  Frontend  : cd LandLytics && python -m http.server 8766")
    print("=" * 60)


if __name__ == "__main__":
    main()
