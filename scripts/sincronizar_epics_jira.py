import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from datetime import datetime, timedelta

# Função para remover fuso horário de um datetime
def remove_timezone(dt):
    if dt and dt.tzinfo:
        return dt.replace(tzinfo=None)
    return dt

# Nova função para padronizar formato de datetime (sem microssegundos)
def padronizar_datetime(dt):
    """Remove timezone e microssegundos de um datetime"""
    if dt and dt.tzinfo:
        dt = dt.replace(tzinfo=None)
    if dt and dt.microsecond:
        dt = dt.replace(microsecond=0)
    return dt

# Função para converter string de data ISO para datetime padronizado
def converter_data_jira(data_str):
    """Converte data do Jira para datetime padronizado (sem timezone e microssegundos)"""
    if not data_str:
        return None
    try:
        if 'Z' in data_str:
            dt = datetime.fromisoformat(data_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(data_str)
        return padronizar_datetime(dt)
    except Exception as e:
        logger.warning(f"Erro ao converter data: {e}. Valor original: {data_str}")
        return None
import aiohttp
from app.db.session import AsyncSessionLocal
# Assumindo que SQLAlchemyProjetoRepository interage com sua tabela 'projeto' local
from app.infrastructure.repositories.sqlalchemy_projeto_repository import SQLAlchemyProjetoRepository
from app.application.dtos.projeto_dtos import ProjetoCreateDTO, ProjetoUpdateDTO # Seus DTOs
import logging
from sqlalchemy import select
from app.db.orm_models import Secao # Seu modelo ORM para a tabela 'secao'

# Configuração de logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(levelname)s:%(name)s:%(message)s'
)
logger = logging.getLogger("sincronizar_epics_para_projetos_locais") # Nome do logger atualizado

# Mapeamento CORRIGIDO entre chave do Projeto Jira (Seção) e secao_id local
# Conforme sua última informação: 1=SEG, 2=SGI, 3=TIN
JIRA_SECOES_MAPEAMENTO = {
    "SEG": 1,  # "SEG Seção Segurança da Informação e Riscos TI"
    "SGI": 2,  # "SGI - Seção Suporte Global Infraestrutura"
    "DTIN": 3,  # "DTIN" é o project key correto para TIN no Jira
}

JIRA_AUTH_HEADER = {
    "Authorization": "Basic cm9saXZlaXJhQHdlZy5uZXQ6QVRBVFQzeEZmR0YwZG0xUzdSSHNReGFSTDZkNmZiaEZUMFNxSjZLbE9ScWRXQzg1M1Jlb3hFMUpnM0dSeXRUVTN4dG5McjdGVWg3WWFKZ2M1RDZwd3J5bjhQc3lHVDNrSklyRUlyVHpmNF9lMGJYLUdJdmxOOFIxanhyMV9GVGhLY1h3V1N0dU9VbE5ucEY2eFlhclhfWFpRb3RhTzlXeFhVaXlIWkdHTDFaMEx5cmJ4VzVyNVYwPUYxMDA3MDNF",
    "Accept": "application/json"
}

JIRA_API_SEARCH_URL = "https://jiracloudweg.atlassian.net/rest/api/3/search" # Endpoint para buscar issues (Epics)
STATUS_NAO_INICIADO_ID = 2
MAX_RESULTS_PER_PAGE = 50 # Quantidade de issues/epics por página da API

def extrair_texto_descricao_jira(description_field):
    """
    Extrai o texto de um campo de descrição do Jira, que pode ser uma string simples
    ou um objeto Atlassian Document Format (ADF) mais complexo.
    Esta é uma extração simplificada para parágrafos de texto.
    """
    if not description_field:
        return None
    if isinstance(description_field, str):
        return description_field
    
    # Tratamento básico para Atlassian Document Format (ADF)
    if isinstance(description_field, dict) and description_field.get("type") == "doc":
        texts = []
        for node in description_field.get("content", []):
            if node.get("type") == "paragraph":
                for content_item in node.get("content", []):
                    if content_item.get("type") == "text" and "text" in content_item:
                        texts.append(content_item["text"])
        return "\n".join(texts) if texts else None # Junta parágrafos com nova linha
    
    # Fallback para outros formatos inesperados, converte para string
    return str(description_field)

async def buscar_epics_do_projeto_jira(session_http, chave_jira_secao):
    """
    Busca todos os issues do tipo 'Epic' para um determinado Projeto Jira (Seção).
    Lida com a paginação da API do Jira.
    """
    all_epics = []
    start_at = 0
    while True:
        params = {
            "jql": f'project = "{chave_jira_secao}" AND issuetype = Epic', # Chave do projeto entre aspas na JQL
            "fields": "summary,key,description,project,status,duedate,created,updated,customfield_10020", # Campos necessários incluindo customfield_10020 para datas de sprint/epic
            "startAt": start_at,
            "maxResults": 100
        }
        logger.info(f"Buscando Epics para seção Jira '{chave_jira_secao}' (página começando em: {start_at})...")
        async with session_http.get(JIRA_API_SEARCH_URL, headers=JIRA_AUTH_HEADER, params=params) as resp:
            if resp.status != 200:
                logger.error(f"Erro ao buscar Epics da seção Jira '{chave_jira_secao}': {resp.status} - {await resp.text()}")
                break  # Sai do loop de paginação em caso de erro

            data = await resp.json()
            issues_na_pagina = data.get("issues", [])
            total_issues_jira = data.get("total", 0)
            logger.info(f"Secao {chave_jira_secao} (página startAt={start_at}): {len(issues_na_pagina)} epics encontrados | total reportado pela API: {total_issues_jira}")
            if not issues_na_pagina:
                logger.info(f"Nenhum Epic a mais encontrado para '{chave_jira_secao}' nesta página.")
                break # Fim da paginação

            all_epics.extend(issues_na_pagina)
            start_at += len(issues_na_pagina) # Incrementa para a próxima página
            
            if start_at >= total_issues_jira:
                logger.info(f"Todos os {total_issues_jira} Epics para '{chave_jira_secao}' foram buscados.")
                break # Fim da paginação
    return all_epics

async def sincronizar_epics_jira():
    logger.info("Iniciando sincronização de Epics do Jira para a tabela 'projeto' local...")
    async with aiohttp.ClientSession() as session_http:
        async with AsyncSessionLocal() as db_session:
            # 'repo_projeto_local' interage com sua tabela 'projeto' (que armazena Epics)
            repo_projeto_local = SQLAlchemyProjetoRepository(db_session)

            for chave_jira_secao, _ in JIRA_SECOES_MAPEAMENTO.items():
                logger.info(f"Processando Epics da Seção Jira: '{chave_jira_secao}'")
                # LOG DETALHADO DO QUE ESTÁ SENDO BUSCADO NO BANCO
                logger.info(f"[DEBUG] Buscando secao com jira_project_key='{chave_jira_secao}' na tabela secao...")
                result = await db_session.execute(select(Secao).where(Secao.jira_project_key == chave_jira_secao))
                secao = result.scalars().first()
                if not secao:
                    logger.error(f"[ERRO] NÃO encontrou secao para jira_project_key='{chave_jira_secao}'. Os Epics dessa seção NÃO terão secao_id vinculado!")
                    secao_id = None
                else:
                    logger.info(f"[DEBUG] Encontrou secao: id={secao.id}, nome='{secao.nome}', jira_project_key='{secao.jira_project_key}' para chave_jira_secao='{chave_jira_secao}'")
                    secao_id = secao.id

                epics_do_jira = await buscar_epics_do_projeto_jira(session_http, chave_jira_secao)

                if not epics_do_jira:
                    logger.info(f"Nenhum Epic encontrado no Jira para a seção '{chave_jira_secao}'.")
                    continue

                for epic_data_jira in epics_do_jira:
                    fields = epic_data_jira.get("fields", {})
                    epic_key_jira = epic_data_jira.get("key") # Chave do Epic, ex: "SEG-1234"
                    epic_name_jira = fields.get("summary")
                    epic_description_jira = extrair_texto_descricao_jira(fields.get("description"))
                    
                    # Status do Epic no Jira (para lógica de 'ativo')
                    status_obj_epic_jira = fields.get("status", {})
                    nome_status_epic_jira = status_obj_epic_jira.get("name", "").lower()
                    
                    # Lógica para definir se o projeto local (Epic) está ativo
                    # Ajuste esta lista conforme os nomes de status do seu Jira que indicam um Epic "não ativo"
                    epic_nao_ativo = nome_status_epic_jira in ['concluído', 'fechado', 'resolvido', 'cancelado', 'done', 'closed', 'resolved', 'cancelled']
                    projeto_ativo_local = not epic_nao_ativo

                    # Processa data de criação
                    created_str = fields.get("created")
                    if created_str:
                        data_criacao = converter_data_jira(created_str)
                        logger.info(f"Data de criação extraída do Jira para {epic_key_jira}: {data_criacao}")
                    else:
                        logger.warning(f"Campo 'created' não encontrado para {epic_key_jira}, usando data atual")
                        data_criacao = padronizar_datetime(datetime.now())

                    # Extrai datas de início e fim do Epic (customfield_10020 para sprints)
                    data_inicio_prevista = None
                    data_fim_prevista = None
                    
                    # Tenta extrair datas do campo customfield_10020 (sprints)
                    sprint_data = fields.get("customfield_10020", [])
                    if sprint_data and len(sprint_data) > 0:
                        logger.debug(f"Sprint data para {epic_key_jira}: {sprint_data}")
                        sprint_info = sprint_data[0]
                        logger.debug(f"Sprint info para {epic_key_jira}: {sprint_info}")
                        
                        start_date_str = sprint_info.get("startDate")
                        end_date_str = sprint_info.get("endDate")
                        
                        logger.debug(f"Datas encontradas para {epic_key_jira}: startDate={start_date_str}, endDate={end_date_str}")
                        
                        if start_date_str:
                            start_datetime = converter_data_jira(start_date_str)
                            if start_datetime:
                                data_inicio_prevista = start_datetime.date()
                                logger.info(f"Data início extraída para {epic_key_jira}: {data_inicio_prevista}")
                        
                        if end_date_str:
                            end_datetime = converter_data_jira(end_date_str)
                            if end_datetime:
                                data_fim_prevista = end_datetime.date()
                                logger.info(f"Data fim extraída para {epic_key_jira}: {data_fim_prevista}")
                    else:
                        logger.warning(f"Nenhum dado de sprint encontrado para {epic_key_jira}")
                    
                    # Fallback para duedate se não tiver endDate
                    if data_fim_prevista is None:
                        duedate_str = fields.get("duedate")
                        if duedate_str:
                            due_datetime = converter_data_jira(duedate_str)
                            if due_datetime:
                                data_fim_prevista = due_datetime.date()
                                logger.info(f"Data fim extraída de duedate para {epic_key_jira}: {data_fim_prevista}")
                    
                    # Fallback para data de criação se não tiver data de início
                    if data_inicio_prevista is None and data_criacao:
                        data_inicio_prevista = data_criacao.date()
                        logger.info(f"Usando data de criação como fallback para data de início para {epic_key_jira}: {data_inicio_prevista}")
                    
                    # Fallback para data de início + 30 dias se não tiver data de fim
                    if data_fim_prevista is None and data_inicio_prevista is not None:
                        data_fim_prevista = data_inicio_prevista + timedelta(days=30)
                        logger.info(f"Usando data de início + 30 dias como fallback para data de fim para {epic_key_jira}: {data_fim_prevista}")

                    if not epic_key_jira or not epic_name_jira:
                        logger.warning(f"Epic no Jira com dados incompletos (chave ou nome faltando) na seção '{chave_jira_secao}', ID Jira: {epic_data_jira.get('id')}. Pulando.")
                        continue

                    projeto_local_existente = await repo_projeto_local.get_by_jira_project_key(epic_key_jira)
                    now = padronizar_datetime(datetime.now())  # Padroniza também o datetime atual

                    if projeto_local_existente is None:
                        # INSERT novo projeto local (Epic)
                        logger.info(f"Usando data de criação padronizada para {epic_key_jira}: {data_criacao}")

                        dto_create = ProjetoCreateDTO(
                            nome=epic_name_jira,
                            jira_project_key=epic_key_jira,
                            secao_id=secao_id,
                            status_projeto_id=STATUS_NAO_INICIADO_ID,
                            ativo=projeto_ativo_local,
                            descricao=epic_description_jira,
                            codigo_empresa=None,
                            data_inicio_prevista=data_inicio_prevista,
                            data_fim_prevista=data_fim_prevista,
                            data_criacao=data_criacao,
                            data_atualizacao=now
                        )
                        try:
                            await repo_projeto_local.create(dto_create)
                            logger.info(f"Projeto local (Epic {epic_key_jira}) inserido com sucesso para seção '{chave_jira_secao}'.")
                        except Exception as e:
                            logger.error(f"Erro ao inserir projeto local para Epic {epic_key_jira}: {e}")
                    else:
                        # UPDATE projeto local existente (Epic)
                        logger.info(f"Data de atualização padronizada para {epic_key_jira}: {now}")
                        
                        update_data = {
                            "nome": epic_name_jira,
                            "descricao": epic_description_jira,
                            "ativo": projeto_ativo_local,
                            "data_atualizacao": now,
                            "secao_id": secao_id
                        }
                        if data_inicio_prevista:
                            update_data["data_inicio_prevista"] = data_inicio_prevista
                        if data_fim_prevista:
                             update_data["data_fim_prevista"] = data_fim_prevista
                        else:
                            update_data["data_fim_prevista"] = None

                        dto_update = ProjetoUpdateDTO(**{k: v for k, v in update_data.items() if v is not None or k in ["descricao", "data_inicio_prevista", "data_fim_prevista"]})
                        
                        try:
                            await repo_projeto_local.update(projeto_local_existente.id, dto_update)
                            logger.info(f"Projeto local (Epic {epic_key_jira}) atualizado com sucesso.")
                        except Exception as e:
                            logger.error(f"Erro ao atualizar projeto local para Epic {epic_key_jira}: {e}")
            
            await db_session.commit() # Commit ao final do processamento de todas as seções
            logger.info("Sincronização de Epics do Jira para projetos locais concluída.")

if __name__ == "__main__":
    asyncio.run(sincronizar_epics_jira())