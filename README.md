# Golden Raspberry Awards - Pior Filme (GRA Awards API)

API RESTful, somente leitura, para consultar a lista de indicados e vencedores da categoria **Pior Filme** do Golden Raspberry Awards (Razzies).

Os dados são carregados a partir de um CSV (`data/Movielist.csv`) para um banco **SQLite em memória** na inicialização da aplicação. Não há persistência entre execuções: a cada start, o banco é recriado do zero a partir do CSV.

## Sumário

- [Stack](#stack)
- [Estrutura do projeto](#estrutura-do-projeto)
- [Como rodar](#como-rodar)
- [Configuração](#configuração)
- [Endpoints da API](#endpoints-da-api)
- [Testes](#testes)

## Stack

- **Python** 3.11+ (o código usa `int | None`, `from __future__ import annotations`, etc.)
- **FastAPI** (`fastapi[standard]`, que já inclui Uvicorn e o CLI `fastapi`)
- **SQLite** embutido (stdlib `sqlite3`), em memória

## Estrutura do projeto

```
outsera-v1/
├── pytest.ini                 # pythonpath=src para os testes importarem gra_awards
├── data/
│   └── Movielist.csv          # dataset fonte (delimitador ";")
├── src/
│   └── gra_awards/
│       ├── app.py             # criação da app FastAPI + lifespan (carga do CSV)
│       ├── config.py          # caminho do CSV (GRA_CSV_PATH)
│       ├── api/
│       │   ├── routes.py      # endpoints HTTP
│       │   └── schemas.py     # modelos de resposta (Pydantic)
│       ├── domain/
│       │   ├── intervals.py   # regra de intervalo entre prêmios consecutivos
│       │   ├── producers.py   # separação de produtores (texto livre -> lista)
│       │   └── studios.py     # separação de estúdios
│       └── infra/
│           ├── database.py    # schema do SQLite em memória
│           ├── csv_loader.py  # ETL do CSV -> SQLite
│           └── repository.py  # queries
└── tests/
    ├── conftest.py             # fixtures: connection, loaded_connection, client
    ├── fixtures/
    │   └── movies_sample.csv   # dataset fixo usado pelos testes de infra/api
    ├── domain/                 # testes das regras puras
    ├── infra/                  # testes de csv_loader e repository
    └── api/                    # testes end-to-end dos endpoints
```

Arquitetura em camadas: `api` (HTTP/schemas) → `domain` (regras de negócio puras) → `infra` (SQLite/CSV).

## Como rodar

```bash
# 1. Criar e ativar um ambiente virtual
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 2. Instalar dependências
pip install -r requirements.txt
# (opcional, para desenvolvimento/testes)
pip install -r requirements-dev.txt

# 3. Rodar a aplicação
fastapi dev src/gra_awards/app.py
```

A aplicação sobe em `http://127.0.0.1:8000` por padrão.

Alternativas para o passo 3:

```bash
# Modo produção (fastapi CLI)
fastapi run src/gra_awards/app.py

# Diretamente via Uvicorn
uvicorn gra_awards.app:app --reload --app-dir src
```

Documentação interativa gerada automaticamente pelo FastAPI:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Configuração

| Variável       | Padrão                    | Descrição                                              |
|----------------|----------------------------|----------------------------------------------------------|
| `GRA_CSV_PATH` | `data/Movielist.csv`      | Caminho do CSV carregado na inicialização da aplicação. |

Não há outras variáveis de ambiente, arquivos `.env` ou banco externo — a aplicação é autocontida.

## Endpoints da API

Todos os endpoints são `GET` (API somente leitura).

### `GET /producers/intervals`

Retorna o(s) produtor(es) com o **maior** intervalo entre dois prêmios consecutivos e o(s) com o **menor** intervalo. Empates produzem múltiplos elementos na lista; se não houver produtor elegível, as listas vêm vazias (HTTP 200).

**Resposta `200`:**

```json
{
  "min": [
    {
      "producer": "Producer Name",
      "interval": 1,
      "previousWin": 2008,
      "followingWin": 2009
    }
  ],
  "max": [
    {
      "producer": "Producer Name",
      "interval": 13,
      "previousWin": 1990,
      "followingWin": 2003
    }
  ]
}
```

### `GET /movies`

Lista paginada de filmes indicados/vencedores, com filtros combináveis.

**Query params:**

| Parâmetro | Tipo   | Padrão | Descrição                                        |
|-----------|--------|--------|---------------------------------------------------|
| `year`    | int    | —      | Filtra pelo ano da indicação                      |
| `winner`  | bool   | —      | `true` só vencedores, `false` só não vencedores   |
| `page`    | int    | `1`    | Página desejada (`>= 1`)                          |
| `size`    | int    | `50`   | Itens por página (`>= 1` e `<= 100`)              |

**Resposta `200`:**

```json
{
  "items": [
    {
      "id": 1,
      "year": 1980,
      "title": "Can't Stop the Music",
      "studios": ["Associated Film Distribution"],
      "producers": ["Allan Carr"],
      "winner": true
    }
  ],
  "page": 1,
  "size": 50,
  "total": 206
}
```

`total` reflete o total de filmes que satisfazem os filtros (em todas as páginas), independente do tamanho da página retornada.

### `GET /movies/{movie_id}`

Retorna um único filme pelo identificador.

**Path param:** `movie_id` (int)

**Resposta `200`:**

```json
{
  "id": 1,
  "year": 1980,
  "title": "Can't Stop the Music",
  "studios": ["Associated Film Distribution"],
  "producers": ["Allan Carr"],
  "winner": true
}
```

**Resposta `404`** (filme inexistente):

```json
{
  "detail": "Filme nao encontrado"
}
```

## Testes

A suíte cobre as três camadas do projeto:

- `tests/domain/` — funções puras (`split_producers`, `split_studios`, `compute_award_intervals`), incluindo casos de empate, deduplicação e listas vazias.
- `tests/infra/` — carga do CSV para o SQLite (`csv_loader`) e as consultas do `repository` (filtros, paginação, ordenação).
- `tests/api/` — endpoints via `TestClient`, cobrindo filtros combinados, paginação, validação de query params, 404 e o formato camelCase de `/producers/intervals`.

Rodar com (após instalar `requirements-dev.txt`):

```bash
pytest
```
