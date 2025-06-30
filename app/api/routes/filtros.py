from fastapi import APIRouter, Query, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_async_db
from app.db.orm_models import Secao, Equipe, Recurso, AlocacaoRecursoProjeto, Projeto
from sqlalchemy.future import select

router = APIRouter()

@router.get("/filtros-populados", tags=["Filtros"], summary="Popula filtros de equipes, recursos, alocações e projetos")
async def get_filtros_populados(
    secao_id: Optional[int] = Query(None, description="ID da seção selecionada"),
    equipe_id: Optional[int] = Query(None, description="ID da equipe selecionada"),
    recurso_id: Optional[int] = Query(None, description="ID do recurso selecionado"),
    db: AsyncSession = Depends(get_async_db)
):
    # Equipes
    equipes_query = select(Equipe)
    if secao_id:
        equipes_query = equipes_query.where(Equipe.secao_id == secao_id)
    equipes_query = equipes_query.where(Equipe.ativo == True)
    equipes = (await db.execute(equipes_query)).scalars().all()

    recursos = []
    alocacoes = []
    projetos = []

    # Se filtrando por seção (com ou sem equipe): trazer todos os recursos das equipes da seção
    if secao_id:
        equipes_ids = [e.id for e in equipes]
        if equipe_id:
            recursos_query = select(Recurso).where(Recurso.equipe_principal_id == equipe_id, Recurso.ativo == True)
        else:
            recursos_query = select(Recurso).where(Recurso.equipe_principal_id.in_(equipes_ids), Recurso.ativo == True)
        recursos = (await db.execute(recursos_query)).scalars().all()
    # Se filtrando só por equipe (sem secao_id)
    elif equipe_id:
        equipe = await db.get(Equipe, equipe_id)
        equipes = [equipe] if equipe and equipe.ativo else []
        recursos_query = select(Recurso).where(Recurso.equipe_principal_id == equipe_id, Recurso.ativo == True)
        recursos = (await db.execute(recursos_query)).scalars().all()
    # Se filtrando só por recurso (sem secao_id, sem equipe_id)
    elif recurso_id:
        recurso = await db.get(Recurso, recurso_id)
        recursos = [recurso] if recurso and recurso.ativo else []
        equipe = await db.get(Equipe, recurso.equipe_principal_id) if recurso and recurso.equipe_principal_id else None
        equipes = [equipe] if equipe and equipe.ativo else []
    # Se não há filtro, não retorna recursos nem equipes

    # Alocações e projetos apenas se recurso_id
    if recurso_id:
        alocacoes_query = select(AlocacaoRecursoProjeto).where(AlocacaoRecursoProjeto.recurso_id == recurso_id)
        alocacoes = (await db.execute(alocacoes_query)).scalars().all()
        projetos_ids = set([a.projeto_id for a in alocacoes])
        if projetos_ids:
            projetos_query = select(Projeto).where(Projeto.id.in_(projetos_ids), Projeto.ativo == True)
            projetos = (await db.execute(projetos_query)).scalars().all()

    return {
        "equipes": [{"id": e.id, "nome": e.nome} for e in equipes],
        "recursos": [{"id": r.id, "nome": r.nome, "equipe_id": r.equipe_principal_id} for r in recursos],
        "alocacoes": [{"id": a.id, "projeto_id": a.projeto_id, "recurso_id": a.recurso_id} for a in alocacoes],
        "projetos": [{"id": p.id, "nome": p.nome} for p in projetos]
    }
