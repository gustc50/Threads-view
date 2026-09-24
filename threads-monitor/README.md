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

### Interface web local (recomendado)

Abre uma página no navegador com três abas — **Configurações**, **Execução** (log ao vivo) e **Resultados** — rodando só na sua máquina (`http://127.0.0.1:5000`).

- **Windows:** duplo-clique em **`run.bat`**. Na primeira execução ele cria o `.venv`, instala as dependências e abre o navegador sozinho.
- **Linux/Mac ou linha de comando:**
  ```bash
  python app.py
  ```
  O navegador abre automaticamente. Para encerrar, use `Ctrl+C` no terminal (ou feche a janela preta no Windows).

Na aba **Configurações** você cola o token da API, define tipo/páginas e as palavras-chave, e clica em **Salvar** (grava no `.env`). Na aba **Execução**, o botão **Rodar agora** dispara a coleta e mostra o progresso em tempo real. A aba **Resultados** lista os links coletados a partir de `resultados.xlsx`.

> O token é gravado localmente no `.env` e nunca sai da sua máquina.

### Modo terminal (opcional)

```bash
python main.py             # usa o SEARCH_TYPE do .env (default RECENT)
python main.py --tipo TOP  # força TOP
python main.py --tipo RECENT
```

No Windows, o **`run_cli.bat`** faz o mesmo sem abrir o navegador (`run_cli.bat`, `run_cli.bat TOP`).

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
├── app.py               # Interface web (Flask) com as 3 abas
├── templates/index.html # Pagina da interface
├── main.py              # Ponto de entrada da CLI
├── collector.py         # Logica de coleta (compartilhada CLI + web)
├── settings.py          # ABA DE CONFIGURACOES + leitura/escrita de .env/keywords
├── threads_client.py    # Cliente HTTP da Threads API (retry, paginacao)
├── storage.py           # Planilha + seen_ids
├── refresh_token.py     # Renova o long-lived token
├── keywords.txt         # Lista de palavras-chave
├── requirements.txt
├── run.bat              # Abre a interface web no navegador (Windows)
├── run_cli.bat          # Modo terminal (Windows)
├── .env.example
├── .gitignore
└── tests/
    ├── test_dedup.py
    └── test_api_response.py
```

---

## 9. Primeira execução — passo a passo

1. **Windows:** duplo-clique em `run.bat`. **Outros:** `pip install -r requirements.txt` e depois `python app.py`.
2. O navegador abre em `http://127.0.0.1:5000`. Na aba **Configurações**, cole o token, ajuste as palavras-chave e clique em **Salvar**.
3. Vá na aba **Execução** e clique em **Rodar agora** — acompanhe o log ao vivo.
4. Veja os links na aba **Resultados** (também salvos em `resultados.xlsx`). Da segunda execução em diante, só entram publicações novas.
