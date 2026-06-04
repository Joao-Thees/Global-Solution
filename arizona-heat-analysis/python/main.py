"""
Arizona Datacenter Heat Analysis v2 - Pipeline Completo
Executa na ordem:
  1. generate_report_v2.py   — relatório PDF (LST absoluta 2025)
  2. generate_heatmap_v2.py  — mapa de calor PNG (Landsat LST)
  3. generate_background.py  — imagem RGB de fundo para o frontend
"""

import subprocess
import sys
from pathlib import Path

scripts = [
    Path(__file__).parent / "generate_report_v2.py",
    Path(__file__).parent / "generate_heatmap_v2.py",
    Path(__file__).parent / "generate_background.py",
]

for script in scripts:
    print(f"\n{'='*60}")
    print(f"  Executando: {script.name}")
    print(f"{'='*60}")
    result = subprocess.run([sys.executable, str(script)], check=False)
    if result.returncode != 0:
        print(f"\n[ERRO] {script.name} falhou com código {result.returncode}")
        sys.exit(result.returncode)

print("\n" + "="*60)
print("  Pipeline v2 concluído.")
print("  Relatório : arizona-heat-analysis/data/relatorio_v2.pdf")
print("  Frontend  : cd frontend_v2 && python -m http.server 8766")
print("="*60)
