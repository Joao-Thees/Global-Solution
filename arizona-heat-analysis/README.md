# Arizona Datacenter Heat Analysis

Análise do efeito de ilha de calor urbana gerado por datacenters no Arizona (EUA).
Baseado na metodologia de [El calor detrás de la nube](https://github.com/AmenazaRoboto/El-calor-detras-de-la-nube) (Amenaza Roboto, Uruguai).

## Sites analisados

| Site | Tipo | Localização |
|------|------|-------------|
| Meta Platforms | Datacenter (tratamento) | Mesa, AZ |
| Google LLC | Datacenter (tratamento) | Mesa/Phoenix, AZ |
| CyrusOne | Datacenter (tratamento) | Phoenix, AZ |
| Superstition Springs Center | Shopping (controle) | Mesa, AZ |
| SanTan Village | Shopping (controle) | Gilbert, AZ |

## Fluxo de trabalho

### 1. Extrair dados do Google Earth Engine

1. Acesse https://code.earthengine.google.com
2. Execute cada script da pasta `gee/` na ordem:
   - `01_dados_sat.js` → exporta `dados_sat.csv`
   - `02_reflst.js` → exporta `reflst.csv`
   - `03_lst_image_export.js` → exporta `delta_lst.tif`
3. Baixe os arquivos do Google Drive (pasta `GEE_Arizona`) para `data/gee_exports/`

### 2. Rodar a análise Python

```bash
cd python
pip install -r requirements.txt
python run_all.py
```

Isso executa o modelo diferenças-em-diferenças e gera o mapa de calor.

### 3. Visualizar

Abra `frontend/index.html` em um servidor HTTP local:

```bash
cd frontend
python -m http.server 8765
# Acesse: http://localhost:8765
```

## Metodologia

**Modelo:** Diferenças em diferenças com controles de cobertura

```
ihi ~ ndvi + ndbi + zone × trat + trat × period
```

- `ihi` = temperatura local − média regional anual (índice de ilha de calor)
- `ndvi` = índice de vegetação (controla mudança de cobertura)
- `ndbi` = índice de construção (controla impermeabilização)
- `zone` = sitio / inner (0-150m) / outer (150-300m)
- `trat` = TRUE (datacenter) / FALSE (controle)
- `period` = pre (2000-2015) / ops (2019-2025)

**Períodos:**
- `pre`: 2000–2015 (pré-construção)
- `build`: 2016–2018 (obras — excluído do modelo)
- `ops`: 2019–2025 (datacenters operacionais)

**Dados:** Landsat 7/8/9 (30m resolução), LST via módulo `sofiaermida/landsat_smw_lst`

## Estrutura

```
arizona-heat-analysis/
├── gee/                    # Scripts Google Earth Engine (JavaScript)
├── python/                 # Análise estatística (Python/statsmodels)
├── frontend/               # Visualização web (Leaflet + Chart.js)
└── data/
    ├── sites.geojson       # Polígonos dos sites
    ├── heatmap.png         # Mapa de calor (gerado pelo Python)
    ├── heatmap_bounds.json # Coordenadas do heatmap
    ├── results.json        # Resultados do modelo (gerado pelo Python)
    └── gee_exports/        # CSVs e GeoTIFF do GEE (colocar aqui)
```
