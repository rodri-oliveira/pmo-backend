import logging
logging.basicConfig(level=logging.INFO)
logging.info("[SINCRONIZACOES_JIRA] Arquivo sincronizacoes_jira.py foi carregado!")
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query, Path
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from pydantic import BaseModel
import uuid
import asyncio

from app.core.security import get_current_admin_user
from app.db.session import get_db, get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.usuario import UsuarioInDB
from app.services.sincronizacao_jira_service import SincronizacaoJiraService
from app.services.log_service import LogService
from app.integrations.jira_client import JiraClient
from app.schemas.sincronizacao_schemas import SincronizacaoJiraRequest, SincronizacaoJiraResponse

# Configurar logger específico para este módulo
logger = logging.getLogger(__name__)

# 🔥 SISTEMA DE STATUS EM MEMÓRIA PARA SINCRONIZAÇÕES
sync_status_store: Dict[str, Dict[str, Any]] = {}

def create_sync_status(sync_id: str, total_projects: int = 4) -> None:
    """Cria um novo status de sincronização"""
    sync_status_store[sync_id] = {
        "status": "running",
        "processed_count": 0,
        "total_count": total_projects,
        "message": "Iniciando sincronização...",
        "error": None,
        "start_time": datetime.now().isoformat(),
        "end_time": None
    }
    logger.info(f"[SYNC_STATUS] Criado status para sync_id: {sync_id}")

def update_sync_status(sync_id: str, **kwargs) -> None:
    """Atualiza o status de uma sincronização"""
    if sync_id in sync_status_store:
        sync_status_store[sync_id].update(kwargs)
        logger.info(f"[SYNC_STATUS] Atualizado sync_id {sync_id}: {kwargs}")
    else:
        logger.warning(f"[SYNC_STATUS] Tentativa de atualizar sync_id inexistente: {sync_id}")

def get_sync_status(sync_id: str) -> Dict[str, Any]:
    """Obtém o status de uma sincronização"""
    try:
        logger.info(f"[STATUS_CONSULTA] Buscando status para sync_id: {sync_id}")
        
        if sync_id not in sync_status_store:
            logger.warning(f"[STATUS_NOT_FOUND] sync_id não encontrado: {sync_id}")
            return {
                "status": "not_found",
                "processed_count": 0,
                "total_count": 0,
                "message": "Sincronização não encontrada",
                "error": None
            }
        
        result = sync_status_store[sync_id]
        logger.info(f"[STATUS_RESULT] Status encontrado: {result}")
        return result
        
    except Exception as e:
        logger.error(f"[STATUS_ERROR] Erro ao buscar status {sync_id}: {str(e)}")
        return {
            "status": "error",
            "processed_count": 0,
            "total_count": 0,
            "message": "Erro interno ao consultar status",
            "error": str(e)
        }

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

@router.post("/sincronizar-periodo", response_model=SincronizacaoJiraResponse)
async def sincronizar_periodo_jira(
    request: SincronizacaoJiraRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Sincroniza worklogs do Jira para um período específico.
    
    - **data_inicio**: Data de início da sincronização (YYYY-MM-DD)
    - **data_fim**: Data de fim da sincronização (YYYY-MM-DD)  
    - **projetos**: Lista de projetos Jira (opcional, padrão: DTIN, SGI, TIN, SEG)
    
    **Protegido**: requer autenticação de admin.
    
    **Retorno**: Estatísticas detalhadas da sincronização.
    
    **Exemplo de uso:**
    ```json
    {
        "data_inicio": "2024-07-01",
        "data_fim": "2024-07-24",
        "projetos": ["DTIN", "SGI"]
    }
    ```
    """
    try:
        logger.info(f"[SYNC_ENDPOINT] Usuário {current_user.email} iniciou sincronização: {request.data_inicio} até {request.data_fim}")
        
        # Converter dates para datetime
        data_inicio = datetime.combine(request.data_inicio, datetime.min.time())
        data_fim = datetime.combine(request.data_fim, datetime.max.time())
        
        # Criar service de sincronização
        sync_service = SincronizacaoJiraCorrigidaService(db)
        
        # Executar sincronização
        resultado = await sync_service.sincronizar_periodo(
            data_inicio=data_inicio,
            data_fim=data_fim,
            projetos=request.projetos
        )
        
        # Log do resultado
        if resultado["status"] == "success":
            logger.info(f"[SYNC_SUCCESS] Sincronização concluída: {resultado['resultados']}")
        else:
            logger.error(f"[SYNC_ERROR] Erro na sincronização: {resultado.get('erro')}")
        
        return SincronizacaoJiraResponse(**resultado)
        
    except Exception as e:
        logger.error(f"[SYNC_ENDPOINT_ERROR] Erro no endpoint de sincronização: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno na sincronização: {str(e)}"
        )


@router.post("/sincronizar-mes-ano", response_model=Dict[str, Any])
async def sincronizar_mes_ano_jira(
    mes_inicio: int = Query(..., ge=1, le=12, description="Mês de início (1-12)"),
    ano_inicio: int = Query(..., ge=2020, le=2030, description="Ano de início"),
    mes_fim: int = Query(..., ge=1, le=12, description="Mês de fim (1-12)"),
    ano_fim: int = Query(..., ge=2020, le=2030, description="Ano de fim"),
    projetos: Optional[List[str]] = Query(None, description="Lista de projetos Jira (ex: DTIN,SGI,TIN,SEG)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_async_db),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """
    Sincroniza worklogs do Jira por período de mês/ano.
    
    - **mes_inicio**: Mês de início (1-12)
    - **ano_inicio**: Ano de início
    - **mes_fim**: Mês de fim (1-12)  
    - **ano_fim**: Ano de fim
    - **projetos**: Lista de projetos Jira (opcional, padrão: DTIN, SGI, TIN, SEG)
    
    **Protegido**: requer autenticação de admin.
    
    **Exemplo de uso:**
    ```
    POST /backend/sincronizacoes-jira/sincronizar-mes-ano?mes_inicio=1&ano_inicio=2025&mes_fim=7&ano_fim=2025&projetos=DTIN&projetos=SGI
    ```
    """
    try:
        from calendar import monthrange
        
        logger.info(f"[SYNC_MES_ANO] Usuário {current_user.email} iniciou sincronização: {mes_inicio}/{ano_inicio} até {mes_fim}/{ano_fim}")
        
        # Converter mês/ano para datas
        data_inicio = datetime(ano_inicio, mes_inicio, 1)
        
        # Último dia do mês de fim
        ultimo_dia = monthrange(ano_fim, mes_fim)[1]
        data_fim = datetime(ano_fim, mes_fim, ultimo_dia, 23, 59, 59)
        
        # Usar projetos padrão se não especificados
        if not projetos:
            projetos = ["DTIN", "SGI", "TIN", "SEG"]
        
        # 🔥 GERAR SYNC_ID ÚNICO
        sync_id = str(uuid.uuid4())
        
        # 🔥 CRIAR STATUS INICIAL
        create_sync_status(sync_id, total_projects=len(projetos))
        
        # 🔥 EXECUTAR SINCRONIZAÇÃO DIRETAMENTE COM O SCRIPT QUE FUNCIONA
        async def executar_sync_mes_ano():
            try:
                logger.info(f"[SYNC_SCRIPT] Iniciando sincronização {sync_id} com script que funciona...")
                
                # Atualizar status: processando
                update_sync_status(sync_id, 
                    message=f"Processando sincronização para {len(projetos)} projetos...",
                    status="running"
                )
                
                # Importar o script que funciona
                import sys
                import os
                sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'scripts'))
                
                from scripts.sincronizacao_jira_funcional import SincronizacaoJiraFuncional
                from app.db.session import AsyncSessionLocal
                
                # Usar sessão do banco
                async with AsyncSessionLocal() as session:
                    sync_service = SincronizacaoJiraFuncional(session)
                    
                    # Executar processamento do período
                    await sync_service.processar_periodo(data_inicio, data_fim)
                    
                    # Atualizar status: concluído
                    apontamentos_criados = sync_service.stats.get('apontamentos_criados', 0)
                    update_sync_status(sync_id,
                        status="completed",
                        processed_count=len(projetos),
                        message=f"Sincronização concluída! {apontamentos_criados} apontamentos criados.",
                        end_time=datetime.now().isoformat()
                    )
                    
                    logger.info(f"[SYNC_SCRIPT_SUCCESS] Concluída {sync_id}: {apontamentos_criados} apontamentos criados")
                
            except Exception as e:
                logger.error(f"[SYNC_SCRIPT_ERROR] Erro {sync_id}: {str(e)}")
                # Atualizar status: erro
                update_sync_status(sync_id,
                    status="error",
                    message=f"Erro durante sincronização: {str(e)}",
                    error=str(e),
                    end_time=datetime.now().isoformat()
                )
        
        # Executar em background
        background_tasks.add_task(executar_sync_mes_ano)
        
        # Log simples
        logger.info(f"[SYNC_ENDPOINT] Sincronização {mes_inicio}/{ano_inicio} até {mes_fim}/{ano_fim} agendada")
        
        return {
            "status": "success",
            "sync_id": sync_id,
            "status_url": f"/backend/sincronizacoes-jira/sincronizar-status/{sync_id}",
            "mensagem": f"Sincronização de {mes_inicio}/{ano_inicio} até {mes_fim}/{ano_fim} iniciada com sucesso",
            "periodo": {
                "data_inicio": data_inicio.isoformat(),
                "data_fim": data_fim.isoformat(),
                "projetos": projetos
            }
        }
        
    except Exception as e:
        logger.error(f"[SYNC_MES_ANO_ERROR] Erro no endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao iniciar sincronização: {str(e)}"
        )

@router.get("/sincronizar-status/{sync_id}", response_model=Dict[str, Any])
async def obter_status_sincronizacao(
    sync_id: str = Path(..., description="ID da sincronização"),
    current_user: UsuarioInDB = Depends(get_current_admin_user)
):
    """Retorna o status atual da sincronização"""
    return get_sync_status(sync_id)

# -- fim do arquivo --