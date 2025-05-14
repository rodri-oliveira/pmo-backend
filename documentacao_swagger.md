# Documentação da API - WEG Automação PMO

## Visão Geral

Esta documentação descreve os endpoints disponíveis na API do Sistema de Gestão de Projetos e Melhorias da WEG.

**URL Base**: `/backend/v1`

## Autenticação

A API utiliza autenticação via token OAuth2. Todos os endpoints (exceto o webhook do Jira) requerem autenticação.

### Endpoints de Autenticação

#### Login

```
POST /token
```

**Descrição**: Autentica um usuário e retorna um token de acesso.

**Parâmetros**:
- `username`: Nome de usuário
- `password`: Senha do usuário

**Respostas**:
- `200 OK`: Autenticação bem-sucedida
  ```json
  {
    "access_token": "string",
    "token_type": "bearer"
  }
  ```
- `401 Unauthorized`: Credenciais inválidas

## Alocações

Endpoints para gerenciar alocações de recursos em projetos.

### Listar Alocações

```
GET /alocacoes/
```

**Descrição**: Lista alocações com opção de filtros.

**Parâmetros**:
- `recurso_id` (query, opcional): Filtrar por ID do recurso
- `projeto_id` (query, opcional): Filtrar por ID do projeto
- `data_inicio` (query, opcional): Filtrar por data inicial do período (formatos: YYYY-MM-DD ou DD/MM/YYYY)
- `data_fim` (query, opcional): Filtrar por data final do período (formatos: YYYY-MM-DD ou DD/MM/YYYY)

**Respostas**:
- `200 OK`: Lista de alocações
  ```json
  [
    {
      "id": 0,
      "recurso_id": 0,
      "projeto_id": 0,
      "data_inicio": "2023-01-01",
      "data_fim": "2023-12-31",
      "percentual_alocacao": 0,
      "horas_alocadas": 0,
      "recurso_nome": "string",
      "projeto_nome": "string"
    }
  ]
  ```
- `400 Bad Request`: Erro de validação
- `500 Internal Server Error`: Erro do servidor

### Obter Alocação por ID

```
GET /alocacoes/{alocacao_id}
```

**Descrição**: Obtém uma alocação pelo ID.

**Parâmetros**:
- `alocacao_id` (path): ID da alocação

**Respostas**:
- `200 OK`: Dados da alocação
- `404 Not Found`: Alocação não encontrada
- `500 Internal Server Error`: Erro do servidor

### Criar Alocação

```
POST /alocacoes/
```

**Descrição**: Cria uma nova alocação de recurso em projeto.

**Corpo da Requisição**:
```json
{
  "recurso_id": 0,         // Obrigatório
  "projeto_id": 0,         // Obrigatório
  "data_inicio": "2023-01-01", // Obrigatório
  "data_fim": "2023-12-31",    // Obrigatório
  "percentual_alocacao": 0,    // Obrigatório
  "horas_alocadas": 0          // Obrigatório
}
```

**Respostas**:
- `201 Created`: Alocação criada com sucesso
- `400 Bad Request`: Erro de validação
- `500 Internal Server Error`: Erro do servidor

### Atualizar Alocação

```
PUT /alocacoes/{alocacao_id}
```

**Descrição**: Atualiza uma alocação existente.

**Parâmetros**:
- `alocacao_id` (path): ID da alocação

**Corpo da Requisição**:
```json
{
  "recurso_id": 0,         // Opcional
  "projeto_id": 0,         // Opcional
  "data_inicio": "2023-01-01", // Opcional
  "data_fim": "2023-12-31",    // Opcional
  "percentual_alocacao": 0,    // Opcional
  "horas_alocadas": 0          // Opcional
}
```

**Respostas**:
- `200 OK`: Alocação atualizada com sucesso
- `400 Bad Request`: Erro de validação
- `404 Not Found`: Alocação não encontrada
- `500 Internal Server Error`: Erro do servidor

### Excluir Alocação

```
DELETE /alocacoes/{alocacao_id}
```

**Descrição**: Remove uma alocação.

**Parâmetros**:
- `alocacao_id` (path): ID da alocação

**Respostas**:
- `204 No Content`: Alocação removida com sucesso
- `404 Not Found`: Alocação não encontrada
- `500 Internal Server Error`: Erro do servidor

## Projetos

Endpoints para gerenciamento de projetos e seus status.

### Listar Projetos

```
GET /projetos/
```

**Descrição**: Lista todos os projetos com opção de filtros.

**Parâmetros**:
- `nome` (query, opcional): Filtrar por nome do projeto
- `status_projeto` (query, opcional): Filtrar por status do projeto
- `ativo` (query, opcional): Filtrar por projetos ativos/inativos

**Respostas**:
- `200 OK`: Lista de projetos
- `500 Internal Server Error`: Erro do servidor

### Obter Projeto por ID

```
GET /projetos/{projeto_id}
```

**Descrição**: Obtém um projeto pelo ID.

**Parâmetros**:
- `projeto_id` (path): ID do projeto

**Respostas**:
- `200 OK`: Dados do projeto
- `404 Not Found`: Projeto não encontrado
- `500 Internal Server Error`: Erro do servidor

### Criar Projeto

```
POST /projetos/
```

**Descrição**: Cria um novo projeto.

**Corpo da Requisição**:
```json
{
  "nome": "string",           // Obrigatório
  "status_projeto_id": 0,     // Obrigatório
  "jira_project_key": "string", // Opcional
  "codigo_empresa": "string",   // Opcional
  "descricao": "string",        // Opcional
  "data_inicio": "2023-01-01",  // Opcional
  "data_fim": "2023-12-31"      // Opcional
}
```

**Respostas**:
- `201 Created`: Projeto criado com sucesso
- `400 Bad Request`: Erro de validação
- `500 Internal Server Error`: Erro do servidor

### Atualizar Projeto

```
PUT /projetos/{projeto_id}
```

**Descrição**: Atualiza um projeto existente.

**Parâmetros**:
- `projeto_id` (path): ID do projeto

**Corpo da Requisição**:
```json
{
  "nome": "string",           // Opcional
  "status_projeto_id": 0,     // Opcional
  "jira_project_key": "string", // Opcional
  "codigo_empresa": "string",   // Opcional
  "descricao": "string",        // Opcional
  "data_inicio": "2023-01-01",  // Opcional
  "data_fim": "2023-12-31"      // Opcional
}
```

**Respostas**:
- `200 OK`: Projeto atualizado com sucesso
- `400 Bad Request`: Erro de validação
- `404 Not Found`: Projeto não encontrado
- `500 Internal Server Error`: Erro do servidor

### Excluir Projeto

```
DELETE /projetos/{projeto_id}
```

**Descrição**: Remove um projeto.

**Parâmetros**:
- `projeto_id` (path): ID do projeto

**Respostas**:
- `204 No Content`: Projeto removido com sucesso
- `404 Not Found`: Projeto não encontrado
- `409 Conflict`: Projeto possui dependências (alocações)
- `500 Internal Server Error`: Erro do servidor

## Recursos

Endpoints para gerenciamento de recursos humanos.

### Listar Recursos

```
GET /recursos/
```

**Descrição**: Lista todos os recursos com opção de filtros.

**Parâmetros**:
- `nome` (query, opcional): Filtrar por nome do recurso
- `equipe_id` (query, opcional): Filtrar por equipe
- `ativo` (query, opcional): Filtrar por recursos ativos/inativos

**Respostas**:
- `200 OK`: Lista de recursos
- `500 Internal Server Error`: Erro do servidor

### Obter Recurso por ID

```
GET /recursos/{recurso_id}
```

**Descrição**: Obtém um recurso pelo ID.

**Parâmetros**:
- `recurso_id` (path): ID do recurso

**Respostas**:
- `200 OK`: Dados do recurso
- `404 Not Found`: Recurso não encontrado
- `500 Internal Server Error`: Erro do servidor

### Criar Recurso

```
POST /recursos/
```

**Descrição**: Cria um novo recurso.

**Corpo da Requisição**:
```json
{
  "nome": "string",           // Obrigatório
  "email": "string",          // Obrigatório
  "equipe_id": 0,             // Obrigatório
  "jira_account_id": "string", // Opcional
  "horas_diarias": 0,          // Obrigatório
  "ativo": true                // Opcional (default: true)
}
```

**Respostas**:
- `201 Created`: Recurso criado com sucesso
- `400 Bad Request`: Erro de validação
- `500 Internal Server Error`: Erro do servidor

## Equipes

Endpoints para gerenciamento de equipes.

### Listar Equipes

```
GET /equipes/
```

**Descrição**: Lista todas as equipes com opção de filtros.

**Parâmetros**:
- `nome` (query, opcional): Filtrar por nome da equipe
- `secao_id` (query, opcional): Filtrar por seção

**Respostas**:
- `200 OK`: Lista de equipes
- `500 Internal Server Error`: Erro do servidor

## Seções

Endpoints para gerenciamento de seções.

### Listar Seções

```
GET /secoes/
```

**Descrição**: Lista todas as seções.

**Respostas**:
- `200 OK`: Lista de seções
- `500 Internal Server Error`: Erro do servidor

## Status de Projetos

Endpoints para gerenciamento de status de projetos.

### Listar Status de Projetos

```
GET /status-projetos/
```

**Descrição**: Lista todos os status de projetos disponíveis.

**Respostas**:
- `200 OK`: Lista de status de projetos
- `500 Internal Server Error`: Erro do servidor

## Planejamento de Horas

Endpoints para gerenciamento de planejamento de horas.

### Listar Planejamentos

```
GET /planejamento-horas/
```

**Descrição**: Lista todos os planejamentos de horas com opção de filtros.

**Parâmetros**:
- `alocacao_id` (query, opcional): Filtrar por alocação
- `ano` (query, opcional): Filtrar por ano
- `mes` (query, opcional): Filtrar por mês

**Respostas**:
- `200 OK`: Lista de planejamentos
- `500 Internal Server Error`: Erro do servidor

## Apontamentos

Endpoints para gerenciamento de apontamentos de horas.

### Listar Apontamentos

```
GET /apontamentos/
```

**Descrição**: Lista todos os apontamentos com opção de filtros.

**Parâmetros**:
- `recurso_id` (query, opcional): Filtrar por recurso
- `projeto_id` (query, opcional): Filtrar por projeto
- `data_inicio` (query, opcional): Filtrar por data inicial
- `data_fim` (query, opcional): Filtrar por data final

**Respostas**:
- `200 OK`: Lista de apontamentos
- `500 Internal Server Error`: Erro do servidor

## Relatórios

Endpoints para geração de relatórios.

### Relatório de Alocação

```
GET /relatorios/alocacao
```

**Descrição**: Gera um relatório de alocação de recursos.

**Parâmetros**:
- `ano` (query): Ano para o relatório
- `mes` (query, opcional): Mês para o relatório
- `formato` (query, opcional): Formato do relatório (pdf, excel, csv)

**Respostas**:
- `200 OK`: Relatório gerado com sucesso
- `400 Bad Request`: Erro de validação
- `500 Internal Server Error`: Erro do servidor

## Saúde da Aplicação

Endpoints para verificar a saúde da aplicação.

### Verificar Status

```
GET /health/
```

**Descrição**: Verifica o status da aplicação e suas dependências.

**Respostas**:
- `200 OK`: Aplicação funcionando normalmente
- `500 Internal Server Error`: Problemas na aplicação

## Modelos de Dados

### Alocação

```json
{
  "id": 0,
  "recurso_id": 0,
  "projeto_id": 0,
  "data_inicio": "2023-01-01",
  "data_fim": "2023-12-31",
  "percentual_alocacao": 0,
  "horas_alocadas": 0,
  "recurso_nome": "string",
  "projeto_nome": "string"
}
```

### Projeto

```json
{
  "id": 0,
  "nome": "string",
  "status_projeto_id": 0,
  "status_projeto_nome": "string",
  "jira_project_key": "string",
  "codigo_empresa": "string",
  "descricao": "string",
  "data_inicio": "2023-01-01",
  "data_fim": "2023-12-31",
  "ativo": true
}
```

### Recurso

```json
{
  "id": 0,
  "nome": "string",
  "email": "string",
  "equipe_id": 0,
  "equipe_nome": "string",
  "jira_account_id": "string",
  "horas_diarias": 0,
  "ativo": true
}
```

### Equipe

```json
{
  "id": 0,
  "nome": "string",
  "secao_id": 0,
  "secao_nome": "string"
}
```

### Seção

```json
{
  "id": 0,
  "nome": "string"
}
```

### Status de Projeto

```json
{
  "id": 0,
  "nome": "string",
  "descricao": "string"
}
```

### Planejamento de Horas

```json
{
  "id": 0,
  "alocacao_id": 0,
  "ano": 0,
  "mes": 0,
  "horas_planejadas": 0
}
```

### Apontamento

```json
{
  "id": 0,
  "recurso_id": 0,
  "projeto_id": 0,
  "data": "2023-01-01",
  "horas_apontadas": 0,
  "jira_issue_key": "string",
  "descricao": "string"
}
```
