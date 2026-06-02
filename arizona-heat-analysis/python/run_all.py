"""
Arizona Datacenter Heat Analysis - Pipeline Completo
Executa: análise estatística → geração do mapa de calor
"""

import subprocess
import sys
from pathlib import Path

scripts = [
    Path(__file__).parent / "analysis.py",
    Path(__file__).parent / "generate_heatmap.py",
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
print("  Pipeline concluído.")
print("  Abra arizona-heat-analysis/frontend/index.html no navegador.")
print("="*60)
