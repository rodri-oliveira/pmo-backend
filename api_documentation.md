# Guia de Integração Front-end com API PMO

Este guia descreve como as telas do front-end podem interagir com os endpoints da API do Sistema de Gestão de Projetos PMO, com foco nos campos de dados e requisitos. A **URL Base** da API é `/backend/v1`.

## Autenticação 🔑

* **Tela de Login:**
    * **Rota Sugerida:** `/login`
    * **Objetivo:** Autenticar o usuário no sistema.
    * **Endpoint da API:** `POST /auth/token`
    * **Dados para Enviar (Front-end -> Back-end):**
        * `username` (string, **obrigatório**, corresponde ao email do usuário)
        * `password` (string, **obrigatório**)
    * **Dados a Receber (Back-end -> Front-end em caso de sucesso):**
        * `access_token` (string)
        * `token_type` (string, ex: "bearer")
    * **Lógica Front-end:**
        * Coletar `username` e `password`.
        * Enviar para `POST /auth/token`.
        * Em caso de sucesso (200 OK), armazenar o `access_token` de forma segura (ex: LocalStorage, Vuex, Redux state) e incluí-lo nos cabeçalhos das requisições subsequentes como `Authorization: Bearer <access_token>`.
        * Em caso de falha (401 Unauthorized), exibir mensagem de erro apropriada.

* **Tela de Criação de Usuário (Administração):**
    * **Contexto/Rota Sugerida:** Acessível através de um painel de administração, ex: `/admin/usuarios/criar`
    * **Objetivo:** Permitir que um administrador crie novas contas de usuário.
    * **Endpoint da API:** `POST /usuarios` (relativo à URL Base `/backend/v1`)
    * **Autenticação:** Requer Bearer Token JWT de um usuário com `role` "admin".
    * **Dados para Enviar (Front-end -> Back-end - Schema `UserCreate`):
        * `email` (string, formato de email, **obrigatório**)
        * `nome` (string, **obrigatório**)
        * `password` (string, mínimo 8 caracteres, **obrigatório**)
        * `role` (string enum: "admin", "gestor", "recurso", **obrigatório**)
        * `recurso_id` (integer, opcional): ID do recurso (da entidade `Recurso`) associado a este usuário, se aplicável.
        * `ativo` (boolean, opcional, default: `true`): Define se o usuário será criado como ativo.
    * **Dados a Receber (Back-end -> Front-end em caso de sucesso - Schema `UserBase`):
        * `email` (string)
        * `nome` (string)
        * `role` (string enum)
        * `recurso_id` (integer, opcional)
        * `ativo` (boolean)
    * **Lógica Front-end:**
        * Exibir um formulário para o administrador preencher os dados do novo usuário.
        * Realizar validações de front-end (ex: formato do email, complexidade da senha se desejado).
        * Ao submeter, enviar a requisição `POST` para `/usuarios` incluindo o token JWT do administrador no header `Authorization`.
        * Em caso de sucesso (200 OK), informar o administrador e, opcionalmente, redirecionar para a lista de usuários ou limpar o formulário.
        * Em caso de falha, exibir mensagens de erro específicas:
            * `400 Bad Request`: Dados inválidos (ex: email já existe, senha curta). Exibir detalhes do erro se fornecidos pela API.
            * `401 Unauthorized`: Token do administrador ausente, inválido ou expirado. Pode sugerir relogar.
            * `403 Forbidden`: O usuário autenticado não é um administrador. (Menos provável se o acesso à tela já for restrito).

* **Tela de Listagem/Cadastro de Seções:**
    * **Rota Sugerida:** `/secoes`
    * **Objetivo:** Listar, criar, editar e visualizar seções.
    * **Endpoints da API:**
        * Listar: `GET /secoes/`
        * Criar: `POST /secoes/`
        * Obter por ID: `GET /secoes/{secao_id}`
        * Atualizar: `PUT /secoes/{secao_id}`
        * Excluir: `DELETE /secoes/{secao_id}`
    * **Segurança:**
        * `GET`: Acessível por qualquer usuário autenticado.
        * `POST`, `PUT`, `DELETE`: Apenas usuários com role "admin".
    * **Dados para Criar Nova Seção (Front-end -> Back-end via `POST /secoes/` - Schema `SecaoCreateDTO`):
        * `nome` (string, **obrigatório**)
        * `descricao` (string, opcional)
    * **Dados para Atualizar Seção (Front-end -> Back-end via `PUT /secoes/{secao_id}` - Schema `SecaoUpdateDTO`):
        * `nome` (string, opcional)
        * `descricao` (string, opcional)
        * `ativo` (boolean, opcional)
    * **Dados Retornados (Back-end -> Front-end - Schema `SecaoDTO`):
        * `id` (integer)
        * `nome` (string)
        * `descricao` (string, opcional)
        * `ativo` (boolean)
        * `data_criacao` (datetime)
        * `data_atualizacao` (datetime)
    * **Lógica Front-end (Criação/Edição):**
        * Formulário com os campos `nome` e `descricao`. Para edição, incluir o campo `ativo`.
        * Validação dos campos obrigatórios.
        * Ao submeter, enviar para `POST /secoes/` (criar) ou `PUT /secoes/{secao_id}` (atualizar).
    * **Lógica Front-end (Listagem):**
        * Chamar `GET /secoes/`.
        * Exibir a lista de seções em uma tabela/cards.
        * Permitir filtros por `apenas_ativos` (boolean).
        * Permitir paginação (`skip`, `limit`).
    * **Campos a Exibir na Listagem (exemplos):** `nome`, `descricao`, `ativo`.

* **Tela de Listagem/Cadastro de Equipes:**
    * **Rota Sugerida:** `/equipes`
    * **Objetivo:** Listar, criar, editar e visualizar equipes.
    * **Endpoints da API:**
        * Listar: `GET /equipes/`
        * Criar: `POST /equipes/`
        * Obter por ID: `GET /equipes/{equipe_id}`
        * Atualizar: `PUT /equipes/{equipe_id}`
        * Excluir: `DELETE /equipes/{equipe_id}`
    * **Dados para Criar Nova Equipe (Front-end -> Back-end via `POST /equipes/` - Schema `EquipeCreateDTO`):
        * `nome` (string, **obrigatório**)
        * `descricao` (string, opcional)
        * `secao_id` (integer, **obrigatório**) - *Front-end deve permitir selecionar de uma lista de seções (`GET /secoes/`)*.
    * **Dados para Atualizar Equipe (Front-end -> Back-end via `PUT /equipes/{equipe_id}` - Schema `EquipeUpdateDTO`):
        * `nome` (string, opcional)
        * `descricao` (string, opcional)
        * `secao_id` (integer, opcional)
        * `ativo` (boolean, opcional)
    * **Dados Retornados (Back-end -> Front-end - Schema `EquipeDTO`):
        * `id` (integer)
        * `nome` (string)
        * `descricao` (string, opcional)
        * `secao_id` (integer)
        * `ativo` (boolean)
        * `data_criacao` (datetime)
        * `data_atualizacao` (datetime)
    * **Lógica Front-end (Criação/Edição):**
        * Formulário com os campos `nome`, `descricao`, e `secao_id`. Para edição, incluir o campo `ativo`.
        * Dropdown para `secao_id` populado via `GET /secoes/`.
        * Validação dos campos obrigatórios.
        * Ao submeter, enviar para `POST /equipes/` (criar) ou `PUT /equipes/{equipe_id}` (atualizar).
    * **Lógica Front-end (Listagem):**
        * Chamar `GET /equipes/`.
        * Exibir a lista de equipes em uma tabela/cards.
        * Permitir filtros por `apenas_ativos` (boolean) e `secao_id` (integer).
        * Permitir paginação (`skip`, `limit`).
    * **Campos a Exibir na Listagem (exemplos):** `nome`, `descricao`, `secao_id` (ou nome da seção), `ativo`.

* **Tela de Listagem/Cadastro de Recursos:**
    * **Rota Sugerida:** `/recursos`
    * **Objetivo:** Listar, criar, editar e visualizar recursos humanos.
    * **Endpoints da API:**
        * Listar: `GET /recursos/`
        * Criar: `POST /recursos/`
        * Obter por ID: `GET /recursos/{recurso_id}`
        * Atualizar: `PUT /recursos/{recurso_id}`
        * Excluir: `DELETE /recursos/{recurso_id}`
    * **Dados para Criar Novo Recurso (Front-end -> Back-end via `POST /recursos/` - Schema `RecursoCreateDTO`):
        * `nome` (string, **obrigatório**)
        * `email` (string, formato email, **obrigatório**)
        * `matricula` (string, opcional)
        * `cargo` (string, opcional)
        * `jira_user_id` (string, opcional)
        * `data_admissao` (date, opcional, formato "YYYY-MM-DD")
        * `equipe_principal_id` (integer, opcional) - *Front-end deve permitir selecionar de uma lista de equipes (`GET /equipes/`)*.
    * **Dados para Atualizar Recurso (Front-end -> Back-end via `PUT /recursos/{recurso_id}` - Schema `RecursoUpdateDTO`):
        * `nome` (string, opcional)
        * `email` (string, formato email, opcional)
        * `matricula` (string, opcional)
        * `cargo` (string, opcional)
        * `jira_user_id` (string, opcional)
        * `data_admissao` (date, opcional, formato "YYYY-MM-DD")
        * `equipe_principal_id` (integer, opcional)
        * `ativo` (boolean, opcional)
    * **Dados Retornados (Back-end -> Front-end - Schema `RecursoDTO`):
        * `id` (integer)
        * `nome` (string)
        * `email` (string)
        * `matricula` (string, opcional)
        * `cargo` (string, opcional)
        * `jira_user_id` (string, opcional)
        * `data_admissao` (date, opcional)
        * `equipe_principal_id` (integer, opcional)
        * `ativo` (boolean)
        * `data_criacao` (datetime)
        * `data_atualizacao` (datetime)
    * **Lógica Front-end (Criação/Edição):**
        * Formulário com os campos relevantes.
        * Dropdown para `equipe_principal_id` populado via `GET /equipes/`.
        * Validação dos campos obrigatórios e formato do email.
        * Ao submeter, enviar para `POST /recursos/` (criar) ou `PUT /recursos/{recurso_id}` (atualizar).
    * **Lógica Front-end (Listagem):**
        * Chamar `GET /recursos/`.
        * Exibir a lista de recursos.
        * Permitir filtros por `apenas_ativos` (boolean) e `equipe_id` (integer).
        * Permitir paginação (`skip`, `limit`).
    * **Campos a Exibir na Listagem (exemplos):** `nome`, `email`, `matricula`, `cargo`, `equipe_principal_id` (ou nome da equipe), `ativo`.

* **Tela de Listagem/Cadastro de Projetos:**
    * **Rota Sugerida:** `/projetos`
    * **Objetivo:** Listar, criar e (potencialmente) editar/visualizar projetos.
    * **Endpoints da API:**
        * Listar: `GET /projetos/`
        * Criar: `POST /projetos/`
        * Obter por ID: `GET /projetos/{projeto_id}`
        * Atualizar: `PUT /projetos/{projeto_id}`
    * **Dados para Criar/Atualizar Projeto (Front-end -> Back-end via `POST` ou `PUT`):**
        * `nome` (string, **obrigatório** para criar, opcional para atualizar)
        * `status_projeto_id` (integer, **obrigatório** para criar, opcional para atualizar) - *Front-end deve permitir selecionar de uma lista de status de projetos (`GET /status-projetos/`)*.
        * `jira_project_key` (string, opcional)
        * `codigo_empresa` (string, opcional)
        * `descricao` (string, opcional)
        * `data_inicio` (date, "YYYY-MM-DD", opcional)
        * `data_fim` (date, "YYYY-MM-DD", opcional)
        * *(Outros campos do modelo `Projeto` da API, como `ativo`, `orcamento_total`, etc., podem ser incluídos)*
    * **Lógica Front-end (Criação/Edição):**
        * Formulário com os campos acima.
        * Dropdown para `status_projeto_id` populado via `GET /status-projetos/`.
        * Calendários para seleção de datas.
    * **Lógica Front-end (Listagem):**
        * Chamar `GET /projetos/`.
        * Exibir lista. Permitir filtros por `nome`, `status_projeto`, `ativo`.
    * **Campos a Exibir na Listagem (exemplos):** `nome`, `status_projeto_nome` (se a API retornar), `data_inicio`, `data_fim`, `ativo`.

* **Tela de Gerenciamento de Alocações:**
    * **Rota Sugerida:** `/alocacoes` (geral) ou `/projetos/{projeto_id}/alocacoes` (específico do projeto) ou `/recursos/{recurso_id}/alocacoes` (específico do recurso).
    * **Objetivo:** Alocar recursos a projetos, definir o período e o esforço.
    * **Endpoints da API:**
        * Listar: `GET /alocacoes/` (pode ser filtrado por `recurso_id`, `projeto_id`, etc.)
        * Criar: `POST /alocacoes/`
        * Obter por ID: `GET /alocacoes/{alocacao_id}`
        * Atualizar: `PUT /alocacoes/{alocacao_id}`
    * **Dados para Criar/Atualizar Alocação (Front-end -> Back-end via `POST` ou `PUT`):**
        * `recurso_id` (integer, **obrigatório** para criar) - *Dropdown populado por `GET /recursos/`*.
        * `projeto_id` (integer, **obrigatório** para criar) - *Dropdown populado por `GET /projetos/`*.
        * `data_inicio` (date, "YYYY-MM-DD", **obrigatório** para criar)
        * `data_fim` (date, "YYYY-MM-DD", **obrigatório** para criar)
        * `percentual_alocacao` (number, **obrigatório** para criar)
        * `horas_alocadas` (number, **obrigatório** para criar)
    * **Lógica Front-end:**
        * Formulário com seleção de recurso, projeto e os campos de data e esforço.
        * Validações para garantir que `data_fim` seja posterior a `data_inicio`.
    * **Campos a Exibir na Listagem (exemplos):** `recurso_nome`, `projeto_nome` (se a API retornar), `data_inicio`, `data_fim`, `percentual_alocacao`.

* **Tela de Planejamento de Horas:** (Esta tela seria idealmente acessada no contexto de uma *Alocação específica*).
    * **Rota Sugerida:** `/alocacoes/{alocacao_id}/planejamento-horas`
    * **Objetivo:** Detalhar ou visualizar, para uma alocação existente, quantas horas são planejadas por mês.
    * **Endpoints da API:**
        * Listar: `GET /planejamento-horas/?alocacao_id={alocacao_id}`
        * *(A API Swagger não detalha `POST`/`PUT` para `planejamento-horas`. Assumindo que o back-end oferece um endpoint para criar/atualizar esses planejamentos, por exemplo, `POST /planejamento-horas/` ou `PUT /planejamento-horas/{planejamento_id}`)*.
    * **Dados para Criar/Atualizar Planejamento (Front-end -> Back-end - hipotético):**
        * `alocacao_id` (integer, **obrigatório**)
        * `ano` (integer, **obrigatório**)
        * `mes` (integer, **obrigatório**)
        * `horas_planejadas` (number, **obrigatório**)
    * **Lógica Front-end (Visualização/Edição):**
        * Ao visualizar uma alocação, esta tela/componente seria carregada.
        * Chamar `GET /planejamento-horas/` filtrando por `alocacao_id`.
        * Exibir uma grade/lista com `ano`, `mes` e `horas_planejadas`.
        * Permitir adicionar novos planejamentos mensais ou editar existentes (ex: uma tabela onde cada linha é um mês/ano e as horas podem ser inseridas/editadas). A submissão de cada linha/novo item chamaria o endpoint `POST` ou `PUT` apropriado.

* **Tela de Apontamentos de Horas:**
    * **Rota Sugerida:** `/apontamentos` ou `/apontamentos/consulta`
    * **Objetivo:** Listar e filtrar apontamentos de horas.
    * **Endpoint da API:** `GET /apontamentos/`
    * **Lógica Front-end:**
        * Permitir filtros por `recurso_id`, `projeto_id`, `data_inicio`, `data_fim`.
        * Exibir os resultados em uma tabela.
        * **Campos a Exibir (exemplos, baseados no modelo `Apontamento` da API):** `recurso_nome` (ou ID), `projeto_nome` (ou ID), `data_apontamento`, `horas_apontadas`, `descricao`, `jira_issue_key`.

* **Tela de Criação Manual de Apontamento:**
    * **Rota Sugerida:** `/apontamentos/criar`
    * **Objetivo:** Permitir que um usuário crie um apontamento manualmente.
    * **Endpoint da API:** `POST /apontamentos/` (Assumindo que este endpoint existe, conforme modelo `Apontamento` da API e necessidade).
    * **Dados para Criar Novo Apontamento Manual (Front-end -> Back-end):**
        * `recurso_id` (integer, **obrigatório**) - *Dropdown populado por `GET /recursos/`*.
        * `projeto_id` (integer, **obrigatório**) - *Dropdown populado por `GET /projetos/`*.
        * `alocacao_id` (integer, opcional mas recomendado) - *Dropdown de alocações do recurso no projeto*.
        * `data` (date, "YYYY-MM-DD", **obrigatório** - referente a `data_apontamento` da tabela)
        * `horas_apontadas` (number, **obrigatório**)
        * `jira_issue_key` (string, opcional)
        * `descricao` (string, opcional)
        * `fonte_apontamento` (string, ENUM, ex: 'MANUAL', **obrigatório**)
    * **Lógica Front-end:**
        * Formulário para preenchimento dos dados.
        * Ao selecionar Recurso e Projeto, o dropdown de `alocacao_id` poderia ser filtrado para mostrar apenas alocações ativas daquele recurso naquele projeto.

* **Tela de Gerenciamento de Horas Disponíveis:**
    * **Rota Sugerida:** `/capacidade-rh/horas-recurso` (ou similar, como no seu exemplo de URL).
    * **Objetivo:** Definir e consultar as horas disponíveis de um recurso para um determinado mês/ano.
    * **Endpoints da API:** *(A API Swagger não detalha explicitamente endpoints para `horas_disponiveis_rh`. Seriam necessários `GET` para consultar e `POST`/`PUT` para definir/atualizar. Ex: `GET /recursos/{recurso_id}/horas-disponiveis?ano=AAAA&mes=MM` e `POST /recursos/{recurso_id}/horas-disponiveis`)*.
    * **Dados para Definir/Atualizar Horas Disponíveis (Front-end -> Back-end - hipotético):**
        * `recurso_id` (integer, **obrigatório**) - *Selecionado no dropdown "Pesquisar recurso"*.
        * `ano` (integer, **obrigatório**) - *Selecionado no dropdown "Ano"*.
        * `mes` (integer, **obrigatório**) - *Selecionado no dropdown "Mês"*.
        * `horas_disponiveis_mes` (number, **obrigatório**) - *Campo para inserir/atualizar horas*.
    * **Lógica Front-end:**
        * Dropdowns para selecionar `Recurso`, `Ano` e `Mês` conforme a imagem.
        * Ao selecionar os três filtros, fazer uma chamada `GET` (hipotética) para buscar as `horas_disponiveis_mes` atuais para esses parâmetros e exibir no campo apropriado.
        * Permitir a edição do valor e, ao clicar em um botão "Salvar" ou "Atualizar", enviar os dados para o endpoint `POST` ou `PUT` correspondente.

* **Telas de Apoio (Dropdowns) 🗂️**

* **Equipes:**
    * **Endpoint:** `GET /equipes/`
    * **Uso no Front-end:** Popular dropdowns de seleção de equipe (ex: no cadastro de Recursos).
    * **Campos para Dropdown:** `id`, `nome`.
* **Seções:**
    * **Endpoint:** `GET /secoes/`
    * **Uso no Front-end:** Popular dropdowns (ex: no cadastro de Equipes, se houver um CRUD dedicado para Equipes).
    * **Campos para Dropdown:** `id`, `nome`.
* **Status de Projetos:**
    * **Endpoint:** `GET /status-projetos/`
    * **Uso no Front-end:** Popular dropdowns na criação/edição de Projetos.
    * **Campos para Dropdown:** `id`, `nome`.

## Gerenciamento de Relatórios 📈

* **Tela de Relatório de Alocação:**
    * **Rota Sugerida:** `/relatorios/alocacao`
    * **Endpoint da API:** `GET /relatorios/alocacao`
    * **Lógica Front-end (Campos para o usuário preencher/selecionar):**
        * `ano` (select/input, **obrigatório**)
        * `mes` (select/input, opcional)
        * `formato` (select: 'pdf', 'excel', 'csv', opcional)
    * **Interação:** Ao solicitar o relatório, fazer a chamada GET ao endpoint com os parâmetros selecionados. O back-end deve retornar o arquivo ou um link para download.

## Gerenciamento de Status de Projetos

Endpoints para gerenciar os diferentes status que um projeto pode assumir (ex: "Em Andamento", "Concluído", "Pendente").

### Criar Status de Projeto

-   **Endpoint:** `POST /status-projetos/`
-   **Descrição:** Cria um novo status de projeto.
-   **Corpo da Requisição (`StatusProjetoCreateDTO`):**
    ```json
    {
      "nome": "Em Análise",
      "descricao": "Projeto aguardando análise inicial.",
      "is_final": false,
      "ordem_exibicao": 1
    }
    ```
-   **Campos da Requisição:**
    -   `nome` (string, obrigatório): Nome do status.
    -   `descricao` (string, opcional): Descrição detalhada do status.
    -   `is_final` (boolean, opcional, default: `false`): Indica se o status é um estado final de projeto.
    -   `ordem_exibicao` (integer, opcional): Ordem para exibição do status.
-   **Resposta de Sucesso (201 CREATED - `StatusProjetoDTO`):**
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
-   **Respostas de Erro Comuns:**
    -   `422 Unprocessable Entity`: Dados de entrada inválidos.
    -   `500 Internal Server Error`: Erro interno no servidor.

### Listar Status de Projetos

-   **Endpoint:** `GET /status-projetos/`
-   **Descrição:** Lista todos os status de projeto cadastrados, com paginação.
-   **Parâmetros (Query):**
    -   `skip` (integer, opcional, default: 0): Número de registros a pular.
    -   `limit` (integer, opcional, default: 100): Número máximo de registros a retornar (1 <= limit <= 1000).
-   **Resposta de Sucesso (200 OK - `List[StatusProjetoDTO]`):**
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
-   **Respostas de Erro Comuns:**
    -   `500 Internal Server Error`: Erro interno no servidor.

### Obter Status de Projeto por ID

-   **Endpoint:** `GET /status-projetos/{status_id}`
-   **Descrição:** Obtém um status de projeto específico pelo seu ID.
-   **Parâmetros (Path):**
    -   `status_id` (integer, obrigatório): ID do status de projeto.
-   **Resposta de Sucesso (200 OK - `StatusProjetoDTO`):**
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
-   **Respostas de Erro Comuns:**
    -   `404 Not Found`: Status de projeto não encontrado.
    -   `500 Internal Server Error`.

### Atualizar Status de Projeto

-   **Endpoint:** `PUT /status-projetos/{status_id}`
-   **Descrição:** Atualiza um status de projeto existente.
-   **Parâmetros (Path):**
    -   `status_id` (integer, obrigatório): ID do status de projeto a ser atualizado.
-   **Corpo da Requisição (`StatusProjetoUpdateDTO`):**
    ```json
    {
      "nome": "Análise Concluída",
      "descricao": "Análise inicial do projeto foi concluída.",
      "is_final": false,
      "ordem_exibicao": 1
    }
    ```
-   **Campos da Requisição:**
    -   `nome` (string, opcional): Novo nome do status.
    -   `descricao` (string, opcional): Nova descrição do status.
    -   `is_final` (boolean, opcional): Novo indicador se o status é final.
    -   `ordem_exibicao` (integer, opcional): Nova ordem de exibição.
-   **Resposta de Sucesso (200 OK - `StatusProjetoDTO`):**
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
-   **Respostas de Erro Comuns:**
    -   `404 Not Found`: Status de projeto não encontrado para atualização.
    -   `422 Unprocessable Entity`: Dados de entrada inválidos.
    -   `500 Internal Server Error`.

### Excluir Status de Projeto

-   **Endpoint:** `DELETE /status-projetos/{status_id}`
-   **Descrição:** Exclui um status de projeto (geralmente uma exclusão lógica, dependendo da implementação do serviço).
-   **Parâmetros (Path):**
    -   `status_id` (integer, obrigatório): ID do status de projeto a ser excluído.
-   **Resposta de Sucesso (200 OK - `StatusProjetoDTO`):** (Retorna os dados do status de projeto excluído)
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
-   **Respostas de Erro Comuns:**
    -   `404 Not Found`: Status de projeto não encontrado para exclusão.
    -   `500 Internal Server Error`.

## 7. Gerenciamento de Planejamento de Horas

Esta seção descreve os endpoints para criar, listar e excluir planejamentos de horas para recursos alocados em projetos.

O planejamento de horas permite definir quantas horas um recurso específico deve dedicar a um projeto (através de sua alocação) em um determinado mês e ano.

**Autenticação**: Todos os endpoints nesta seção requerem autenticação de administrador.

### 7.1. Criar ou Atualizar Planejamento de Horas

-   **Endpoint**: `POST /planejamento-horas/`
-   **Descrição**: Cria um novo planejamento de horas para uma alocação em um mês/ano específico ou atualiza um existente se já houver um registro para a mesma combinação de alocação, ano e mês.
-   **Corpo da Requisição (JSON)** (Schema: `PlanejamentoHorasCreate`):
    -   `alocacao_id` (integer, obrigatório): ID da alocação do recurso ao projeto.
    -   `ano` (integer, obrigatório): Ano do planejamento.
    -   `mes` (integer, obrigatório): Mês do planejamento (1-12).
    -   `horas_planejadas` (float, obrigatório): Quantidade de horas planejadas.
-   **Exemplo de Requisição**:

    ```json
    {
      "alocacao_id": 5,
      "ano": 2024,
      "mes": 9,
      "horas_planejadas": 80.5
    }
    ```

-   **Resposta de Sucesso (201 CREATED)** (Schema: `PlanejamentoHorasResponse`):
    -   Retorna o objeto do planejamento de horas criado ou atualizado, incluindo `id`, `projeto_id` e `recurso_id` (derivados da alocação).
-   **Exemplo de Resposta de Sucesso**:

    ```json
    {
      "id": 12,
      "alocacao_id": 5,
      "projeto_id": 101,
      "recurso_id": 25,
      "ano": 2024,
      "mes": 9,
      "horas_planejadas": 80.5
    }
    ```

-   **Respostas de Erro Comuns**:
    -   `400 Bad Request`: Dados inválidos, por exemplo, `alocacao_id` inexistente, ano/mês inválido.
    -   `422 Unprocessable Entity`: Campos obrigatórios faltando ou tipo incorreto.
    -   `500 Internal Server Error`.

### 7.2. Listar Planejamentos por Alocação

-   **Endpoint**: `GET /planejamento-horas/alocacao/{alocacao_id}`
-   **Descrição**: Retorna uma lista de todos os planejamentos de horas associados a uma alocação específica.
-   **Parâmetros de Path**:
    -   `alocacao_id` (integer, obrigatório): ID da alocação.
-   **Resposta de Sucesso (200 OK)** (Schema: `List[PlanejamentoHorasResponse]`):
    -   Retorna uma lista de objetos de planejamento de horas.
-   **Exemplo de Resposta de Sucesso (lista com um planejamento)**:

    ```json
    [
      {
        "id": 12,
        "alocacao_id": 5,
        "projeto_id": 101,
        "recurso_id": 25,
        "ano": 2024,
        "mes": 9,
        "horas_planejadas": 80.5
      },
      {
        "id": 15,
        "alocacao_id": 5,
        "projeto_id": 101,
        "recurso_id": 25,
        "ano": 2024,
        "mes": 10,
        "horas_planejadas": 75.0
      }
    ]
    ```

-   **Respostas de Erro Comuns**:
    -   `400 Bad Request`: Se `alocacao_id` for inválido (e.g., não encontrado).
    -   `500 Internal Server Error`.

### 7.3. Listar Planejamentos por Recurso e Período

-   **Endpoint**: `GET /planejamento-horas/recurso/{recurso_id}`
-   **Descrição**: Retorna uma lista de planejamentos de horas para um recurso específico, dentro de um intervalo de meses em um ano.
-   **Parâmetros de Path**:
    -   `recurso_id` (integer, obrigatório): ID do recurso.
-   **Parâmetros de Query**:
    -   `ano` (integer, obrigatório): Ano para filtrar os planejamentos.
    -   `mes_inicio` (integer, opcional, default: 1): Mês inicial do período (1-12).
    -   `mes_fim` (integer, opcional, default: 12): Mês final do período (1-12).
-   **Resposta de Sucesso (200 OK)** (Schema: `List[PlanejamentoHorasResponse]`):
    -   Retorna uma lista de objetos de planejamento de horas que correspondem aos critérios.
-   **Exemplo de Resposta de Sucesso (filtrando para recurso 25, ano 2024, meses 9 a 10)**:

    ```json
    [
      {
        "id": 12,
        "alocacao_id": 5,  // Supondo que esta alocação seja do recurso 25
        "projeto_id": 101,
        "recurso_id": 25,
        "ano": 2024,
        "mes": 9,
        "horas_planejadas": 80.5
      },
      {
        "id": 15,
        "alocacao_id": 5,  // Supondo que esta alocação seja do recurso 25
        "projeto_id": 101,
        "recurso_id": 25,
        "ano": 2024,
        "mes": 10,
        "horas_planejadas": 75.0
      }
      // ... outros planejamentos do recurso 25 no período para diferentes alocações
    ]
    ```

-   **Respostas de Erro Comuns**:
    -   `500 Internal Server Error`.

### 7.4. Excluir Planejamento de Horas

-   **Endpoint**: `DELETE /planejamento-horas/{planejamento_id}`
-   **Descrição**: Remove um planejamento de horas específico pelo seu ID.
-   **Parâmetros de Path**:
    -   `planejamento_id` (integer, obrigatório): ID do planejamento de horas a ser excluído.
-   **Resposta de Sucesso (204 NO CONTENT)**:
    -   Nenhum corpo de resposta em caso de sucesso.
-   **Respostas de Erro Comuns**:
    -   `404 Not Found`: Planejamento de horas com o ID especificado não encontrado.
    -   `500 Internal Server Error`.

## 8. Gerenciamento de Apontamentos de Horas

Esta seção detalha os endpoints para criar, listar, atualizar, excluir e agregar apontamentos de horas. Os apontamentos podem ser manuais (criados por um administrador) ou sincronizados do Jira.

**Autenticação**: Todos os endpoints nesta seção requerem autenticação de administrador.

**Enum `FonteApontamento`**:
-   `MANUAL`: Apontamento criado manualmente no sistema.
-   `JIRA`: Apontamento sincronizado a partir de um worklog do Jira.

### 8.1. Criar Apontamento Manual

-   **Endpoint**: `POST /apontamentos/`
-   **Descrição**: Cria um novo apontamento de horas do tipo `MANUAL`.
-   **Corpo da Requisição (JSON)** (Schema: `ApontamentoCreateSchema`):
    -   `recurso_id` (integer, obrigatório): ID do recurso que realizou o trabalho.
    -   `projeto_id` (integer, obrigatório): ID do projeto ao qual o trabalho se refere.
    -   `jira_issue_key` (string, opcional, max 50): Chave da issue do Jira, se aplicável.
    -   `data_hora_inicio_trabalho` (string, opcional, formato `YYYY-MM-DDTHH:MM:SS`): Data e hora de início do trabalho.
    -   `data_apontamento` (string, obrigatório, formato `YYYY-MM-DD`): Data em que o trabalho foi realizado/registrado.
    -   `horas_apontadas` (number, obrigatório): Quantidade de horas (>0 e <=24).
    -   `descricao` (string, opcional): Descrição do trabalho realizado.
-   **Exemplo de Requisição**:

    ```json
    {
      "recurso_id": 10,
      "projeto_id": 5,
      "data_apontamento": "2024-08-21",
      "horas_apontadas": 4.5,
      "descricao": "Desenvolvimento da funcionalidade X"
    }
    ```

-   **Resposta de Sucesso (201 CREATED)** (Schema: `ApontamentoResponseSchema`):
    -   Retorna o objeto do apontamento criado, incluindo seu `id`, `fonte_apontamento` (será `MANUAL`) e `id_usuario_admin_criador`.
-   **Exemplo de Resposta de Sucesso**:

    ```json
    {
      "id": 150,
      "created_at": "2024-08-21T10:00:00Z",
      "updated_at": "2024-08-21T10:00:00Z",
      "recurso_id": 10,
      "projeto_id": 5,
      "jira_issue_key": null,
      "jira_worklog_id": null,
      "data_hora_inicio_trabalho": null,
      "data_apontamento": "2024-08-21",
      "horas_apontadas": 4.5,
      "descricao": "Desenvolvimento da funcionalidade X",
      "fonte_apontamento": "MANUAL",
      "id_usuario_admin_criador": 1, // ID do admin que criou
      "data_sincronizacao_jira": null
    }
    ```

-   **Respostas de Erro Comuns**:
    -   `400 Bad Request`: Dados inválidos (e.g., recurso/projeto não existe, horas inválidas).
    -   `422 Unprocessable Entity`: Campos obrigatórios faltando ou tipo incorreto.

### 8.2. Listar Apontamentos

-   **Endpoint**: `GET /apontamentos/`
-   **Descrição**: Lista apontamentos com filtros avançados e paginação.
-   **Parâmetros de Query** (Schema: `ApontamentoFilterSchema` - todos opcionais):
    -   `skip` (integer, default: 0): Número de registros a pular (para paginação).
    -   `limit` (integer, default: 100): Número máximo de registros a retornar.
    -   `recurso_id` (integer): Filtrar por ID do recurso.
    -   `projeto_id` (integer): Filtrar por ID do projeto.
    -   `equipe_id` (integer): Filtrar por ID da equipe do recurso.
    -   `secao_id` (integer): Filtrar por ID da seção do recurso.
    -   `data_inicio` (string, formato `YYYY-MM-DD`): Data inicial do período de filtro.
    -   `data_fim` (string, formato `YYYY-MM-DD`): Data final do período de filtro.
    -   `fonte_apontamento` (string, enum: `MANUAL`, `JIRA`): Filtrar pela fonte do apontamento.
    -   `jira_issue_key` (string): Filtrar pela chave da issue do Jira.
-   **Resposta de Sucesso (200 OK)** (Schema: `List[ApontamentoResponseSchema]`):
    -   Retorna uma lista de objetos de apontamento.

### 8.3. Obter Agregações de Apontamentos

-   **Endpoint**: `GET /apontamentos/agregacoes`
-   **Descrição**: Retorna a soma de horas e contagem de registros de apontamentos, com filtros e opções de agrupamento.
-   **Parâmetros de Query (Filtros - todos opcionais):**
    -   Mesmos filtros de `recurso_id` a `jira_issue_key` do endpoint de listagem.
-   **Parâmetros de Query (Agrupamento - todos opcionais, booleanos, default: false)**:
    -   `agrupar_por_recurso`: Agrupar resultados por `recurso_id`.
    -   `agrupar_por_projeto`: Agrupar resultados por `projeto_id`.
    -   `agrupar_por_data`: Agrupar resultados por `data_apontamento`.
    -   `agrupar_por_mes`: Agrupar resultados por mês/ano (campos `mes` e `ano` na resposta).
-   **Resposta de Sucesso (200 OK)** (Schema: `List[ApontamentoAggregationSchema]`):
    -   Retorna uma lista de objetos de agregação.
-   **Exemplo de Resposta (agrupado por recurso e mês)**:

    ```json
    [
      {
        "id": null, // ID não aplicável para agregação, pode ser omitido ou nulo
        "created_at": "2024-08-21T11:00:00Z",
        "updated_at": "2024-08-21T11:00:00Z",
        "total_horas": 120.5,
        "total_registros": 15,
        "recurso_id": 10,
        "projeto_id": null, // Se não agrupado por projeto
        "data_apontamento": null, // Se agrupado por mês
        "mes": 8,
        "ano": 2024
      },
      {
        "id": null,
        "created_at": "2024-08-21T11:00:00Z",
        "updated_at": "2024-08-21T11:00:00Z",
        "total_horas": 80.0,
        "total_registros": 10,
        "recurso_id": 15,
        "projeto_id": null,
        "data_apontamento": null,
        "mes": 8,
        "ano": 2024
      }
    ]
    ```

### 8.4. Obter Apontamento por ID

-   **Endpoint**: `GET /apontamentos/{apontamento_id}`
-   **Descrição**: Retorna um apontamento específico pelo seu ID.
-   **Parâmetros de Path**:
    -   `apontamento_id` (integer, obrigatório): ID do apontamento.
-   **Resposta de Sucesso (200 OK)** (Schema: `ApontamentoResponseSchema`):
    -   Retorna o objeto do apontamento.
-   **Respostas de Erro Comuns**:
    -   `404 Not Found`: Apontamento não encontrado.

### 8.5. Atualizar Apontamento Manual

-   **Endpoint**: `PUT /apontamentos/{apontamento_id}`
-   **Descrição**: Atualiza um apontamento existente. **Importante: Somente apontamentos com `fonte_apontamento` = `MANUAL` podem ser atualizados por este endpoint.**
-   **Parâmetros de Path**:
    -   `apontamento_id` (integer, obrigatório): ID do apontamento a ser atualizado.
-   **Corpo da Requisição (JSON)** (Schema: `ApontamentoUpdateSchema` - todos os campos são opcionais):
    -   Mesmos campos de `ApontamentoCreateSchema`, mas todos opcionais. Fornecer apenas os campos a serem alterados.
-   **Exemplo de Requisição (alterando horas e descrição)**:

    ```json
    {
      "horas_apontadas": 5.0,
      "descricao": "Correção da funcionalidade X e testes"
    }
    ```

-   **Resposta de Sucesso (200 OK)** (Schema: `ApontamentoResponseSchema`):
    -   Retorna o objeto do apontamento atualizado.
-   **Respostas de Erro Comuns**:
    -   `404 Not Found`: Apontamento não encontrado.
    -   `403 Forbidden`: Tentativa de atualizar um apontamento do tipo `JIRA`.
    -   `400 Bad Request`: Dados inválidos.
    -   `422 Unprocessable Entity`.

### 8.6. Excluir Apontamento Manual

-   **Endpoint**: `DELETE /apontamentos/{apontamento_id}`
-   **Descrição**: Remove um apontamento existente. **Importante: Somente apontamentos com `fonte_apontamento` = `MANUAL` podem ser excluídos por este endpoint.**
-   **Parâmetros de Path**:
    -   `apontamento_id` (integer, obrigatório): ID do apontamento a ser excluído.
-   **Resposta de Sucesso (204 NO CONTENT)**:
    -   Nenhum corpo de resposta.
-   **Respostas de Erro Comuns**:
    -   `404 Not Found`: Apontamento não encontrado.
    -   `403 Forbidden`: Tentativa de excluir um apontamento do tipo `JIRA`.
    -   `400 Bad Request`.
```

### 9. Gerenciamento de Relatórios

Endpoints para gerar diversos relatórios sobre horas, recursos e projetos. Todos os endpoints requerem autenticação de administrador.

#### 9.1. Relatório de Horas Apontadas

Gera um relatório de horas apontadas com diversas opções de filtro e agrupamento. Este endpoint é similar ao de agregações de apontamentos, mas pode oferecer uma formatação ou conjunto de dados ligeiramente diferente, geralmente como uma lista de dicionários.

- **Endpoint:** `/relatorios/horas-apontadas`
- **Método:** `GET`
- **Autenticação:** Administrador
- **Parâmetros de Query (Opcionais):**
  - `recurso_id` (integer): Filtrar por ID do recurso.
  - `projeto_id` (integer): Filtrar por ID do projeto.
  - `equipe_id` (integer): Filtrar por ID da equipe do recurso.
  - `secao_id` (integer): Filtrar por ID da seção do recurso.
  - `data_inicio` (date): Data inicial do período (formato: YYYY-MM-DD).
  - `data_fim` (date): Data final do período (formato: YYYY-MM-DD).
  - `fonte_apontamento` (string, enum: `MANUAL`, `JIRA`): Filtrar pela fonte do apontamento.
  - `agrupar_por_recurso` (boolean, default: `false`): Agrupar resultados por recurso.
  - `agrupar_por_projeto` (boolean, default: `false`): Agrupar resultados por projeto.
  - `agrupar_por_data` (boolean, default: `false`): Agrupar resultados por data.
  - `agrupar_por_mes` (boolean, default: `true`): Agrupar resultados por mês/ano.
- **Resposta de Sucesso (200 OK):** Uma lista de objetos, onde cada objeto representa um grupo agregado.
  ```json
  [
    {
      "recurso_id": 10,
      "recurso_nome": "Recurso A", // Exemplo, pode não estar presente
      "total_horas": 75.5,
      "total_registros": 10
    },
    {
      "projeto_id": 5,
      "projeto_nome": "Projeto X", // Exemplo
      "total_horas": 120.0,
      "total_registros": 15
    }
    // ... outros agrupamentos dependendo dos parâmetros
  ]
  ```

#### 9.2. Relatório Comparativo: Planejado vs. Realizado (Query Direta)

Gera um relatório comparativo entre horas planejadas e horas realizadas/apontadas. Este endpoint específico pode usar uma query SQL mais direta para consolidação.

- **Endpoint:** `/relatorios/comparativo-planejado-realizado`
- **Método:** `GET`
- **Autenticação:** Administrador
- **Parâmetros de Query:**
  - `ano` (integer, obrigatório): Ano do relatório.
  - `mes` (integer, opcional): Mês do relatório (1-12).
  - `recurso_id` (integer, opcional): Filtrar por ID do recurso.
  - `projeto_id` (integer, opcional): Filtrar por ID do projeto.
  - `equipe_id` (integer, opcional): Filtrar por ID da equipe.
- **Resposta de Sucesso (200 OK):** Lista de objetos com a comparação.
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
    // ... mais resultados
  ]
  ```

#### 9.3. Relatório de Horas por Projeto

Obtém um relatório de horas apontadas, agregadas por projeto, para um determinado período e filtros.

- **Endpoint:** `/relatorios/horas-por-projeto`
- **Método:** `GET`
- **Autenticação:** Administrador
- **Parâmetros de Query (Opcionais):**
  - `data_inicio` (date): Data inicial do período.
  - `data_fim` (date): Data final do período.
  - `secao_id` (integer): Filtrar por ID da seção.
  - `equipe_id` (integer): Filtrar por ID da equipe.
- **Resposta de Sucesso (200 OK):** Lista de objetos, cada um representando um projeto e suas horas.
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
    // ... mais projetos
  ]
  ```

#### 9.4. Relatório de Horas por Recurso

Obtém um relatório de horas apontadas, agregadas por recurso, para um determinado período e filtros.

- **Endpoint:** `/relatorios/horas-por-recurso`
- **Método:** `GET`
- **Autenticação:** Administrador
- **Parâmetros de Query (Opcionais):**
  - `data_inicio` (date): Data inicial do período.
  - `data_fim` (date): Data final do período.
  - `projeto_id` (integer): Filtrar por ID do projeto.
  - `equipe_id` (integer): Filtrar por ID da equipe.
  - `secao_id` (integer): Filtrar por ID da seção.
- **Resposta de Sucesso (200 OK):** Lista de objetos, cada um representando um recurso e suas horas.
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
    // ... mais recursos
  ]
  ```

#### 9.5. Relatório Planejado vs. Realizado (Service-based)

Obtém um relatório comparativo entre horas planejadas e horas realizadas (apontadas), utilizando a lógica de serviço. Este é geralmente mais robusto e preferível ao endpoint com query direta para consistência.

- **Endpoint:** `/relatorios/planejado-vs-realizado`
- **Método:** `GET`
- **Autenticação:** Administrador
- **Parâmetros de Query:**
  - `ano` (integer, obrigatório): Ano de referência.
  - `mes` (integer, opcional): Mês de referência (1-12). Se não informado, considera o ano todo.
  - `projeto_id` (integer, opcional): Filtrar por ID do projeto.
  - `recurso_id` (integer, opcional): Filtrar por ID do recurso.
  - `equipe_id` (integer, opcional): Filtrar por ID da equipe.
  - `secao_id` (integer, opcional): Filtrar por ID da seção.
- **Resposta de Sucesso (200 OK):** Lista de objetos com a análise comparativa.
  ```json
  [
    {
      // A estrutura exata pode variar dependendo da implementação do serviço,
      // mas geralmente inclui identificadores, horas planejadas e horas realizadas.
      "identificador_grupo": "Projeto Alpha / Recurso Beta", // ou similar
      "ano": 2024,
      "mes": 8,
      "horas_planejadas": 100.0,
      "horas_realizadas": 95.5,
      "saldo_horas": -4.5, // Planejado - Realizado
      "percentual_realizacao": 95.5 // (Realizado / Planejado) * 100
    }
    // ... mais entradas
  ]
  ```
  - **Nota:** O erro `400 Bad Request` é retornado se o mês for inválido (e.g., < 1 ou > 12).

#### 9.6. Relatório de Disponibilidade de Recursos

Retorna um relatório detalhado sobre a disponibilidade dos recursos, incluindo horas de cadastro (RH), horas planejadas, horas realizadas, horas livres e percentuais de alocação/utilização.

- **Endpoint:** `/relatorios/disponibilidade-recursos`
- **Método:** `GET`
- **Autenticação:** Administrador
- **Parâmetros de Query:**
  - `ano` (integer, obrigatório): Ano de referência para a disponibilidade.
  - `mes` (integer, opcional, 1-12): Mês de referência. Se não informado, retorna para o ano todo.
  - `recurso_id` (integer, opcional): Filtrar para um recurso específico.
- **Resposta de Sucesso (200 OK):** Lista de objetos, cada um detalhando a disponibilidade de um recurso.
  ```json
  [
    {
      "recurso_id": 10,
      "recurso_nome": "Carlos Andrade",
      "ano": 2024,
      "mes": 8, // ou null se consulta anual
      "horas_capacidade_rh": 160.0, // Horas do cadastro do recurso no período
      "horas_planejadas_total": 150.0,
      "horas_realizadas_total": 145.5,
      "horas_disponiveis_planejamento": 10.0, // Capacidade RH - Planejado Total
      "horas_saldo_realizado_vs_planejado": -4.5, // Realizado - Planejado
      "percentual_alocacao_planejada": 93.75, // (Planejado / Capacidade RH) * 100
      "percentual_utilizacao_realizada": 90.94 // (Realizado / Capacidade RH) * 100
      // Outros campos podem estar presentes dependendo da lógica do serviço
    }
    // ... mais recursos
  ]
  ```
- **Respostas de Erro:**
  - `500 Internal Server Error`: Em caso de erro interno ao processar o relatório.

## 10. Autenticação

A API gerencia a autenticação e criação de usuários através dos seguintes endpoints. Embora exista um sistema interno de gerenciamento de usuários e tokens JWT, o fluxo principal de autenticação da aplicação pode ser delegado a um sistema externo da WEG, conforme a configuração do ambiente.

### 10.1. Obter Token de Acesso

**Endpoint:** `POST /auth/token`

**Descrição:** Autentica um usuário com base em email (username) e senha, retornando um token de acesso JWT.

**Corpo da Requisição (application/x-www-form-urlencoded):**

*   `username` (string, obrigatório): O email do usuário.
*   `password` (string, obrigatório): A senha do usuário.

**Exemplo de Resposta (200 OK):**

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Respostas de Erro Possíveis:**

*   `401 Unauthorized`: Email ou senha incorretos, ou usuário inativo.

### 10.2. Criar Novo Usuário

**Endpoint:** `POST /usuarios`

**Descrição:** Cria um novo usuário no sistema. Esta operação requer autenticação como administrador.

**Corpo da Requisição (application/json):**

```json
{
  "email": "novo.usuario@example.com",
  "nome": "Novo Usuário",
  "role": "recurso", // Pode ser "admin", "gestor", ou "recurso"
  "password": "senhaSegura123",
  "recurso_id": null, // Opcional, ID do recurso associado
  "ativo": true
}
```

**Exemplo de Resposta (200 OK):**

```json
{
  "email": "novo.usuario@example.com",
  "nome": "Novo Usuário",
  "role": "recurso",
  "recurso_id": null,
  "ativo": true
}
```

**Respostas de Erro Possíveis:**

*   `400 Bad Request`: Se o email já estiver em uso ou a senha não atender aos critérios.
*   `401 Unauthorized`: Se o usuário autenticado não for um administrador.

## 11. Health Check

A API fornece endpoints para verificar seu estado operacional.

### 11.1. Verificação de Saúde Principal

**Endpoint:** `GET /health`

**Descrição:** Endpoint principal para verificar se a API está em execução e respondendo.

**Parâmetros da Query:** Nenhum.

**Exemplo de Resposta (200 OK):**

```json
{
  "status": "ok"
}
```

**Outros Endpoints de Health (uso interno/específico):**

*   `GET /readiness`: Indica se a aplicação está pronta para aceitar tráfego.
*   `GET /liveness`: Indica se a aplicação está viva (não travou).

Ambos retornam `{"status": "ok"}` e geralmente não são incluídos na documentação Swagger pública.