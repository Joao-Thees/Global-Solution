"""
Arizona Datacenter Heat Analysis - Modelo Estatístico Principal
Reproduz a metodologia de "El calor detrás de la nube" (Amenaza Roboto)
em Python/statsmodels no lugar do R.

Modelo: diferenças em diferenças com controles de cobertura
  ihi ~ ndvi + ndbi + zone*trat + trat*period
  onde ihi = lst - ref2  (ilha de calor urbana local - referência regional)
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).parent))
import config

# ──────────────────────────────────────────────────────────────────────────────
# 1. CARGA E PREPARAÇÃO DOS DADOS
# ──────────────────────────────────────────────────────────────────────────────

def load_data():
    dados = pd.read_csv(config.DADOS_SAT_CSV, sep=",", decimal=".")
    ref   = pd.read_csv(config.REFLST_CSV,   sep=",", decimal=".")
    ref.columns = ["year", "sat", "ref2"]

    # IHI = temperatura local - média regional do ano (mesma fórmula do projeto original)
    dados = dados.merge(ref, on=["year", "sat"], how="left")
    dados["ihi"] = dados["lst"] - dados["ref2"]
    dados = dados.dropna(subset=["ihi", "ndvi", "ndbi"])

    # Período (exclui build do modelo, igual ao projeto original)
    pre_min,  pre_max  = config.PERIODS["pre"]
    bld_min,  bld_max  = config.PERIODS["build"]
    ops_min,  ops_max  = config.PERIODS["ops"]

    def classify_period(y):
        if pre_min <= y <= pre_max:
            return "pre"
        if ops_min <= y <= ops_max:
            return "ops"
        if bld_min <= y <= bld_max:
            return "build"
        return None

    dados["period"] = dados["year"].apply(classify_period)
    dados = dados[dados["period"].isin(["pre", "ops"])]  # exclui build

    # Categorias com níveis de referência corretos
    dados["period"] = pd.Categorical(dados["period"], categories=["pre", "ops"])
    dados["zone"]   = pd.Categorical(dados["zone"],   categories=["sitio", "inner", "outer"])
    dados["trat"]   = (dados["trat"] == "dc")

    return dados


# ──────────────────────────────────────────────────────────────────────────────
# 2. MODELO DIFERENÇAS EM DIFERENÇAS
# ──────────────────────────────────────────────────────────────────────────────

def run_model(dados: pd.DataFrame):
    # Exatamente a mesma fórmula do projeto de referência (R → Python)
    # m1 <- lm(ihi ~ ndvi + ndbi + zone * trat + trat * period, data = dados)
    formula = "ihi ~ ndvi + ndbi + C(zone) * C(trat) + C(trat) * C(period)"
    model   = smf.ols(formula, data=dados).fit()
    return model


# ──────────────────────────────────────────────────────────────────────────────
# 3. DECOMPOSIÇÃO DA ANOMALIA TÉRMICA
# ──────────────────────────────────────────────────────────────────────────────

def decompose_anomaly(model, dados: pd.DataFrame, site_id: str):
    coefs = model.params
    dc    = dados[dados["site"] == site_id]

    pre_means = dc[dc["period"] == "pre"] [["ndvi", "ndbi"]].mean()
    ops_means = dc[dc["period"] == "ops"] [["ndvi", "ndbi"]].mean()

    d_ndvi = ops_means["ndvi"] - pre_means["ndvi"]
    d_ndbi = ops_means["ndbi"] - pre_means["ndbi"]

    c_terreno   = coefs["ndvi"] * d_ndvi + coefs["ndbi"] * d_ndbi
    c_geral     = coefs.get("C(period)[T.ops]", 0.0)
    c_operacao  = coefs.get("C(trat)[T.True]:C(period)[T.ops]", 0.0)
    total       = c_terreno + c_geral + c_operacao

    pct_terreno  = (c_terreno  / total * 100) if total != 0 else 0
    pct_geral    = (c_geral    / total * 100) if total != 0 else 0
    pct_operacao = (c_operacao / total * 100) if total != 0 else 0

    return {
        "site":          site_id,
        "c_terreno":     round(float(c_terreno),  3),
        "c_geral":       round(float(c_geral),    3),
        "c_operacao":    round(float(c_operacao), 3),
        "total_anomalia":round(float(total),      3),
        "pct_terreno":   round(float(pct_terreno), 1),
        "pct_geral":     round(float(pct_geral),   1),
        "pct_operacao":  round(float(pct_operacao),1),
    }


# ──────────────────────────────────────────────────────────────────────────────
# 4. SÉRIE TEMPORAL MÉDIA POR SITE/ZONA
# ──────────────────────────────────────────────────────────────────────────────

def build_time_series(dados: pd.DataFrame):
    ts = (
        dados[dados["zone"] == "sitio"]
        .groupby(["year", "site"])["ihi"]
        .mean()
        .reset_index()
        .rename(columns={"ihi": "ihi_mean"})
    )
    result = {}
    for site in ts["site"].unique():
        sub = ts[ts["site"] == site].sort_values("year")
        result[site] = {
            "years": sub["year"].tolist(),
            "ihi":   [round(v, 3) for v in sub["ihi_mean"].tolist()],
        }
    return result


# ──────────────────────────────────────────────────────────────────────────────
# 5. EXPORTAR RESULTADOS PARA O FRONTEND
# ──────────────────────────────────────────────────────────────────────────────

def export_results(model, dados: pd.DataFrame):
    coefs  = model.params
    pvals  = model.pvalues
    dc_sites = [s for s, v in config.SITES.items() if v["trat"] == "dc"]

    output = {
        "n_obs": int(len(dados)),
        "r2":    round(float(model.rsquared), 4),
        "r2_adj":round(float(model.rsquared_adj), 4),
        "coeficientes": {
            "operacao":      round(float(coefs.get("C(trat)[T.True]:C(period)[T.ops]", 0)), 4),
            "operacao_pval": float(pvals.get("C(trat)[T.True]:C(period)[T.ops]", 1)),
            "periodo_ops":   round(float(coefs.get("C(period)[T.ops]", 0)), 4),
            "ndvi":          round(float(coefs.get("ndvi", 0)), 4),
            "ndbi":          round(float(coefs.get("ndbi", 0)), 4),
        },
        "decomposicao": [decompose_anomaly(model, dados, s) for s in dc_sites],
        "series_temporais": build_time_series(dados),
        "sites": config.SITES,
        "periodos": config.PERIODS,
    }

    Path(config.RESULTS_JSON).parent.mkdir(parents=True, exist_ok=True)
    with open(config.RESULTS_JSON, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✓ Resultados salvos em: {config.RESULTS_JSON}")
    return output


# ──────────────────────────────────────────────────────────────────────────────
# 6. MAIN
# ──────────────────────────────────────────────────────────────────────────────

def main():
    print("=" * 70)
    print("  ARIZONA DATACENTER HEAT ANALYSIS — Modelo Estatístico Principal")
    print("=" * 70)

    print("\n>> Carregando dados satelitais e referência regional...")
    dados = load_data()
    print(f"   {len(dados):,} observações após filtros (pré + ops, sem build)")

    print("\n>> Executando modelo diferenças em diferenças...")
    model = run_model(dados)
    print(model.summary())

    print("\n" + "=" * 70)
    print("  DECOMPOSIÇÃO DA ANOMALIA TÉRMICA POR DATACENTER")
    print("=" * 70)
    dc_sites = [s for s, v in config.SITES.items() if v["trat"] == "dc"]
    for site in dc_sites:
        d = decompose_anomaly(model, dados, site)
        name = config.SITES[site]["name"]
        print(f"\n  [{name}]")
        print(f"    Cobertura (vegetação→pavimento): {d['c_terreno']:+.3f} °K")
        print(f"    Tendência regional:              {d['c_geral']:+.3f} °K")
        print(f"    OPERAÇÃO DOS SERVIDORES:         {d['c_operacao']:+.3f} °K  ← HUELLA")
        print(f"    ─────────────────────────────────────────────")
        print(f"    TOTAL anomalia PRÉ → OPS:        {d['total_anomalia']:+.3f} °K")
        print(f"    Repartição: {d['pct_terreno']:.0f}% cobertura | "
              f"{d['pct_geral']:.0f}% tendência | {d['pct_operacao']:.0f}% operação")

    coef_op = model.params.get("C(trat)[T.True]:C(period)[T.ops]", 0)
    pval_op = model.pvalues.get("C(trat)[T.True]:C(period)[T.ops]", 1)
    print(f"\n  Coef. operação: {coef_op:+.3f} °K  |  p-valor: {pval_op:.2e}")

    print("\n>> Exportando resultados para o frontend...")
    export_results(model, dados)
    print("\n  Execute agora: python generate_heatmap.py")


if __name__ == "__main__":
    main()
