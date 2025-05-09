Documentação Completa da API - Sistema de Gestão de Projetos e Melhorias
Informações Gerais
URL Base: http://localhost:8000/backend/v1
Documentação Interativa: http://localhost:8000/docs
Formato de Dados: JSON
Autenticação: Bearer Token JWT
Content-Type: application/json

Autenticação e UsuáriosAutenticação e Usuários
Login

POST /auth/token

Corpo da Requisição:

{
  "username": "email@exemplo.com",
  "password": "senha"
}

Resposta (200 OK):

{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "nome": "Nome do Usuário",
    "email": "email@exemplo.com",
    "role": "admin",
    "recurso_id": 5
  }
}

Erro (401 Unauthorized):

{
  "detail": "Credenciais incorretas"
}

Obter Usuário Atual

GET /auth/me

Headers:

Authorization: Bearer {token}

Resposta (200 OK):

{
  "id": 1,
  "nome": "Nome do Usuário",
  "email": "email@exemplo.com",
  "role": "admin",
  "recurso_id": 5,
  "ativo": true,
  "ultimo_acesso": "2025-05-10T14:30:15"
}

Listar Usuários

GET /usuarios

Parâmetros de Consulta:
skip (integer, padrão=0): Paginação
limit (integer, padrão=100): Paginação
ativo (boolean, opcional): Filtrar por status ativo
role (string, opcional): Filtrar por perfil (admin, gestor, recurso)
Resposta (200 OK):

{
  "items": [
    {
      "id": 1,
      "nome": "Administrador",
      "email": "admin@exemplo.com",
      "role": "admin",
      "recurso_id": null,
      "ativo": true,
      "ultimo_acesso": "2025-05-10T14:30:15"
    },
    {
      "id": 2,
      "nome": "Gerente de Projetos",
      "email": "gerente@exemplo.com",
      "role": "gestor",
      "recurso_id": 3,
      "ativo": true,
      "ultimo_acesso": "2025-05-09T10:15:20"
    }
  ],
  "total": 10,
  "page": 1,
  "pages": 1
}

Criar Usuário

POST /usuarios

Corpo da Requisição:

{
  "nome": "Novo Usuário",
  "email": "novo.usuario@exemplo.com",
  "role": "recurso",
  "recurso_id": 8,
  "senha": "senha123"
}

Resposta (201 Created):

{
  "id": 11,
  "nome": "Novo Usuário",
  "email": "novo.usuario@exemplo.com",
  "role": "recurso",
  "recurso_id": 8,
  "ativo": true
}

Atualizar Usuário

PUT /usuarios/{usuario_id}

{
  "nome": "Nome Atualizado",
  "email": "email.atualizado@exemplo.com",
  "role": "gestor",
  "ativo": true
}

Resposta (200 OK):

{
  "id": 11,
  "nome": "Nome Atualizado",
  "email": "email.atualizado@exemplo.com",
  "role": "gestor",
  "recurso_id": 8,
  "ativo": true
}

Alterar Senha

PUT /usuarios/{usuario_id}/alterar-senha

Corpo da Requisição:

{
  "senha_atual": "senha123",
  "nova_senha": "novaSenha456"
}

Resposta (200 OK):

{
  "message": "Senha alterada com sucesso"
}

Desativar Usuário

DELETE /usuarios/{usuario_id}

Resposta (200 OK):

{
  "message": "Usuário desativado com sucesso"
}

Seções
Listar Seções

GET /secoes

Parâmetros de Consulta:
skip (integer, padrão=0): Paginação
limit (integer, padrão=100): Paginação
ativo (boolean, opcional): Filtrar por status ativo
nome (string, opcional): Filtrar por nome (pesquisa parcial)
Resposta (200 OK):

{
  "items": [
    {
      "id": 1,
      "nome": "Desenvolvimento",
      "descricao": "Equipe de desenvolvimento de software",
      "data_criacao": "2025-01-15T10:00:00",
      "ativo": true
    },
    {
      "id": 2,
      "nome": "Infraestrutura",
      "descricao": "Equipe de infraestrutura e DevOps",
      "data_criacao": "2025-01-15T10:00:00",
      "ativo": true
    }
  ],
  "total": 5,
  "page": 1,
  "pages": 1
}

Obter Seção por ID

GET /secoes/{secao_id}

Resposta (200 OK):

{
  "id": 1,
  "nome": "Desenvolvimento",
  "descricao": "Equipe de desenvolvimento de software",
  "data_criacao": "2025-01-15T10:00:00",
  "data_atualizacao": "2025-01-15T10:00:00",
  "ativo": true
}

Criar Seção

POST /secoes

Corpo da Requisição:

{
  "nome": "Nova Seção",
  "descricao": "Descrição da nova seção"
}

Resposta (201 Created):

{
  "id": 6,
  "nome": "Nova Seção",
  "descricao": "Descrição da nova seção",
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T14:30:00",
  "ativo": true
}

Atualizar Seção

PUT /secoes/{secao_id}

Corpo da Requisição:

{
  "nome": "Nome Atualizado",
  "descricao": "Descrição atualizada",
  "ativo": true
}

Resposta (200 OK):

{
  "id": 6,
  "nome": "Nome Atualizado",
  "descricao": "Descrição atualizada",
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T15:45:00",
  "ativo": true
}

Desativar Seção

DELETE /secoes/{secao_id}

Resposta (200 OK):

{
  "message": "Seção desativada com sucesso"
}

Listar Equipes por Seção

GET /secoes/{secao_id}/equipes

Parâmetros de Consulta:
ativo (boolean, opcional): Filtrar por status ativo
Resposta (200 OK):

{
  "items": [
    {
      "id": 1,
      "nome": "Equipe Frontend",
      "descricao": "Equipe responsável pelo frontend",
      "ativo": true
    },
    {
      "id": 2,
      "nome": "Equipe Backend",
      "descricao": "Equipe responsável pelo backend",
      "ativo": true
    }
  ],
  "total": 2
}

Equipes

Listar Equipes

GET /equipes

Parâmetros de Consulta:
skip (integer, padrão=0): Paginação
limit (integer, padrão=100): Paginação
ativo (boolean, opcional): Filtrar por status ativo
secao_id (integer, opcional): Filtrar por seção
nome (string, opcional): Filtrar por nome (pesquisa parcial)
Resposta (200 OK):

{
  "items": [
    {
      "id": 1,
      "nome": "Equipe Frontend",
      "descricao": "Equipe responsável pelo frontend",
      "secao_id": 1,
      "secao": {
        "id": 1,
        "nome": "Desenvolvimento"
      },
      "ativo": true
    },
    {
      "id": 2,
      "nome": "Equipe Backend",
      "descricao": "Equipe responsável pelo backend",
      "secao_id": 1,
      "secao": {
        "id": 1,
        "nome": "Desenvolvimento"
      },
      "ativo": true
    }
  ],
  "total": 8,
  "page": 1,
  "pages": 1
}

Obter Equipe por ID
GET /equipes/{equipe_id}

Resposta (200 OK):
{
  "id": 1,
  "nome": "Equipe Frontend",
  "descricao": "Equipe responsável pelo frontend",
  "secao_id": 1,
  "secao": {
    "id": 1,
    "nome": "Desenvolvimento"
  },
  "data_criacao": "2025-01-15T10:00:00",
  "data_atualizacao": "2025-01-15T10:00:00",
  "ativo": true
}

Criar Equipe
POST /equipes
Corpo da Requisição:
{
  "nome": "Nova Equipe",
  "descricao": "Descrição da nova equipe",
  "secao_id": 1
}
Resposta (201 Created):
{
  "id": 9,
  "nome": "Nova Equipe",
  "descricao": "Descrição da nova equipe",
  "secao_id": 1,
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T14:30:00",
  "ativo": true
}
Atualizar Equipe
PUT /equipes/{equipe_id}
Corpo da Requisição:
{
  "nome": "Nome Atualizado",
  "descricao": "Descrição atualizada",
  "secao_id": 2,
  "ativo": true
}
Resposta (200 OK):
{
  "id": 9,
  "nome": "Nome Atualizado",
  "descricao": "Descrição atualizada",
  "secao_id": 2,
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T15:45:00",
  "ativo": true
}
Desativar Equipe
DELETE /equipes/{equipe_id}
Resposta (200 OK):
{
  "message": "Equipe desativada com sucesso"
}
Listar Recursos por Equipe
GET /equipes/{equipe_id}/recursos
Parâmetros de Consulta:
ativo (boolean, opcional): Filtrar por status ativo
Resposta (200 OK):
{
  "items": [
    {
      "id": 1,
      "nome": "João Silva",
      "email": "joao.silva@exemplo.com",
      "matricula": "123456",
      "cargo": "Desenvolvedor Frontend",
      "ativo": true
    },
    {
      "id": 2,
      "nome": "Maria Oliveira",
      "email": "maria.oliveira@exemplo.com",
      "matricula": "234567",
      "cargo": "UX Designer",
      "ativo": true
    }
  ],
  "total": 5
}

Recursos (Colaboradores)
Listar Recursos
GET /recursos
Parâmetros de Consulta:
skip (integer, padrão=0): Paginação
limit (integer, padrão=100): Paginação
ativo (boolean, opcional): Filtrar por status ativo
equipe_id (integer, opcional): Filtrar por equipe principal
nome (string, opcional): Filtrar por nome (pesquisa parcial)
email (string, opcional): Filtrar por email
matricula (string, opcional): Filtrar por matrícula
Resposta (200 OK):
{
  "items": [
    {
      "id": 1,
      "nome": "João Silva",
      "email": "joao.silva@exemplo.com",
      "matricula": "123456",
      "cargo": "Desenvolvedor Frontend",
      "jira_user_id": "joao.silva",
      "equipe_principal_id": 1,
      "equipe": {
        "id": 1,
        "nome": "Equipe Frontend"
      },
      "data_admissao": "2023-01-10",
      "ativo": true
    },
    {
      "id": 2,
      "nome": "Maria Oliveira",
      "email": "maria.oliveira@exemplo.com",
      "matricula": "234567",
      "cargo": "UX Designer",
      "jira_user_id": "maria.oliveira",
      "equipe_principal_id": 1,
      "equipe": {
        "id": 1,
        "nome": "Equipe Frontend"
      },
      "data_admissao": "2023-02-15",
      "ativo": true
    }
  ],
  "total": 15,
  "page": 1,
  "pages": 1
}
Obter Recurso por ID
GET /recursos/{recurso_id}
Resposta (200 OK):
{
  "id": 1,
  "nome": "João Silva",
  "email": "joao.silva@exemplo.com",
  "matricula": "123456",
  "cargo": "Desenvolvedor Frontend",
  "jira_user_id": "joao.silva",
  "equipe_principal_id": 1,
  "equipe": {
    "id": 1,
    "nome": "Equipe Frontend"
  },
  "data_admissao": "2023-01-10",
  "data_criacao": "2025-01-15T10:00:00",
  "data_atualizacao": "2025-01-15T10:00:00",
  "ativo": true
}
Criar Recurso
Corpo da Requisição:
{
  "nome": "Novo Recurso",
  "email": "novo.recurso@exemplo.com",
  "matricula": "345678",
  "cargo": "Desenvolvedor Backend",
  "jira_user_id": "novo.recurso",
  "equipe_principal_id": 2,
  "data_admissao": "2025-04-01"
}
Resposta (201 Created):
{
  "id": 16,
  "nome": "Novo Recurso",
  "email": "novo.recurso@exemplo.com",
  "matricula": "345678",
  "cargo": "Desenvolvedor Backend",
  "jira_user_id": "novo.recurso",
  "equipe_principal_id": 2,
  "data_admissao": "2025-04-01",
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T14:30:00",
  "ativo": true
}
Criar Recurso
POST /recursos
Corpo da Requisição:
{
  "nome": "Novo Recurso",
  "email": "novo.recurso@exemplo.com",
  "matricula": "345678",
  "cargo": "Desenvolvedor Backend",
  "jira_user_id": "novo.recurso",
  "equipe_principal_id": 2,
  "data_admissao": "2025-04-01"
}
Resposta (201 Created):
{
  "id": 16,
  "nome": "Novo Recurso",
  "email": "novo.recurso@exemplo.com",
  "matricula": "345678",
  "cargo": "Desenvolvedor Backend",
  "jira_user_id": "novo.recurso",
  "equipe_principal_id": 2,
  "data_admissao": "2025-04-01",
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T14:30:00",
  "ativo": true
}
Atualizar Recurso
PUT /recursos/{recurso_id}
Corpo da Requisição:
{
  "nome": "Nome Atualizado",
  "email": "email.atualizado@exemplo.com",
  "cargo": "Analista Desenvolvedor",
  "equipe_principal_id": 3,
  "ativo": true
}
Resposta (200 OK):
{
  "id": 16,
  "nome": "Nome Atualizado",
  "email": "email.atualizado@exemplo.com",
  "matricula": "345678",
  "cargo": "Analista Desenvolvedor",
  "jira_user_id": "novo.recurso",
  "equipe_principal_id": 3,
  "data_admissao": "2025-04-01",
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T15:45:00",
  "ativo": true
}
Desativar Recurso
DELETE /recursos/{recurso_id}
Resposta (200 OK):
{
  "message": "Recurso desativado com sucesso"
}
Listar Projetos de um Recurso
GET /recursos/{recurso_id}/projetos
Parâmetros de Consulta:
ativo (boolean, opcional): Filtrar por alocações ativas
data (date, opcional): Filtrar por alocações ativas na data
Resposta (200 OK):
{
  "items": [
    {
      "projeto_id": 1,
      "nome": "Projeto A",
      "codigo_empresa": "PRJ001",
      "data_inicio_alocacao": "2025-01-01",
      "data_fim_alocacao": "2025-06-30"
    },
    {
      "projeto_id": 3,
      "nome": "Projeto C",
      "codigo_empresa": "PRJ003",
      "data_inicio_alocacao": "2025-04-01",
      "data_fim_alocacao": null
    }
  ]
}
Listar Apontamentos de um Recurso
GET /recursos/{recurso_id}/apontamentos
Parâmetros de Consulta:
data_inicio (date, opcional): Filtrar a partir desta data
data_fim (date, opcional): Filtrar até esta data
projeto_id (integer, opcional): Filtrar por projeto
Resposta (200 OK):
{
  "items": [
    {
      "id": 101,
      "projeto_id": 1,
      "projeto": {
        "id": 1,
        "nome": "Projeto A"
      },
      "data_apontamento": "2025-05-10",
      "horas_apontadas": 8.0,
      "descricao": "Desenvolvimento de funcionalidade X",
      "jira_issue_key": "PRJA-123"
    },
    {
      "id": 102,
      "projeto_id": 3,
      "projeto": {
        "id": 3,
        "nome": "Projeto C"
      },
      "data_apontamento": "2025-05-11",
      "horas_apontadas": 4.0,
      "descricao": "Reunião de Sprint",
      "jira_issue_key": "PRJC-45"
    }
  ],
  "total": 32
}
Disponibilidade de Horas do Recurso
GET /recursos/{recurso_id}/disponibilidade
Parâmetros de Consulta:
ano (integer, obrigatório): Ano para consulta
mes (integer, opcional): Mês específico (1-12)
Resposta (200 OK):
{
  "recurso_id": 1,
  "nome_recurso": "João Silva",
  "disponibilidade": [
    {
      "ano": 2025,
      "mes": 5,
      "horas_disponiveis": 168.0,
      "horas_planejadas": 160.0,
      "horas_apontadas": 152.0,
      "saldo": 8.0
    },
    {
      "ano": 2025,
      "mes": 6,
      "horas_disponiveis": 160.0,
      "horas_planejadas": 160.0,
      "horas_apontadas": 0.0,
      "saldo": 0.0
    }
  ]
}

Status de Projeto
Listar Status de Projeto
GET /status-projetos
Parâmetros de Consulta:
is_final (boolean, opcional): Filtrar por status final
Resposta (200 OK):
{
  "items": [
    {
      "id": 1,
      "nome": "Não Iniciado",
      "descricao": "Projeto ainda não iniciado",
      "is_final": false,
      "ordem_exibicao": 1
    },
    {
      "id": 2,
      "nome": "Em Andamento",
      "descricao": "Projeto em execução",
      "is_final": false,
      "ordem_exibicao": 2
    },
    {
      "id": 3,
      "nome": "Pausado",
      "descricao": "Projeto temporariamente pausado",
      "is_final": false,
      "ordem_exibicao": 3
    },
    {
      "id": 4,
      "nome": "Concluído",
      "descricao": "Projeto finalizado com sucesso",
      "is_final": true,
      "ordem_exibicao": 4
    },
    {
      "id": 5,
      "nome": "Cancelado",
      "descricao": "Projeto cancelado",
      "is_final": true,
      "ordem_exibicao": 5
    }
  ]
}
Obter Status de Projeto por ID
GET /status-projetos/{status_id}
Resposta (200 OK):
{
  "id": 2,
  "nome": "Em Andamento",
  "descricao": "Projeto em execução",
  "is_final": false,
  "ordem_exibicao": 2,
  "data_criacao": "2025-01-15T10:00:00",
  "data_atualizacao": "2025-01-15T10:00:00"
}
Criar Status de Projeto
POST /status-projetos
Corpo da Requisição:
{
  "nome": "Novo Status",
  "descricao": "Descrição do novo status",
  "is_final": false,
  "ordem_exibicao": 6
}
Resposta (201 Created):
{
  "id": 6,
  "nome": "Novo Status",
  "descricao": "Descrição do novo status",
  "is_final": false,
  "ordem_exibicao": 6,
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T14:30:00"
}
Atualizar Status de Projeto
PUT /status-projetos/{status_id}
Corpo da Requisição:
{
  "nome": "Nome Atualizado",
  "descricao": "Descrição atualizada",
  "is_final": true,
  "ordem_exibicao": 7
}
Resposta (200 OK):
{
  "id": 6,
  "nome": "Nome Atualizado",
  "descricao": "Descrição atualizada",
  "is_final": true,
  "ordem_exibicao": 7,
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T15:45:00"
}
Excluir Status de Projeto
DELETE /status-projetos/{status_id}
Resposta (200 OK):
{
  "message": "Status excluído com sucesso"
}

Projetos
Listar Projetos
GET /projetos
Parâmetros de Consulta:
skip (integer, padrão=0): Paginação
limit (integer, padrão=100): Paginação
ativo (boolean, opcional): Filtrar por status ativo
status_id (integer, opcional): Filtrar por ID de status
nome (string, opcional): Filtrar por nome (pesquisa parcial)
codigo_empresa (string, opcional): Filtrar por código da empresa
data_inicio (date, opcional): Filtrar por data de início
data_fim (date, opcional): Filtrar por data de fim
Resposta (200 OK):
{
  "items": [
    {
      "id": 1,
      "nome": "Projeto A",
      "codigo_empresa": "PRJ001",
      "descricao": "Descrição do projeto A",
      "jira_project_key": "PRJA",
      "status_projeto_id": 2,
      "status_projeto": {
        "id": 2,
        "nome": "Em Andamento"
      },
      "data_inicio_prevista": "2025-01-01",
      "data_fim_prevista": "2025-06-30",
      "ativo": true
    },
    {
      "id": 2,
      "nome": "Projeto B",
      "codigo_empresa": "PRJ002",
      "descricao": "Descrição do projeto B",
      "jira_project_key": "PRJB",
      "status_projeto_id": 1,
      "status_projeto": {
        "id": 1,
        "nome": "Não Iniciado"
      },
      "data_inicio_prevista": "2025-07-01",
      "data_fim_prevista": "2025-12-31",
      "ativo": true
    }
  ],
  "total": 12,
  "page": 1,
  "pages": 1
}
Obter Projeto por ID
{
  "id": 1,
  "nome": "Projeto A",
  "codigo_empresa": "PRJ001",
  "descricao": "Descrição do projeto A",
  "jira_project_key": "PRJA",
  "status_projeto_id": 2,
  "status_projeto": {
    "id": 2,
    "nome": "Em Andamento"
  },
  "data_inicio_prevista": "2025-01-01",
  "data_fim_prevista": "2025-06-30",
  "data_criacao": "2025-01-15T10:00:00",
  "data_atualizacao": "2025-01-15T10:00:00",
  "ativo": true
}
Criar Projeto
POST /projetos
Corpo da Requisição:
{
  "nome": "Novo Projeto",
  "codigo_empresa": "PRJ013",
  "descricao": "Descrição do novo projeto",
  "jira_project_key": "PRJN",
  "status_projeto_id": 1,
  "data_inicio_prevista": "2025-08-01",
  "data_fim_prevista": "2026-02-28"
}
Resposta (201 Created):
{
  "id": 13,
  "nome": "Novo Projeto",
  "codigo_empresa": "PRJ013",
  "descricao": "Descrição do novo projeto",
  "jira_project_key": "PRJN",
  "status_projeto_id": 1,
  "data_inicio_prevista": "2025-08-01",
  "data_fim_prevista": "2026-02-28",
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T14:30:00",
  "ativo": true
}
Atualizar Projeto
PUT /projetos/{projeto_id}

**Corpo da Requisição**:
```json
{
  "nome": "Nome Atualizado",
  "descricao": "Descrição atualizada",
  "status_projeto_id": 2,
  "data_inicio_prevista": "2025-09-01",
  "data_fim_prevista": "2026-03-31",
  "ativo": true
}
```

**Resposta (200 OK)**:
```json
{
  "id": 13,
  "nome": "Nome Atualizado",
  "codigo_empresa": "PRJ013",
  "descricao": "Descrição atualizada",
  "jira_project_key": "PRJN",
  "status_projeto_id": 2,
  "data_inicio_prevista": "2025-09-01",
  "data_fim_prevista": "2026-03-31",
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T15:45:00",
  "ativo": true
}
```
### Desativar Projeto
DELETE /projetos/{projeto_id}

**Resposta (200 OK)**:
```json
{
  "message": "Projeto desativado com sucesso"
}
```

### Listar Recursos Alocados no Projeto
GET /projetos/{projeto_id}/recursos

**Parâmetros de Consulta**:
- `ativo` (boolean, opcional): Filtrar por alocações ativas
- `data` (date, opcional): Filtrar por alocações ativas na data

**Resposta (200 OK)**:
```json
{
  "items": [
    {
      "recurso_id": 1,
      "nome": "João Silva",
      "email": "joao.silva@exemplo.com",
      "data_inicio_alocacao": "2025-01-01",
      "data_fim_alocacao": "2025-06-30"
    },
    {
      "recurso_id": 3,
      "nome": "Pedro Santos",
      "email": "pedro.santos@exemplo.com",
      "data_inicio_alocacao": "2025-01-15",
      "data_fim_alocacao": null
    }
  ],
  "total": 5
}
```

### Alocar Recurso ao Projeto
POST /projetos/{projeto_id}/alocacoes

**Corpo da Requisição**:
```json
{
  "recurso_id": 5,
  "data_inicio_alocacao": "2025-06-01",
  "data_fim_alocacao": "2025-12-31",
  "horas_planejadas": [
    {
      "ano": 2025,
      "mes": 6,
      "horas_planejadas": 120.0
    },
    {
      "ano": 2025,
      "mes": 7,
      "horas_planejadas": 160.0
    }
  ]
}
```

**Resposta (201 Created)**:
```json
{
  "id": 25,
  "projeto_id": 13,
  "recurso_id": 5,
  "recurso": {
    "id": 5,
    "nome": "Ana Souza"
  },
  "data_inicio_alocacao": "2025-06-01",
  "data_fim_alocacao": "2025-12-31",
  "data_criacao": "2025-05-11T14:30:00"
}
```

### Atualizar Alocação
PUT /projetos/{projeto_id}/alocacoes/{alocacao_id}

**Corpo da Requisição**:
```json
{
  "data_inicio_alocacao": "2025-07-01",
  "data_fim_alocacao": "2026-01-31"
}
```

**Resposta (200 OK)**:
```json
{
  "id": 25,
  "projeto_id": 13,
  "recurso_id": 5,
  "data_inicio_alocacao": "2025-07-01",
  "data_fim_alocacao": "2026-01-31",
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T15:45:00"
}
```

### Remover Alocação
DELETE /projetos/{projeto_id}/alocacoes/{alocacao_id}

**Resposta (200 OK)**:
```json
{
  "message": "Alocação removida com sucesso"
}
```

### Planejar Horas de Alocação
POST /projetos/{projeto_id}/alocacoes/{alocacao_id}/planejamento

**Corpo da Requisição**:
```json
{
  "planejamentos": [
    {
      "ano": 2025,
      "mes": 7,
      "horas_planejadas": 120.0
    },
    {
      "ano": 2025,
      "mes": 8,
      "horas_planejadas": 160.0
    }
  ]
}
```

**Resposta (201 Created)**:
```json
{
  "message": "Planejamento de horas atualizado com sucesso",
  "planejamentos": [
    {
      "id": 45,
      "ano": 2025,
      "mes": 7,
      "horas_planejadas": 120.0
    },
    {
      "id": 46,
      "ano": 2025,
      "mes": 8,
      "horas_planejadas": 160.0
    }
  ]
}
```

---

## Apontamentos

### Listar Apontamentos
GET /apontamentos

**Parâmetros de Consulta**:
- `skip` (integer, padrão=0): Paginação
- `limit` (integer, padrão=100): Paginação
- `data_inicio` (date, opcional): Filtrar a partir desta data
- `data_fim` (date, opcional): Filtrar até esta data
- `recurso_id` (integer, opcional): Filtrar por recurso
- `projeto_id` (integer, opcional): Filtrar por projeto
- `fonte_apontamento` (string, opcional): Filtrar por fonte (JIRA, MANUAL)

**Resposta (200 OK)**:
```json
{
  "items": [
    {
      "id": 101,
      "recurso_id": 1,
      "recurso": {
        "id": 1,
        "nome": "João Silva"
      },
      "projeto_id": 1,
      "projeto": {
        "id": 1,
        "nome": "Projeto A"
      },
      "data_apontamento": "2025-05-10",
      "horas_apontadas": 8.0,
      "descricao": "Desenvolvimento de funcionalidade X",
      "jira_issue_key": "PRJA-123",
      "fonte_apontamento": "MANUAL",
      "data_criacao": "2025-05-10T18:30:00"
    },
    {
      "id": 102,
      "recurso_id": 3,
      "recurso": {
        "id": 3,
        "nome": "Pedro Santos"
      },
      "projeto_id": 2,
      "projeto": {
        "id": 2,
        "nome": "Projeto B"
      },
      "data_apontamento": "2025-05-10",
      "horas_apontadas": 6.5,
      "descricao": "Desenvolvimento de API",
      "jira_issue_key": "PRJB-45",
      "fonte_apontamento": "MANUAL",
      "data_criacao": "2025-05-10T17:45:00"
    }
  ],
  "total": 523,
  "page": 1,
  "pages": 6
}
```

### Obter Apontamento por ID
GET /apontamentos/{apontamento_id}

**Resposta (200 OK)**:
```json
{
  "id": 101,
  "recurso_id": 1,
  "recurso": {
    "id": 1,
    "nome": "João Silva"
  },
  "projeto_id": 1,
  "projeto": {
    "id": 1,
    "nome": "Projeto A"
  },
  "data_apontamento": "2025-05-10",
  "horas_apontadas": 8.0,
  "descricao": "Desenvolvimento de funcionalidade X",
  "jira_issue_key": "PRJA-123",
  "fonte_apontamento": "MANUAL",
  "id_usuario_admin_criador": 1,
  "data_hora_inicio_trabalho": "2025-05-10T08:00:00",
  "data_criacao": "2025-05-10T18:30:00",
  "data_atualizacao": "2025-05-10T18:30:00"
}
```

### Criar Apontamento
POST /apontamentos

**Corpo da Requisição**:
```json
{
  "recurso_id": 1,
  "projeto_id": 1,
  "data_apontamento": "2025-05-12",
  "horas_apontadas": 7.5,
  "descricao": "Reunião de planejamento e desenvolvimento",
  "jira_issue_key": "PRJA-124",
  "data_hora_inicio_trabalho": "2025-05-12T09:00:00"
}
```

**Resposta (201 Created)**:
```json
{
  "id": 524,
  "recurso_id": 1,
  "projeto_id": 1,
  "data_apontamento": "2025-05-12",
  "horas_apontadas": 7.5,
  "descricao": "Reunião de planejamento e desenvolvimento",
  "jira_issue_key": "PRJA-124",
  "fonte_apontamento": "MANUAL",
  "id_usuario_admin_criador": 1,
  "data_hora_inicio_trabalho": "2025-05-12T09:00:00",
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T14:30:00"
}
```

### Atualizar Apontamento
PUT /apontamentos/{apontamento_id}

**Corpo da Requisição**:
```json
{
  "horas_apontadas": 8.0,
  "descricao": "Descrição atualizada",
  "jira_issue_key": "PRJA-124-UPDATE"
}
```

**Resposta (200 OK)**:
```json
{
  "id": 524,
  "recurso_id": 1,
  "projeto_id": 1,
  "data_apontamento": "2025-05-12",
  "horas_apontadas": 8.0,
  "descricao": "Descrição atualizada",
  "jira_issue_key": "PRJA-124-UPDATE",
  "fonte_apontamento": "MANUAL",
  "id_usuario_admin_criador": 1,
  "data_hora_inicio_trabalho": "2025-05-12T09:00:00",
  "data_criacao": "2025-05-11T14:30:00",
  "data_atualizacao": "2025-05-11T15:45:00"
}
```

### Excluir Apontamento
DELETE /apontamentos/{apontamento_id}

**Resposta (200 OK)**:
```json
{
  "message": "Apontamento excluído com sucesso"
}
```

### Apontamentos em Lote
POST /apontamentos/lote

**Corpo da Requisição**:
```json
{
  "recurso_id": 1,
  "projeto_id": 1,
  "apontamentos": [
    {
      "data_apontamento": "2025-05-13",
      "horas_apontadas": 8.0,
      "descricao": "Desenvolvimento dia 1",
      "jira_issue_key": "PRJA-125"
    },
    {
      "data_apontamento": "2025-05-14",
      "horas_apontadas": 8.0,
      "descricao": "Desenvolvimento dia 2",
      "jira_issue_key": "PRJA-125"
    }
  ]
}
```

**Resposta (201 Created)**:
```json
{
  "message": "Apontamentos em lote criados com sucesso",
  "apontamentos": [
    {
      "id": 525,
      "data_apontamento": "2025-05-13",
      "horas_apontadas": 8.0
    },
    {
      "id": 526,
      "data_apontamento": "2025-05-14",
      "horas_apontadas": 8.0
    }
  ]
}
```

---

## Relatórios

### Horas por Projeto
GET /relatorios/horas-por-projeto

**Parâmetros de Consulta**:
- `data_inicio` (date, obrigatório): Data inicial
- `data_fim` (date, obrigatório): Data final
- `projeto_id` (integer, opcional): Filtrar por projeto

**Resposta (200 OK)**:
```json
{
  "periodo": {
    "data_inicio": "2025-05-01",
    "data_fim": "2025-05-31"
  },
  "projetos": [
    {
      "id": 1,
      "nome": "Projeto A",
      "codigo_empresa": "PRJ001",
      "horas_totais": 450.5,
      "recursos": [
        {
          "id": 1,
          "nome": "João Silva",
          "horas": 160.0
        },
        {
          "id": 3,
          "nome": "Pedro Santos",
          "horas": 142.5
        },
        {
          "id": 5,
          "nome": "Ana Souza",
          "horas": 148.0
        }
      ]
    },
    {
      "id": 2,
      "nome": "Projeto B",
      "codigo_empresa": "PRJ002",
      "horas_totais": 320.0,
      "recursos": [
        {
          "id": 2,
          "nome": "Maria Oliveira",
          "horas": 160.0
        },
        {
          "id": 4,
          "nome": "Carlos Lima",
          "horas": 160.0
        }
      ]
    }
  ],
  "total_horas": 770.5
}
```

### Alocação de Recursos
GET /relatorios/alocacao-recursos

**Parâmetros de Consulta**:
- `ano` (integer, obrigatório): Ano para relatório
- `mes` (integer, opcional): Mês específico
- `recurso_id` (integer, opcional): Filtrar por recurso

**Resposta (200 OK)**:
```json
{
  "periodo": {
    "ano": 2025,
    "mes": 5
  },
  "recursos": [
    {
      "id": 1,
      "nome": "João Silva",
      "horas_disponiveis": 168.0,
      "horas_planejadas": 160.0,
      "horas_apontadas": 152.0,
      "projetos": [
        {
          "id": 1,
          "nome": "Projeto A",
          "horas_planejadas": 160.0,
          "horas_apontadas": 152.0
        }
      ]
    },
    {
      "id": 2,
      "nome": "Maria Oliveira",
      "horas_disponiveis": 168.0,
      "horas_planejadas": 160.0,
      "horas_apontadas": 155.0,
      "projetos": [
        {
          "id": 2,
          "nome": "Projeto B",
          "horas_planejadas": 160.0,
          "horas_apontadas": 155.0
        }
      ]
    }
  ]
}
```

### Dashboard de Projetos
GET /relatorios/dashboard

**Parâmetros de Consulta**:
- `data_inicio` (date, opcional): Data inicial para estatísticas
- `data_fim` (date, opcional): Data final para estatísticas

**Resposta (200 OK)**:
```json
{
  "projetos": {
    "total": 12,
    "nao_iniciados": 2,
    "em_andamento": 7,
    "pausados": 1,
    "concluidos": 1,
    "cancelados": 1
  },
  "recursos": {
    "total": 15,
    "ativos": 14
  },
  "apontamentos": {
    "total_periodo": 523,
    "horas_totais": 3945.5
  },
  "projetos_recentes": [
    {
      "id": 1,
      "nome": "Projeto A",
      "status": "Em Andamento",
      "apontamentos_recentes": 45,
      "horas_recentes": 320.5
    },
    {
      "id": 2,
      "nome": "Projeto B",
      "status": "Em Andamento",
      "apontamentos_recentes": 38,
      "horas_recentes": 285.0
    }
  ]
}
```

---

## Integração com JIRA

### Sincronizar Apontamentos
POST /jira/sincronizar

**Corpo da Requisição**:
```json
{
  "data_inicio": "2025-05-01",
  "data_fim": "2025-05-15"
}
```

**Resposta (202 Accepted)**:
```json
{
  "status": "success",
  "mensagem": "Sincronização iniciada",
  "id_tarefa": "123456"
}
```

### Status da Sincronização
GET /jira/sincronizacao/{id_tarefa}

**Resposta (200 OK)**:
```json
{
  "id_tarefa": "123456",
  "status": "completed",
  "inicio": "2025-05-11T14:30:00",
  "termino": "2025-05-11T14:45:00",
  "resultados": {
    "registros_processados": 180,
    "apontamentos_criados": 45,
    "apontamentos_atualizados": 12,
    "erros": 0
  }
}
```

### Histórico de Sincronizações
GET /jira/sincronizacao/historico

**Parâmetros de Consulta**:
- `skip` (integer, padrão=0): Paginação
- `limit` (integer, padrão=100): Paginação

**Resposta (200 OK)**:
```json
{
  "items": [
    {
      "id": 25,
      "data_inicio": "2025-05-11T14:30:00",
      "data_fim": "2025-05-11T14:45:00",
      "status": "completed",
      "usuario": {
        "id": 1,
        "nome": "Administrador"
      },
      "quantidade_apontamentos_processados": 57
    },
    {
      "id": 24,
      "data_inicio": "2025-05-10T10:15:00",
      "data_fim": "2025-05-10T10:30:00",
      "status": "completed",
      "usuario": {
        "id": 1,
        "nome": "Administrador"
      },
      "quantidade_apontamentos_processados": 42
    }
  ],
  "total": 25
}
```

### Configuração JIRA
GET /jira/configuracao

**Resposta (200 OK)**:
```json
{
  "jira_base_url": "https://your-domain.atlassian.net",
  "jira_sync_enabled": true,
  "jira_sync_interval": 60,
  "ultima_sincronizacao": "2025-05-11T14:45:00"
}
```

### Atualizar Configuração JIRA
PUT /jira/configuracao

**Corpo da Requisição**:
```json
{
  "jira_sync_enabled": true,
  "jira_sync_interval": 120
}
```

**Resposta (200 OK)**:
```json
{
  "message": "Configuração atualizada com sucesso",
  "jira_base_url": "https://your-domain.atlassian.net",
  "jira_sync_enabled": true,
  "jira_sync_interval": 120
}
```

---

## Configurações do Sistema

### Obter Configurações
GET /configuracoes

**Resposta (200 OK)**:
```json
{
  "items": [
    {
      "chave": "hora_padrao_dia",
      "valor": "8",
      "descricao": "Quantidade padrão de horas disponíveis por dia útil"
    },
    {
      "chave": "jira_sync_enabled",
      "valor": "true",
      "descricao": "Define se a sincronização com o Jira está habilitada"
    },
    {
      "chave": "jira_sync_interval",
      "valor": "60",
      "descricao": "Intervalo de sincronização com o Jira em minutos"
    }
  ]
}
```

### Atualizar Configuração
PUT /configuracoes/{chave}

**Corpo da Requisição**:
```json
{
  "valor": "9",
  "descricao": "Novo padrão de horas por dia útil"
}
```

**Resposta (200 OK)**:
```json
{
  "chave": "hora_padrao_dia",
  "valor": "9",
  "descricao": "Novo padrão de horas por dia útil",
  "data_atualizacao": "2025-05-11T15:45:00"
}
```

---

## Logs de Atividade

### Listar Logs
GET /logs

**Parâmetros de Consulta**:
- `skip` (integer, padrão=0): Paginação
- `limit` (integer, padrão=100): Paginação
- `usuario_id` (integer, opcional): Filtrar por usuário
- `data_inicio` (datetime, opcional): Filtrar a partir desta data/hora
- `data_fim` (datetime, opcional): Filtrar até esta data/hora
- `acao` (string, opcional): Filtrar por tipo de ação
- `tabela_afetada` (string, opcional): Filtrar por tabela afetada

**Resposta (200 OK)**:
```json
{
  "items": [
    {
      "id": 1503,
      "usuario_id": 1,
      "usuario": {
        "id": 1,
        "nome": "Administrador"
      },
      "acao": "CREATE",
      "tabela_afetada": "projeto",
      "registro_id": "13",
      "detalhes": "Criação de novo projeto",
      "ip_origem": "192.168.1.100",
      "data_hora": "2025-05-11T14:30:00"
    },
    {
      "id": 1502,
      "usuario_id": 1,
      "usuario": {
        "id": 1,
        "nome": "Administrador"
      },
      "acao": "UPDATE",
      "tabela_afetada": "recurso",
      "registro_id": "5",
      "detalhes": "Atualização de dados do recurso",
      "ip_origem": "192.168.1.100",
      "data_hora": "2025-05-11T14:15:00"
    }
  ],
  "total": 1503,
  "page": 1,
  "pages": 16
}
```

---

## Códigos de Erro Comuns

- `400 Bad Request`: Dados inválidos ou ausentes
- `401 Unauthorized`: Autenticação necessária ou credenciais inválidas
- `403 Forbidden`: Sem permissão para acessar o recurso
- `404 Not Found`: Recurso não encontrado
- `409 Conflict`: Conflito com o estado atual do recurso
- `422 Unprocessable Entity`: Validação falhou
- `500 Internal Server Error`: Erro interno do servidor

### Formato de Erros

```json
{
  "detail": "Mensagem descritiva do erro",
  "code": "codigo_erro_especifico",
  "field": "campo_com_erro",  // opcional
  "timestamp": "2025-05-11T14:30:00.123456"
}
```

---

## Recomendações para o Frontend

1. **Cache de Dados**: Implemente cache para dados que mudam pouco (status, equipes, seções)

2. **Tratamento de Erros**: Sempre verifique os códigos HTTP e implemente tratamento de erro adequado

3. **Paginação**: Use os parâmetros `skip` e `limit` para uma experiência melhor em listas grandes

4. **Token de Autenticação**: Armazene de forma segura e inclua em todas as requisições

5. **Validação dos Formulários**: Implemente validação no cliente seguindo as mesmas regras do backend

6. **Gerenciamento de Estado**: Use solução de gerenciamento de estado (Redux, Context API, etc.)

7. **Refrescamento de Token**: Implemente lógica para renovar o token JWT quando necessário

8. **Loading States**: Mostre indicadores de carregamento durante operações assíncronas

9. **Otimização de Requisições**: Minimize o número de requisições combinando chamadas quando possível

10. **Tratamento Offline**: Considere implementar funcionalidade offline para apontamentos

---

Para detalhes completos de cada endpoint, consulte a documentação interativa Swagger disponível em `http://localhost:8000/docs`.

