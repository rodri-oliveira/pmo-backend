import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from datetime import datetime
import aiohttp
from app.db.session import AsyncSessionLocal
from app.infrastructure.repositories.sqlalchemy_projeto_repository import SQLAlchemyProjetoRepository
from app.application.dtos.projeto_dtos import ProjetoCreateDTO, ProjetoUpdateDTO
import logging

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sincronizar_epics_jira")

# Mapeamento entre chave do projeto Jira e secao_id local
JIRA_SECOES = {
    "SEG": 1,  # SEG Seção Segurança da Informação e Riscos TI
    "SGI": 2,  # SGI - Seção Suporte Global Infraestrutura
    "TIN": 3,  # TIN - Seção Tecnologia de Infraestrutura
}

JIRA_AUTH_HEADER = {
    "Authorization": "Basic cm9saXZlaXJhQHdlZy5uZXQ6QVRBVFQzeEZmR0YwZG0xUzdSSHNReGFSTDZkNmZiaEZUMFNxSjZLbE9ScWRXQzg1M1Jlb3hFMUpnM0dSeXRUVTN4dG5McjdGVWg3WWFKZ2M1RDZwd3J5bjhQc3lHVDNrSklyRUlyVHpmNF9lMGJYLUdJdmxOOFIxanhyMV9GVGhLY1h3V1N0dU9VbE5ucEY2eFlhclhfWFpRb3RhTzlXeFhVaXlIWkdHTDFaMEx5cmJ4VzVyNVYwPUYxMDA3MDNF",
    "Accept": "application/json"
}

JIRA_SEARCH_API = "https://jiracloudweg.atlassian.net/rest/api/3/search"
STATUS_NAO_INICIADO_ID = 2
MAX_RESULTS = 50

def extrair_descricao(description):
    if not description:
        return None
    if isinstance(description, str):
        return description
    if isinstance(description, dict):
        if "plain" in description and isinstance(description["plain"], str):
            return description["plain"]
        if "content" in description and isinstance(description["content"], list):
            def extract_from_content(content):
                texts = []
                for item in content:
                    if isinstance(item, dict):
                        if "text" in item and isinstance(item["text"], str):
                            texts.append(item["text"])
                        elif "content" in item:
                            texts.append(extract_from_content(item["content"]))
                return " ".join(texts)
            return extract_from_content(description["content"])
        return str(description)
    if isinstance(description, list):
        return " ".join([extrair_descricao(item) for item in description])
    return str(description)

async def buscar_epics_jira(session_http, chave_jira):
    epics = []
    start_at = 0
    total = 1  # placeholder para entrar no loop
    while start_at < total:
        params = {
            "jql": f"project = {chave_jira} AND issuetype = Epic",
            "fields": "summary,key,description,project,status",
            "startAt": start_at,
            "maxResults": MAX_RESULTS,
        }
        async with session_http.get(JIRA_SEARCH_API, headers=JIRA_AUTH_HEADER, params=params) as resp:
            if resp.status != 200:
                logger.error(f"Erro ao buscar Epics do projeto {chave_jira}: {resp.status} - {await resp.text()}")
                break
            data = await resp.json()
            issues = data.get("issues", [])
            total = data.get("total", 0)
            epics.extend(issues)
            start_at += MAX_RESULTS
    return epics

async def sincronizar_epics():
    async with aiohttp.ClientSession() as session_http:
        async with AsyncSessionLocal() as db_session:
            repo = SQLAlchemyProjetoRepository(db_session)
            for chave_jira, secao_id in JIRA_SECOES.items():
                logger.info(f"Sincronizando Epics do projeto {chave_jira} (secao_id={secao_id})...")
                epics = await buscar_epics_jira(session_http, chave_jira)
                for epic in epics:
                    fields = epic.get("fields", {})
                    epic_key = epic.get("key")
                    epic_name = fields.get("summary")
                    epic_description = extrair_descricao(fields.get("description"))
                    epic_status_jira = (fields.get("status") or {}).get("name", "")
                    now = datetime.now()

                    existente = await repo.get_by_jira_project_key(epic_key)
                    if existente is None:
                        dto = ProjetoCreateDTO(
                            nome=epic_name,
                            codigo_empresa=None,
                            descricao=epic_description,
                            jira_project_key=epic_key,
                            status_projeto_id=STATUS_NAO_INICIADO_ID,
                            data_inicio_prevista=None,
                            data_fim_prevista=None,
                            ativo=True,  # Pode refinar depois usando epic_status_jira
                            data_criacao=now,
                            data_atualizacao=now,
                            secao_id=secao_id,
                        )
                        try:
                            await repo.create(dto)
                            logger.info(f"Epic {epic_key} inserido com sucesso.")
                        except Exception as e:
                            logger.error(f"Erro ao inserir Epic {epic_key}: {e}")
                    else:
                        dto = ProjetoUpdateDTO(
                            nome=epic_name,
                            descricao=epic_description,
                            ativo=True,  # Pode refinar depois usando epic_status_jira
                            data_atualizacao=now,
                            secao_id=secao_id,
                        )
                        try:
                            await repo.update(existente.id, dto)
                            logger.info(f"Epic {epic_key} atualizado com sucesso.")
                        except Exception as e:
                            logger.error(f"Erro ao atualizar Epic {epic_key}: {e}")

if __name__ == "__main__":
    asyncio.run(sincronizar_epics())
