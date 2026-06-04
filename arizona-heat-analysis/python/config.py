"""
Configuração central do projeto Arizona Datacenter Heat Analysis.
Ajuste os períodos e coordenadas aqui conforme necessário.
"""

# ──────────────────────────────────────────────────
# SITES
# trat: "dc" = tratamento (datacenter) | "green" = área verde
# ──────────────────────────────────────────────────
SITES = { # dicionario chave x valor com dados de cada local a partir da bbox deles.
    "phoenix_cyrius": {
        "name": "Phoenix Cyrius DataCenter",
        "trat": "dc",
        "color": "#FF00FF",
        "center": [-111.889, 33.276],
        "bbox": [-111.901, 33.261, -111.876, 33.291],
    },
    "dc_demarcado": {
        "name": "CyrusOne Phoenix Datacenter (KML)",
        "trat": "dc",
        "color": "#FF6600",
        "center": [-111.8814, 33.2712],
        "bbox": [-111.8844, 33.2653, -111.8805, 33.2724],
    },
    "area_verde": {
        "name": "Area Verde (KML)",
        "trat": "green",
        "color": "#00AA00",
        "center": [-111.8927, 33.2677],
        "bbox": [-111.8933, 33.2673, -111.8892, 33.2723],
    },
}

# ──────────────────────────────────────────────────
# ÁREA DE ESTUDO (bbox do KML demarcado no googleearth)
# ──────────────────────────────────────────────────
STUDY_BBOX = {
    "west":  -112.116,
    "east":  -111.498,
    "south":  33.222,
    "north":  33.504,
}

RESULTS_DIR       = "../data"

# ──────────────────────────────────────────────────
# PERÍODOS — analysis_v2.py (ferramenta DiD separada)
# ──────────────────────────────────────────────────
PERIODS_V2 = {
    "pre": (2020, 2022),
    "ops": (2024, 2026),
}

# ──────────────────────────────────────────────────
# CAMINHOS — V2 (snapshot 2025)
# ──────────────────────────────────────────────────
DATA_DIR_V2         = "../data/gee_exports_v2"
DADOS_SAT_CSV_V2    = f"{DATA_DIR_V2}/dados_sat_v2.csv"
REFLST_CSV_V2       = f"{DATA_DIR_V2}/reflst_v2.csv"
DELTA_LST_TIF_V2    = f"{DATA_DIR_V2}/delta_lst_v2.tif"
LST_OPS_TIF_V2      = f"{DATA_DIR_V2}/lst_ops_v2.tif"
RGB_BACKGROUND_TIF  = f"{DATA_DIR_V2}/rgb_background_v2.tif"
RESULTS_JSON_V2     = f"{RESULTS_DIR}/results_v2.json"
HEATMAP_PNG_V2      = f"{RESULTS_DIR}/heatmap_v2.png"
HEATMAP_BOUNDS_JSON_V2 = f"{RESULTS_DIR}/heatmap_bounds_v2.json"
RGB_PNG             = f"{RESULTS_DIR}/rgb_background.png"
RGB_BOUNDS_JSON     = f"{RESULTS_DIR}/rgb_bounds.json"
