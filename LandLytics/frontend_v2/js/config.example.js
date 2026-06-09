// MODELO de configuração local — NÃO é usado em runtime e NÃO contém segredo.
//
// O arquivo real, js/config.js, é GERADO por python/main.py a partir da variável
// de ambiente MAPBOX_TOKEN (os.getenv) e fica no .gitignore (não sobe pro GitHub).
//
// Para rodar o mapa dos EUA (usa.html):
//   1. Crie uma conta grátis em https://www.mapbox.com e gere um token público (pk.).
//   2. Defina a variável de ambiente:
//        PowerShell:  $env:MAPBOX_TOKEN = "pk...."
//        Linux/Mac:   export MAPBOX_TOKEN="pk...."
//   3. Rode:  python python/main.py   (gera js/config.js)
//
// Veja o README, seção "Configurar o Mapbox", para os detalhes.
window.LANDLYTICS_CONFIG = {
  MAPBOX_TOKEN: "COLE_AQUI_SEU_TOKEN_PUBLICO_DO_MAPBOX_pk"
};
