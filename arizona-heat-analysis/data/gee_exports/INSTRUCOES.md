# Instruções — Dados do GEE

Coloque aqui os arquivos exportados pelo Google Earth Engine:

| Arquivo           | Script GEE              | Descrição                              |
|-------------------|-------------------------|----------------------------------------|
| `dados_sat.csv`   | `gee/01_dados_sat.js`   | LST, NDVI, NDBI por cena/site/zona     |
| `reflst.csv`      | `gee/02_reflst.js`      | LST regional anual (referência)        |
| `delta_lst.tif`   | `gee/03_lst_image_export.js` | Raster GeoTIFF de anomalia térmica |

## Como executar no GEE

1. Acesse https://code.earthengine.google.com
2. Copie e cole cada script `.js` da pasta `gee/`
3. Clique em **Run** → vá na aba **Tasks** → clique **Run** em cada tarefa
4. Os arquivos serão exportados para o Google Drive, pasta `GEE_Arizona`
5. Baixe e coloque nesta pasta

## Após baixar os dados

```bash
cd python
pip install -r requirements.txt
python run_all.py
```

Depois abra `frontend/index.html` no navegador.
