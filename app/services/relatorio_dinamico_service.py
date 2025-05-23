from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, and_, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.orm_models import Apontamento, Recurso, Equipe, Secao, Projeto, HorasDisponiveisRH

def get_groupby_columns(agrupar_por):
    columns = []
    if not agrupar_por:
        return columns
    if "recurso" in agrupar_por:
        columns.append(Recurso.id.label("recurso_id"))
        columns.append(Recurso.nome.label("recurso_nome"))
    if "equipe" in agrupar_por:
        columns.append(Equipe.id.label("equipe_id"))
        columns.append(Equipe.nome.label("equipe_nome"))
    if "secao" in agrupar_por:
        columns.append(Secao.id.label("secao_id"))
        columns.append(Secao.nome.label("secao_nome"))
    if "projeto" in agrupar_por:
        columns.append(Projeto.id.label("projeto_id"))
        columns.append(Projeto.nome.label("projeto_nome"))
    if "mes" in agrupar_por:
        columns.append(extract('month', Apontamento.data_apontamento).label("mes"))
    if "ano" in agrupar_por:
        columns.append(extract('year', Apontamento.data_apontamento).label("ano"))
    return columns

class RelatorioDinamicoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_relatorio(self,
        recurso_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None,
        projeto_id: Optional[int] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None,
        agrupar_por: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        columns = [func.sum(Apontamento.horas_apontadas).label("total_horas")]
        columns += get_groupby_columns(agrupar_por)
        query = select(*columns)
        # Joins necessários
        query = query.join(Recurso, Apontamento.recurso_id == Recurso.id)
        query = query.join(Equipe, Recurso.equipe_principal_id == Equipe.id)
        query = query.join(Secao, Equipe.secao_id == Secao.id)
        query = query.join(Projeto, Apontamento.projeto_id == Projeto.id)
        # Filtros
        if recurso_id:
            query = query.where(Recurso.id == recurso_id)
        if equipe_id:
            query = query.where(Equipe.id == equipe_id)
        if secao_id:
            query = query.where(Secao.id == secao_id)
        if projeto_id:
            query = query.where(Projeto.id == projeto_id)
        if data_inicio:
            query = query.where(Apontamento.data_apontamento >= data_inicio)
        if data_fim:
            query = query.where(Apontamento.data_apontamento <= data_fim)
        # Group by
        groupby_cols = get_groupby_columns(agrupar_por)
        if groupby_cols:
            query = query.group_by(*groupby_cols)
        result = await self.db.execute(query)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

    async def get_horas_disponiveis(self, recurso_id: Optional[int] = None, ano: Optional[int] = None, mes: Optional[int] = None) -> List[Dict[str, Any]]:
        query = select(HorasDisponiveisRH.recurso_id, HorasDisponiveisRH.ano, HorasDisponiveisRH.mes, HorasDisponiveisRH.horas_disponiveis_mes)
        if recurso_id:
            query = query.where(HorasDisponiveisRH.recurso_id == recurso_id)
        if ano:
            query = query.where(HorasDisponiveisRH.ano == ano)
        if mes:
            query = query.where(HorasDisponiveisRH.mes == mes)
        result = await self.db.execute(query)
        rows = result.fetchall()
        return [dict(row._mapping) for row in rows]
