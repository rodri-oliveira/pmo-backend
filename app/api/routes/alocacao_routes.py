from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dtos.alocacao_schema import AlocacaoCreate, AlocacaoUpdate, AlocacaoResponse
from app.core.security import get_current_admin_user
from app.db.session import get_async_db
from app.services.alocacao_service import AlocacaoService

# Configurar o router para aceitar URLs com e sem barra final
router = APIRouter(
    prefix="/alocacoes",
    tags=["Alocações"],
    dependencies=[Depends(get_current_admin_user)],
    include_in_schema=True,
    redirect_slashes=False  # Desabilitar redirecionamento automático de URLs
)

@router.post("/", response_model=AlocacaoResponse, status_code=status.HTTP_201_CREATED)
async def create_alocacao(
    alocacao: AlocacaoCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Cria uma nova alocação de recurso em projeto.
    
    Args:
        alocacao: Dados da alocação a ser criada
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        AlocacaoResponse: Dados da alocação criada
    
    Raises:
        HTTPException: Se houver erro na criação
    """
    try:
        service = AlocacaoService(db)
        result = await service.create(alocacao.dict())
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get("/", response_model=List[AlocacaoResponse])
async def list_alocacoes(
    recurso_id: Optional[int] = Query(None, gt=0, description="Filtrar por ID do recurso"),
    projeto_id: Optional[int] = Query(None, gt=0, description="Filtrar por ID do projeto"),
    data_inicio: Optional[date] = Query(None, description="Filtrar por data inicial do período"),
    data_fim: Optional[date] = Query(None, description="Filtrar por data final do período"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Lista alocações com opção de filtros.
    
    Args:
        recurso_id: Filtrar por ID do recurso
        projeto_id: Filtrar por ID do projeto
        data_inicio: Filtrar por data inicial do período
        data_fim: Filtrar por data final do período
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        List[AlocacaoResponse]: Lista de alocações
    """
    service = AlocacaoService(db)
    
    # Aplicar filtros conforme parâmetros
    if recurso_id:
        return await service.list_by_recurso(recurso_id)
    elif projeto_id:
        return await service.list_by_projeto(projeto_id)
    elif data_inicio or data_fim:
        return await service.list_by_periodo(data_inicio, data_fim)
    else:
        return await service.list_all()

@router.get("/{alocacao_id}", response_model=AlocacaoResponse)
async def get_alocacao(
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Obtém uma alocação pelo ID.
    
    Args:
        alocacao_id: ID da alocação
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
    Returns:
        AlocacaoResponse: Dados da alocação
    
    Raises:
        HTTPException: Se a alocação não for encontrada
    """
    service = AlocacaoService(db)
    alocacao = await service.get(alocacao_id)
    
    if not alocacao:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alocação com ID {alocacao_id} não encontrada"
        )
    
    return alocacao

@router.put("/{alocacao_id}", response_model=AlocacaoResponse)
async def update_alocacao(
    alocacao_update: AlocacaoUpdate,
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Atualiza uma alocação existente.
    
    Args:
        alocacao_update: Dados para atualização
        alocacao_id: ID da alocação
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
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

@router.delete("/{alocacao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alocacao(
    alocacao_id: int = Path(..., gt=0, description="ID da alocação"),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    """
    Remove uma alocação.
    
    Args:
        alocacao_id: ID da alocação
        db: Sessão do banco de dados
        current_user: Usuário administrador autenticado
    
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
