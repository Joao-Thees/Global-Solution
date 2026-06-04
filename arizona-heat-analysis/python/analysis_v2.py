"""
Arizona Datacenter Heat Analysis v2 - Modelo Estatístico (2020-2026)
Sites: CyrusOne Phoenix (dc) vs Área Verde (green/controle)
Períodos: pre(2020-2022) vs ops(2024-2026) — sem período build
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

sys.path.insert(0, str(Path(__file__).parent))
import config


def load_data():
    try:
        dados = pd.read_csv(config.DADOS_SAT_CSV_V2, sep=",", decimal=".")
    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado: {config.DADOS_SAT_CSV_V2}")
        sys.exit(1)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
        print(f"[ERRO] Arquivo inválido ou corrompido ({config.DADOS_SAT_CSV_V2}): {e}")
        sys.exit(1)

    try:
        ref = pd.read_csv(config.REFLST_CSV_V2, sep=",", decimal=".")
        ref.columns = ["year", "sat", "ref2"]
    except FileNotFoundError:
        print(f"[ERRO] Arquivo não encontrado: {config.REFLST_CSV_V2}")
        sys.exit(1)
    except (pd.errors.EmptyDataError, pd.errors.ParserError) as e:
        print(f"[ERRO] Arquivo inválido ou corrompido ({config.REFLST_CSV_V2}): {e}")
        sys.exit(1)

    try:
        dados = dados.merge(ref, on=["year", "sat"], how="left")
        dados["ihi"] = dados["lst"] - dados["ref2"]
    except KeyError as e:
        print(f"[ERRO] Coluna ausente nos dados: {e}. Verifique os cabeçalhos dos CSVs.")
        sys.exit(1)
    dados = dados.dropna(subset=["ihi", "ndvi", "ndbi"])

    pre_min, pre_max = config.PERIODS_V2["pre"]
    ops_min, ops_max = config.PERIODS_V2["ops"]

    def classify_period(y):
        if pre_min <= y <= pre_max:
            return "pre"
        if ops_min <= y <= ops_max:
            return "ops"
        return None

    dados["period"] = dados["year"].apply(classify_period)
    dados = dados[dados["period"].isin(["pre", "ops"])]

    if dados.empty:
        print("[ERRO] Nenhuma observação encontrada após filtros de período. Verifique os dados.")
        sys.exit(1)

    dados["period"] = pd.Categorical(dados["period"], categories=["pre", "ops"])
    dados["zone"]   = pd.Categorical(dados["zone"],   categories=["sitio", "inner", "outer"])
    dados["trat"]   = (dados["trat"] == "dc")

    return dados


def run_model(dados: pd.DataFrame):
    formula = "ihi ~ ndvi + ndbi + C(zone) * C(trat) + C(trat) * C(period)"
    try:
        model = smf.ols(formula, data=dados).fit()
    except Exception as e:
        print(f"[ERRO] Falha no ajuste do modelo estatístico: {e}")
        sys.exit(1)
    return model


def decompose_anomaly(model, dados: pd.DataFrame, site_id: str):
    coefs = model.params
    dc    = dados[dados["site"] == site_id]

    pre_means = dc[dc["period"] == "pre"][["ndvi", "ndbi"]].mean()
    ops_means = dc[dc["period"] == "ops"][["ndvi", "ndbi"]].mean()

    d_ndvi = ops_means["ndvi"] - pre_means["ndvi"]
    d_ndbi = ops_means["ndbi"] - pre_means["ndbi"]

    c_terreno  = coefs["ndvi"] * d_ndvi + coefs["ndbi"] * d_ndbi
    c_geral    = coefs.get("C(period)[T.ops]", 0.0)
    c_operacao = coefs.get("C(trat)[T.True]:C(period)[T.ops]", 0.0)
    total      = c_terreno + c_geral + c_operacao

    pct_terreno  = (c_terreno  / total * 100) if total != 0 else 0
    pct_geral    = (c_geral    / total * 100) if total != 0 else 0
    pct_operacao = (c_operacao / total * 100) if total != 0 else 0

    return {
        "site":           site_id,
        "c_terreno":      round(float(c_terreno),   3),
        "c_geral":        round(float(c_geral),     3),
        "c_operacao":     round(float(c_operacao),  3),
        "total_anomalia": round(float(total),        3),
        "pct_terreno":    round(float(pct_terreno),  1),
        "pct_geral":      round(float(pct_geral),    1),
        "pct_operacao":   round(float(pct_operacao), 1),
    }


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


def export_results(model, dados: pd.DataFrame):
    coefs    = model.params
    pvals    = model.pvalues
    dc_sites = [s for s, v in config.SITES.items() if v["trat"] == "dc"]

    output = {
        "versao":  "v2",
        "periodos": config.PERIODS_V2,
        "n_obs":   int(len(dados)),
        "r2":      round(float(model.rsquared),     4),
        "r2_adj":  round(float(model.rsquared_adj), 4),
        "coeficientes": {
            "operacao":      round(float(coefs.get("C(trat)[T.True]:C(period)[T.ops]", 0)), 4),
            "operacao_pval": float(pvals.get("C(trat)[T.True]:C(period)[T.ops]", 1)),
            "periodo_ops":   round(float(coefs.get("C(period)[T.ops]", 0)), 4),
            "ndvi":          round(float(coefs.get("ndvi", 0)), 4),
            "ndbi":          round(float(coefs.get("ndbi", 0)), 4),
        },
        "decomposicao":     [decompose_anomaly(model, dados, s) for s in dc_sites],
        "series_temporais": build_time_series(dados),
        "sites":            config.SITES,
    }

    try:
        Path(config.RESULTS_JSON_V2).parent.mkdir(parents=True, exist_ok=True)
        with open(config.RESULTS_JSON_V2, "w", encoding="utf-8") as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
    except OSError as e:
        print(f"[ERRO] Não foi possível salvar os resultados em {config.RESULTS_JSON_V2}: {e}")
        sys.exit(1)

    print(f"\n[OK] Resultados v2 salvos em: {config.RESULTS_JSON_V2}")
    return output


def main():
    print("=" * 70)
    print("  ARIZONA HEAT ANALYSIS v2 — Modelo Estatístico (2020-2026)")
    print("=" * 70)

    print("\n>> Carregando dados v2...")
    dados = load_data()
    print(f"   {len(dados):,} observações (pré + ops, sem 2023)")
    print(f"   Sites: {dados['site'].unique().tolist()}")

    print("\n>> Executando modelo DiD...")
    model = run_model(dados)
    print(model.summary())

    print("\n" + "=" * 70)
    print("  DECOMPOSIÇÃO DA ANOMALIA TÉRMICA")
    print("=" * 70)
    dc_sites = [s for s, v in config.SITES.items() if v["trat"] == "dc"]
    for site in dc_sites:
        if site not in dados["site"].values:
            continue
        d    = decompose_anomaly(model, dados, site)
        name = config.SITES[site]["name"]
        print(f"\n  [{name}]")
        print(f"    Cobertura (vegetação→pavimento): {d['c_terreno']:+.3f} K")
        print(f"    Tendência regional:              {d['c_geral']:+.3f} K")
        print(f"    OPERAÇÃO DOS SERVIDORES:         {d['c_operacao']:+.3f} K")
        print(f"    ─────────────────────────────────────────")
        print(f"    TOTAL anomalia PRÉ → OPS:        {d['total_anomalia']:+.3f} K")

    coef_op = model.params.get("C(trat)[T.True]:C(period)[T.ops]", 0)
    pval_op = model.pvalues.get("C(trat)[T.True]:C(period)[T.ops]", 1)
    print(f"\n  Coef. operação: {coef_op:+.3f} K  |  p-valor: {pval_op:.2e}")

    print("\n>> Exportando resultados v2...")
    export_results(model, dados)


if __name__ == "__main__":
    main()
