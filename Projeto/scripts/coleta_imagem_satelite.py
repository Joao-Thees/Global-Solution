''' construir o motor analítico da missão. Usando Python, sua equipe vai criar 
uma aplicação capaz de ingerir lotes de dados espaciais (simulados), aplicar regras de negócio estritas através 
de lógica de programação estruturada, e gerar relatórios, alertas ou decisões essenciais para o sucesso do 
projeto integrado. '''

''' A missão é da sua equipe, e os dados 
podem ser adaptados à sua narrativa '''

''' processamento via API do consumo de IA, convertendo uso em litros de água e emissão de CO₂. '''

'''NASA GIBS API'''

'''Funcionamento API: NASA GIBS Usa protocolo WMS -> Web Map Service. faz uma requisição HTTP passando quatro parametros:
1. Layer (Camada de Dados) - Imagem real - Indice de Vegetação - Temperatura da superfície - Focos de incendio - Extensão gelo marinho (2000-Hoje)
2. Bounding Box (região geografica)
3. Time (data)
4. Tamanho imagem em pixels

RETORNO DA API AO SISTEMA: 

Imagem PNG ou JPEG pronta para uso.
Satelite de uso: MODIS
'''
"""
coleta_imagens_gibs.py

Módulo de coleta de imagens satelitais via NASA GIBS (WMS).
Não contém input() nem execução direta — é chamado pelo Flask (app.py).

NASA GIBS usa protocolo WMS (Web Map Service).
Parâmetros da requisição: layer, bbox, time, size.
Retorno: imagem PNG salva em disco.
Satélite: MODIS / SMAP
"""

from owslib.wms import WebMapService
from PIL import Image
import os
import io

# ── configurações da API ───────────────────────────────────────────────────────

URL_GIBS = "https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi?"

REGIOES = {
    "amazonia":         [-73.0, -15.0, -44.0,  5.0],
    "artico":           [-180.0, 60.0, 180.0, 90.0],
    # Pando bbox pequena, centrada no datacenter Antel.
    "pando_datacenter": [-56.02, -34.73, -55.85, -34.60],
    # Ashburn, Virgínia  epicentro do Datacenter Alley
    "datacenter_alley": [-77.55, 38.99, -77.42, 39.10],
}

LAYERS = {
    "true_color":   "MODIS_Terra_CorrectedReflectance_TrueColor",
    "vegetacao":    "MODIS_Terra_NDVI_8Day",
    "queimadas":    "MODIS_Terra_Thermal_Anomalies_Day",
    "vapor_agua":   "MODIS_Terra_Water_Vapor_5km_Day",
    "temperatura_superficie": "MODIS_Terra_Land_Surface_Temp_Day"
}

ANOS_DISPONIVEIS = [2000, 2005, 2010, 2015, 2020, 2021, 2022, 2023, 2024, 2025, 2026]

LARGURA     = 2048
ALTURA      = 1536
PASTA_SAIDA = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "imagens")) # 

# ── funções ────────────────────────────────────────────────────────────────────

def conectar_gibs():
    """Abre e retorna a conexão WMS com o servidor NASA GIBS."""
    print("Conectando ao servidor NASA GIBS...")
    wms = WebMapService(URL_GIBS, version="1.1.1")
    print("Conexão estabelecida.")
    return wms


def baixar_imagem(wms, nome_regiao, bbox, nome_layer, id_layer, ano, mes, dia):
    """
    Baixa uma imagem PNG do GIBS e salva em disco.
    Retorna o caminho relativo do arquivo salvo, ou None em caso de erro.

    Parâmetros recebidos do Flask (vindos do formulário web):
        ano  : int  — ex: 2024
        mes  : str  — ex: "06"
        dia  : str  — ex: "15"
    """
    data   = f"{ano}-{mes}-{dia}"
    pasta  = os.path.join(PASTA_SAIDA, nome_regiao)
    os.makedirs(pasta, exist_ok=True)
    caminho_absoluto = os.path.join(pasta, f"{nome_layer}_{ano}.png")
    # caminho relativo para o Flask servir como URL
    caminho_relativo = f"{nome_regiao}/{nome_layer}_{ano}.png"

    # se já foi baixado antes, não baixa de novo
    if os.path.exists(caminho_absoluto):
        print(f"  [já existe] {caminho_relativo}")
        return caminho_relativo

    print(f"  Baixando: {nome_regiao} / {nome_layer} / {data}...")
    try:
        resposta = wms.getmap(
            layers=[id_layer],
            srs="EPSG:4326",
            bbox=bbox,
            size=(LARGURA, ALTURA),
            format="image/png",
            time=data,
            transparent=True,
        )
        imagem = Image.open(io.BytesIO(resposta.read()))
        imagem.save(caminho_absoluto)
        print(f"  [salvo] {caminho_relativo}")
        return caminho_relativo

    except Exception as erro:
        print(f"  [ERRO] {nome_regiao}/{nome_layer}/{ano}: {erro}")
        return None


def coletar(regiao, mes, dia, anos, layers_escolhidas=None):
    """
    Função principal chamada pelo Flask.

    Parâmetros:
        regiao           : str  — chave do dicionário REGIOES (ex: "amazonia")
        mes              : str  — "01" a "12"
        dia              : str  — "01" a "28"
        anos             : list — ex: [2000, 2015, 2024]
        layers_escolhidas: list — ex: ["vegetacao", "true_color"]
                           se None, usa todas as LAYERS

    Retorna:
        dict com os caminhos das imagens geradas.
        ex: { "vegetacao_2000": "amazonia/vegetacao_2000.png", ... }
    """
    if regiao not in REGIOES:
        raise ValueError(f"Região '{regiao}' não encontrada. Disponíveis: {list(REGIOES.keys())}")

    anos_validos = [a for a in anos if a in ANOS_DISPONIVEIS]
    if not anos_validos:
        raise ValueError(f"Nenhum ano válido informado. Disponíveis: {ANOS_DISPONIVEIS}")

    layers_usar = {}
    if layers_escolhidas:
        for l in layers_escolhidas:
            if l in LAYERS:
                layers_usar[l] = LAYERS[l]
    else:
        layers_usar = LAYERS  # usa todas se não especificado

    bbox = REGIOES[regiao]
    wms  = conectar_gibs()
    imagens_geradas = {}

    total = len(layers_usar) * len(anos_validos)
    atual = 0

    for nome_layer, id_layer in layers_usar.items():
        for ano in anos_validos:
            atual += 1
            print(f"\n[{atual}/{total}]")

            # SMAP só existe a partir de 2015
            if nome_layer == "umidade_solo" and ano < 2015:
                print(f"  [ignorado] umidade_solo não disponível antes de 2015.")
                continue

            caminho = baixar_imagem(wms, regiao, bbox, nome_layer, id_layer, ano, mes, dia)
            if caminho:
                imagens_geradas[f"{nome_layer}_{ano}"] = caminho

    return imagens_geradas
        