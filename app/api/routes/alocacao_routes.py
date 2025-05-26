from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from datetime import datetime
import logging

from app.api.dtos.alocacao_schema import AlocacaoCreate, AlocacaoUpdate, AlocacaoResponse
# Manter a importação para compatibilidade, mas não usar como dependência
from app.core.security import get_current_admin_user
from app.db.session import get_async_db
from app.services.alocacao_service import AlocacaoService
logging.basicConfig(level=logging.INFO)
logging.info("Arquivo alocacao_routes.py foi carregado!")

# Configurar o router para aceitar URLs com e sem barra final
router = APIRouter(
    # Restaurar o prefixo, já que removemos em api_main.py
    prefix="/alocacoes",
    tags=["Alocações"],
    # Autenticação é tratada pelo Keycloak no frontend
    include_in_schema=True,
    # Permitir redirecionamento automático de URLs com barras finais
    redirect_slashes=True
)

# NOTA: A autenticação é tratada pelo Keycloak no frontend
# O backend não precisa verificar autenticação, pois o frontend já garante que apenas usuários autenticados acessem a aplicação
# Ambos os caminhos funcionam: "/backend/v1/alocacoes/" e "/backend/v1/alocacoes/alocacoes/"

@router.post("/", response_model=AlocacaoResponse, status_code=status.HTTP_201_CREATED)
async def create_alocacao(
    alocacao: AlocacaoCreate,
    db: AsyncSession = Depends(get_async_db)
):
    logger = logging.getLogger("app.api.routes.alocacao_routes")
    logger.info("[create_alocacao] Início")
    try:
        service = AlocacaoService(db)
        result = await service.create(alocacao.dict())
        logger.info("[create_alocacao] Sucesso")
        return result
    except ValueError as e:
        logger.warning(f"[create_alocacao] ValueError: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[create_alocacao] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao criar alocação: {str(e)}")

    """
    Cria uma nova alocação de recurso em projeto.
    
    Args:
        alocacao: Dados da alocação a ser criada
        db: Sessão do banco de dados
    
    Returns:
        AlocacaoResponse: Dados da alocação criada
    
    Raises:
        HTTPException: Se houver erro na criação
    """

@router.post("/alocacoes/", response_model=AlocacaoResponse, status_code=status.HTTP_201_CREATED, include_in_schema=False)
async def create_alocacao_duplicated_path(
    alocacao: AlocacaoCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint para lidar com a URL duplicada /alocacoes/alocacoes/"""
    logging.info("Endpoint duplicado /alocacoes/alocacoes/ foi chamado")
    logging.info(f"Dados recebidos: {alocacao.dict()}")
    # Reutilizar a mesma lógica do endpoint principal
    return await create_alocacao(alocacao, db)

@router.get("/", response_model=dict)
async def list_alocacoes(
    recurso_id: Optional[int] = Query(None, gt=0, description="Filtrar por ID do recurso"),
    projeto_id: Optional[int] = Query(None, gt=0, description="Filtrar por ID do projeto"),
    data_inicio: Optional[str] = Query(None, description="Filtrar por data inicial do período (formatos: YYYY-MM-DD ou DD/MM/YYYY)"),
    data_fim: Optional[str] = Query(None, description="Filtrar por data final do período (formatos: YYYY-MM-DD ou DD/MM/YYYY)"),
    db: AsyncSession = Depends(get_async_db)
):
    logger = logging.getLogger("app.api.routes.alocacao_routes")
    logger.info(f"[list_alocacoes] Início - filtros: recurso_id={recurso_id}, projeto_id={projeto_id}, data_inicio={data_inicio}, data_fim={data_fim}")
    try:
        service = AlocacaoService(db)
        result = await service.list(
            recurso_id=recurso_id,
            projeto_id=projeto_id,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        logger.info(f"[list_alocacoes] Sucesso - {len(result)} alocações encontradas")
        return {"items": result}
    except ValueError as e:
        logger.warning(f"[list_alocacoes] ValueError: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"[list_alocacoes] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao listar alocações: {str(e)}")

    """
    Lista alocações com opção de filtros.
    
    Args:
        recurso_id: Filtrar por ID do recurso
        projeto_id: Filtrar por ID do projeto
        data_inicio: Filtrar por data inicial do período (formatos: YYYY-MM-DD ou DD/MM/YYYY)
        data_fim: Filtrar por data final do período (formatos: YYYY-MM-DD ou DD/MM/YYYY)
        db: Sessão do banco de dados
    
    Returns:
        List[AlocacaoResponse]: Lista de alocações
    """
    service = AlocacaoService(db)
    
    # Converter strings de data para objetos date
    data_inicio_obj = None
    data_fim_obj = None
    
    def parse_date(date_str):
        """Tenta converter uma string de data em vários formatos."""
        if not date_str:
            return None
            
        formats = [
            "%Y-%m-%d",  # ISO (YYYY-MM-DD)
            "%d/%m/%Y",  # Brasileiro (DD/MM/YYYY)
            "%d-%m-%Y"   # Alternativo (DD-MM-YYYY)
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
                
        # Se nenhum formato funcionar, lança exceção
        raise ValueError(f"Formato de data inválido: {date_str}. Use YYYY-MM-DD ou DD/MM/YYYY.")
    
    # Processar data_inicio
    if data_inicio:
        try:
            data_inicio_obj = parse_date(data_inicio)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    
    # Processar data_fim
    if data_fim:
        try:
            data_fim_obj = parse_date(data_fim)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
    
    if recurso_id:
        return await service.list_by_recurso(recurso_id)
    elif projeto_id:
        return await service.list_by_projeto(projeto_id)
    elif data_inicio_obj or data_fim_obj:
        return await service.list_by_periodo(data_inicio_obj, data_fim_obj)
    else:
        return await service.list_all()

@router.get("/alocacoes/", response_model=dict, include_in_schema=False)
async def list_alocacoes_duplicated_path(
    recurso_id: Optional[int] = Query(None, gt=0, description="Filtrar por ID do recurso"),
    projeto_id: Optional[int] = Query(None, gt=0, description="Filtrar por ID do projeto"),
    data_inicio: Optional[str] = Query(None, description="Filtrar por data inicial do período (formatos: YYYY-MM-DD ou DD/MM/YYYY)"),
    data_fim: Optional[str] = Query(None, description="Filtrar por data final do período (formatos: YYYY-MM-DD ou DD/MM/YYYY)"),
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint para lidar com a URL duplicada /alocacoes/alocacoes/"""
    logging.info("Endpoint duplicado /alocacoes/alocacoes/ foi chamado")
    logging.info(f"Dados recebidos: recurso_id={recurso_id}, projeto_id={projeto_id}, data_inicio={data_inicio}, data_fim={data_fim}")
    # Reutilizar a mesma lógica do endpoint principal
    from datetime import datetime, date
    def parse_date_field(v):
        if v is None:
            return v
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            try:
                return datetime.fromisoformat(v.replace('Z', '+00:00')).date()
            except Exception:
                pass
            try:
                return datetime.strptime(v, "%d/%m/%Y").date()
            except Exception:
                pass
        return v
    data_inicio_conv = parse_date_field(data_inicio)
    data_fim_conv = parse_date_field(data_fim)
    return await list_alocacoes(recurso_id, projeto_id, data_inicio_conv, data_fim_conv, db)

@router.get("/{alocacao_id}", response_model=AlocacaoResponse)
async def get_alocacao(
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtém uma alocação pelo ID.
    
    Args:
        alocacao_id: ID da alocação
        db: Sessão do banco de dados
    
    Returns:
        AlocacaoResponse: Dados da alocação
    
    Raises:
        HTTPException: Se a alocação não for encontrada
    """
    try:
        service = AlocacaoService(db)
        alocacao = await service.get(alocacao_id)
        
        if not alocacao:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alocação com ID {alocacao_id} não encontrada"
            )
        
        return alocacao
    except ValueError as e:
        # Tratamento específico para erros de validação
        logging.error(f"Erro de validação ao buscar alocação {alocacao_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SQLAlchemyError as e:
        # Tratamento para erros de banco de dados
        logging.error(f"Erro de banco de dados ao buscar alocação {alocacao_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar alocação: {str(e)}"
        )
    except Exception as e:
        # Tratamento para outros erros não previstos
        logging.error(f"Erro inesperado ao buscar alocação {alocacao_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao processar a solicitação"
        )

@router.get("/alocacoes/{alocacao_id}", response_model=AlocacaoResponse, include_in_schema=False)
async def get_alocacao_duplicated_path(
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint para lidar com a URL duplicada /alocacoes/alocacoes/"""
    logging.info("Endpoint duplicado /alocacoes/alocacoes/ foi chamado")
    logging.info(f"Dados recebidos: alocacao_id={alocacao_id}")
    # Reutilizar a mesma lógica do endpoint principal
    return await get_alocacao(alocacao_id, db)

@router.put("/{alocacao_id}", response_model=AlocacaoResponse)
async def update_alocacao(
    alocacao_update: AlocacaoUpdate,
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Atualiza uma alocação existente.
    
    Args:
        alocacao_update: Dados para atualização
        alocacao_id: ID da alocação
        db: Sessão do banco de dados
    
    Returns:
        AlocacaoResponse: Dados da alocação atualizada
    
    Raises:
        HTTPException: Se a alocação não for encontrada ou houver erro na atualização
    """
    try:
        service = AlocacaoService(db)
        
        # Verificar se a alocação existe
        alocacao = await service.get(alocacao_id)
        if not alocacao:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alocação com ID {alocacao_id} não encontrada"
            )
        
        # Atualizar apenas os campos não nulos
        update_data = {k: v for k, v in alocacao_update.dict().items() if v is not None}
        
        # Se não há dados para atualizar, retornar a alocação atual
        if not update_data:
            return alocacao
        
        # Atualizar a alocação
        return await service.update(alocacao_id, update_data)
    
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.put("/alocacoes/{alocacao_id}", response_model=AlocacaoResponse, include_in_schema=False)
async def update_alocacao_duplicated_path(
    alocacao_update: AlocacaoUpdate,
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint para lidar com a URL duplicada /alocacoes/alocacoes/"""
    logging.info("Endpoint duplicado /alocacoes/alocacoes/ foi chamado")
    logging.info(f"Dados recebidos: alocacao_update={alocacao_update.dict()}, alocacao_id={alocacao_id}")
    # Reutilizar a mesma lógica do endpoint principal
    return await update_alocacao(alocacao_update, alocacao_id, db)

@router.delete("/{alocacao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alocacao(
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Remove uma alocação.
    
    Args:
        alocacao_id: ID da alocação
        db: Sessão do banco de dados
    
    Raises:
        HTTPException: Se a alocação não for encontrada ou houver erro na remoção
    """
    try:
        service = AlocacaoService(db)
        
        # Verificar se a alocação existe
        alocacao = await service.get(alocacao_id)
        if not alocacao:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alocação com ID {alocacao_id} não encontrada"
            )
        
        # Remover a alocação
        await service.delete(alocacao_id)
        
    except ValueError as e:
        # Tratamento específico para erros de validação
        logging.error(f"Erro de validação ao excluir alocação {alocacao_id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SQLAlchemyError as e:
        # Tratamento para erros de banco de dados
        logging.error(f"Erro de banco de dados ao excluir alocação {alocacao_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir alocação: {str(e)}"
        )
    except Exception as e:
        # Tratamento para outros erros não previstos
        logging.error(f"Erro inesperado ao excluir alocação {alocacao_id}: {str(e)}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno do servidor ao processar a solicitação"
        )

@router.delete("/alocacoes/{alocacao_id}", status_code=status.HTTP_204_NO_CONTENT, include_in_schema=False)
async def delete_alocacao_duplicated_path(
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    db: AsyncSession = Depends(get_async_db)
):
    """Endpoint para lidar com a URL duplicada /alocacoes/alocacoes/"""
    logging.info("Endpoint duplicado /alocacoes/alocacoes/ foi chamado")
    logging.info(f"Dados recebidos: alocacao_id={alocacao_id}")
    # Reutilizar a mesma lógica do endpoint principal
    return await delete_alocacao(alocacao_id, db)