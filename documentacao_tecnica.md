# Documentação Técnica - Sistema de Automação PMO

## Sumário

1. [Visão Geral do Projeto](#visão-geral-do-projeto)
2. [Stack Tecnológica](#stack-tecnológica)
3. [Arquitetura do Sistema](#arquitetura-do-sistema)
4. [Padrões de Projeto](#padrões-de-projeto)
5. [Estrutura do Projeto](#estrutura-do-projeto)
6. [Banco de Dados](#banco-de-dados)
7. [API e Endpoints](#api-e-endpoints)
8. [Autenticação e Segurança](#autenticação-e-segurança)
9. [Tratamento de Erros](#tratamento-de-erros)
10. [Migração para SQLAlchemy Assíncrono](#migração-para-sqlalchemy-assíncrono)
11. [Boas Práticas e Recomendações](#boas-práticas-e-recomendações)
12. [Troubleshooting](#troubleshooting)
13. [Referências](#referências)

## Visão Geral do Projeto

O Sistema de Automação PMO é uma aplicação backend desenvolvida para gerenciar projetos, recursos, alocações e planejamento de horas na WEG. A aplicação utiliza FastAPI como framework web e SQLAlchemy para ORM (Object-Relational Mapping), com uma arquitetura em camadas que segue os princípios de Clean Architecture.

O sistema foi recentemente migrado de SQLAlchemy síncrono para assíncrono, utilizando o driver asyncpg para PostgreSQL, o que melhorou significativamente a performance e a capacidade de lidar com múltiplas requisições simultâneas.

## Stack Tecnológica

### Backend

- **Linguagem de Programação**: Python 3.8+
- **Framework Web**: FastAPI 0.111.0
- **ORM**: SQLAlchemy (versão assíncrona)
- **Driver de Banco de Dados**: asyncpg (PostgreSQL assíncrono)
- **Migração de Banco de Dados**: Alembic
- **Validação de Dados**: Pydantic
- **Configuração**: pydantic-settings 2.3.3
- **Servidor ASGI**: Uvicorn
- **Autenticação**: python-jose (JWT), passlib (bcrypt)
- **Processamento de Formulários**: python-multipart

### Banco de Dados

- **Sistema de Gerenciamento**: PostgreSQL
- **Conexão**: asyncpg (driver assíncrono)
- **Modelagem**: SQLAlchemy ORM
- **Migrações**: Alembic

### Ferramentas de Desenvolvimento

- **Controle de Versão**: Git
- **CI/CD**: GitLab CI
- **Documentação da API**: Swagger UI (integrado ao FastAPI)
- **Containerização**: Docker (Kubernetes)

## Arquitetura do Sistema

O sistema segue uma arquitetura em camadas inspirada nos princípios de Clean Architecture, com separação clara de responsabilidades:

### Camadas da Aplicação

1. **API (Presentation Layer)**
   - Rotas e endpoints FastAPI
   - DTOs (Data Transfer Objects) usando Pydantic
   - Tratamento de requisições e respostas HTTP

2. **Serviços (Service Layer)**
   - Lógica de negócio
   - Orquestração de operações
   - Validações específicas de domínio

3. **Repositórios (Data Access Layer)**
   - Acesso ao banco de dados
   - Operações CRUD
   - Consultas específicas

4. **Modelos (Domain Layer)**
   - Entidades de domínio
   - Regras de negócio
   - Validações de domínio

5. **Infraestrutura (Infrastructure Layer)**
   - Configuração do banco de dados
   - Middlewares
   - Utilitários e ferramentas

### Fluxo de Dados

```
Cliente HTTP → FastAPI → Rotas → Serviços → Repositórios → Banco de Dados
                  ↑          ↓        ↓          ↓
                  └──────────────── Modelos ─────┘
```

## Padrões de Projeto

### Padrões Arquiteturais

1. **Repository Pattern**
   - Abstração do acesso a dados
   - Implementado através de classes base genéricas
   - Facilita testes e substituição da fonte de dados

2. **Dependency Injection**
   - Injeção de dependências via FastAPI
   - Facilita testes e desacoplamento

3. **Service Layer**
   - Encapsula a lógica de negócio
   - Orquestra operações entre repositórios
   - Implementa validações específicas

4. **DTO (Data Transfer Object)**
   - Implementado via Pydantic schemas
   - Validação de dados de entrada e saída
   - Conversão entre formatos

### Padrões de Implementação

1. **Generic Repository**
   - Classe base genérica para operações CRUD
   - Reduz duplicação de código
   - Implementado com TypeVar e Generic

2. **Async/Await**
   - Operações assíncronas para I/O bound
   - Melhor utilização de recursos
   - Maior capacidade de processamento simultâneo

3. **Factory Method**
   - Criação de sessões de banco de dados
   - Implementado via async_sessionmaker

4. **Error Handling Middleware**
   - Tratamento centralizado de exceções
   - Conversão para respostas HTTP apropriadas

## Estrutura do Projeto

```
automacaopmobackend/
├── alembic/                  # Migrações de banco de dados
├── app/                      # Código-fonte principal
│   ├── api/                  # Camada de API
│   │   ├── dtos/             # Schemas Pydantic
│   │   ├── routes/           # Rotas e endpoints
│   │   └── main.py           # Configuração do router principal
│   ├── application/          # Lógica de aplicação
│   ├── core/                 # Configurações e utilitários core
│   │   ├── config.py         # Configurações da aplicação
│   │   ├── security.py       # Autenticação e segurança
│   │   └── logging.py        # Configuração de logs
│   ├── db/                   # Configuração de banco de dados
│   │   ├── session.py        # Configuração de sessão assíncrona
│   │   └── orm_models.py     # Modelos ORM
│   ├── domain/               # Regras de domínio
│   │   └── repositories/     # Interfaces de repositórios
│   ├── infrastructure/       # Implementações de infraestrutura
│   │   ├── database/         # Modelos SQL
│   │   └── repositories/     # Implementações de repositórios
│   ├── integrations/         # Integrações com sistemas externos
│   ├── models/               # Modelos de domínio
│   ├── repositories/         # Repositórios de acesso a dados
│   ├── services/             # Serviços de negócio
│   ├── utils/                # Utilitários
│   ├── main.py               # Ponto de entrada da aplicação
│   └── start.py              # Script de inicialização
├── k8s/                      # Configurações Kubernetes
├── recursos/                 # Recursos estáticos
├── .env                      # Variáveis de ambiente
├── .gitignore                # Arquivos ignorados pelo Git
├── alembic.ini               # Configuração do Alembic
├── requirements.txt          # Dependências do projeto
└── README.md                 # Documentação básica
```

## Banco de Dados

### Modelagem

O sistema utiliza um banco de dados PostgreSQL com as seguintes entidades principais:

1. **Seção**: Representa uma seção ou departamento
2. **Equipe**: Equipes dentro de uma seção
3. **Recurso**: Colaboradores ou recursos humanos
4. **StatusProjeto**: Status possíveis para projetos
5. **Projeto**: Projetos gerenciados pelo sistema
6. **AlocacaoRecursoProjeto**: Alocação de recursos em projetos
7. **HorasDisponiveisRH**: Horas disponíveis de recursos por mês
8. **HorasPlanejadas**: Planejamento de horas por alocação
9. **Apontamento**: Registro de horas trabalhadas
10. **Usuario**: Usuários do sistema
11. **Configuracao**: Configurações do sistema
12. **LogAtividade**: Logs de atividades dos usuários
13. **SincronizacaoJira**: Registros de sincronização com o Jira

### Relacionamentos Principais

- Seção (1) → Equipe (N)
- Equipe (1) → Recurso (N)
- StatusProjeto (1) → Projeto (N)
- Recurso (1) → AlocacaoRecursoProjeto (N)
- Projeto (1) → AlocacaoRecursoProjeto (N)
- AlocacaoRecursoProjeto (1) → HorasPlanejadas (N)
- Recurso (1) → Apontamento (N)
- Projeto (1) → Apontamento (N)
- Recurso (1) → Usuario (1)

### Configuração de Conexão

A conexão com o banco de dados é configurada de forma assíncrona usando o driver asyncpg:

```python
async_engine = create_async_engine(
    settings.DATABASE_URI,
    echo=False,
    pool_pre_ping=True,      # Garante que a conexão está viva antes de usar
    pool_recycle=1800,       # Recicla conexões antigas a cada 30 minutos
    pool_size=10,            # Número de conexões simultâneas
    max_overflow=20          # Número extra de conexões temporárias
)
```

### Gerenciamento de Sessões

O sistema utiliza sessões assíncronas com o padrão de context manager:

```python
async def get_async_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
```

### Migrações

As migrações de banco de dados são gerenciadas pelo Alembic, permitindo:
- Versionamento do esquema
- Atualizações incrementais
- Rollback de alterações

## API e Endpoints

### Estrutura da API

A API segue uma estrutura RESTful com os seguintes grupos de endpoints:

1. **Autenticação**: Login e gerenciamento de tokens
2. **Seções**: CRUD de seções
3. **Equipes**: CRUD de equipes
4. **Recursos**: CRUD de recursos
5. **Status de Projetos**: CRUD de status de projetos
6. **Projetos**: CRUD de projetos
7. **Alocações**: Gerenciamento de alocações de recursos em projetos
8. **Planejamento de Horas**: Planejamento de horas por alocação
9. **Apontamentos**: Registro de horas trabalhadas
10. **Relatórios**: Relatórios diversos

### Documentação da API

A documentação da API é gerada automaticamente pelo FastAPI e está disponível em:
- `/docs`: Swagger UI
- `/redoc`: ReDoc

### Prefixo da API

Todos os endpoints da API são prefixados com `/backend/v1`, por exemplo:
- `/backend/v1/projetos`
- `/backend/v1/recursos`
- `/backend/v1/alocacoes`

## Autenticação e Segurança

### Mecanismo de Autenticação

O sistema utiliza autenticação baseada em JWT (JSON Web Tokens) com:
- Tokens de acesso com tempo de expiração
- Algoritmo HS256 para assinatura
- Armazenamento seguro de senhas com bcrypt

### Middleware de Segurança

- CORS (Cross-Origin Resource Sharing) configurado para permitir origens específicas
- Proteção contra CSRF (Cross-Site Request Forgery)
- Validação de tokens em endpoints protegidos

### Funções de Segurança

```python
# Obter usuário atual (autenticado)
async def get_current_user(token: str, db: AsyncSession) -> Usuario:
    # Decodifica o token e valida o usuário
    
# Obter usuário administrador
async def get_current_admin_user(user: Usuario = Depends(get_current_user)) -> Usuario:
    # Verifica se o usuário tem permissão de administrador
```

## Tratamento de Erros

### Padrão de Tratamento de Erros

O sistema implementa um padrão consistente de tratamento de erros em todos os endpoints:

1. **Erros de Validação**:
   - Capturados via `ValueError`
   - Retornam HTTP 400 (Bad Request)
   - Incluem mensagem descritiva

2. **Erros de Banco de Dados**:
   - Capturados via `SQLAlchemyError`
   - Retornam HTTP 500 (Internal Server Error)
   - Incluem detalhes técnicos para depuração
   - Realizam rollback automático da transação

3. **Erros Inesperados**:
   - Capturados via `Exception` genérica
   - Retornam HTTP 500 (Internal Server Error)
   - Ocultam detalhes técnicos em produção
   - Registram o erro completo nos logs

### Exemplo de Implementação

```python
try:
    # Lógica de negócio
except ValueError as e:
    # Tratamento específico para erros de validação
    logging.error(f"Erro de validação: {str(e)}")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
except SQLAlchemyError as e:
    # Tratamento para erros de banco de dados
    logging.error(f"Erro de banco de dados: {str(e)}")
    await db.rollback()
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Erro de banco de dados: {str(e)}"
    )
except Exception as e:
    # Tratamento para outros erros não previstos
    logging.error(f"Erro inesperado: {str(e)}")
    await db.rollback()
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Erro interno do servidor ao processar a solicitação"
    )
```

### Logging

O sistema utiliza o módulo `logging` do Python para registrar eventos e erros:

```python
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
```

## Migração para SQLAlchemy Assíncrono

### Visão Geral da Migração

O projeto foi migrado de SQLAlchemy síncrono para assíncrono, o que envolveu:

1. **Alteração da String de Conexão**:
   - Mudança do driver para `asyncpg`
   - Exemplo: `postgresql+asyncpg://user:password@host:port/dbname`

2. **Configuração de Engine e Sessão**:
   - Uso de `create_async_engine` em vez de `create_engine`
   - Uso de `AsyncSession` em vez de `Session`
   - Uso de `async_sessionmaker` em vez de `sessionmaker`

3. **Alteração de Métodos**:
   - Conversão de métodos síncronos para assíncronos (`async def`)
   - Adição de `await` em todas as operações de banco de dados
   - Substituição de consultas síncronas por consultas assíncronas

4. **Tratamento de Erros**:
   - Adição de `await session.rollback()` em blocos `except`
   - Tratamento adequado de exceções em operações assíncronas

5. **Middleware**:
   - Adição de middleware para suporte a greenlet

### Exemplo de Código Assíncrono

```python
# Consulta assíncrona
query = select(Model).filter(Model.field == value)
result = await session.execute(query)
items = result.scalars().all()

# Operação de escrita assíncrona
session.add(item)
await session.commit()
await session.refresh(item)
```

## Boas Práticas e Recomendações

### Desenvolvimento

1. **Estrutura de Código**:
   - Seguir a estrutura de pastas estabelecida
   - Manter a separação de responsabilidades entre camadas
   - Usar nomes descritivos para arquivos e classes

2. **Padrões de Código**:
   - Seguir PEP 8 para estilo de código Python
   - Usar type hints para melhorar a legibilidade e permitir verificação estática
   - Documentar classes e métodos com docstrings

3. **Operações Assíncronas**:
   - Sempre usar `await` em operações de I/O
   - Evitar bloqueio do loop de eventos
   - Usar `asyncio.gather` para operações paralelas

4. **Tratamento de Erros**:
   - Sempre incluir blocos try/except em operações críticas
   - Fazer rollback explícito em caso de erro
   - Registrar erros com detalhes suficientes para depuração

### Banco de Dados

1. **Consultas**:
   - Usar consultas parametrizadas para evitar injeção de SQL
   - Otimizar consultas com índices apropriados
   - Limitar resultados para evitar sobrecarga de memória

2. **Transações**:
   - Usar transações para operações que exigem atomicidade
   - Garantir que todas as operações de escrita sejam seguidas por commit ou rollback
   - Evitar transações longas que podem bloquear recursos

3. **Conexões**:
   - Configurar pool de conexões adequadamente
   - Usar `pool_pre_ping` para verificar conexões antes de usá-las
   - Configurar `pool_recycle` para evitar conexões obsoletas

### API

1. **Endpoints**:
   - Seguir princípios RESTful
   - Usar códigos de status HTTP apropriados
   - Implementar paginação para listas grandes

2. **Validação**:
   - Validar todos os dados de entrada usando Pydantic
   - Fornecer mensagens de erro claras e úteis
   - Implementar validações de negócio nos serviços

3. **Documentação**:
   - Manter a documentação Swagger atualizada
   - Documentar todos os parâmetros e respostas
   - Incluir exemplos de uso quando possível

## Troubleshooting

### Problemas Comuns e Soluções

1. **Erros de Conexão com Banco de Dados**:
   - Verificar string de conexão
   - Verificar se o banco está acessível
   - Verificar configurações de firewall
   - Verificar credenciais

2. **Erros 500 (Internal Server Error)**:
   - Verificar logs para detalhes do erro
   - Verificar se todas as operações assíncronas têm `await`
   - Verificar tratamento de erros nos repositórios e serviços

3. **Erros 401 (Unauthorized)**:
   - Verificar se o token JWT é válido
   - Verificar se as funções de autenticação estão usando sessões assíncronas
   - Verificar se o usuário existe e está ativo

4. **Erros 422 (Unprocessable Entity)**:
   - Verificar se os dados enviados correspondem ao schema Pydantic
   - Verificar se há campos obrigatórios faltando
   - Verificar se os tipos de dados estão corretos

5. **Problemas de Performance**:
   - Otimizar consultas SQL
   - Verificar índices no banco de dados
   - Implementar caching quando apropriado
   - Verificar configurações do pool de conexões

### Logs e Monitoramento

1. **Logs**:
   - Verificar logs da aplicação para erros
   - Usar níveis de log apropriados (INFO, WARNING, ERROR)
   - Incluir contexto suficiente nos logs

2. **Monitoramento**:
   - Monitorar uso de CPU e memória
   - Monitorar tempo de resposta dos endpoints
   - Monitorar número de conexões com o banco de dados

## Referências

### Documentação Oficial

- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLAlchemy](https://docs.sqlalchemy.org/)
- [Pydantic](https://docs.pydantic.dev/)
- [Alembic](https://alembic.sqlalchemy.org/)
- [Asyncpg](https://magicstack.github.io/asyncpg/current/)

### Artigos e Tutoriais

- [Migrating from Synchronous to Asynchronous SQLAlchemy](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/advanced/best-practices/)
- [Clean Architecture with Python](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

### Ferramentas Recomendadas

- [PyCharm](https://www.jetbrains.com/pycharm/) - IDE para desenvolvimento Python
- [Visual Studio Code](https://code.visualstudio.com/) - Editor de código leve
- [DBeaver](https://dbeaver.io/) - Cliente universal de banco de dados
- [Postman](https://www.postman.com/) - Ferramenta para testar APIs
- [pgAdmin](https://www.pgadmin.org/) - Ferramenta de administração para PostgreSQL
