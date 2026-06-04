# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos principais

**Instalar dependências:**
```powershell
.venv\Scripts\Activate.ps1
pip install -r arizona-heat-analysis/python/requirements.txt
```

**Rodar o pipeline completo (análise + heatmap):**
```powershell
cd arizona-heat-analysis/python
python run_all.py
```

**Rodar scripts individualmente:**
```powershell
python arizona-heat-analysis/python/analysis.py       # modelo DiD (v1)
python arizona-heat-analysis/python/analysis_v2.py    # modelo DiD (v2)
python arizona-heat-analysis/python/generate_heatmap.py    # heatmap v1
python arizona-heat-analysis/python/generate_heatmap_v2.py # heatmap v2
python arizona-heat-analysis/python/generate_background.py # RGB background v2
```

**Servir o frontend:**
```powershell
cd arizona-heat-analysis/frontend
python -m http.server 8765
# http://localhost:8765

cd arizona-heat-analysis/frontend_v2
python -m http.server 8766
# http://localhost:8766
```

## Arquitetura

O projeto tem dois pipelines paralelos (v1 e v2), com a mesma estrutura:

```
GEE (JavaScript) → CSVs/GeoTIFF → Python (análise + heatmap) → JSON/PNG → Frontend (Leaflet)
```

### GEE (`gee/`)
Scripts executados manualmente no [Google Earth Engine](https://code.earthengine.google.com). Dependem do módulo externo `sofiaermida/landsat_smw_lst`. Exportam para o Google Drive (pasta `GEE_Arizona`) e os arquivos devem ser baixados manualmente para `data/gee_exports/` (v1) ou `data/gee_exports_v2/` (v2).

- `01_dados_sat.js` — extrai LST, NDVI, NDBI por site/zona/ano → `dados_sat.csv`
- `02_reflst.js` — extrai temperatura de referência regional → `reflst.csv`
- `03_lst_image_export.js` — exporta imagem raster de anomalia → `delta_lst.tif`

### Python (`python/`)
- `config.py` — fonte única de verdade para: períodos de análise, definições de sites (bbox, center, trat), e todos os caminhos de arquivo. **Edite aqui para ajustar parâmetros.**
- `analysis.py` / `analysis_v2.py` — modelo diferenças-em-diferenças com statsmodels. Lê os CSVs do GEE, calcula IHI (temperatura local − referência regional anual), roda OLS com fórmula `ihi ~ ndvi + ndbi + C(zone)*C(trat) + C(trat)*C(period)`, e exporta `results.json`.
- `generate_heatmap.py` / `generate_heatmap_v2.py` — converte `delta_lst.tif` em PNG com paleta divergente (azul→amarelo→vermelho). Se o `.tif` não existir, gera um mapa sintético para demonstração.
- `generate_background.py` — converte imagem RGB do GEE em PNG para uso como camada base no frontend v2.

### Frontend (`frontend/`, `frontend_v2/`)
Visualização estática com Leaflet (mapa) + Chart.js (gráficos). Carrega `results.json`, `heatmap.png` e `heatmap_bounds.json` via fetch. Não há build step — abrir direto com `python -m http.server`.

### Dados (`data/`)
- `gee_exports/` — inputs brutos do GEE (v1): `dados_sat.csv`, `reflst.csv`, `delta_lst.tif`
- `gee_exports_v2/` — inputs brutos do GEE (v2)
- `results.json` / `results_v2.json` — output do modelo Python, consumido pelo frontend
- `heatmap.png` / `heatmap_v2.png` + `*_bounds.json` — overlay do mapa de calor para o Leaflet

## Versões do pipeline

| | v1 | v2 |
|---|---|---|
| Período | 2000–2025 | 2020–2026 |
| Sites | Meta, Google, CyrusOne (DCs) + 2 shoppings (controle) | CyrusOne Phoenix (DC) + Área Verde (controle) |
| Caminhos em `config.py` | `DATA_DIR`, `RESULTS_JSON`, etc. | `DATA_DIR_V2`, `RESULTS_JSON_V2`, etc. |

## Metodologia (referência rápida)

Reproduz [El calor detrás de la nube](https://github.com/AmenazaRoboto/El-calor-detras-de-la-nube) (Amenaza Roboto) em Python/statsmodels.

- **IHI** = LST local − temperatura média regional do ano (`ref2`)
- **Zonas**: `sitio` (polígono do site), `inner` (buffer 0–150m), `outer` (150–300m)
- **Período `build` (2016–2018)** é excluído do modelo, mas presente nos dados brutos
- Coeficiente-chave: `C(trat)[T.True]:C(period)[T.ops]` = efeito causal da operação dos servidores sobre a temperatura
