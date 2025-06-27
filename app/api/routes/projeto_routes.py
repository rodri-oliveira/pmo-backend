from fastapi import APIRouter, HTTPException, Depends, Query
import logging
from starlette import status
from decimal import Decimal
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.dtos.projeto_schema import ProjetoCreateSchema
from app.application.dtos.projeto_dtos import ProjetoDTO, ProjetoUpdateDTO, ProjetoComAlocacoesCreateDTO
from app.application.dtos.projeto_detalhado_dtos import ProjetoDetalhadoDTO
from app.application.services.projeto_service import ProjetoService
from app.repositories.alocacao_repository import AlocacaoRepository
from app.repositories.planejamento_horas_repository import PlanejamentoHorasRepository
from app.repositories.recurso_repository import RecursoRepository
from app.services.alocacao_service import AlocacaoService
from app.application.dtos.alocacao_dtos import AlocacaoUpdateDTO, AlocacaoResponseDTO
from app.application.services.status_projeto_service import StatusProjetoService 
from app.infrastructure.repositories.sqlalchemy_projeto_repository import SQLAlchemyProjetoRepository
from app.infrastructure.repositories.sqlalchemy_status_projeto_repository import SQLAlchemyStatusProjetoRepository 
from app.db.session import get_db, get_async_db
from app.db.orm_models import Projeto, equipe_projeto_association, Apontamento, Recurso, Equipe, StatusProjeto, AlocacaoRecursoProjeto, HorasPlanejadas
from app.core.security import get_current_admin_user

router = APIRouter()

# DTO para entrada de horas planejadas
class HorasPlanejadasInputDTO(BaseModel):
    ano: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12, description="Mês 1-12")
    horas_planejadas: Decimal = Field(..., gt=0, description="Horas positivas")

    model_config = {"from_attributes": True}


from sqlalchemy.future import select
from sqlalchemy import delete
from sqlalchemy import or_, func, select

@router.get("/autocomplete", response_model=dict)
async def autocomplete_projetos(
    search: str = Query(..., min_length=1, description="Termo a ser buscado (nome ou código da empresa)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    apenas_ativos: bool = Query(False),
    status_projeto: int = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: dict = Depends(get_current_admin_user)
):
    query = select(Projeto).where(
        or_(
            Projeto.nome.ilike(f"%{search}%"),
            Projeto.codigo_empresa.ilike(f"%{search}%")
        )
    )
    if apenas_ativos:
        query = query.where(Projeto.ativo == True)
    if status_projeto:
        query = query.where(Projeto.status_projeto_id == status_projeto)
    query = query.order_by(Projeto.nome.asc()).offset(skip).limit(limit)
    result = await db.execute(query)
    projetos = result.scalars().all()
    items = [{ "id": p.id, "nome": p.nome } for p in projetos]
    return {"items": items}

# Dependency for ProjetoService
async def get_projeto_service(db: AsyncSession = Depends(get_async_db)) -> ProjetoService:
    projeto_repository = SQLAlchemyProjetoRepository(db_session=db)
    status_projeto_repository = SQLAlchemyStatusProjetoRepository(db_session=db)
    alocacao_repository = AlocacaoRepository(db)
    horas_planejadas_repository = PlanejamentoHorasRepository(db)
    recurso_repository = RecursoRepository(db)
    return ProjetoService(
        projeto_repository=projeto_repository,
        status_projeto_repository=status_projeto_repository,
        alocacao_repository=alocacao_repository,
        horas_planejadas_repository=horas_planejadas_repository,
        recurso_repository=recurso_repository
    )

@router.post("/", response_model=ProjetoDTO, status_code=status.HTTP_201_CREATED)
async def create_projeto(projeto_create: ProjetoCreateSchema, service: ProjetoService = Depends(get_projeto_service)):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info("[create_projeto] Início")
    try:
        result = await service.create_projeto(projeto_create)
        logger.info("[create_projeto] Sucesso")
        return result
    except HTTPException as e:
        logger.warning(f"[create_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[create_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao criar projeto: {str(e)}")


# Novo endpoint completo para projeto + alocações
@router.post("/com-alocacoes", response_model=ProjetoDTO, status_code=status.HTTP_201_CREATED)
async def create_projeto_com_alocacoes(
    payload: ProjetoComAlocacoesCreateDTO,
    service: ProjetoService = Depends(get_projeto_service),
    db: AsyncSession = Depends(get_async_db)
):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info("[create_projeto_com_alocacoes] Início")
    try:
        novo = await service.create_projeto_com_alocacoes(payload, db)
        logger.info("[create_projeto_com_alocacoes] Sucesso")
        return novo
    except HTTPException as e:
        logger.warning(f"[create_projeto_com_alocacoes] HTTPException: {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"[create_projeto_com_alocacoes] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao criar projeto com alocações: {str(e)}")

@router.get("/filtrar", response_model=List[ProjetoDTO])
async def filtrar_projetos(
    secao_id: Optional[int] = Query(None),
    equipe_id: Optional[int] = Query(None),
    recurso_id: Optional[int] = Query(None),
    data_inicio: Optional[date] = Query(None),
    data_fim: Optional[date] = Query(None),
    ativo: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Filtra projetos com base na existência de apontamentos que correspondam
    aos critérios de seção, equipe e recurso, em cascata.
    Permite filtrar adicionalmente por projetos ativos ou inativos.
    Retorna apenas projetos que possuem horas apontadas que satisfaçam os filtros.
    """
    # A query base seleciona projetos distintos que possuem pelo menos um apontamento.
    query = select(Projeto).distinct().join(Apontamento)

    # CORREÇÃO: Usamos outerjoin para não excluir apontamentos de recursos 
    # que não tenham uma equipe principal definida.
    if secao_id is not None or equipe_id is not None:
        query = query.outerjoin(Recurso, Apontamento.recurso_id == Recurso.id).outerjoin(Equipe, Recurso.equipe_principal_id == Equipe.id)
    elif recurso_id is not None:
        query = query.outerjoin(Recurso, Apontamento.recurso_id == Recurso.id)

    # Aplica os filtros de cascata
    if secao_id is not None:
        query = query.where(Equipe.secao_id == secao_id)
    
    if equipe_id is not None:
        query = query.where(Equipe.id == equipe_id)
        
    if recurso_id is not None:
        query = query.where(Recurso.id == recurso_id)

    # Aplica o filtro de período nos apontamentos
    if data_inicio:
        query = query.where(Apontamento.data_apontamento >= data_inicio)
    if data_fim:
        query = query.where(Apontamento.data_apontamento <= data_fim)

    # Filtra por projetos ativos, se especificado
    if ativo is not None:
        query = query.where(Projeto.ativo == ativo)

    query = query.order_by(Projeto.nome)
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/", response_model=dict)
async def get_all_projetos(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    status_projeto: Optional[int] = None,
    search: Optional[str] = None,
    nome: Optional[str] = Query(None),
    include_inactive: bool = False,  
    service: ProjetoService = Depends(get_projeto_service)
):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info(f"[get_all_projetos] Início - skip={skip}, limit={limit}, status_projeto={status_projeto}, search='{search}'")
    try:
        # Frontend antigo envia parâmetro "nome"; convertemos se "search" não veio.
        if not search and nome:
            search = nome
        items = await service.get_all_projetos(skip=skip, limit=limit, include_inactive=include_inactive, status_projeto=status_projeto, search=search)
        total = await service.count_projetos(include_inactive=include_inactive, status_projeto=status_projeto, search=search)
        logger.info(f"[get_all_projetos] Sucesso - {len(items)} registros retornados de {total} total")
        return {"items": items, "total": total}
    except HTTPException as e:
        logger.warning(f"[get_all_projetos] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[get_all_projetos] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao listar projetos: {str(e)}")

@router.get("/detalhados", response_model=dict, summary="Obter lista detalhada de projetos com alocações e horas")
async def get_projetos_detalhados(
    service: ProjetoService = Depends(get_projeto_service),
    page: int = Query(1, ge=1, description="Número da página"),
    per_page: int = Query(10, ge=1, le=100, description="Itens por página"),
    search: Optional[str] = Query(None, description="Termo de busca para nome ou descrição"),
    ativo: Optional[bool] = Query(None, description="Filtrar por projetos ativos ou inativos"),
    secao_id: Optional[int] = Query(None, description="Filtrar pela seção do projeto"),
    recurso: Optional[str] = Query(None, description="Pesquisar pelo nome do recurso alocado"),
    com_alocacoes: Optional[bool] = Query(True, description="Filtrar projetos que possuem alocações")
):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info("[get_projetos_detalhados] Início")
    try:
        items = await service.get_projetos_detalhados(
            page=page,
            per_page=per_page,
            search=search,
            ativo=ativo,
            com_alocacoes=com_alocacoes,
            secao_id=secao_id,
            recurso=recurso
        )
        total = await service.count_projetos_detalhados(
            search=search,
            ativo=ativo,
            com_alocacoes=com_alocacoes,
            secao_id=secao_id,
            recurso=recurso
        )
        return {"items": items, "total": total}
    except HTTPException as e:
        logger.warning("[get_projetos_detalhados] HTTPException: %s", str(e.detail))
        raise e
    except Exception as e:
        logger.error("[get_projetos_detalhados] Erro inesperado: %s", str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Erro inesperado ao listar projetos detalhados")

@router.get("/{projeto_id}", response_model=ProjetoDTO)
async def get_projeto(projeto_id: int, service: ProjetoService = Depends(get_projeto_service)):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info(f"[get_projeto] Início - projeto_id: {projeto_id}")
    try:
        projeto = await service.get_projeto_by_id(projeto_id)
        if projeto is None:
            logger.warning(f"[get_projeto] Projeto não encontrado - projeto_id: {projeto_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado")
        logger.info(f"[get_projeto] Sucesso - projeto_id: {projeto_id}")
        return projeto
    except HTTPException as e:
        logger.warning(f"[get_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[get_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao buscar projeto: {str(e)}")
    return projeto

@router.put("/{projeto_id}", response_model=ProjetoDTO)
async def update_projeto(projeto_id: int, projeto_update: ProjetoUpdateDTO, service: ProjetoService = Depends(get_projeto_service)):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info(f"[update_projeto] Início - projeto_id: {projeto_id}")
    logger.info(f"[update_projeto] Payload recebido: {projeto_update.model_dump(exclude_unset=True)}")
    try:
        result = await service.update_projeto(projeto_id, projeto_update)
        logger.info(f"[update_projeto] Sucesso - projeto_id: {projeto_id}")
        return result
    except HTTPException as e:
        logger.warning(f"[update_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[update_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao atualizar projeto: {str(e)}")

@router.delete("/{projeto_id}", response_model=ProjetoDTO)
async def delete_projeto(projeto_id: int, service: ProjetoService = Depends(get_projeto_service)):
    logger = logging.getLogger("app.api.routes.projeto_routes")
    logger.info(f"[delete_projeto] Início - projeto_id: {projeto_id}")
    try:
        result = await service.delete_projeto(projeto_id)
        if not result:
            logger.warning(f"[delete_projeto] Projeto não encontrado para exclusão - projeto_id: {projeto_id}")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Projeto não encontrado para exclusão")
        logger.info(f"[delete_projeto] Sucesso - projeto_id: {projeto_id}")
        return result
    except HTTPException as e:
        logger.warning(f"[delete_projeto] HTTPException: {str(e.detail)}")
        raise e
    except Exception as e:
        logger.error(f"[delete_projeto] Erro inesperado: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Erro inesperado ao excluir projeto: {str(e)}")

# --------------------------
# Alocações aninhadas em Projeto
# --------------------------
@router.put("/{projeto_id}/alocacoes/{alocacao_id}", response_model=AlocacaoResponseDTO, status_code=status.HTTP_200_OK)
async def update_alocacao_projeto(
    projeto_id: int,
    alocacao_id: int,
    payload: AlocacaoUpdateDTO,
    db: AsyncSession = Depends(get_async_db)
):
    """Atualiza uma alocação específica dentro de um projeto."""
    service = AlocacaoService(db)
    alocacao = await service.get(alocacao_id)
    if not alocacao or alocacao.projeto_id != projeto_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alocação não encontrada")
    update_data = payload.model_dump(exclude_unset=True)
    try:
        return await service.update(alocacao_id, update_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{projeto_id}/alocacoes/{alocacao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alocacao_projeto(
    projeto_id: int,
    alocacao_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """Remove uma alocação específica de um projeto."""
    service = AlocacaoService(db)
    alocacao = await service.get(alocacao_id)
    if not alocacao or alocacao.projeto_id != projeto_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alocação não encontrada")
    await service.delete(alocacao_id)

@router.post("/{projeto_id}/alocacoes/{alocacao_id}/planejamento-horas", status_code=status.HTTP_201_CREATED)
async def save_planejamento_horas(
    projeto_id: int,
    alocacao_id: int,
    payload: List[HorasPlanejadasInputDTO],
    db: AsyncSession = Depends(get_async_db)
):
    """Substitui a lista de horas planejadas de uma alocação."""
    # Verificar alocação
    aloc = await db.get(AlocacaoRecursoProjeto, alocacao_id)
    if not aloc or aloc.projeto_id != projeto_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alocação não encontrada")

    # Remover horas existentes
    await db.execute(delete(HorasPlanejadas).where(HorasPlanejadas.alocacao_id == alocacao_id))

    # Inserir novas horas
    novas = [
        HorasPlanejadas(
            alocacao_id=alocacao_id,
            ano=item.ano,
            mes=item.mes,
            horas_planejadas=item.horas_planejadas,
        ) for item in payload
    ]
    db.add_all(novas)
    try:
        await db.commit()
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Dados inválidos: " + str(e.orig))

    return {"detail": "Horas planejadas salvas com sucesso", "itens_inseridos": len(novas)}
