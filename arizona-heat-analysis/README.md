# Arizona Datacenter Heat Analysis — V2

Análise do impacto térmico do **CyrusOne Phoenix Datacenter** sobre a temperatura superficial (LST) em relação a uma área verde adjacente, Phoenix, AZ — 2025.

Corrobora os achados de [techxplore.com/news/2026-05-centers-nearby-temperatures-degrees-phoenix](https://techxplore.com/news/2026-05-centers-nearby-temperatures-degrees-phoenix.html) usando dados Landsat via Google Earth Engine.

---

## Dados pesados (TIF) — download obrigatório

Os arquivos GeoTIFF não estão no repositório (tamanho > 100 MB). Baixe o `.zip` no link abaixo e extraia o conteúdo dentro de `data/gee_exports_v2/`:

**Download:** https://drive.google.com/drive/u/4/folders/1thUj2OWMXYefcRDSgmpq38qUsucMlkAZ

Arquivos esperados após extração:

```
data/gee_exports_v2/
├── delta_lst_v2.tif       # anomalia térmica (heatmap)
├── lst_ops_v2.tif         # LST absoluta período operacional
└── rgb_background.tif     # imagem RGB Sentinel-2 (fundo do mapa)
```

> Os CSVs (`dados_sat_v2.csv`, `reflst_v2.csv`) já estão no repositório.

---

## Instalação

```powershell
# Ativar ambiente virtual
.venv\Scripts\Activate.ps1

# Instalar dependências
pip install -r arizona-heat-analysis/python/requirements.txt
```

---

## Rodar o pipeline V2

```powershell
cd arizona-heat-analysis/python
python main.py
```

Executa em sequência:
1. `generate_report_v2.py` → `data/relatorio_v2.pdf` (LST 2025: datacenter vs área verde)
2. `generate_heatmap_v2.py` → `data/heatmap_v2.png` (mapa de calor Landsat)
3. `generate_background.py` → `data/rgb_background.png` (fundo Sentinel-2 para o mapa)

### Visualizar no navegador

```powershell
cd arizona-heat-analysis/frontend_v2
python -m http.server 8766
# Acesse: http://localhost:8766
```

### Ferramenta DiD (opcional)

```powershell
python arizona-heat-analysis/python/analysis_v2.py
```

Roda o modelo Diferenças-em-Diferenças (2020–2026) e atualiza `data/results_v2.json` usado pelos gráficos do frontend.

---

## Estrutura

```
arizona-heat-analysis/
├── gee_v2/                        # Scripts Google Earth Engine (JavaScript)
│   ├── 01_dados_sat.js            # extrai LST, NDVI, NDBI por site/zona/ano
│   ├── 02_reflst.js               # temperatura de referência regional
│   ├── 03_lst_image_export.js     # exporta raster de anomalia e LST ops
│   └── 04_rgb_background.js       # exporta imagem RGB Sentinel-2 (10m)
├── python/
│   ├── config.py                  # fonte única de verdade (sites, caminhos)
│   ├── main.py                    # pipeline completo (roda tudo)
│   ├── generate_report_v2.py      # relatório PDF — LST absoluta 2025
│   ├── generate_heatmap_v2.py     # mapa de calor PNG
│   ├── generate_background.py     # imagem RGB de fundo
│   ├── analysis_v2.py             # modelo DiD (ferramenta separada)
│   └── requirements.txt
├── frontend_v2/                   # Visualização web (Leaflet + Chart.js)
└── data/
    ├── gee_exports_v2/            # inputs do GEE (TIFs via Drive, CSVs no repo)
    ├── sites.geojson
    ├── results_v2.json            # output do DiD (usado pelo frontend)
    ├── heatmap_bounds_v2.json
    └── rgb_bounds.json
```

---

## Metodologia

**Relatório (V2 principal):** compara LST absoluta média de 2025 (79 cenas Landsat) entre o CyrusOne Phoenix Datacenter e a área verde adjacente demarcada por KML.

**Modelo DiD (ferramenta adicional):**

```
ihi ~ ndvi + ndbi + C(zone)*C(trat) + C(trat)*C(period)
```

- `ihi` = LST local − temperatura média regional do ano (`ref2`)
- `period`: `pre` (2020–2022) vs `ops` (2024–2026)
- Coeficiente-chave: `C(trat)[T.True]:C(period)[T.ops]`

**Dados:** Landsat 8/9 (30 m) via módulo `sofiaermida/landsat_smw_lst` no GEE.
