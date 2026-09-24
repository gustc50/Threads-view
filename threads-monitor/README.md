# Threads Monitor

Monitora publicações do **Threads** por palavras-chave usando a **API oficial da Meta** e salva os links (permalinks) em uma planilha `.xlsx`, sem repetir publicações já coletadas.

---

## 1. Pré-requisitos

- Python 3.10 ou superior
- Uma conta no [Meta for Developers](https://developers.facebook.com/) com um app configurado para a **Threads API**

### 1.1 Criar o app na Meta

1. Acesse <https://developers.facebook.com/apps/> e crie um novo app do tipo **Business**.
2. Em *Produtos*, adicione **Threads**.
3. Em *Threads > Configurações*, peça as permissões:
   - `threads_basic`
   - `threads_keyword_search`
4. Passe pelo fluxo de OAuth do Threads e gere um **long-lived access token** (60 dias).
5. Copie também o `App ID` e o `App Secret` (necessários apenas para o `refresh_token.py`).

> Documentação de referência:
> - Keyword Search: <https://developers.facebook.com/docs/threads/keyword-search>
> - Tokens de longa duração: <https://developers.facebook.com/docs/threads/get-started/long-lived-tokens>

---

## 2. Instalação

```bash
git clone <este-repo>
cd threads-monitor
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/Mac:
source .venv/bin/activate

pip install -r requirements.txt
```

---

## 3. Configuração

Há **duas maneiras** de fornecer o token — escolha uma:

### A) Via `.env` (recomendado)

```bash
cp .env.example .env
```

Edite `.env` e preencha:

```
THREADS_ACCESS_TOKEN=seu_token_long_lived
THREADS_APP_ID=seu_app_id
THREADS_APP_SECRET=seu_app_secret
MAX_PAGES=3
SEARCH_TYPE=RECENT
```

### B) Aba de configurações (`settings.py`) — para teste rápido

Abra `settings.py`, procure o bloco marcado **`ABA DE CONFIGURACOES`** e cole seu token dentro das variáveis:

```python
TEST_ACCESS_TOKEN = "cole_aqui_para_testar"
TEST_APP_ID       = ""
TEST_APP_SECRET   = ""
```

Se o `.env` estiver preenchido, ele **tem prioridade** sobre esses valores.

### 3.1 Palavras-chave

Edite `keywords.txt` (uma por linha). Linhas começadas com `#` são ignoradas.

```
inteligencia artificial
python
open source
```

---

## 4. Como rodar

### Linha de comando

```bash
python main.py             # usa o SEARCH_TYPE do .env (default RECENT)
python main.py --tipo TOP  # força TOP
python main.py --tipo RECENT
```

### Windows (script `.bat`)

Dê duplo-clique em `run.bat`, ou:

```bat
run.bat
run.bat RECENT
run.bat TOP
```

Na **primeira execução** o `run.bat` cria automaticamente o `.venv` e instala as dependências.

---

## 5. Saída

- **`resultados.xlsx`** — planilha com colunas:
  `data_coleta`, `palavra_chave`, `usuario`, `data_publicacao`, `texto`, `link`.
- **`seen_ids.json`** — cache dos ids já coletados. **Não apague**: é o que evita repetição entre execuções.

---

## 6. Renovando o token (long-lived)

O token de longa duração vale 60 dias. Renove antes disso com:

```bash
python refresh_token.py
```

O script:
- Chama `GET /refresh_access_token`
- Atualiza `THREADS_ACCESS_TOKEN` dentro do `.env`
- Alerta no log se faltar **menos de 10 dias** para expirar

---

## 7. Testes

Testes usam respostas simuladas (mock) — **não fazem chamadas reais** à API.

```bash
pytest
```

Cobrem:
- Deduplicação por id + persistência do `seen_ids.json`
- Resposta vazia da API
- Paginação até `max_pages`
- Token inválido/expirado
- Rate limit (retry + falha persistente)

---

## 8. Estrutura do projeto

```
threads-monitor/
├── main.py              # Ponto de entrada
├── settings.py          # ABA DE CONFIGURACOES (token de teste + constantes)
├── threads_client.py    # Cliente HTTP da Threads API (retry, paginacao)
├── storage.py           # Planilha + seen_ids
├── refresh_token.py     # Renova o long-lived token
├── keywords.txt         # Lista de palavras-chave
├── requirements.txt
├── run.bat              # Atalho para Windows
├── .env.example
├── .gitignore
└── tests/
    ├── test_dedup.py
    └── test_api_response.py
```

---

## 9. Primeira execução — passo a passo

1. Preencha o token em `.env` **ou** em `settings.py` (bloco `ABA DE CONFIGURACOES`).
2. Ajuste `keywords.txt`.
3. Rode `python main.py` (ou `run.bat` no Windows).
4. Abra `resultados.xlsx`. Da segunda execução em diante, só entram publicações novas.
