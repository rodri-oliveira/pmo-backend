# Documentação dos Endpoints da API e Conexão Frontend-Backend

## Estrutura Geral da API

A API está estruturada com o prefixo base `/backend/v1` e utiliza o framework FastAPI. Todas as requisições do frontend devem ser feitas para este caminho base seguido pelo endpoint específico.

## Autenticação

- **Método**: A autenticação é feita via Keycloak
- **Endpoint**: `/verificar-token` - Para verificar se o token JWT é válido
- **Conexão**: O frontend deve incluir o token JWT no header `Authorization` para todos os endpoints protegidos

## Endpoints Disponíveis

### 1. Recursos (`/recursos`)

- **GET `/recursos`**: Lista todos os recursos com opções de filtro (nome, email, matricula, equipe_id, ativo)
- **GET `/recursos/{recurso_id}`**: Obtém detalhes de um recurso específico
- **POST `/recursos`**: Cria um novo recurso
- **PUT `/recursos/{recurso_id}`**: Atualiza um recurso existente
- **DELETE `/recursos/{recurso_id}`**: Remove um recurso (exclusão lógica)
- **GET `/recursos/{recurso_id}/disponibilidade`**: Obtém relatório de disponibilidade para um recurso específico

### 2. Projetos (`/projetos`)

- **GET `/projetos`**: Lista todos os projetos com opções de filtro
- **GET `/projetos/{projeto_id}`**: Obtém detalhes de um projeto específico
- **POST `/projetos`**: Cria um novo projeto
- **PUT `/projetos/{projeto_id}`**: Atualiza um projeto existente
- **DELETE `/projetos/{projeto_id}`**: Remove um projeto

### 3. Equipes (`/equipes`)

- **GET `/equipes`**: Lista todas as equipes
- **GET `/equipes/{equipe_id}`**: Obtém detalhes de uma equipe específica
- **POST `/equipes`**: Cria uma nova equipe
- **PUT `/equipes/{equipe_id}`**: Atualiza uma equipe existente
- **DELETE `/equipes/{equipe_id}`**: Remove uma equipe

### 4. Seções (`/secoes`)

- **GET `/secoes`**: Lista todas as seções
- **GET `/secoes/{secao_id}`**: Obtém detalhes de uma seção específica
- **POST `/secoes`**: Cria uma nova seção
- **PUT `/secoes/{secao_id}`**: Atualiza uma seção existente
- **DELETE `/secoes/{secao_id}`**: Remove uma seção

### 5. Status de Projetos (`/status-projetos`)

- **GET `/status-projetos`**: Lista todos os status de projetos
- **GET `/status-projetos/{status_id}`**: Obtém detalhes de um status específico
- **POST `/status-projetos`**: Cria um novo status
- **PUT `/status-projetos/{status_id}`**: Atualiza um status existente
- **DELETE `/status-projetos/{status_id}`**: Remove um status

### 6. Planejamento de Horas (`/planejamento-horas`)

- **GET `/planejamento-horas`**: Lista todos os planejamentos de horas
- **GET `/planejamento-horas/{planejamento_id}`**: Obtém detalhes de um planejamento específico
- **POST `/planejamento-horas`**: Cria um novo planejamento
- **PUT `/planejamento-horas/{planejamento_id}`**: Atualiza um planejamento existente
- **DELETE `/planejamento-horas/{planejamento_id}`**: Remove um planejamento

### 7. Apontamentos (`/apontamentos`)

- **GET `/apontamentos`**: Lista todos os apontamentos
- **GET `/apontamentos/{apontamento_id}`**: Obtém detalhes de um apontamento específico
- **POST `/apontamentos`**: Cria um novo apontamento
- **PUT `/apontamentos/{apontamento_id}`**: Atualiza um apontamento existente
- **DELETE `/apontamentos/{apontamento_id}`**: Remove um apontamento

### 8. Relatórios (`/relatorios`)

- **GET `/relatorios/planejado-vs-realizado`**: Obtém relatório comparativo entre horas planejadas e realizadas
- Outros endpoints de relatórios específicos

### 9. Alocações (`/alocacoes`)

- **GET `/alocacoes`**: Lista todas as alocações
- **GET `/alocacoes/{alocacao_id}`**: Obtém detalhes de uma alocação específica
- **POST `/alocacoes`**: Cria uma nova alocação
- **PUT `/alocacoes/{alocacao_id}`**: Atualiza uma alocação existente
- **DELETE `/alocacoes/{alocacao_id}`**: Remove uma alocação

## Formato de Resposta da API

A API retorna dados no formato JSON com a seguinte estrutura:

1. **Listas de itens**: Geralmente retornadas como arrays de objetos
   ```json
   [
     { "id": 1, "nome": "Item 1", ... },
     { "id": 2, "nome": "Item 2", ... }
   ]
   ```

2. **Objetos paginados**: Alguns endpoints retornam objetos com paginação
   ```json
   {
     "items": [ ... ],
     "total": 100,
     "page": 1,
     "size": 10
   }
   ```

3. **Objetos individuais**: Retornados como objetos JSON
   ```json
   { "id": 1, "nome": "Item", ... }
   ```

## Conexão Frontend-Backend

### Configuração do Frontend

1. **URL Base**: O frontend deve configurar a URL base para apontar para `/backend/v1`
2. **Proxy**: O Next.js está configurado com um proxy que redireciona requisições de `/backend/*` para o servidor backend em `http://localhost:8000`
3. **Autenticação**: Todas as requisições autenticadas devem incluir o token JWT no header `Authorization`

### Tratamento de Erros

1. **Erros HTTP**: A API retorna códigos de status HTTP apropriados (400, 404, 500, etc.)
2. **Mensagens de Erro**: Erros incluem um campo `detail` com a mensagem de erro
   ```json
   { "detail": "Recurso não encontrado" }
   ```

### Tratamento de Dados no Frontend

1. **Validação de Arrays**: O frontend deve sempre verificar se os dados retornados são arrays válidos
   ```typescript
   const dados = response.items || [];
   ```

2. **Timeout**: Implementar timeout para evitar carregamento infinito
   ```typescript
   const fetchWithTimeout = async (url, options, timeout = 10000) => {
     const controller = new AbortController();
     const id = setTimeout(() => controller.abort(), timeout);
     try {
       const response = await fetch(url, { ...options, signal: controller.signal });
       clearTimeout(id);
       return response;
     } catch (error) {
       clearTimeout(id);
       throw error;
     }
   };
   ```

3. **Tratamento de Resposta**: Sempre verificar e processar adequadamente a resposta da API
   ```typescript
   try {
     const data = await apiGet<any>('/recursos');
     setRecursos(Array.isArray(data) ? data : data.items || []);
   } catch (error) {
     console.error('Erro ao buscar recursos:', error);
     // Tratar o erro adequadamente (exibir mensagem, etc.)
   }
   ```
