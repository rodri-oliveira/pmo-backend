# WEG Automação PMO Backend

## Configuração do Banco de Dados PostgreSQL

### Credenciais de acesso
- **Database**: automacaopmopostgre
- **Username**: 5e0dceda-d930-5742-a8d9-1f2d1ff22159
- **Password**: b@p5rk8&9BJRVEQ
- **Host**: qas-postgresql-ap.weg.net
- **Port**: 40030

### Inicialização do Banco de Dados

1. **Testar a conexão**:
   ```
   python -m app.db.test_connection
   ```

2. **Criar as migrações com Alembic**:
   ```
   # Iniciar uma nova migração
   alembic revision --autogenerate -m "Criação inicial das tabelas"
   
   # Aplicar as migrações
   alembic upgrade head
   ```

3. **Inicializar dados iniciais**:
   ```
   python -m app.db.init_db
   ```

## Execução da API

This is a [FastAPI](https://fastapi.tiangolo.com/) project bootstrapped with [Developers Portal](https://developers-portal.weg.net/).

## Getting Started

First, to run in development you may need to create a `.env` file in the root of the project.

This `.env` file should contain the given variables:

|Name|Description|Example|
|-|-|-|
|SWAGGER_SERVERS_LIST|List of servers divided by `,` that are passed to the [servers](https://swagger.io/docs/specification/api-host-and-base-path/) property of OpenAPI|`/,/api`|


run the development server:

```bash
fastapi dev main.py
```

The API will be available at [http://localhost:3000/api](http://localhost:3000/api).

> You can find the docs at [http://localhost:3000/api](http://localhost:3000/api)

## Learn More

To leare more about FastAPI, take a look at the following resources:

- [FastAPI Documentation](https://fastapi.tiangolo.com/learn/) - learn about FastAPI features and API.

A API estará disponível em http://localhost:8000