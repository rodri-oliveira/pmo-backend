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

#### Obter Token de Acesso

**Endpoint:** `POST /backend/v1/auth/token`

Autentica um usuário e retorna um token de acesso JWT.

**Corpo da Requisição (application/x-www-form-urlencoded):**

- `username` (string, obrigatório): O email do usuário.
- `password` (string, obrigatório): A senha do usuário.

**Resposta de Sucesso (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Campos da Resposta:**

- `access_token` (string): O token JWT.
- `token_type` (string): Tipo do token, geralmente "bearer".

**Respostas de Erro:**

- `401 Unauthorized`: Credenciais inválidas ou usuário inativo.
  ```json
  {
    "detail": "Email ou senha incorretos" 
  }
  ```
  ou
  ```json
  {
    "detail": "Usuário inativo"
  }
  ```

### Criar Usuário

**Endpoint:** `POST /backend/v1/usuarios`

Cria um novo usuário no sistema. **Requer autenticação de administrador (Bearer Token JWT).**

**Segurança:**

- `Authorization: Bearer <seu_token_jwt>`

**Corpo da Requisição (application/json - Schema: `UserCreate`):**

```json
{
  "email": "novo.usuario@example.com",
  "nome": "Novo Usuário de Teste",
  "password": "senhaSegura123",
  "role": "recurso",
  "recurso_id": 10,
  "ativo": true
}
```

**Campos da Requisição:**

- `email` (string, formato de email, obrigatório): Email do novo usuário.
- `nome` (string, obrigatório): Nome completo do usuário.
- `password` (string, mínimo 8 caracteres, obrigatório): Senha para o novo usuário.
- `role` (string enum: ["admin", "gestor", "recurso"], obrigatório): Papel do usuário.
- `recurso_id` (integer, opcional): ID do recurso ao qual este usuário está associado, se aplicável.
- `ativo` (boolean, opcional, default: `true`): Define se o usuário está ativo.

**Resposta de Sucesso (200 OK - Schema: `UserBase`):**

```json
{
  "email": "novo.usuario@example.com",
  "nome": "Novo Usuário de Teste",
  "role": "recurso",
  "recurso_id": 10,
  "ativo": true
}
```

**Campos da Resposta:**

- `email` (string): Email do usuário criado.
- `nome` (string): Nome do usuário criado.
- `role` (string enum): Papel do usuário.
- `recurso_id` (integer, opcional): ID do recurso associado.
- `ativo` (boolean): Status de ativação do usuário.

**Respostas de Erro:**

- `400 Bad Request`: Email já está em uso ou dados inválidos (ex: senha muito curta).
  ```json
  {
    "detail": "Email já está em uso"
  }
  ```
  ou
  ```json
  {
    "detail": [
      {
        "loc": ["body", "password"],
        "msg": "A senha deve ter pelo menos 8 caracteres",
        "type": "value_error"
      }
    ]
  }
  ```
- `401 Unauthorized`: Token JWT ausente, inválido ou expirado.
- `403 Forbidden`: O usuário autenticado não possui permissão de administrador para criar usuários.

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

### Criar Recurso

```
POST /recursos/
```

**Descrição**: Cria um novo recurso humano.

**Corpo da Requisição (application/json - Schema: `RecursoCreateDTO`):**

```json
{
  "nome": "João Silva",
  "email": "joao.silva@example.com",
  "matricula": "12345",
  "cargo": "Desenvolvedor Pleno",
  "jira_user_id": "joao.silva.jira",
  "data_admissao": "2023-01-15",
  "equipe_principal_id": 1
}
```

**Campos da Requisição:**

- `nome` (string, obrigatório): Nome completo do recurso.
- `email` (string, EmailStr, obrigatório): Email do recurso.
- `matricula` (string, opcional): Matrícula do recurso.
- `cargo` (string, opcional): Cargo do recurso.
- `jira_user_id` (string, opcional): ID do usuário no Jira.
- `data_admissao` (date, opcional, formato "YYYY-MM-DD"): Data de admissão do recurso.
- `equipe_principal_id` (integer, opcional): ID da equipe principal do recurso.

**Resposta de Sucesso (201 CREATED - Schema: `RecursoDTO`):**

```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao.silva@example.com",
  "matricula": "12345",
  "cargo": "Desenvolvedor Pleno",
  "jira_user_id": "joao.silva.jira",
  "data_admissao": "2023-01-15",
  "equipe_principal_id": 1,
  "ativo": true,
  "data_criacao": "2024-07-30T11:00:00Z",
  "data_atualizacao": "2024-07-30T11:00:00Z"
}
```

**Respostas de Erro:**

- `422 Unprocessable Entity`: Dados inválidos (ex: `equipe_principal_id` não existe, email inválido).
- `500 Internal Server Error`: Outros erros.

### Listar Recursos

```
GET /recursos/
```

**Descrição**: Lista todos os recursos com opção de filtros e paginação.

**Parâmetros (Query):**

- `skip` (integer, opcional, default: 0): Número de registros a pular.
- `limit` (integer, opcional, default: 100): Número máximo de registros (1 <= limit <= 1000).
- `apenas_ativos` (boolean, opcional, default: False): Filtrar por recursos ativos.
- `equipe_id` (integer, opcional): Filtrar recursos por ID da equipe principal.

**Resposta de Sucesso (200 OK - Schema: `List[RecursoDTO]`):**

```json
[
  {
    "id": 1,
    "nome": "João Silva",
    "email": "joao.silva@example.com",
    "matricula": "12345",
    "cargo": "Desenvolvedor Pleno",
    "jira_user_id": "joao.silva.jira",
    "data_admissao": "2023-01-15",
    "equipe_principal_id": 1,
    "ativo": true,
    "data_criacao": "2024-07-30T11:00:00Z",
    "data_atualizacao": "2024-07-30T11:00:00Z"
  },
  {
    "id": 2,
    "nome": "Maria Oliveira",
    "email": "maria.oliveira@example.com",
    "matricula": "67890",
    "cargo": "Analista de Sistemas",
    "jira_user_id": "maria.oliveira.jira",
    "data_admissao": "2022-06-20",
    "equipe_principal_id": null,
    "ativo": false,
    "data_criacao": "2024-07-29T14:00:00Z",
    "data_atualizacao": "2024-07-29T14:30:00Z"
  }
]
```

### Obter Recurso por ID

```
GET /recursos/{recurso_id}
```

**Descrição**: Obtém um recurso específico pelo seu ID.

**Parâmetros (Path):**

- `recurso_id` (integer, obrigatório): ID do recurso.

**Resposta de Sucesso (200 OK - Schema: `RecursoDTO`):**

```json
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao.silva@example.com",
  "matricula": "12345",
  "cargo": "Desenvolvedor Pleno",
  "jira_user_id": "joao.silva.jira",
  "data_admissao": "2023-01-15",
  "equipe_principal_id": 1,
  "ativo": true,
  "data_criacao": "2024-07-30T11:00:00Z",
  "data_atualizacao": "2024-07-30T11:00:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Recurso não encontrado.

### Atualizar Recurso

```
PUT /recursos/{recurso_id}
```

**Descrição**: Atualiza um recurso existente.

**Parâmetros (Path):**

- `recurso_id` (integer, obrigatório): ID do recurso a ser atualizado.

**Corpo da Requisição (application/json - Schema: `RecursoUpdateDTO`):**

```json
{
  "nome": "João Silva (Atualizado)",
  "email": "joao.silva.novo@example.com",
  "cargo": "Desenvolvedor Sênior",
  "ativo": true
}
```

**Campos da Requisição:**

- `nome` (string, opcional): Novo nome do recurso.
- `email` (string, EmailStr, opcional): Novo email do recurso.
- `matricula` (string, opcional): Nova matrícula.
- `cargo` (string, opcional): Novo cargo.
- `jira_user_id` (string, opcional): Novo ID do Jira.
- `data_admissao` (date, opcional, formato "YYYY-MM-DD"): Nova data de admissão.
- `equipe_principal_id` (integer, opcional): Novo ID da equipe principal.
- `ativo` (boolean, opcional): Novo status de ativação.

**Resposta de Sucesso (200 OK - Schema: `RecursoDTO`):**

```json
{
  "id": 1,
  "nome": "João Silva (Atualizado)",
  "email": "joao.silva.novo@example.com",
  "matricula": "12345",
  "cargo": "Desenvolvedor Sênior",
  "jira_user_id": "joao.silva.jira",
  "data_admissao": "2023-01-15",
  "equipe_principal_id": 1,
  "ativo": true,
  "data_criacao": "2024-07-30T11:00:00Z",
  "data_atualizacao": "2024-07-30T11:05:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Recurso não encontrado.
- `422 Unprocessable Entity`: Dados inválidos.
- `500 Internal Server Error`: Outros erros.

### Excluir Recurso

```
DELETE /recursos/{recurso_id}
```

**Descrição**: Exclui um recurso pelo seu ID.

**Parâmetros (Path):**

- `recurso_id` (integer, obrigatório): ID do recurso a ser excluído.

**Resposta de Sucesso (200 OK - Schema: `RecursoDTO`):** (Retorna os dados do recurso excluído)

```json
{
  "id": 1,
  "nome": "João Silva (Excluído)",
  "email": "joao.silva.novo@example.com",
  "matricula": "12345",
  "cargo": "Desenvolvedor Sênior",
  "jira_user_id": "joao.silva.jira",
  "data_admissao": "2023-01-15",
  "equipe_principal_id": 1,
  "ativo": false,
  "data_criacao": "2024-07-30T11:00:00Z",
  "data_atualizacao": "2024-07-30T11:05:00Z" 
}
```

**Respostas de Erro:**

- `404 Not Found`: Recurso não encontrado.

## Equipes

Endpoints para gerenciamento de equipes.

### Criar Equipe

```
POST /equipes/
```

**Descrição**: Cria uma nova equipe.

**Corpo da Requisição (application/json - Schema: `EquipeCreateDTO`):**

```json
{
  "nome": "Nova Equipe Exemplo",
  "descricao": "Descrição opcional da nova equipe.",
  "secao_id": 1
}
```

**Campos da Requisição:**

- `nome` (string, obrigatório): Nome da equipe.
- `descricao` (string, opcional): Descrição da equipe.
- `secao_id` (integer, obrigatório): ID da seção à qual a equipe pertence.

**Resposta de Sucesso (201 CREATED - Schema: `EquipeDTO`):**

```json
{
  "id": 1,
  "nome": "Nova Equipe Exemplo",
  "descricao": "Descrição opcional da nova equipe.",
  "secao_id": 1,
  "ativo": true,
  "data_criacao": "2024-07-29T10:00:00Z",
  "data_atualizacao": "2024-07-29T10:00:00Z"
}
```

**Respostas de Erro:**

- `422 Unprocessable Entity`: Dados inválidos.

### Listar Equipes

```
GET /equipes/
```

**Descrição**: Lista todas as equipes com opção de filtros e paginação.

**Parâmetros (Query):**

- `skip` (integer, opcional, default: 0): Número de registros a pular.
- `limit` (integer, opcional, default: 100): Número máximo de registros (1 <= limit <= 1000).
- `apenas_ativos` (boolean, opcional, default: False): Filtrar por equipes ativas.
- `secao_id` (integer, opcional): Filtrar equipes por ID da seção.

**Resposta de Sucesso (200 OK - Schema: `List[EquipeDTO]`):**

```json
[
  {
    "id": 1,
    "nome": "Equipe Alpha",
    "descricao": "Equipe de desenvolvimento frontend.",
    "secao_id": 1,
    "ativo": true,
    "data_criacao": "2024-07-29T10:00:00Z",
    "data_atualizacao": "2024-07-29T10:00:00Z"
  },
  {
    "id": 2,
    "nome": "Equipe Beta",
    "descricao": null,
    "secao_id": 2,
    "ativo": false,
    "data_criacao": "2024-07-28T15:30:00Z",
    "data_atualizacao": "2024-07-28T16:00:00Z"
  }
]
```

### Obter Equipe por ID

```
GET /equipes/{equipe_id}
```

**Descrição**: Obtém uma equipe específica pelo seu ID.

**Parâmetros (Path):**

- `equipe_id` (integer, obrigatório): ID da equipe.

**Resposta de Sucesso (200 OK - Schema: `EquipeDTO`):**

```json
{
  "id": 1,
  "nome": "Equipe Alpha",
  "descricao": "Equipe de desenvolvimento frontend.",
  "secao_id": 1,
  "ativo": true,
  "data_criacao": "2024-07-29T10:00:00Z",
  "data_atualizacao": "2024-07-29T10:00:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Equipe não encontrada.

### Atualizar Equipe

```
PUT /equipes/{equipe_id}
```

**Descrição**: Atualiza uma equipe existente.

**Parâmetros (Path):**

- `equipe_id` (integer, obrigatório): ID da equipe a ser atualizada.

**Corpo da Requisição (application/json - Schema: `EquipeUpdateDTO`):**

```json
{
  "nome": "Nome Atualizado da Equipe",
  "descricao": "Descrição atualizada.",
  "secao_id": 2,
  "ativo": false
}
```

**Campos da Requisição:**

- `nome` (string, opcional): Novo nome da equipe.
- `descricao` (string, opcional): Nova descrição da equipe.
- `secao_id` (integer, opcional): Novo ID da seção.
- `ativo` (boolean, opcional): Novo status de ativação da equipe.

**Resposta de Sucesso (200 OK - Schema: `EquipeDTO`):**

```json
{
  "id": 1,
  "nome": "Nome Atualizado da Equipe",
  "descricao": "Descrição atualizada.",
  "secao_id": 2,
  "ativo": false,
  "data_criacao": "2024-07-29T10:00:00Z",
  "data_atualizacao": "2024-07-29T10:05:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Equipe não encontrada.
- `422 Unprocessable Entity`: Dados inválidos.
- `500 Internal Server Error`: Outros erros.

### Excluir Equipe

```
DELETE /equipes/{equipe_id}
```

**Descrição**: Exclui uma equipe pelo seu ID.

**Parâmetros (Path):**

- `equipe_id` (integer, obrigatório): ID da equipe a ser excluída.

**Resposta de Sucesso (200 OK - Schema: `EquipeDTO`):** (Retorna os dados da equipe excluída)

```json
{
  "id": 1,
  "nome": "Equipe Excluída",
  "descricao": "Esta equipe foi excluída.",
  "secao_id": 1,
  "ativo": false,
  "data_criacao": "2024-07-29T10:00:00Z",
  "data_atualizacao": "2024-07-29T10:05:00Z" 
}
```

**Respostas de Erro:**

- `404 Not Found`: Equipe não encontrada.

## Seções

Endpoints para gerenciar seções.

### Criar Seção

```
POST /secoes/
```

**Descrição**: Cria uma nova seção.

**Corpo da Requisição (application/json - Schema: `SecaoCreateDTO`):**

```json
{
  "nome": "Nova Seção Exemplo",
  "descricao": "Descrição opcional da nova seção."
}
```

**Campos da Requisição:**

- `nome` (string, obrigatório): Nome da seção.
- `descricao` (string, opcional): Descrição da seção.

**Resposta de Sucesso (201 CREATED - Schema: `SecaoDTO`):**

```json
{
  "id": 1,
  "nome": "Nova Seção Exemplo",
  "descricao": "Descrição opcional da nova seção.",
  "ativo": true,
  "data_criacao": "2024-07-29T10:00:00Z",
  "data_atualizacao": "2024-07-29T10:00:00Z"
}
```

**Respostas de Erro:**

- `422 Unprocessable Entity`: Dados inválidos.

### Listar Seções

```
GET /secoes/
```

**Descrição**: Lista todas as seções com opção de filtros e paginação.

**Parâmetros (Query):**

- `skip` (integer, opcional, default: 0): Número de registros a pular.
- `limit` (integer, opcional, default: 100): Número máximo de registros (1 <= limit <= 1000).
- `apenas_ativos` (boolean, opcional, default: False): Filtrar por seções ativas.

**Resposta de Sucesso (200 OK - Schema: `List[SecaoDTO]`):**

```json
[
  {
    "id": 1,
    "nome": "Seção Exemplo 1",
    "descricao": "Descrição da Seção 1.",
    "ativo": true,
    "data_criacao": "2024-07-29T10:00:00Z",
    "data_atualizacao": "2024-07-29T10:00:00Z"
  },
  {
    "id": 2,
    "nome": "Seção Exemplo 2",
    "descricao": null,
    "ativo": false,
    "data_criacao": "2024-07-28T15:30:00Z",
    "data_atualizacao": "2024-07-28T16:00:00Z"
  }
]
```

### Obter Seção por ID

```
GET /secoes/{secao_id}
```

**Descrição**: Obtém uma seção específica pelo seu ID.

**Parâmetros (Path):**

- `secao_id` (integer, obrigatório): ID da seção.

**Resposta de Sucesso (200 OK - Schema: `SecaoDTO`):**

```json
{
  "id": 1,
  "nome": "Seção Exemplo 1",
  "descricao": "Descrição da Seção 1.",
  "ativo": true,
  "data_criacao": "2024-07-29T10:00:00Z",
  "data_atualizacao": "2024-07-29T10:00:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Seção não encontrada.

### Atualizar Seção

```
PUT /secoes/{secao_id}
```

**Descrição**: Atualiza uma seção existente.

**Parâmetros (Path):**

- `secao_id` (integer, obrigatório): ID da seção a ser atualizada.

**Corpo da Requisição (application/json - Schema: `SecaoUpdateDTO`):**

```json
{
  "nome": "Nome Atualizado da Seção",
  "descricao": "Descrição atualizada.",
  "ativo": false
}
```

**Campos da Requisição:**

- `nome` (string, opcional): Novo nome da seção.
- `descricao` (string, opcional): Nova descrição da seção.
- `ativo` (boolean, opcional): Novo status de ativação da seção.

**Resposta de Sucesso (200 OK - Schema: `SecaoDTO`):**

```json
{
  "id": 1,
  "nome": "Nome Atualizado da Seção",
  "descricao": "Descrição atualizada.",
  "ativo": false,
  "data_criacao": "2024-07-29T10:00:00Z",
  "data_atualizacao": "2024-07-29T10:05:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Seção não encontrada.
- `422 Unprocessable Entity`: Dados inválidos.

### Excluir Seção

```
DELETE /secoes/{secao_id}
```

**Descrição**: Exclui uma seção pelo seu ID.

**Parâmetros (Path):**

- `secao_id` (integer, obrigatório): ID da seção a ser excluída.

**Resposta de Sucesso (200 OK - Schema: `SecaoDTO`):** (Retorna os dados da seção excluída)

```json
{
  "id": 1,
  "nome": "Seção Excluída",
  "descricao": "Esta seção foi excluída.",
  "ativo": false,
  "data_criacao": "2024-07-29T10:00:00Z",
  "data_atualizacao": "2024-07-29T10:05:00Z" 
}
```

**Respostas de Erro:**

- `404 Not Found`: Seção não encontrada.

## Status de Projetos

Endpoints para gerenciar os diferentes status que um projeto pode assumir.

### Criar Status de Projeto

```
POST /status-projetos/
```

**Descrição**: Cria um novo status de projeto.

**Corpo da Requisição (application/json - Schema: `StatusProjetoCreateDTO`):**

```json
{
  "nome": "Em Análise",
  "descricao": "Projeto aguardando análise inicial.",
  "is_final": false,
  "ordem_exibicao": 1
}
```

**Campos da Requisição:**

- `nome` (string, obrigatório): Nome do status.
- `descricao` (string, opcional): Descrição detalhada do status.
- `is_final` (boolean, opcional, default: `false`): Indica se o status é um estado final de projeto.
- `ordem_exibicao` (integer, opcional): Ordem para exibição do status.

**Resposta de Sucesso (201 CREATED - Schema: `StatusProjetoDTO`):**

```json
{
  "id": 1,
  "nome": "Em Análise",
  "descricao": "Projeto aguardando análise inicial.",
  "is_final": false,
  "ordem_exibicao": 1,
  "data_criacao": "2024-07-31T12:00:00Z",
  "data_atualizacao": "2024-07-31T12:00:00Z"
}
```

**Respostas de Erro:**

- `422 Unprocessable Entity`: Dados inválidos.
- `500 Internal Server Error`: Outros erros.

### Listar Status de Projetos

```
GET /status-projetos/
```

**Descrição**: Lista todos os status de projeto cadastrados, com paginação.

**Parâmetros (Query):**

- `skip` (integer, opcional, default: 0): Número de registros a pular.
- `limit` (integer, opcional, default: 100): Número máximo de registros a retornar (1 <= limit <= 1000).

**Resposta de Sucesso (200 OK - Schema: `List[StatusProjetoDTO]`):**

```json
[
  {
    "id": 1,
    "nome": "Em Análise",
    "descricao": "Projeto aguardando análise inicial.",
    "is_final": false,
    "ordem_exibicao": 1,
    "data_criacao": "2024-07-31T12:00:00Z",
    "data_atualizacao": "2024-07-31T12:00:00Z"
  },
  {
    "id": 2,
    "nome": "Em Andamento",
    "descricao": "Projeto em fase de execução.",
    "is_final": false,
    "ordem_exibicao": 2,
    "data_criacao": "2024-07-31T12:05:00Z",
    "data_atualizacao": "2024-07-31T12:05:00Z"
  }
]
```

**Respostas de Erro:**

- `500 Internal Server Error`: Outros erros.

### Obter Status de Projeto por ID

```
GET /status-projetos/{status_id}
```

**Descrição**: Obtém um status de projeto específico pelo seu ID.

**Parâmetros (Path):**

- `status_id` (integer, obrigatório): ID do status de projeto.

**Resposta de Sucesso (200 OK - Schema: `StatusProjetoDTO`):**

```json
{
  "id": 1,
  "nome": "Em Análise",
  "descricao": "Projeto aguardando análise inicial.",
  "is_final": false,
  "ordem_exibicao": 1,
  "data_criacao": "2024-07-31T12:00:00Z",
  "data_atualizacao": "2024-07-31T12:00:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Status de projeto não encontrado.
- `500 Internal Server Error`: Outros erros.

### Atualizar Status de Projeto

```
PUT /status-projetos/{status_id}
```

**Descrição**: Atualiza um status de projeto existente.

**Parâmetros (Path):**

- `status_id` (integer, obrigatório): ID do status de projeto a ser atualizado.

**Corpo da Requisição (application/json - Schema: `StatusProjetoUpdateDTO`):**

```json
{
  "nome": "Análise Concluída",
  "descricao": "Análise inicial do projeto foi concluída.",
  "is_final": false
}
```

**Campos da Requisição:**

- `nome` (string, opcional): Novo nome do status.
- `descricao` (string, opcional): Nova descrição do status.
- `is_final` (boolean, opcional): Novo indicador se o status é final.
- `ordem_exibicao` (integer, opcional): Nova ordem de exibição.

**Resposta de Sucesso (200 OK - Schema: `StatusProjetoDTO`):**

```json
{
  "id": 1,
  "nome": "Análise Concluída",
  "descricao": "Análise inicial do projeto foi concluída.",
  "is_final": false,
  "ordem_exibicao": 1,
  "data_criacao": "2024-07-31T12:00:00Z",
  "data_atualizacao": "2024-07-31T12:10:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Status de projeto não encontrado para atualização.
- `422 Unprocessable Entity`: Dados inválidos.
- `500 Internal Server Error`: Outros erros.

### Excluir Status de Projeto

```
DELETE /status-projetos/{status_id}
```

**Descrição**: Exclui um status de projeto pelo seu ID.

**Parâmetros (Path):**

- `status_id` (integer, obrigatório): ID do status de projeto a ser excluído.

**Resposta de Sucesso (200 OK - Schema: `StatusProjetoDTO`):** (Retorna os dados do status de projeto excluído)

```json
{
  "id": 1,
  "nome": "Análise Concluída",
  "descricao": "Análise inicial do projeto foi concluída.",
  "is_final": false,
  "ordem_exibicao": 1,
  "data_criacao": "2024-07-31T12:00:00Z",
  "data_atualizacao": "2024-07-31T12:10:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Status de projeto não encontrado para exclusão.
- `500 Internal Server Error`: Outros erros.

## Planejamento de Horas

Endpoints para gerenciar o planejamento de horas de recursos em projetos.

### PlanejamentoHorasCreate

```yaml
PlanejamentoHorasCreate:
  type: object
  required:
    - alocacao_id
    - ano
    - mes
    - horas_planejadas
  properties:
    alocacao_id:
      type: integer
      description: ID da alocação do recurso ao projeto.
    ano:
      type: integer
      description: Ano do planejamento.
    mes:
      type: integer
      description: Mês do planejamento (1-12).
      minimum: 1
      maximum: 12
    horas_planejadas:
      type: number
      format: float
      description: Quantidade de horas planejadas.
  example:
    alocacao_id: 5
    ano: 2024
    mes: 9
    horas_planejadas: 80.5
```

### PlanejamentoHorasResponse

```yaml
PlanejamentoHorasResponse:
  type: object
  properties:
    id:
      type: integer
      description: ID único do planejamento de horas.
      readOnly: true
    alocacao_id:
      type: integer
      description: ID da alocação associada.
    projeto_id:
      type: integer
      description: ID do projeto associado (via alocação).
      readOnly: true
    recurso_id:
      type: integer
      description: ID do recurso associado (via alocação).
      readOnly: true
    ano:
      type: integer
      description: Ano do planejamento.
    mes:
      type: integer
      description: Mês do planejamento.
    horas_planejadas:
      type: number
      format: float
      description: Quantidade de horas planejadas.
  example:
    id: 12
    alocacao_id: 5
    projeto_id: 101
    recurso_id: 25
    ano: 2024
    mes: 9
    horas_planejadas: 80.5
```

### Criar ou Atualizar Planejamento de Horas

```
POST /planejamento-horas/
```

**Sumário**: Cria ou atualiza um planejamento de horas para uma alocação, ano e mês.

**Tags**: 
  - Planejamento de Horas

**Segurança**:
  - bearerAuth: []

**Corpo da Requisição**:

- `application/json` (Schema: `#/components/schemas/PlanejamentoHorasCreate`)

**Respostas**:

- `201 Created`: Planejamento criado/atualizado com sucesso.
  - Content: `application/json` (Schema: `#/components/schemas/PlanejamentoHorasResponse`)
- `400 Bad Request`: Dados inválidos (e.g., alocação não encontrada).
- `422 Unprocessable Entity`: Erro de validação dos dados de entrada.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPValidationError`)
- `500 Internal Server Error`: Erro interno no servidor.

### Listar Planejamentos por Alocação

```
GET /planejamento-horas/alocacao/{alocacao_id}
```

**Sumário**: Lista todos os planejamentos de horas para uma alocação específica.

**Tags**: 
  - Planejamento de Horas

**Segurança**:
  - bearerAuth: []

**Parâmetros (Path)**:

- `alocacao_id` (integer, obrigatório, `gt: 0`): ID da alocação.

**Respostas**:

- `200 OK`: Lista de planejamentos recuperada com sucesso.
  - Content: `application/json` (Schema: Array of `#/components/schemas/PlanejamentoHorasResponse`)
- `400 Bad Request`: ID da alocação inválido.
- `500 Internal Server Error`: Erro interno no servidor.

### Listar Planejamentos por Recurso e Período

```
GET /planejamento-horas/recurso/{recurso_id}
```

**Sumário**: Lista planejamentos de horas para um recurso em um período específico.

**Tags**: 
  - Planejamento de Horas

**Segurança**:
  - bearerAuth: []

**Parâmetros (Path)**:

- `recurso_id` (integer, obrigatório, `gt: 0`): ID do recurso.

**Parâmetros (Query)**:

- `ano` (integer, obrigatório, `gt: 0`): Ano para filtrar.
- `mes_inicio` (integer, opcional, default: 1, `ge: 1, le: 12`): Mês inicial do período.
- `mes_fim` (integer, opcional, default: 12, `ge: 1, le: 12`): Mês final do período.

**Respostas**:

- `200 OK`: Lista de planejamentos recuperada com sucesso.
  - Content: `application/json` (Schema: Array of `#/components/schemas/PlanejamentoHorasResponse`)
- `500 Internal Server Error`: Erro interno no servidor.

### Excluir Planejamento de Horas

```
DELETE /planejamento-horas/{planejamento_id}
```

**Sumário**: Remove um planejamento de horas pelo seu ID.

**Tags**: 
  - Planejamento de Horas

**Segurança**:
  - bearerAuth: []

**Parâmetros (Path)**:

- `planejamento_id` (integer, obrigatório, `gt: 0`): ID do planejamento a ser excluído.

**Respostas**:

- `204 No Content`: Planejamento excluído com sucesso.
- `404 Not Found`: Planejamento não encontrado.
- `500 Internal Server Error`: Erro interno no servidor.

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

## Status de Projetos

Endpoints para gerenciar os diferentes status que um projeto pode assumir.

### Criar Status de Projeto

```
POST /status-projetos/
```

**Descrição**: Cria um novo status de projeto.

**Corpo da Requisição (application/json - Schema: `StatusProjetoCreateDTO`):**

```json
{
  "nome": "Em Análise",
  "descricao": "Projeto aguardando análise inicial.",
  "is_final": false,
  "ordem_exibicao": 1
}
```

**Campos da Requisição:**

- `nome` (string, obrigatório): Nome do status.
- `descricao` (string, opcional): Descrição detalhada do status.
- `is_final` (boolean, opcional, default: `false`): Indica se o status é um estado final de projeto.
- `ordem_exibicao` (integer, opcional): Ordem para exibição do status.

**Resposta de Sucesso (201 CREATED - Schema: `StatusProjetoDTO`):**

```json
{
  "id": 1,
  "nome": "Em Análise",
  "descricao": "Projeto aguardando análise inicial.",
  "is_final": false,
  "ordem_exibicao": 1,
  "data_criacao": "2024-07-31T12:00:00Z",
  "data_atualizacao": "2024-07-31T12:00:00Z"
}
```

**Respostas de Erro:**

- `422 Unprocessable Entity`: Dados inválidos.
- `500 Internal Server Error`: Outros erros.

### Listar Status de Projetos

```
GET /status-projetos/
```

**Descrição**: Lista todos os status de projeto cadastrados, com paginação.

**Parâmetros (Query):**

- `skip` (integer, opcional, default: 0): Número de registros a pular.
- `limit` (integer, opcional, default: 100): Número máximo de registros a retornar (1 <= limit <= 1000).

**Resposta de Sucesso (200 OK - Schema: `List[StatusProjetoDTO]`):**

```json
[
  {
    "id": 1,
    "nome": "Em Análise",
    "descricao": "Projeto aguardando análise inicial.",
    "is_final": false,
    "ordem_exibicao": 1,
    "data_criacao": "2024-07-31T12:00:00Z",
    "data_atualizacao": "2024-07-31T12:00:00Z"
  },
  {
    "id": 2,
    "nome": "Em Andamento",
    "descricao": "Projeto em fase de execução.",
    "is_final": false,
    "ordem_exibicao": 2,
    "data_criacao": "2024-07-31T12:05:00Z",
    "data_atualizacao": "2024-07-31T12:05:00Z"
  }
]
```

**Respostas de Erro:**

- `500 Internal Server Error`: Outros erros.

### Obter Status de Projeto por ID

```
GET /status-projetos/{status_id}
```

**Descrição**: Obtém um status de projeto específico pelo seu ID.

**Parâmetros (Path):**

- `status_id` (integer, obrigatório): ID do status de projeto.

**Resposta de Sucesso (200 OK - Schema: `StatusProjetoDTO`):**

```json
{
  "id": 1,
  "nome": "Em Análise",
  "descricao": "Projeto aguardando análise inicial.",
  "is_final": false,
  "ordem_exibicao": 1,
  "data_criacao": "2024-07-31T12:00:00Z",
  "data_atualizacao": "2024-07-31T12:00:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Status de projeto não encontrado.
- `500 Internal Server Error`: Outros erros.

### Atualizar Status de Projeto

```
PUT /status-projetos/{status_id}
```

**Descrição**: Atualiza um status de projeto existente.

**Parâmetros (Path):**

- `status_id` (integer, obrigatório): ID do status de projeto a ser atualizado.

**Corpo da Requisição (application/json - Schema: `StatusProjetoUpdateDTO`):**

```json
{
  "nome": "Análise Concluída",
  "descricao": "Análise inicial do projeto foi concluída.",
  "is_final": false
}
```

**Campos da Requisição:**

- `nome` (string, opcional): Novo nome do status.
- `descricao` (string, opcional): Nova descrição do status.
- `is_final` (boolean, opcional): Novo indicador se o status é final.
- `ordem_exibicao` (integer, opcional): Nova ordem de exibição.

**Resposta de Sucesso (200 OK - Schema: `StatusProjetoDTO`):**

```json
{
  "id": 1,
  "nome": "Análise Concluída",
  "descricao": "Análise inicial do projeto foi concluída.",
  "is_final": false,
  "ordem_exibicao": 1,
  "data_criacao": "2024-07-31T12:00:00Z",
  "data_atualizacao": "2024-07-31T12:10:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Status de projeto não encontrado para atualização.
- `422 Unprocessable Entity`: Dados inválidos.
- `500 Internal Server Error`: Outros erros.

### Excluir Status de Projeto

```
DELETE /status-projetos/{status_id}
```

**Descrição**: Exclui um status de projeto pelo seu ID.

**Parâmetros (Path):**

- `status_id` (integer, obrigatório): ID do status de projeto a ser excluído.

**Resposta de Sucesso (200 OK - Schema: `StatusProjetoDTO`):** (Retorna os dados do status de projeto excluído)

```json
{
  "id": 1,
  "nome": "Análise Concluída",
  "descricao": "Análise inicial do projeto foi concluída.",
  "is_final": false,
  "ordem_exibicao": 1,
  "data_criacao": "2024-07-31T12:00:00Z",
  "data_atualizacao": "2024-07-31T12:10:00Z"
}
```

**Respostas de Erro:**

- `404 Not Found`: Status de projeto não encontrado para exclusão.
- `500 Internal Server Error`: Outros erros.

## Modelos de Dados

### StatusProjetoUpdateDTO

```yaml
StatusProjetoUpdateDTO:
  type: object
  properties:
    nome:
      type: string
      description: Novo nome para o status do projeto.
      nullable: true
    descricao:
      type: string
      description: Nova descrição para o status do projeto.
      nullable: true
    is_final:
      type: boolean
      description: Indica se o status é um estado final de projeto.
      nullable: true
    ordem_exibicao:
      type: integer
      description: Nova ordem de exibição para o status.
      nullable: true
  example:
    nome: "Em Validação (Atualizado)"
    descricao: "Projeto aguardando validação após desenvolvimento."
    is_final: false
    ordem_exibicao: 3
```

### ProjetoCreateSchema

```yaml
ProjetoCreateSchema:
  type: object
  required:
    - nome
    - status_projeto_id
  properties:
    nome:
      type: string
      description: Nome do projeto.
    codigo_empresa:
      type: string
      description: Código do projeto na empresa (se aplicável).
      nullable: true
    descricao:
      type: string
      description: Descrição detalhada do projeto.
      nullable: true
    jira_project_key:
      type: string
      description: Chave do projeto no Jira (se integrado).
      nullable: true
    status_projeto_id:
      type: integer
      description: ID do status inicial do projeto.
    data_inicio_prevista:
      type: string
      format: date
      description: Data prevista para o início do projeto (YYYY-MM-DD).
      nullable: true
    data_fim_prevista:
      type: string
      format: date
      description: Data prevista para o término do projeto (YYYY-MM-DD).
      nullable: true
    ativo:
      type: boolean
      description: Indica se o projeto está ativo.
      default: true
      nullable: true
  example:
    nome: "Desenvolvimento Alpha"
    codigo_empresa: "PRJ-ALPHA-001"
    descricao: "Fase Alpha do novo desenvolvimento."
    jira_project_key: "ALPHA"
    status_projeto_id: 1
    data_inicio_prevista: "2024-10-01"
    data_fim_prevista: "2025-01-15"
    ativo: true
```

### ProjetoUpdateDTO

```yaml
ProjetoUpdateDTO:
  type: object
  properties:
    nome:
      type: string
      description: Novo nome do projeto.
      nullable: true
    codigo_empresa:
      type: string
      description: Novo código do projeto na empresa.
      nullable: true
    descricao:
      type: string
      description: Nova descrição detalhada do projeto.
      nullable: true
    jira_project_key:
      type: string
      description: Nova chave do projeto no Jira.
      nullable: true
    status_projeto_id:
      type: integer
      description: Novo ID do status do projeto.
      nullable: true
    data_inicio_prevista:
      type: string
      format: date
      description: Nova data prevista para o início do projeto (YYYY-MM-DD).
      nullable: true
    data_fim_prevista:
      type: string
      format: date
      description: Nova data prevista para o término do projeto (YYYY-MM-DD).
      nullable: true
    ativo:
      type: boolean
      description: Novo status de ativação do projeto.
      nullable: true
  example:
    descricao: "Descrição do projeto Alpha atualizada."
    status_projeto_id: 2
```

### ProjetoDTO

```yaml
ProjetoDTO:
  type: object
  properties:
    id:
      type: integer
      description: ID único do projeto.
      readOnly: true
    nome:
      type: string
      description: Nome do projeto.
    codigo_empresa:
      type: string
      description: Código do projeto na empresa.
      nullable: true
    descricao:
      type: string
      description: Descrição detalhada do projeto.
      nullable: true
    jira_project_key:
      type: string
      description: Chave do projeto no Jira.
      nullable: true
    status_projeto_id:
      type: integer
      description: ID do status atual do projeto.
    data_inicio_prevista:
      type: string
      format: date
      description: Data prevista para o início do projeto.
      nullable: true
    data_fim_prevista:
      type: string
      format: date
      description: Data prevista para o término do projeto.
      nullable: true
    ativo:
      type: boolean
      description: Indica se o projeto está ativo.
    data_criacao:
      type: string
      format: date-time
      description: Data e hora de criação do projeto.
      readOnly: true
    data_atualizacao:
      type: string
      format: date-time
      description: Data e hora da última atualização do projeto.
      readOnly: true
  example:
    id: 1
    nome: "Desenvolvimento Alpha"
    codigo_empresa: "PRJ-ALPHA-001"
    descricao: "Fase Alpha do novo desenvolvimento."
    jira_project_key: "ALPHA"
    status_projeto_id: 1
    data_inicio_prevista: "2024-10-01"
    data_fim_prevista: "2025-01-15"
    ativo: true
    data_criacao: "2024-08-20T14:30:00Z"
    data_atualizacao: "2024-08-20T14:30:00Z"
```

{{ ... }}

## Projetos

Endpoints para gerenciar projetos.

### Criar Projeto

```
POST /projetos/
```

**Sumário**: Cria um novo projeto.

**Tags**: 
  - Projetos

**Corpo da Requisição**:

- `application/json` (Schema: `#/components/schemas/ProjetoCreateSchema`)

**Respostas**:

- `201 Created`: Projeto criado com sucesso.
  - Content: `application/json` (Schema: `#/components/schemas/ProjetoDTO`)
- `422 Unprocessable Entity`: Dados de entrada inválidos.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPValidationError`)
- `500 Internal Server Error`: Erro interno no servidor.

### Listar Projetos

```
GET /projetos/
```

**Sumário**: Lista todos os projetos com paginação e filtros.

**Tags**: 
  - Projetos

**Parâmetros (Query)**:

- `skip` (integer, opcional, default: 0): Número de registros a pular.
- `limit` (integer, opcional, default: 100, minimum: 1, maximum: 1000): Número máximo de registros a retornar.
- `apenas_ativos` (boolean, opcional, default: false): Filtrar por projetos ativos.
- `status_projeto` (integer, opcional): Filtrar projetos por ID do status.

**Respostas**:

- `200 OK`: Lista de projetos recuperada com sucesso.
  - Content: `application/json` (Schema: Array of `#/components/schemas/ProjetoDTO`)
- `500 Internal Server Error`: Erro interno no servidor.

### Obter Projeto por ID

```
GET /projetos/{projeto_id}
```

**Sumário**: Obtém um projeto específico pelo seu ID.

**Tags**: 
  - Projetos

**Parâmetros (Path)**:

- `projeto_id` (integer, obrigatório): ID do projeto.

**Respostas**:

- `200 OK`: Projeto recuperado com sucesso.
  - Content: `application/json` (Schema: `#/components/schemas/ProjetoDTO`)
- `404 Not Found`: Projeto não encontrado.
- `500 Internal Server Error`: Erro interno no servidor.

### Atualizar Projeto

```
PUT /projetos/{projeto_id}
```

**Sumário**: Atualiza um projeto existente.

**Tags**: 
  - Projetos

**Parâmetros (Path)**:

- `projeto_id` (integer, obrigatório): ID do projeto a ser atualizado.

**Corpo da Requisição**:

- `application/json` (Schema: `#/components/schemas/ProjetoUpdateDTO`)

**Respostas**:

- `200 OK`: Projeto atualizado com sucesso.
  - Content: `application/json` (Schema: `#/components/schemas/ProjetoDTO`)
- `404 Not Found`: Projeto não encontrado para atualização.
- `422 Unprocessable Entity`: Dados de entrada inválidos.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPValidationError`)
- `500 Internal Server Error`: Erro interno no servidor.

### Excluir Projeto

```
DELETE /projetos/{projeto_id}
```

**Sumário**: Exclui um projeto pelo seu ID.

**Tags**: 
  - Projetos

**Parâmetros (Path)**:

- `projeto_id` (integer, obrigatório): ID do projeto a ser excluído.

**Respostas**:

- `204 No Content`: Projeto excluído com sucesso.
- `404 Not Found`: Projeto não encontrado.
- `500 Internal Server Error`: Erro interno no servidor.

{{ ... }}

## Apontamentos

Endpoints para gerenciar apontamentos de horas. Todos requerem autenticação de administrador.

### Criar Apontamento Manual

```
POST /apontamentos/
```

**Sumário**: Cria um novo apontamento de horas do tipo `MANUAL`.

**Tags**: 
  - Apontamentos

**Segurança**:
  - bearerAuth: []

**Corpo da Requisição**:

- `application/json` (Schema: `#/components/schemas/ApontamentoCreateSchema`)

**Respostas**:

- `201 Created`: Apontamento criado com sucesso.
  - Content: `application/json` (Schema: `#/components/schemas/ApontamentoResponseSchema`)
- `400 Bad Request`: Dados inválidos.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPError`)
- `422 Unprocessable Entity`: Erro de validação.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPValidationError`)

### Listar Apontamentos

```
GET /apontamentos/
```

**Sumário**: Lista apontamentos com filtros avançados e paginação.

**Tags**: 
  - Apontamentos

**Segurança**:
  - bearerAuth: []

**Parâmetros (Query)**:

- `skip` (integer, opcional, default: 0): Número de registros a pular.
- `limit` (integer, opcional, default: 100): Número máximo de registros.
- `recurso_id` (integer, opcional): Filtrar por ID do recurso.
- `projeto_id` (integer, opcional): Filtrar por ID do projeto.
- `equipe_id` (integer, opcional): Filtrar por ID da equipe do recurso.
- `secao_id` (integer, opcional): Filtrar por ID da seção do recurso.
- `data_inicio` (string, opcional, format: date): Data inicial do período.
- `data_fim` (string, opcional, format: date): Data final do período.
- `fonte_apontamento` (string, opcional, enum: [MANUAL, JIRA]): Filtrar por fonte.
- `jira_issue_key` (string, opcional): Filtrar por chave da issue do Jira.

**Respostas**:

- `200 OK`: Lista de apontamentos.
  - Content: `application/json` (Schema: Array of `#/components/schemas/ApontamentoResponseSchema`)

### Obter Agregações de Apontamentos

```
GET /apontamentos/agregacoes
```

**Sumário**: Retorna a soma de horas e contagem de registros de apontamentos, com filtros e opções de agrupamento.

**Tags**: 
  - Apontamentos

**Segurança**:
  - bearerAuth: []

**Parâmetros (Query - Filtros, todos opcionais)**:

- `recurso_id` (integer): ID do recurso.
- `projeto_id` (integer): ID do projeto.
- `equipe_id` (integer): ID da equipe do recurso.
- `secao_id` (integer): ID da seção do recurso.
- `data_inicio` (string, format: date): Data inicial.
- `data_fim` (string, format: date): Data final.

**Parâmetros (Query - Agrupamento, todos booleanos, opcionais, default: false)**:

- `agrupar_por_recurso` (boolean): Agrupar por recurso.
- `agrupar_por_projeto` (boolean): Agrupar por projeto.
- `agrupar_por_data` (boolean): Agrupar por data.
- `agrupar_por_mes` (boolean): Agrupar por mês/ano.

**Respostas**:

- `200 OK`: Lista de agregações.
  - Content: `application/json` (Schema: Array of `#/components/schemas/ApontamentoAggregationSchema`)

### Obter Apontamento por ID

```
GET /apontamentos/{apontamento_id}
```

**Sumário**: Retorna um apontamento específico pelo seu ID.

**Tags**: 
  - Apontamentos

**Segurança**:
  - bearerAuth: []

**Parâmetros (Path)**:

- `apontamento_id` (integer, obrigatório): ID do apontamento.

**Respostas**:

- `200 OK`: Dados do apontamento.
  - Content: `application/json` (Schema: `#/components/schemas/ApontamentoResponseSchema`)
- `404 Not Found`: Apontamento não encontrado.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPError`)

### Atualizar Apontamento Manual

```
PUT /apontamentos/{apontamento_id}
```

**Sumário**: Atualiza um apontamento. Somente para fonte `MANUAL`.

**Tags**: 
  - Apontamentos

**Segurança**:
  - bearerAuth: []

**Parâmetros (Path)**:

- `apontamento_id` (integer, obrigatório): ID do apontamento a ser atualizado.

**Corpo da Requisição**:

- `application/json` (Schema: `#/components/schemas/ApontamentoUpdateSchema`)

**Respostas**:

- `200 OK`: Apontamento atualizado com sucesso.
  - Content: `application/json` (Schema: `#/components/schemas/ApontamentoResponseSchema`)
- `400 Bad Request`: Dados inválidos.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPError`)
- `403 Forbidden`: Tentativa de atualizar um apontamento que não é `MANUAL`.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPError`)
- `404 Not Found`: Apontamento não encontrado.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPError`)
- `422 Unprocessable Entity`: Erro de validação.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPValidationError`)

### Excluir Apontamento Manual

```
DELETE /apontamentos/{apontamento_id}
```

**Sumário**: Remove um apontamento. Somente para fonte `MANUAL`.

**Tags**: 
  - Apontamentos

**Segurança**:
  - bearerAuth: []

**Parâmetros (Path)**:

- `apontamento_id` (integer, obrigatório): ID do apontamento a ser excluído.

**Respostas**:

- `204 No Content`: Apontamento excluído com sucesso.
- `400 Bad Request`: Erro na exclusão.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPError`)
- `403 Forbidden`: Tentativa de excluir um apontamento que não é `MANUAL`.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPError`)
- `404 Not Found`: Apontamento não encontrado.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPError`)

{{ ... }}

```
### Relatórios

Endpoints para geração de relatórios. Todos requerem autenticação de administrador.

### Relatório de Horas Apontadas

```
GET /relatorios/horas-apontadas
```

**Sumário**: Gera relatório de horas apontadas com filtros e agrupamentos.

**Tags**: 
  - Relatórios

**Segurança**:
  - bearerAuth: []

**Parâmetros (Query)**:

- `recurso_id` (integer, opcional): ID do recurso.
- `projeto_id` (integer, opcional): ID do projeto.
- `equipe_id` (integer, opcional): ID da equipe.
- `secao_id` (integer, opcional): ID da seção.
- `data_inicio` (string, opcional, format: date): Data inicial (YYYY-MM-DD).
- `data_fim` (string, opcional, format: date): Data final (YYYY-MM-DD).
- `fonte_apontamento` (string, opcional, enum: [MANUAL, JIRA]): Fonte do apontamento.
- `agrupar_por_recurso` (boolean, opcional, default: false): Agrupar por recurso.
- `agrupar_por_projeto` (boolean, opcional, default: false): Agrupar por projeto.
- `agrupar_por_data` (boolean, opcional, default: false): Agrupar por data.
- `agrupar_por_mes` (boolean, opcional, default: true): Agrupar por mês/ano.

**Respostas**:

- `200 OK`: Lista de agregações de horas.
  - Content: `application/json` 
    - Schema: `#/components/schemas/GenericReportResponse`
    - Example:
      ```json
      [
        {
          "recurso_id": 10,
          "recurso_nome": "Recurso A",
          "total_horas": 75.5,
          "total_registros": 10
        },
        {
          "projeto_id": 5,
          "projeto_nome": "Projeto X",
          "total_horas": 120.0,
          "total_registros": 15
        }
      ]
      ```

### Relatório Comparativo: Planejado vs. Realizado (Query Direta)

```
GET /relatorios/comparativo-planejado-realizado
```

**Sumário**: Compara horas planejadas e apontadas (query direta).

**Tags**: 
  - Relatórios

**Segurança**:
  - bearerAuth: []

**Parâmetros (Query)**:

- `ano` (integer, obrigatório): Ano do relatório.
- `mes` (integer, opcional): Mês do relatório (1-12).
- `recurso_id` (integer, opcional): ID do recurso.
- `projeto_id` (integer, opcional): ID do projeto.
- `equipe_id` (integer, opcional): ID da equipe.

**Respostas**:

- `200 OK`: Relatório comparativo.
  - Content: `application/json`
    - Schema: `#/components/schemas/GenericReportResponse`
    - Example:
      ```json
      [
        {
          "recurso_id": 10,
          "recurso_nome": "Maria Silva",
          "projeto_id": 5,
          "projeto_nome": "Sistema de Gestão Alpha",
          "horas_planejadas": 80.0,
          "horas_apontadas": 75.5,
          "diferenca": 4.5
        }
      ]
      ```

### Relatório de Horas por Projeto

```
GET /relatorios/horas-por-projeto
```

**Sumário**: Obtém relatório de horas apontadas agregadas por projeto.

**Tags**: 
  - Relatórios

**Segurança**:
  - bearerAuth: []

**Parâmetros (Query)**:

- `data_inicio` (string, opcional, format: date): Data inicial.
- `data_fim` (string, opcional, format: date): Data final.
- `secao_id` (integer, opcional): ID da seção.
- `equipe_id` (integer, opcional): ID da equipe.

**Respostas**:

- `200 OK`: Horas agregadas por projeto.
  - Content: `application/json`
    - Schema: `#/components/schemas/GenericReportResponse`
    - Example:
      ```json
      [
        {
          "projeto_id": 5,
          "projeto_nome": "Projeto Phoenix",
          "total_horas_apontadas": 250.75
        },
        {
          "projeto_id": 8,
          "projeto_nome": "Projeto Vega",
          "total_horas_apontadas": 180.5
        }
      ]
      ```

### Relatório de Horas por Recurso

```
GET /relatorios/horas-por-recurso
```

**Sumário**: Obtém relatório de horas apontadas agregadas por recurso.

**Tags**: 
  - Relatórios

**Segurança**:
  - bearerAuth: []

**Parâmetros (Query)**:

- `data_inicio` (string, opcional, format: date): Data inicial.
- `data_fim` (string, opcional, format: date): Data final.
- `projeto_id` (integer, opcional): ID do projeto.
- `equipe_id` (integer, opcional): ID da equipe.
- `secao_id` (integer, opcional): ID da seção.

**Respostas**:

- `200 OK`: Horas agregadas por recurso.
  - Content: `application/json`
    - Schema: `#/components/schemas/GenericReportResponse`
    - Example:
      ```json
      [
        {
          "recurso_id": 10,
          "recurso_nome": "João Neves",
          "total_horas_apontadas": 160.0
        },
        {
          "recurso_id": 12,
          "recurso_nome": "Ana Clara",
          "total_horas_apontadas": 155.25
        }
      ]
      ```

### Relatório Planejado vs. Realizado (Service-based)

```
GET /relatorios/planejado-vs-realizado
```

**Sumário**: Compara planejado vs. realizado (baseado em serviço).

**Tags**: 
  - Relatórios

**Segurança**:
  - bearerAuth: []

**Parâmetros (Query)**:

- `ano` (integer, obrigatório): Ano de referência.
- `mes` (integer, opcional): Mês de referência (1-12).
- `projeto_id` (integer, opcional): ID do projeto.
- `recurso_id` (integer, opcional): ID do recurso.
- `equipe_id` (integer, opcional): ID da equipe.
- `secao_id` (integer, opcional): ID da seção.

**Respostas**:

- `200 OK`: Análise comparativa.
  - Content: `application/json`
    - Schema: `#/components/schemas/GenericReportResponse`
    - Example:
      ```json
      [
        {
          "identificador_grupo": "Projeto Alpha / Recurso Beta",
          "ano": 2024,
          "mes": 8,
          "horas_planejadas": 100.0,
          "horas_realizadas": 95.5,
          "saldo_horas": -4.5,
          "percentual_realizacao": 95.5
        }
      ]
      ```
- `400 Bad Request`: Mês inválido.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPError`)

### Relatório de Disponibilidade de Recursos

```
GET /relatorios/disponibilidade-recursos
```

**Sumário**: Detalha a disponibilidade dos recursos.

**Tags**: 
  - Relatórios

**Segurança**:
  - bearerAuth: []

**Parâmetros (Query)**:

- `ano` (integer, obrigatório): Ano de referência.
- `mes` (integer, opcional, ge: 1, le: 12): Mês de referência (1-12).
- `recurso_id` (integer, opcional): ID do recurso.

**Respostas**:

- `200 OK`: Relatório de disponibilidade.
  - Content: `application/json`
    - Schema: `#/components/schemas/GenericReportResponse`
    - Example:
      ```json
      [
        {
          "recurso_id": 10,
          "recurso_nome": "Carlos Andrade",
          "ano": 2024,
          "mes": 8,
          "horas_capacidade_rh": 160.0,
          "horas_planejadas_total": 150.0,
          "horas_realizadas_total": 145.5,
          "horas_disponiveis_planejamento": 10.0,
          "horas_saldo_realizado_vs_planejado": -4.5,
          "percentual_alocacao_planejada": 93.75,
          "percentual_utilizacao_realizada": 90.94
        }
      ]
      ```
- `500 Internal Server Error`: Erro interno.
  - Content: `application/json` (Schema: `#/components/schemas/HTTPError`)

{{ ... }}
