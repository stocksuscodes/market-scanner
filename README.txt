WYCKOFF + SLJ SCANNER — Flask + Alpaca
=======================================

INSTALAÇÃO
----------
pip install -r requirements.txt


CONFIGURAÇÃO
------------
Edita app.py e preenche as tuas keys:

  ALPACA_API_KEY    = "PKxxxxxxxxxxxxxxxx"
  ALPACA_SECRET_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

Ou usa variáveis de ambiente (recomendado):

  Windows:
    set ALPACA_API_KEY=PKxxxxxxxxxxxxxxxx
    set ALPACA_SECRET_KEY=xxxxxxxx

  Mac/Linux:
    export ALPACA_API_KEY=PKxxxxxxxxxxxxxxxx
    export ALPACA_SECRET_KEY=xxxxxxxx

Para análise IA (opcional):
    export ANTHROPIC_API_KEY=sk-ant-xxxxxxxx


ONDE OBTER AS KEYS ALPACA
--------------------------
1. Regista-te em https://alpaca.markets (gratuito)
2. Dashboard → API Keys → Generate New Key
3. Copia API Key ID e Secret Key
4. O plano gratuito usa o feed IEX (dados ligeiramente atrasados mas funcionais)


COMO CORRER
-----------
  python app.py

Acede em: http://localhost:5000


ESTRUTURA
---------
scanner/
  app.py              ← backend Flask + lógica Wyckoff/SLJ
  requirements.txt    ← dependências Python
  README.txt          ← este ficheiro
  static/
    index.html        ← dashboard web (abre em localhost:5000)


ROTAS DA API
------------
  GET  /api/sectores          → lista de sectores e tickers
  GET  /api/mercado           → estado VTI / mercado geral
  GET  /api/ranking           → ranking sectorial momentum 10d
  POST /api/scan              → executa o scan completo
  POST /api/ai-analysis       → análise Wyckoff/SLJ por IA
  GET  /api/preco/<ticker>    → preço real-time de um ticker
