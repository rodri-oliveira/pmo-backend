import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from datetime import datetime
import aiohttp
from app.db.session import AsyncSessionLocal
from app.db.orm_models import Projeto
from app.infrastructure.repositories.sqlalchemy_projeto_repository import SQLAlchemyProjetoRepository
import logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sincronizar_jira_projetos")

JIRA_PROJECT_KEYS = ["SEG", "SGI", "TIN"]
JIRA_API_URL = "https://jiracloudweg.atlassian.net/rest/api/3/project/{}?expand=description"
JIRA_AUTH_HEADER = {
    "Authorization": "Basic cm9saXZlaXJhQHdlZy5uZXQ6QVRBVFQzeEZmR0YwZG0xUzdSSHNReGFSTDZkNmZiaEZUMFNxSjZLbE9ScWRXQzg1M1Jlb3hFMUpnM0dSeXRUVTN4dG5McjdGVWg3WWFKZ2M1RDZwd3J5bjhQc3lHVDNrSklyRUlyVHpmNF9lMGJYLUdJdmxOOFIxanhyMV9GVGhLY1h3V1N0dU9VbE5ucEY2eFlhclhfWFpRb3RhTzlXeFhVaXlIWkdHTDFaMEx5cmJ4VzVyNVYwPUYxMDA3MDNF",
    "Accept": "application/json"
}

STATUS_NAO_INICIADO_ID = 2  # ID do status 'Não Iniciado' (ajuste se necessário)

async def buscar_projeto_jira(session_http, key):
    url = JIRA_API_URL.format(key)
    async with session_http.get(url, headers=JIRA_AUTH_HEADER) as resp:
        if resp.status != 200:
            logger.error(f"Erro ao buscar projeto {key} no Jira: {resp.status} - {await resp.text()}")
            return None
        data = await resp.json()
        return data

async def sincronizar_projetos_jira():
    async with aiohttp.ClientSession() as session_http:
        async with AsyncSessionLocal() as db_session:
            repo = SQLAlchemyProjetoRepository(db_session)
            for key in JIRA_PROJECT_KEYS:
                logger.info(f"Sincronizando projeto {key}...")
                projeto_jira = await buscar_projeto_jira(session_http, key)
                if not projeto_jira:
                    logger.warning(f"Projeto {key} não encontrado no Jira.")
                    continue
                # Extrair campos
                chave_jira = projeto_jira.get("key")
                nome_jira = projeto_jira.get("name")
                id_interno_jira = projeto_jira.get("id")
                descricao_jira = None
                if isinstance(projeto_jira.get("description"), dict):
                    descricao_jira = projeto_jira["description"].get("plain") or projeto_jira["description"].get("content") or str(projeto_jira["description"])
                elif projeto_jira.get("description"):
                    descricao_jira = projeto_jira["description"]
                arquivado_jira = projeto_jira.get("archived", False)
                # Verificar existência
                existente = await repo.get_by_jira_project_key(chave_jira)
                now = datetime.now()
                if existente is None:
                    # INSERT
                    from app.application.dtos.projeto_dtos import ProjetoCreateDTO
                    dto = ProjetoCreateDTO(
                        nome=nome_jira,
                        codigo_empresa=id_interno_jira,
                        descricao=descricao_jira,
                        jira_project_key=chave_jira,
                        status_projeto_id=STATUS_NAO_INICIADO_ID,
                        data_inicio_prevista=None,
                        data_fim_prevista=None,
                        ativo=not arquivado_jira,
                        data_criacao=now,
                        data_atualizacao=now
                    )
                    try:
                        await repo.create(dto)
                        logger.info(f"Projeto {chave_jira} inserido com sucesso.")
                    except Exception as e:
                        logger.error(f"Erro ao inserir projeto {chave_jira}: {e}")
                else:
                    # UPDATE
                    from app.api.dtos.projeto_schema import ProjetoUpdateDTO
                    dto = ProjetoUpdateDTO(
                        nome=nome_jira,
                        descricao=descricao_jira,
                        ativo=not arquivado_jira,
                        data_atualizacao=now
                    )
                    try:
                        await repo.update(existente.id, dto)
                        logger.info(f"Projeto {chave_jira} atualizado com sucesso.")
                    except Exception as e:
                        logger.error(f"Erro ao atualizar projeto {chave_jira}: {e}")

if __name__ == "__main__":
    asyncio.run(sincronizar_projetos_jira())
