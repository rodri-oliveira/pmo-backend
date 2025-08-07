# WEG Automação PMO - Backend

Este repositório contém o backend da **Plataforma de Otimização Estratégica de Recursos do PMO**. A solução foi desenvolvida para transformar dados operacionais em inteligência estratégica, centralizando informações, automatizando processos e fornecendo visibilidade em tempo real para uma tomada de decisão ágil e fundamentada.

---

## Visão Geral

A plataforma substitui o modelo anterior baseado em planilhas, superando seus limites de escalabilidade. O objetivo é ser um hub central de inteligência para a gestão de projetos, equipes e recursos, com integração nativa ao Jira para automação da coleta de apontamentos de horas.

| Pilar de Transformação | Resultado Estratégico |
| :--- | :--- |
| **Eficiência Operacional** | Automação de tarefas manuais, liberando a equipe para atividades de maior valor agregado. |
| **Confiabilidade da Informação** | Dados precisos e em tempo real, servindo como uma fonte única e confiável. |
| **Inteligência de Negócio** | Capacidade de realizar análises preditivas e proativas para otimizar a alocação de talentos. |
| **Governança e Controle** | Visibilidade completa sobre o portfólio de projetos, garantindo alinhamento estratégico. |

---

## Configuração do Ambiente

### 1. Variáveis de Ambiente

Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis. Para o ambiente de desenvolvimento, você pode usar os valores de exemplo abaixo.

```env
# Exemplo de configuração para desenvolvimento local
SWAGGER_SERVERS_LIST=/,/api

# Configurações do Banco de Dados (exemplo)
POSTGRES_SERVER=localhost
POSTGRES_USER=seu_usuario
POSTGRES_PASSWORD=sua_senha
POSTGRES_DB=automacaopmopostgre
POSTGRES_PORT=5432
```

### 2. Configuração do Banco de Dados (PostgreSQL)

As credenciais de acesso para o ambiente de QAS são:

- **Database:** `automacaopmopostgre`
- **Username:** `5e0dceda-d930-5742-a8d9-1f2d1ff22159`
- **Password:** `b@p5rk8&9BJRVEQ`
- **Host:** `qas-postgresql-ap.weg.net`
- **Port:** `40030`

#### Comandos de Inicialização do Banco

Execute os seguintes comandos para preparar o banco de dados:

1.  **Testar a conexão:**
    ```sh
    python -m app.db.test_connection
    ```

2.  **Criar e aplicar as migrações com Alembic:**
    ```sh
    # Gerar um novo arquivo de migração baseado nas mudanças dos modelos
    alembic revision --autogenerate -m "Sua mensagem de migração"

    # Aplicar todas as migrações pendentes
    alembic upgrade head
    ```

3.  **Inicializar com dados básicos (se necessário):**
    ```sh
    python -m app.db.init_db
    ```

---

## Executando a API

Este projeto utiliza FastAPI. Para executar o servidor de desenvolvimento, utilize o comando:

```sh
fastapi dev main.py
```

A API estará disponível em [http://localhost:8000](http://localhost:8000).

A documentação interativa (Swagger UI) pode ser acessada em [http://localhost:8000/docs](http://localhost:8000/docs).
