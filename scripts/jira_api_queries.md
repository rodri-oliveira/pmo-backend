# Queries Jira API para Postman

## Configuração Base
- **Base URL**: `https://jiracloudweg.atlassian.net`
- **Authentication**: Basic Auth (username + API token)
- **Headers**: 
  ```
  Content-Type: application/json
  Accept: application/json
  ```

## 1. Buscar Grupos do Jira
```
GET https://jiracloudweg.atlassian.net/rest/api/3/groups/picker?query=
```

## 2. Buscar Todos os Projetos
```
GET https://jiracloudweg.atlassian.net/rest/api/3/project
```

## 3. Buscar Componentes de um Projeto Específico
```
GET https://jiracloudweg.atlassian.net/rest/api/3/project/DTIN/components
GET https://jiracloudweg.atlassian.net/rest/api/3/project/SGI/components
GET https://jiracloudweg.atlassian.net/rest/api/3/project/TIN/components
GET https://jiracloudweg.atlassian.net/rest/api/3/project/SEG/components
```

## 4. Buscar Custom Fields
```
GET https://jiracloudweg.atlassian.net/rest/api/3/field
```

## 5. Buscar Usuários de um Projeto
```
GET https://jiracloudweg.atlassian.net/rest/api/3/user/assignable/search?project=DTIN&maxResults=100
GET https://jiracloudweg.atlassian.net/rest/api/3/user/assignable/search?project=SGI&maxResults=100
GET https://jiracloudweg.atlassian.net/rest/api/3/user/assignable/search?project=TIN&maxResults=100
GET https://jiracloudweg.atlassian.net/rest/api/3/user/assignable/search?project=SEG&maxResults=100
```

## 6. Buscar Issues com Informações de Assignee e Projeto
```
GET https://jiracloudweg.atlassian.net/rest/api/3/search?jql=project IN (DTIN,SGI,TIN,SEG)&fields=key,summary,assignee,project,components&maxResults=50
```

## 7. Buscar Informações de um Usuário Específico
```
GET https://jiracloudweg.atlassian.net/rest/api/3/user?accountId=712020:ac0b3f89-db0a-4332-9b26-b5699be04fcf
```

## 8. Buscar Grupos de um Usuário
```
GET https://jiracloudweg.atlassian.net/rest/api/3/user/groups?accountId=712020:ac0b3f89-db0a-4332-9b26-b5699be04fcf
```

## 9. JQL para Buscar Issues com Worklogs Recentes
```
GET https://jiracloudweg.atlassian.net/rest/api/3/search?jql=project IN (DTIN,SGI,TIN,SEG) AND worklogDate >= "2024-07-01"&fields=key,summary,assignee,project,components,worklog&maxResults=10
```

## 10. Buscar Todas as Roles de Projeto
```
GET https://jiracloudweg.atlassian.net/rest/api/3/project/DTIN/role
```

## Como Usar no Postman:

1. **Criar Collection**: "Jira API Queries"

2. **Configurar Authorization**:
   - Type: Basic Auth
   - Username: seu email Jira
   - Password: seu API token

3. **Testar Conexão** (comece com esta):
   ```
   GET https://jiracloudweg.atlassian.net/rest/api/3/myself
   ```

4. **Executar as queries** na ordem para entender a estrutura organizacional

## Objetivo:
Identificar como os usuários estão organizados no Jira para mapear corretamente para as "equipes" no banco de dados.

Possíveis estruturas a verificar:
- **Grupos**: Organização por departamento/equipe
- **Componentes**: Subdivisões técnicas dentro de projetos
- **Project Roles**: Papéis específicos em cada projeto
- **Custom Fields**: Campos personalizados com informação de equipe
