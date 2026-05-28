from flask import Flask, request, jsonify, send_from_directory
from coleta_imagem_satelite import conectar_gibs, baixar_imagem, REGIOES, LAYERS
import os

app = Flask(__name__)
wms = None  # conexão lazy — só conecta na primeira requisição

@app.route("/coletar", methods=["POST"])
def coletar():
    global wms
    if wms is None:
        wms = conectar_gibs()

    dados = request.json
    regiao = dados.get("regiao")
    mes    = dados.get("mes")
    dia    = dados.get("dia")
    anos   = dados.get("anos", [])

    # validações
    if regiao not in REGIOES:
        return jsonify({"erro": "Região inválida"}), 400
    if not mes or not mes.isdigit() or not (1 <= int(mes) <= 12):
        return jsonify({"erro": "Mês inválido"}), 400
    if not dia or not dia.isdigit() or not (1 <= int(dia) <= 28):
        return jsonify({"erro": "Dia inválido"}), 400
    if not anos or not isinstance(anos, list):
        return jsonify({"erro": "Anos inválidos"}), 400

    mes = str(int(mes)).zfill(2)
    dia = str(int(dia)).zfill(2)

    bbox = REGIOES[regiao]
    imagens_geradas = {}

    for nome_layer, id_layer in LAYERS.items():
        for ano in anos:
            if nome_layer == "umidade_solo" and ano < 2015:
                continue
            caminho = baixar_imagem(wms, regiao, bbox, nome_layer, id_layer, ano, mes, dia)
            if caminho:
                imagens_geradas[f"{nome_layer}_{ano}"] = caminho

    return jsonify({"imagens": imagens_geradas})

@app.route("/imagens/<path:caminho>")
def servir_imagem(caminho):
    pasta_imagens = os.path.join(os.path.dirname(__file__), "imagens")
    return send_from_directory(pasta_imagens, caminho)

@app.route("/regioes")
def listar_regioes():
    """Endpoint extra: retorna as regiões disponíveis para popular o dropdown do front-end."""
    return jsonify({"regioes": list(REGIOES.keys())})

@app.route("/layers")
def listar_layers():
    """Endpoint extra: retorna as layers disponíveis para o front-end."""
    return jsonify({"layers": list(LAYERS.keys())})

if __name__ == "__main__":
    app.run(debug=True)