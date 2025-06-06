# 📝 Documentação de Endpoints de Relatórios

Este arquivo reúne todos os endpoints de relatórios implementados em:
- `app/api/routes/relatorios_dinamico.py`
- `app/api/routes/relatorios.py`

---
## 1. Relatórios Dinâmicos (`relatorios_dinamico.py`)

### 1.1 GET `/backend/v1/relatorios/dinamico`
- **Query Params**:
  - `recurso_id` (int)             – filtra por recurso
  - `equipe_id` (int)              – filtra por equipe
  - `secao_id` (int)               – filtra por seção
  - `projeto_id` (int)             – filtra por projeto
  - `data_inicio` (string)         – `YYYY-MM-DD` ou `DD/MM/YYYY`
  - `data_fim`    (string)         – `YYYY-MM-DD` ou `DD/MM/YYYY`
  - `agrupar_por` (multi string)   – valores válidos: `recurso`, `equipe`, `secao`, `projeto`, `mes`, `ano`
- **Validação**: retorna `400` se `agrupar_por` contiver valor inválido.
- **Response 200 OK**
  ```json
  {
    "items": [
      { "recurso_id": 10, "nome_recurso": "Fulano", "mes": 6, "ano": 2025, "total_horas": 42.5 },
      ...
    ]
  }
  ```
- **Response 400**
  ```json
  { "detail": "Agrupamentos inválidos: {...}. Valores válidos: {...}" }
  ```

### 1.2 GET `/backend/v1/relatorios/horas-disponiveis`
- **Query Params**:
  - `recurso_id` (int)
  - `ano` (int)
  - `mes` (int)
  - `equipe_id` (int)
  - `secao_id` (int)
- **Response 200 OK**
  ```json
  {
    "items": [
      { "recurso_id": 10, "ano":2025, "mes":6, "horas_disponiveis_mes":160.00 },
      ...
    ]
  }
  ```

---
## 2. Relatórios Legados (`relatorios.py`)

> Usa `parse_date_flex` para aceitar datas em `YYYY-MM-DD` ou `DD/MM/YYYY`.

### 2.1 GET `/backend/v1/relatorios/horas-apontadas`
- **Query Params**:
  - `recurso_id`, `projeto_id`, `equipe_id`, `secao_id` (int)
  - `data_inicio`, `data_fim` (string)
  - `fonte_apontamento` (`JIRA` | `MANUAL`)
  - `agrupar_por_recurso`, `agrupar_por_projeto`, `agrupar_por_data`, `agrupar_por_mes` (bool)
- **Response 200 OK**
  ```json
  [ { /* campos do relatório */ }, ... ]
  ```

### 2.2 GET `/backend/v1/relatorios/comparativo-planejado-realizado`
- **Query Params**:
  - `ano` (int, obrigatório)
  - `mes` (int, opcional)
  - `recurso_id`, `projeto_id`, `equipe_id`, `secao_id` (int)
- **Response 200 OK**
  ```json
  { "items": [ { /* campos comparativo */ } ] }
  ```

### 2.3 GET `/backend/v1/relatorios/planejado-vs-realizado`
- **Query Params**:
  - `ano` (int, obrigatório)
  - `mes` (int, opcional)
  - `projeto_id`, `recurso_id`, `equipe_id`, `secao_id` (int)
- **Response 200 OK**
  ```json
  { "items": [ { /* campos */ } ] }
  ```

### 2.4 GET `/backend/v1/relatorios/disponibilidade-recursos`
- **Query Params**:
  - `ano` (int, obrigatório)
  - `mes` (int, opcional)
  - `recurso_id`, `equipe_id`, `secao_id` (int)
- **Response 200 OK**
  ```json
  { "items": [ { /* disponibilidade */ } ] }
  ```

---
## 3. Tratamento de Erros
- `400 Bad Request`: parâmetro inválido.
- `401 Unauthorized`: token ausente/inválido.
- `404 Not Found`: recurso não encontrado.
- `422 Unprocessable Entity`: formato de data inválido.
- `500 Internal Server Error`: erro interno.

---
## 4. Observações
- **Autenticação**: header `Authorization: Bearer <token>`.
- **Paginação**: `skip` e `limit` quando aplicável.
- **Formato de datas**: `YYYY-MM-DD` ou `DD/MM/YYYY`.
- Endpoints dinâmicos retornam `{ "items": [...] }`; `/horas-apontadas` retorna array puro.
