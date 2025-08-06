
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.db.session import get_async_db
from app.db.orm_models import Secao, Equipe, Recurso, AlocacaoRecursoProjeto, Projeto
from sqlalchemy.future import select
import traceback

router = APIRouter()

@router.get("/filtros-populados", tags=["Filtros"], summary="Popula filtros de equipes, recursos, alocações e projetos")
async def get_filtros_populados(
    entidade: Optional[str] = Query(None, description="Entidade a ser filtrada"),
    search: Optional[str] = Query(None, description="Filtro de busca"),
    secao_id: Optional[int] = Query(None, description="ID da seção selecionada"),
    equipe_id: Optional[int] = Query(None, description="ID da equipe selecionada"),
    recurso_id: Optional[int] = Query(None, description="ID do recurso selecionado"),
    db: AsyncSession = Depends(get_async_db)
):
    secoes = []
    if entidade == "secao":
        secoes_query = select(Secao).where(Secao.ativo == True)
        if search:
            secoes_query = secoes_query.where(Secao.nome.like(f"%{search}%"))
        elif secao_id:
            secoes_query = secoes_query.where(Secao.id == secao_id)
        secoes = (await db.execute(secoes_query)).scalars().all()
        if secao_id:
            return {
                "secoes": [{"id": s.id, "nome": s.nome} for s in secoes]
            }
        elif search:
            return {
                "secoes": [{"id": s.id, "nome": s.nome} for s in secoes]
            }
    else:
        secoes_query = select(Secao).where(Secao.ativo == True)
        if secao_id:
            secoes_query = secoes_query.where(Secao.id == secao_id)
        secoes = (await db.execute(secoes_query)).scalars().all()

    equipes = []
    recursos = []
    alocacoes = []
    projetos = []

    # Filtro estrito: secao_id + equipe_id + recurso_id
    if secao_id and equipe_id and recurso_id:
        secoes_query = select(Secao).where(Secao.id == secao_id, Secao.ativo == True)
        secoes = (await db.execute(secoes_query)).scalars().all()
        equipes_query = select(Equipe).where(Equipe.id == equipe_id, Equipe.secao_id == secao_id, Equipe.ativo == True)
        equipes = (await db.execute(equipes_query)).scalars().all()
        recursos_query = select(Recurso).where(Recurso.id == recurso_id, Recurso.equipe_principal_id == equipe_id, Recurso.ativo == True)
        recursos = (await db.execute(recursos_query)).scalars().all()
        alocacoes_query = select(AlocacaoRecursoProjeto).where(AlocacaoRecursoProjeto.recurso_id == recurso_id)
        alocacoes = (await db.execute(alocacoes_query)).scalars().all()
        projetos_ids = set([a.projeto_id for a in alocacoes])
        projetos = []
        if projetos_ids:
            projetos_query = select(Projeto).where(Projeto.id.in_(projetos_ids), Projeto.ativo == True)
            projetos = (await db.execute(projetos_query)).scalars().all()
        return {
            "secoes": [{"id": s.id, "nome": s.nome} for s in secoes],
            "equipes": [{"id": e.id, "nome": e.nome} for e in equipes],
            "recursos": [{"id": r.id, "nome": r.nome, "equipe_id": r.equipe_principal_id} for r in recursos],
            "alocacoes": [{"id": a.id, "projeto_id": a.projeto_id, "recurso_id": a.recurso_id} for a in alocacoes],
            "projetos": [{"id": p.id, "nome": p.nome} for p in projetos]
        }
    # Equipes
    if secao_id and equipe_id:
        # Retornar apenas a equipe selecionada
        equipes_query = select(Equipe).where(Equipe.id == equipe_id, Equipe.secao_id == secao_id, Equipe.ativo == True)
        equipes = (await db.execute(equipes_query)).scalars().all()
        recursos_query = select(Recurso).where(Recurso.equipe_principal_id == equipe_id, Recurso.ativo == True)
        recursos = (await db.execute(recursos_query)).scalars().all()
    else:
        equipes_query = select(Equipe)
        if secao_id:
            equipes_query = equipes_query.where(Equipe.secao_id == secao_id)
        equipes_query = equipes_query.where(Equipe.ativo == True)
        equipes = (await db.execute(equipes_query)).scalars().all()
        recursos = []
        if secao_id:
            equipes_ids = [e.id for e in equipes]
            recursos_query = select(Recurso).where(Recurso.equipe_principal_id.in_(equipes_ids), Recurso.ativo == True)
            recursos = (await db.execute(recursos_query)).scalars().all()
        elif equipe_id:
            recursos_query = select(Recurso).where(Recurso.equipe_principal_id == equipe_id, Recurso.ativo == True)
            recursos = (await db.execute(recursos_query)).scalars().all()

    # Alocações e projetos apenas se recurso_id
    if recurso_id:
        alocacoes_query = select(AlocacaoRecursoProjeto).where(AlocacaoRecursoProjeto.recurso_id == recurso_id)
        alocacoes = (await db.execute(alocacoes_query)).scalars().all()
        projetos_ids = set([a.projeto_id for a in alocacoes])
        projetos = []
        if projetos_ids:
            projetos_query = select(Projeto).where(Projeto.id.in_(projetos_ids), Projeto.ativo == True)
            projetos = (await db.execute(projetos_query)).scalars().all()

    return {
        "secoes": [{"id": s.id, "nome": s.nome} for s in secoes],
        "equipes": [{"id": e.id, "nome": e.nome} for e in equipes],
        "recursos": [{"id": r.id, "nome": r.nome, "equipe_id": r.equipe_principal_id} for r in recursos],
        "alocacoes": [{"id": a.id, "projeto_id": a.projeto_id, "recurso_id": a.recurso_id} for a in alocacoes],
        "projetos": [{"id": p.id, "nome": p.nome} for p in projetos]
    }
