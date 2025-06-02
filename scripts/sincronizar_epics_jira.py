import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import asyncio
from datetime import datetime
import aiohttp
from app.db.session import AsyncSessionLocal
# Assumindo que SQLAlchemyProjetoRepository interage com sua tabela 'projeto' local
from app.infrastructure.repositories.sqlalchemy_projeto_repository import SQLAlchemyProjetoRepository
from app.application.dtos.projeto_dtos import ProjetoCreateDTO, ProjetoUpdateDTO # Seus DTOs
import logging
from sqlalchemy import select
from app.db.orm_models import Secao # Seu modelo ORM para a tabela 'secao'

# Configuração básica de logging
logging.basicConfig(level=logging.INFO)
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
            "fields": "summary,key,description,project,status,duedate,customfield_XXXXX", # Adicione IDs de custom fields de datas se souber
            "startAt": start_at,
            "maxResults": MAX_RESULTS_PER_PAGE
        }
        logger.info(f"Buscando Epics para seção Jira '{chave_jira_secao}' (página começando em: {start_at})...")
        async with session_http.get(JIRA_API_SEARCH_URL, headers=JIRA_AUTH_HEADER, params=params) as resp:
            if resp.status != 200:
                logger.error(f"Erro ao buscar Epics da seção Jira '{chave_jira_secao}': {resp.status} - {await resp.text()}")
                break  # Sai do loop de paginação em caso de erro

            data = await resp.json()
            issues_na_pagina = data.get("issues", [])
            if not issues_na_pagina:
                logger.info(f"Nenhum Epic a mais encontrado para '{chave_jira_secao}' nesta página.")
                break # Fim da paginação

            all_epics.extend(issues_na_pagina)
            
            total_issues_jira = data.get("total", 0)
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

                    # Datas previstas (exemplo usando 'duedate' para data fim)
                    # Se você tiver campos customizados para data de início, precisará dos IDs deles
                    data_fim_prevista_epic = fields.get("duedate") # Formato 'AAAA-MM-DD'
                    data_inicio_prevista_epic = fields.get("startDate")  # Extrai startDate do JSON para data_inicio_prevista

                    if not epic_key_jira or not epic_name_jira:
                        logger.warning(f"Epic no Jira com dados incompletos (chave ou nome faltando) na seção '{chave_jira_secao}', ID Jira: {epic_data_jira.get('id')}. Pulando.")
                        continue

                    projeto_local_existente = await repo_projeto_local.get_by_jira_project_key(epic_key_jira)
                    now = datetime.now()

                    if projeto_local_existente is None:
                        # INSERT novo projeto local (Epic)
                        created_str = fields.get("created")
                        if created_str:
                            try:
                                data_criacao = datetime.fromisoformat(created_str.replace('Z', '+00:00'))
                            except Exception:
                                data_criacao = now
                        else:
                            data_criacao = now

                        dto_create = ProjetoCreateDTO(
                            nome=epic_name_jira,
                            jira_project_key=epic_key_jira,
                            secao_id=secao_id,  # Preenche corretamente com o id da secao
                            status_projeto_id=STATUS_NAO_INICIADO_ID,
                            ativo=projeto_ativo_local,
                            descricao=epic_description_jira,
                            codigo_empresa=None,
                            data_inicio_prevista=data_inicio_prevista_epic,
                            data_fim_prevista=data_fim_prevista_epic,
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
                        # Defina quais campos devem ser atualizados a partir do Jira
                        update_data = {
                            "nome": epic_name_jira,
                            "descricao": epic_description_jira,
                            "ativo": projeto_ativo_local,
                            "data_atualizacao": now,
                            "secao_id": secao_id  # Preenche corretamente com o id da secao
                            # Considere atualizar status_projeto_id se houver mapeamento do status do Epic Jira
                            # Considere atualizar data_inicio_prevista e data_fim_prevista
                        }
                        if data_inicio_prevista_epic:
                            update_data["data_inicio_prevista"] = data_inicio_prevista_epic
                        if data_fim_prevista_epic: # Se duedate for None, não tentará atualizar para None se o DTO não permitir
                             update_data["data_fim_prevista"] = data_fim_prevista_epic
                        else: # Se duedate for None e você quiser limpar a data_fim_prevista
                            update_data["data_fim_prevista"] = None


                        # Crie o DTO de update com os campos que podem ser None
                        # Certifique-se que seu ProjetoUpdateDTO lida com campos opcionais (None)
                        dto_update = ProjetoUpdateDTO(**{k: v for k, v in update_data.items() if v is not None or k in ["descricao", "data_inicio_prevista", "data_fim_prevista"]}) # Permite None para certos campos
                        
                        try:
                            await repo_projeto_local.update(projeto_local_existente.id, dto_update)
                            logger.info(f"Projeto local (Epic {epic_key_jira}) atualizado com sucesso.")
                        except Exception as e:
                            logger.error(f"Erro ao atualizar projeto local para Epic {epic_key_jira}: {e}")
            
            await db_session.commit() # Commit ao final do processamento de todas as seções
            logger.info("Sincronização de Epics do Jira para projetos locais concluída.")

if __name__ == "__main__":
    asyncio.run(sincronizar_epics_jira())