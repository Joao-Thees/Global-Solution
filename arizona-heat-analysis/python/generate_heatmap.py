"""
Arizona Datacenter Heat Analysis - Geração do Mapa de Calor
Converte o GeoTIFF de anomalia LST (delta_lst.tif) exportado do GEE
em PNG de alto contraste para o frontend.
Resultado: heatmap.png + heatmap_bounds.json (usado pelo Leaflet)
"""

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.colors import LinearSegmentedColormap

sys.path.insert(0, str(Path(__file__).parent))
import config

# ──────────────────────────────────────────────────────────────────────────────
# PALETA DE CORES — igual ao GEE, divergindo azul→amarelo→vermelho
# Máximo contraste entre frio e quente (mesma paleta do projeto de referência)
# ──────────────────────────────────────────────────────────────────────────────
HEAT_COLORS = [
    "#313695",  # -4°K  azul escuro
    "#4575b4",  # -3°K
    "#74add1",  # -2°K
    "#abd9e9",  # -1°K
    "#e0f3f8",  # -0.5°K
    "#ffffbf",  #  0°K  neutro
    "#fee090",  # +1°K
    "#fdae61",  # +2°K
    "#f46d43",  # +3°K
    "#d73027",  # +4°K
    "#a50026",  # +6°K  vermelho intenso
]

VMIN = -3.0  # °K mínimo da escala
VMAX =  6.0  # °K máximo da escala


def build_colormap():
    return LinearSegmentedColormap.from_list(
        "heat_az",
        list(zip(
            np.linspace(0, 1, len(HEAT_COLORS)),
            HEAT_COLORS
        ))
    )


def generate_from_geotiff(tif_path: str):
    """Caminho principal: lê GeoTIFF exportado do GEE."""
    import rasterio
    from rasterio.warp import transform_bounds

    with rasterio.open(tif_path) as src:
        data    = src.read(1).astype(float)
        nodata  = src.nodata
        bounds  = src.bounds
        crs     = src.crs

        if nodata is not None:
            data[data == nodata] = np.nan

        # Stretch de contraste: clip nos percentis 2-98 para máxima nitidez
        valid = data[~np.isnan(data)]
        p2, p98 = np.nanpercentile(valid, 2), np.nanpercentile(valid, 98)
        vmin = max(VMIN, p2)
        vmax = min(VMAX, p98)

    return data, bounds, vmin, vmax


def generate_synthetic(bounds):
    """
    Fallback: gera mapa sintético realista a partir de config.SITES
    para demonstração antes de ter os dados do GEE.
    """
    w, s, e, n = bounds.west, bounds.south, bounds.east, bounds.north
    cols = 1600
    rows = int(cols * (n - s) / (e - w))
    lons = np.linspace(w, e, cols)
    lats = np.linspace(n, s, rows)
    lon_grid, lat_grid = np.meshgrid(lons, lats)

    data = np.zeros((rows, cols))

    # Simula ilha de calor em cada datacenter
    for site_id, site in config.SITES.items():
        cx, cy = site["center"]
        dist = np.sqrt((lon_grid - cx) ** 2 + (lat_grid - cy) ** 2) * 111_000
        if site["trat"] == "dc":
            intensity = 4.5  # datacenter: anomalia forte
            sigma = 1500
        else:
            intensity = 0.8  # shopping: anomalia leve
            sigma = 800
        data += intensity * np.exp(-(dist ** 2) / (2 * sigma ** 2))

    # Ruído base (variação natural do deserto)
    rng = np.random.default_rng(42)
    data += rng.normal(0, 0.3, data.shape)

    return data, VMIN, VMAX


def render_png(data, bounds, vmin, vmax, out_path: str):
    """
    Renderiza o array de anomalia como PNG de alto contraste.
    Sem eixos, sem margens — imagem pura para sobreposição no mapa.
    """
    cmap = build_colormap()
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)

    rgba = cmap(norm(data))
    # Transparência proporcional à magnitude da anomalia (neutro = quase transparente)
    alpha_raw = np.abs(data - 0) / (vmax - vmin + 1e-9)
    alpha_raw = np.clip(alpha_raw * 2.5, 0.0, 1.0)
    # Pixels sem dado = totalmente transparentes
    alpha_raw[np.isnan(data)] = 0.0

    rgba[:, :, 3] = alpha_raw

    matplotlib.image.imsave(out_path, rgba)
    print(f"[OK] Heatmap PNG salvo: {out_path}  ({data.shape[1]}x{data.shape[0]}px)")


def save_bounds(bounds, out_path: str):
    obj = {
        "south": bounds.south if hasattr(bounds, "south") else bounds[1],
        "west":  bounds.west  if hasattr(bounds, "west")  else bounds[0],
        "north": bounds.north if hasattr(bounds, "north") else bounds[3],
        "east":  bounds.east  if hasattr(bounds, "east")  else bounds[2],
    }
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(obj, f, indent=2)
    print(f"[OK] Bounds salvos: {out_path}")


def main():
    print("=" * 60)
    print("  Gerando mapa de calor Arizona...")
    print("=" * 60)

    tif_path = Path(config.DELTA_LST_TIF)

    if tif_path.exists():
        print(f"\n>> Lendo GeoTIFF: {tif_path}")
        data, bounds, vmin, vmax = generate_from_geotiff(str(tif_path))
        print(f"   Dimensões: {data.shape}  |  Range: [{vmin:.2f}, {vmax:.2f}] °K")
    else:
        print(f"\n>> delta_lst.tif não encontrado em {tif_path}")
        print("   Gerando mapa de demonstração (sintético)...")

        from types import SimpleNamespace
        b = config.STUDY_BBOX
        bounds = SimpleNamespace(
            west=b["west"], east=b["east"],
            south=b["south"], north=b["north"]
        )
        data, vmin, vmax = generate_synthetic(bounds)

    out_png    = str(Path(config.HEATMAP_PNG))
    out_bounds = str(Path(config.HEATMAP_BOUNDS_JSON))

    Path(out_png).parent.mkdir(parents=True, exist_ok=True)
    render_png(data, bounds, vmin, vmax, out_png)
    save_bounds(bounds, out_bounds)

    print("\n  Pronto. Abra frontend/index.html no navegador.")



if __name__ == "__main__":
    main()
