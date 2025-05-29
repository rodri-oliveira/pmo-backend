import logging
logging.basicConfig(level=logging.INFO)
logging.info("[SINCRONIZACOES_JIRA] Arquivo sincronizacoes_jira.py foi carregado!")
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Path
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.core.security import get_current_admin_user
from app.db.session import get_db, get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.usuario import UsuarioInDB
from app.services.sincronizacao_jira_service import SincronizacaoJiraService
from app.services.log_service import LogService
from app.integrations.jira_client import JiraClient

router = APIRouter(tags=["Integração Jira"])

class SincronizacaoJiraOut(BaseModel):
    id: int
    data_inicio: str
    data_fim: str
    status: str
    mensagem: Optional[str] = None
    quantidade_apontamentos_processados: Optional[int] = None

from fastapi.responses import JSONResponse

@router.get("/config", response_model=Dict[str, Any])
async def verificar_config_jira(
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Verifica as configurações do Jira sem fazer requisições para a API.
    
    - **Protegido**: requer autenticação de admin.
    - **Retorno**: configurações do Jira.
    """
    from app.core.config import settings
    
    # Verificar se as configurações do Jira estão definidas
    jira_config = {
        "base_url": settings.JIRA_BASE_URL,
        "username": settings.JIRA_USERNAME,
        "api_token_length": len(settings.JIRA_API_TOKEN) if settings.JIRA_API_TOKEN else 0,
        "api_token_preview": f"***{settings.JIRA_API_TOKEN[-5:]}" if settings.JIRA_API_TOKEN and len(settings.JIRA_API_TOKEN) > 5 else "***"
    }
    
    return {
        "status": "success",
        "config": jira_config
    }

@router.get("/testar-curl", response_model=Dict[str, Any])
async def testar_curl_jira(
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Testa a conexão com o Jira usando as credenciais exatas do curl.
    
    - **Protegido**: requer autenticação de admin.
    - **Retorno**: resultado do teste de conexão.
    """
    import requests
    import json
    import logging
    
    logger = logging.getLogger("sincronizacoes_jira.testar_curl")
    
    try:
        # URL e headers exatamente como no curl
        url = 'https://jiracloudweg.atlassian.net/rest/api/3/project/search'
        headers = {
            'Authorization': 'Basic cm9saXZlaXJhQHdlZy5uZXQ6QVRBVFQzeEZmR0YwZG0xUzdSSHNReGFSTDZkNmZiaEZUMFNxSjZLbE9ScWRXQzg1M1Jlb3hFMUpnM0dSeXRUVTN4dG5McjdGVWg3WWFKZ2M1RDZwd3J5bjhQc3lHVDNrSklyRUlyVHpmNF9lMGJYLUdJdmxOOFIxanhyMV9GVGhLY1h3V1N0dU9VbE5ucEY2eFlhclhfWFpRb3RhTzlXeFhVaXlIWkdHTDFaMEx5cmJ4VzVyNVYwPUYxMDA3MDNF',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        logger.info(f"[JIRA_CURL_TEST] Fazendo requisição para {url} com header de autorização do curl")
        
        # Fazer a requisição usando requests
        response = requests.get(url, headers=headers)
        
        # Verificar se a resposta foi bem-sucedida
        if response.status_code == 200:
            # Tentar converter a resposta para JSON
            try:
                jira_data = response.json()
                total_projetos = jira_data.get('total', 0)
                
                return {
                    "status": "success",
                    "mensagem": f"Conexão bem-sucedida! Total de projetos: {total_projetos}",
                    "detalhes": {
                        "total_projetos": total_projetos,
                        "primeiro_projeto": jira_data.get('values', [])[0] if jira_data.get('values') else None
                    }
                }
            except json.JSONDecodeError as e:
                logger.error(f"[JIRA_CURL_TEST] Erro ao decodificar JSON: {str(e)}")
                return {
                    "status": "error",
                    "mensagem": f"Erro ao decodificar resposta JSON: {str(e)}",
                    "detalhes": {
                        "response_text": response.text[:500]  # Limitar para não sobrecarregar a resposta
                    }
                }
        else:
            logger.error(f"[JIRA_CURL_TEST] Erro na requisição: {response.status_code} - {response.text}")
            return {
                "status": "error",
                "mensagem": f"Erro na requisição: {response.status_code}",
                "detalhes": {
                    "status_code": response.status_code,
                    "response_text": response.text[:500]  # Limitar para não sobrecarregar a resposta
                }
            }
    except Exception as e:
        logger.error(f"[JIRA_CURL_TEST] Erro ao testar conexão: {str(e)}")
        return {
            "status": "error",
            "mensagem": f"Erro ao testar conexão: {str(e)}",
            "detalhes": {}
        }

@router.get("/testar-conexao", response_model=Dict[str, Any])
async def testar_conexao_jira(
    db: AsyncSession = Depends(get_async_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Testa a conexão com o Jira.
    
    - **Protegido**: requer autenticação de admin.
    - **Retorno**: resultado do teste de conexão.
    """
    from app.services.sincronizacao_jira_service import SincronizacaoJiraService
    
    service = SincronizacaoJiraService(db)
    
    try:
        resultado = await service.testar_conexao_jira()
        return resultado
    except Exception as e:
        logger.error(f"[JIRA_TESTE_CONEXAO_ERRO] {str(e)}")
        return {
            "status": "error",
            "mensagem": f"Erro ao testar conexão com o Jira: {str(e)}",
            "detalhes": {}
        }

@router.get("/", response_model=Dict[str, Any])
async def listar_sincronizacoes(
    skip: int = Query(0, description="Número de registros a pular para paginação"),
    limit: int = Query(50, description="Número máximo de registros a retornar"),
    status: Optional[str] = Query(None, description="Filtrar por status (RECEBIDO, SUCESSO, ERRO)"),
    tipo_evento: Optional[str] = Query(None, description="Filtrar por tipo de evento (worklog_created, worklog_updated, worklog_deleted)"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Lista o histórico de sincronizações com o Jira (paginado).
    
    - **skip**: Quantidade de registros a pular
    - **limit**: Quantidade máxima de registros
    - **status**: Filtrar por status específico
    - **tipo_evento**: Filtrar por tipo de evento específico
    
    Retorna um objeto com items, total, skip e limit.
    """
    sincronizacao_service = SincronizacaoJiraService(db)
    result = await sincronizacao_service.listar_sincronizacoes(
        skip=skip,
        limit=limit,
        status=status,
        tipo_evento=tipo_evento
    )
    return JSONResponse(content=result)


@router.get("/{id}", response_model=SincronizacaoJiraOut)
async def obter_sincronizacao(
    id: int = Path(..., description="ID da sincronização"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Obtém detalhes de uma sincronização específica.
    
    - **id**: ID da sincronização
    
    Retorna os detalhes da sincronização.
    """
    sincronizacao_service = SincronizacaoJiraService(db)
    sincronizacao = await sincronizacao_service.obter_sincronizacao(id)
    
    if not sincronizacao:
        raise HTTPException(status_code=404, detail="Sincronização não encontrada")
        
    return sincronizacao


async def executar_sincronizacao_background(db: Session, dias: int, usuario_id: int):
    """
    Executa a sincronização em segundo plano.
    
    Args:
        db: Sessão do banco de dados
        dias: Número de dias para sincronizar
        usuario_id: ID do usuário que solicitou a sincronização
    """
    import logging
    import asyncio
    from datetime import datetime, timedelta
    from app.services.sincronizacao_jira_service import SincronizacaoJiraService
    from app.services.apontamento_service import ApontamentoService
    from app.integrations.jira_client import JiraClient
    
    logger = logging.getLogger("sincronizacoes_jira.executar_sincronizacao_background")
    
    # Criar uma nova sessão assíncrona para o background task
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.session import async_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.ext.asyncio import AsyncSession
    
    async_session = sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    
    async with async_session() as session:
        try:
            logger.info(f"[SINCRONIZACAO_BACKGROUND] Iniciando sincronização de {dias} dias")
            
            # Serviços
            sincronizacao_service = SincronizacaoJiraService(session)
            apontamento_service = ApontamentoHoraService(session)
            
            # Cliente Jira
            jira_client = JiraClient()
            
            # Data de início (dias atrás)
            since_date = datetime.now() - timedelta(days=dias)
            
            # Buscar worklogs recentes
            logger.info(f"[SINCRONIZACAO_BACKGROUND] Buscando worklogs desde {since_date.isoformat()}")
            worklogs = jira_client.get_recent_worklogs(dias=dias)
            
            # Processar worklogs
            logger.info(f"[SINCRONIZACAO_BACKGROUND] Processando {len(worklogs)} worklogs")
            
            # Contador de apontamentos processados
            contador = 0
            
            for worklog in worklogs:
                try:
                    # Processar cada worklog
                    await apontamento_service.processar_worklog_jira(worklog)
                    contador += 1
                except Exception as e:
                    logger.error(f"[SINCRONIZACAO_BACKGROUND] Erro ao processar worklog: {str(e)}")
            
            # Atualizar sincronização com sucesso
            await sincronizacao_service.registrar_fim_sincronizacao(
                status="SUCESSO",
                mensagem=f"Sincronização concluída com sucesso. {contador} apontamentos processados.",
                quantidade_apontamentos_processados=contador
            )
            
            logger.info(f"[SINCRONIZACAO_BACKGROUND] Sincronização concluída com sucesso. {contador} apontamentos processados.")
            
        except Exception as e:
            logger.error(f"[SINCRONIZACAO_BACKGROUND] Erro na sincronização: {str(e)}")
            
            # Atualizar sincronização com erro
            await sincronizacao_service.registrar_fim_sincronizacao(
                status="ERRO",
                mensagem=f"Erro na sincronização: {str(e)}"
            )


async def executar_sincronizacao_mes_anterior_background(db: Session, usuario_id: Optional[int], sincronizacao_id: int):
    """
    Executa a sincronização dos worklogs do mês anterior em segundo plano.
    
    Args:
        db: Sessão do banco de dados
        usuario_id: ID do usuário que solicitou a sincronização
        sincronizacao_id: ID da sincronização registrada
    """
    import logging
    import asyncio
    from datetime import datetime
    from app.services.sincronizacao_jira_service import SincronizacaoJiraService
    from app.services.apontamento_hora_service import ApontamentoHoraService
    from app.integrations.jira_client import JiraClient
    
    logger = logging.getLogger("sincronizacoes_jira.executar_sincronizacao_mes_anterior_background")
    
    # Criar uma nova sessão assíncrona para o background task
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.db.session import async_engine
    from sqlalchemy.orm import sessionmaker
    
    async_session = sessionmaker(
        async_engine, expire_on_commit=False, class_=AsyncSession
    )
    
    async with async_session() as session:
        try:
            logger.info(f"[SINCRONIZACAO_MES_ANTERIOR] Iniciando sincronização dos worklogs do mês anterior")
            
            # Serviços
            sincronizacao_service = SincronizacaoJiraService(session)
            apontamento_service = ApontamentoHoraService(session)
            
            # Atualizar o ID da sincronização no serviço
            sincronizacao_service.sincronizacao_id = sincronizacao_id
            
            # Cliente Jira
            jira_client = JiraClient()
            
            # Buscar worklogs do mês anterior
            logger.info(f"[SINCRONIZACAO_MES_ANTERIOR] Buscando worklogs do mês anterior")
            worklogs = jira_client.get_previous_month_worklogs()
            
            # Processar worklogs
            logger.info(f"[SINCRONIZACAO_MES_ANTERIOR] Processando {len(worklogs)} worklogs do mês anterior")
            
            # Contador de apontamentos processados
            contador = 0
            
            for worklog in worklogs:
                try:
                    # Processar cada worklog
                    await apontamento_service.processar_worklog_jira(worklog)
                    contador += 1
                except Exception as e:
                    logger.error(f"[SINCRONIZACAO_MES_ANTERIOR] Erro ao processar worklog: {str(e)}")
            
            # Atualizar sincronização com sucesso
            await sincronizacao_service.registrar_fim_sincronizacao(
                status="SUCESSO",
                mensagem=f"Sincronização do mês anterior concluída com sucesso. {contador} apontamentos processados.",
                quantidade_apontamentos_processados=contador
            )
            
            logger.info(f"[SINCRONIZACAO_MES_ANTERIOR] Sincronização concluída com sucesso. {contador} apontamentos processados.")
            
        except Exception as e:
            logger.error(f"[SINCRONIZACAO_MES_ANTERIOR] Erro na sincronização do mês anterior: {str(e)}")
            
            # Atualizar sincronização com erro
            await sincronizacao_service.registrar_fim_sincronizacao(
                status="ERRO",
                mensagem=f"Erro na sincronização do mês anterior: {str(e)}"
            ) 


@router.post("/importar-mes-anterior", response_model=Dict[str, Any])
async def importar_mes_anterior_jira(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Inicia a sincronização dos worklogs do mês anterior ao atual.
    
    - **Protegido**: requer autenticação de admin.
    - **Retorno**: status de processamento da sincronização.
    """
    import logging
    logger = logging.getLogger("sincronizacoes_jira.importar_mes_anterior")
    
    try:
        # Iniciar a sincronização em background
        jira_client = JiraClient()
        
        # Registrar início no log
        logger.info(f"[IMPORTAR_MES_ANTERIOR] Iniciando sincronização dos worklogs do mês anterior")
        
        # Criar registro de sincronização
        from app.db.orm_models import SincronizacaoJira
        from datetime import datetime
        from sqlalchemy import insert
        
        # Criar registro de sincronização
        query = insert(SincronizacaoJira).values(
            data_inicio=datetime.now(),
            data_fim=datetime.now(),  # Será atualizado ao final
            status="PROCESSANDO",
            mensagem="Sincronização dos worklogs do mês anterior iniciada"
            # Removido tipo_evento pois parece não existir na tabela
        ).returning(SincronizacaoJira.id)
        
        result = await db.execute(query)
        sincronizacao_id = result.scalar_one()
        
        # Adicionar a tarefa em background
        background_tasks.add_task(
            executar_sincronizacao_mes_anterior_background,
            db,
            None,  # Não associar a usuário para evitar erro de chave estrangeira
            sincronizacao_id
        )
        
        return {
            "status": "success",
            "mensagem": "Sincronização dos worklogs do mês anterior iniciada com sucesso",
            "sincronizacao_id": sincronizacao_id
        }
    except Exception as e:
        logger.error(f"[IMPORTAR_MES_ANTERIOR_JIRA] Erro ao iniciar sincronização: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar sincronização: {str(e)}"
        )

@router.post("/importar-tudo", response_model=Dict[str, Any])
async def importar_tudo_jira(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Inicia a sincronização completa do Jira (todos os projetos, issues e worklogs).
    - **Protegido**: requer autenticação de admin.
    - **Retorno**: status de processamento da sincronização.
    """
    logger = logging.getLogger("sincronizacoes_jira.importar_tudo")
    logger.info("[INICIO] Chamada ao endpoint /importar-tudo por usuário %s (id=%s)", current_user.username, current_user.id)
    try:
        async def sync_bg(db: AsyncSession):
            logger.info("[BG] Iniciando sincronização total em background")
            try:
                service = SincronizacaoJiraService(db)
                # Não passar o ID do usuário para evitar erro de chave estrangeira
                await service.sincronizar_tudo(usuario_id=None)
                logger.info("[BG] Sincronização total concluída")
            except Exception as e:
                logger.error("[BG] Erro na sincronização total: %s", str(e))
        background_tasks.add_task(sync_bg, db)
        logger.info("[FIM] Sincronização total agendada para usuario_id=%s", current_user.id)
        return {"status": "processing", "message": "Sincronização completa do Jira iniciada."}
    except Exception as exc:
        logger.error("[ERRO] Falha ao agendar sincronização total: %s", str(exc))
        raise HTTPException(status_code=500, detail=f"Erro ao agendar sincronização total: {str(exc)}")
        raise HTTPException(status_code=500, detail="Erro ao agendar sincronização total do Jira.")

@router.post("/importar", response_model=Dict[str, Any])
async def importar_sincronizacao_jira(
    background_tasks: BackgroundTasks,
    dias: int = Query(7, description="Número de dias para sincronizar"),
    db: AsyncSession = Depends(get_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Endpoint compatível com o frontend para iniciar sincronização manual do Jira.
    """
    try:
        # Registrar o início da sincronização
        sincronizacao_service = SincronizacaoJiraService(db)
        
        # Verificar se o usuário existe antes de associar
        from app.repositories.usuario_repository import UsuarioRepository
        usuario_repo = UsuarioRepository(db)
        
        # Tentar obter o usuário pelo ID
        try:
            usuario = await usuario_repo.get(current_user.id)
            usuario_id = current_user.id if usuario else None
        except Exception:
            # Se houver erro, não associar a nenhum usuário
            usuario_id = None
            
        sincronizacao = await sincronizacao_service.registrar_inicio_sincronizacao(
            usuario_id=usuario_id,
            tipo_evento="sincronizacao_manual",
            mensagem=f"Sincronização manual de {dias} dias iniciada"
        )
        
        # Adicionar a tarefa de sincronização em background
        background_tasks.add_task(
            executar_sincronizacao_background,
            db,
            dias,
            current_user.id
        )
        
        # Registrar log de atividade
        log_service = LogService(db)
        await log_service.registrar_log(
            tipo="SINCRONIZACAO_JIRA",
            descricao=f"Sincronização manual de {dias} dias iniciada pelo usuário {current_user.nome}",
            usuario_id=current_user.id
        )
        
        return {
            "status": "success",
            "mensagem": "Sincronização iniciada com sucesso",
            "sincronizacao_id": sincronizacao.id
        }
    except Exception as e:
        # Usar o logger importado no início do arquivo
        logger = logging.getLogger("sincronizacoes_jira")
        logger.error(f"[IMPORTAR_SINCRONIZACAO_JIRA] Erro ao iniciar sincronização: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar sincronização: {str(e)}"
        )

# Endpoint removido para evitar duplicação