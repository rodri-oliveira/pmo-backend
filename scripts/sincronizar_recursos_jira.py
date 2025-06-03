import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from datetime import datetime
import logging
import aiohttp
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.orm_models import Recurso, Equipe, Secao
from app.infrastructure.repositories.sqlalchemy_recurso_repository import SQLAlchemyRecursoRepository
from app.application.dtos.recurso_dtos import RecursoUpdateDTO, RecursoCreateDTO

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger("sincronizar_recursos_jira")

# Configurações do Jira
JIRA_API_URL = "https://jiracloudweg.atlassian.net/rest/api/3"

JIRA_AUTH_HEADER = {
    "Authorization": "Basic cm9saXZlaXJhQHdlZy5uZXQ6QVRBVFQzeEZmR0YwZG0xUzdSSHNReGFSTDZkNmZiaEZUMFNxSjZLbE9ScWRXQzg1M1Jlb3hFMUpnM0dSeXRUVTN4dG5McjdGVWg3WWFKZ2M1RDZwd3J5bjhQc3lHVDNrSklyRUlyVHpmNF9lMGJYLUdJdmxOOFIxanhyMV9GVGhLY1h3V1N0dU9VbE5ucEY2eFlhclhfWFpRb3RhTzlXeFhVaXlIWkdHTDFaMEx5cmJ4VzVyNVYwPUYxMDA3MDNF",
    "Accept": "application/json"
}

# Função utilitária para extrair dados de usuário Jira
async def extrair_usuarios_jira(session_http, issues):
    usuarios = {}
    campos_usuario = ["assignee", "reporter", "creator"]
    
    # Log para debug
    logger.info(f"Extraindo usuários de {len(issues)} issues...")
    
    for i, issue in enumerate(issues):
        issue_key = issue.get("key", f"Issue #{i}")
        
        for campo in campos_usuario:
            user = issue.get("fields", {}).get(campo)
            
            if user and user.get("accountId"):
                account_id = user.get("accountId")
                
                # Se já temos este usuário, não precisamos processar novamente
                if account_id in usuarios:
                    continue
                
                # Verifica se temos todos os campos necessários
                if not user.get("displayName"):
                    logger.warning(f"Usuário sem displayName em {issue_key}, campo {campo}: {account_id}")
                    continue
                
                # Adiciona o usuário ao dicionário
                usuarios[account_id] = {
                    "accountId": account_id,
                    "displayName": user.get("displayName"),
                    "emailAddress": user.get("emailAddress"),
                    "active": user.get("active", True)
                }
                
                logger.debug(f"Usuário extraído: {user.get('displayName')} ({account_id})")
    
    logger.info(f"Total de usuários únicos extraídos: {len(usuarios)}")
    return usuarios

async def buscar_issues_jira(session_http):
    # Lista de projetos para buscar (SEG, SGI, DTIN)
    projetos = ["SEG", "SGI", "DTIN"]
    todas_issues = []
    data_inicio = "2024-08-01"
    max_results = 100

    for projeto in projetos:
        start_at = 0
        total_issues = 0
        while True:
            # JQL com filtro de data de criação
            jql = f"project = {projeto} AND created >= {data_inicio}"
            url = f"{JIRA_API_URL}/search?jql={jql}&maxResults={max_results}&startAt={start_at}"
            logger.info(f"Buscando issues do projeto {projeto} na URL: {url}")

            async with session_http.get(url, headers=JIRA_AUTH_HEADER) as resp:
                if resp.status != 200:
                    error_text = await resp.text()
                    logger.error(f"Erro ao buscar issues do projeto {projeto}: {resp.status} - {error_text}")
                    break  # Sai da paginação deste projeto

                data = await resp.json()
                issues_do_projeto = data.get("issues", [])
                total_reportado = data.get("total")
                logger.info(f"Projeto {projeto} (página startAt={start_at}): {len(issues_do_projeto)} issues encontradas | total reportado pela API: {total_reportado}")
                total_issues += len(issues_do_projeto)
                todas_issues.extend(issues_do_projeto)

                if len(issues_do_projeto) < max_results:
                    # Última página
                    break
                start_at += max_results
        logger.info(f"Projeto {projeto}: Total de issues coletadas = {total_issues}")

    logger.info(f"Total de issues encontradas em todos os projetos: {len(todas_issues)}")
    return todas_issues

async def sincronizar_recursos_jira():
    async with aiohttp.ClientSession() as session_http:
        async with AsyncSessionLocal() as db_session:
            repo_recurso = SQLAlchemyRecursoRepository(db_session)
            issues = await buscar_issues_jira(session_http)
            usuarios = await extrair_usuarios_jira(session_http, issues)
            logger.info(f"Total de usuários distintos extraídos do Jira: {len(usuarios)}")
            
            # Primeiro, verificar se o recurso existe por jira_user_id
            recursos_atualizados = 0
            recursos_criados = 0
            for accountId, user in usuarios.items():
                nome = user.get("displayName")
                email = user.get("emailAddress")
                ativo = user.get("active", True)
                
                # Verifica se já existe por jira_user_id
                recurso_existente = await repo_recurso.get_by_jira_user_id(accountId)
                
                # Se não encontrou por jira_user_id e tem email, tenta buscar por email
                if recurso_existente is None and email:
                    try:
                        # Buscar por email
                        result = await db_session.execute(select(Recurso).filter(Recurso.email == email))
                        recurso_por_email = result.scalars().first()
                        
                        if recurso_por_email:
                            recurso_existente = recurso_por_email
                            # Atualiza o jira_user_id já que encontramos por email
                            logger.info(f"Recurso encontrado por email: {nome} ({email}). Atualizando jira_user_id.")
                            
                            # Atualiza o jira_user_id
                            dto_update = RecursoUpdateDTO(
                                jira_user_id=accountId,
                                data_atualizacao=datetime.now().replace(microsecond=0)
                            )
                            await repo_recurso.update(recurso_existente.id, dto_update)
                    except Exception as e:
                        logger.error(f"Erro ao buscar recurso por email: {e}")
                
                now = datetime.now().replace(microsecond=0)
                
                if recurso_existente is None:
                    # Inserir novo recurso, conforme solicitado
                    try:
                        dto_create = RecursoCreateDTO(
                            nome=nome,
                            email=email,
                            ativo=ativo,
                            jira_user_id=accountId,
                            equipe_principal_id=None,
                            matricula=None,
                            cargo=None,
                            data_admissao=None
                        )
                        await repo_recurso.create(dto_create)
                        recursos_criados += 1
                        logger.info(f"Novo recurso inserido: {nome} ({accountId}, {email})")
                    except Exception as e:
                        logger.error(f"Erro ao inserir novo recurso {nome} ({accountId}): {e}")
                else:
                    # Atualiza campos mutáveis
                    try:
                        dto_update = RecursoUpdateDTO(
                            nome=nome,
                            email=email,
                            ativo=ativo,
                            jira_user_id=accountId,  # Garante que o jira_user_id esteja atualizado
                            data_atualizacao=now
                        )
                        await repo_recurso.update(recurso_existente.id, dto_update)
                        recursos_atualizados += 1
                        logger.info(f"Recurso atualizado: {nome} ({accountId})")
                    except Exception as e:
                        logger.error(f"Erro ao atualizar recurso {nome} ({accountId}): {e}")
            
            logger.info(f"Sincronização concluída. Recursos atualizados: {recursos_atualizados}. Recursos criados: {recursos_criados}.")


if __name__ == "__main__":
    asyncio.run(sincronizar_recursos_jira())
