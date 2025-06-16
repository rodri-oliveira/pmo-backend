from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy import func, and_, or_, text, extract, select, join

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import (
    Apontamento, 
    Recurso, 
    Projeto, 
    Equipe, 
    Secao, 
    AlocacaoRecursoProjeto, 
    HorasPlanejadas,
    HorasDisponiveisRH
)

class RelatorioService:
    """
    Serviço para geração de relatórios e análises do sistema.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa o serviço com uma sessão do banco de dados.
        
        Args:
            db: Sessão do banco de dados assíncrona
        """
        self.db = db
    
    async def get_horas_por_projeto(
        self, 
        data_inicio: Optional[date] = None, 
        data_fim: Optional[date] = None,
        secao_id: Optional[int] = None,
        equipe_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém o total de horas apontadas por projeto.
        
        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            secao_id: Filtrar por seção
            equipe_id: Filtrar por equipe
            
        Returns:
            Lista de dicionários com informações de horas por projeto
        """
        query = select(
            Projeto.id.label("projeto_id"),
            Projeto.nome.label("projeto_nome"),
            Projeto.codigo_empresa.label("projeto_codigo"),
            func.sum(Apontamento.horas_apontadas).label("total_horas")
        ).join(
            Apontamento, Apontamento.projeto_id == Projeto.id
        ).group_by(
            Projeto.id, Projeto.nome, Projeto.codigo_empresa
        )
        
        if data_inicio:
            query = query.filter(Apontamento.data_apontamento >= data_inicio)
            
        if data_fim:
            query = query.filter(Apontamento.data_apontamento <= data_fim)
            
        if secao_id or equipe_id:
            query = query.join(
                Recurso, Apontamento.recurso_id == Recurso.id
            )
            
            if secao_id:
                query = query.join(Equipe, Recurso.equipe_principal_id == Equipe.id)
                query = query.filter(Equipe.secao_id == secao_id)
                
            if equipe_id:
                query = query.filter(Recurso.equipe_principal_id == equipe_id)
        
        result = await self.db.execute(query)
        rows = result.fetchall()
        
        return [
            {
                "projeto_id": row.projeto_id,
                "projeto_nome": row.projeto_nome,
                "projeto_codigo": row.projeto_codigo,
                "total_horas": float(row.total_horas) if row.total_horas else 0
            }
            for row in rows
        ]
    
    async def get_horas_por_recurso(
        self, 
        data_inicio: Optional[date] = None, 
        data_fim: Optional[date] = None,
        projeto_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtém o total de horas apontadas por recurso.
        
        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            projeto_id: Filtrar por projeto
            equipe_id: Filtrar por equipe
            secao_id: Filtrar por seção
            
        Returns:
            Lista de dicionários com informações de horas por recurso
        """
        query = select(
            Recurso.id.label("recurso_id"),
            Recurso.nome.label("recurso_nome"),
            Equipe.nome.label("equipe_nome"),
            Secao.nome.label("secao_nome"),
            func.sum(Apontamento.horas_apontadas).label("total_horas")
        ).join(
            Apontamento, Apontamento.recurso_id == Recurso.id
        ).join(
            Equipe, Recurso.equipe_principal_id == Equipe.id, isouter=True
        ).join(
            Secao, Equipe.secao_id == Secao.id, isouter=True
        ).group_by(
            Recurso.id, Recurso.nome, Equipe.nome, Secao.nome
        )
        
        if data_inicio:
            query = query.filter(Apontamento.data_apontamento >= data_inicio)
            
        if data_fim:
            query = query.filter(Apontamento.data_apontamento <= data_fim)
            
        if projeto_id:
            query = query.filter(Apontamento.projeto_id == projeto_id)
            
        if equipe_id:
            query = query.filter(Recurso.equipe_principal_id == equipe_id)
            
        if secao_id:
            query = query.filter(Equipe.secao_id == secao_id)
        
        import logging
        try:
            result = await self.db.execute(query)
            rows = result.fetchall()
            return [
                {
                    "recurso_id": row.recurso_id,
                    "recurso_nome": row.recurso_nome,
                    "equipe_nome": row.equipe_nome,
                    "secao_nome": row.secao_nome,
                    "total_horas": float(row.total_horas) if row.total_horas else 0
                }
                for row in rows
            ]
        except Exception as e:
            logging.exception("Erro ao executar query de horas por recurso")
            raise
    
    async def get_analise_planejado_vs_realizado(
        self,
        ano: int,
        mes: Optional[int] = None,
        projeto_id: Optional[int] = None,
        recurso_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None,
        agrupar_por_projeto: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Obtém análise comparativa entre horas planejadas e horas efetivamente apontadas.
        Opcionalmente agrupa os resultados por projeto.
        """

        # --- CTE para Horas Planejadas ---
        planejado_select_cols = [
            AlocacaoRecursoProjeto.recurso_id,
            HorasPlanejadas.ano,
            HorasPlanejadas.mes,
            func.sum(HorasPlanejadas.horas_planejadas).label("horas_planejadas")
        ]
        planejado_group_by_cols = [
            AlocacaoRecursoProjeto.recurso_id,
            HorasPlanejadas.ano,
            HorasPlanejadas.mes
        ]

        if agrupar_por_projeto:
            planejado_select_cols.insert(1, AlocacaoRecursoProjeto.projeto_id)
            planejado_group_by_cols.insert(1, AlocacaoRecursoProjeto.projeto_id)

        planejado_query = select(*planejado_select_cols).join(
            HorasPlanejadas, HorasPlanejadas.alocacao_id == AlocacaoRecursoProjeto.id
        ).filter(HorasPlanejadas.ano == ano)

        if mes:
            planejado_query = planejado_query.filter(HorasPlanejadas.mes == mes)
        if projeto_id:
            planejado_query = planejado_query.filter(AlocacaoRecursoProjeto.projeto_id == projeto_id)
        if recurso_id:
            planejado_query = planejado_query.filter(AlocacaoRecursoProjeto.recurso_id == recurso_id)

        if equipe_id or secao_id:
            planejado_query = planejado_query.join(Recurso, AlocacaoRecursoProjeto.recurso_id == Recurso.id)
            if equipe_id:
                planejado_query = planejado_query.filter(Recurso.equipe_principal_id == equipe_id)
            if secao_id:
                planejado_query = planejado_query.join(Equipe, Recurso.equipe_principal_id == Equipe.id)
                planejado_query = planejado_query.filter(Equipe.secao_id == secao_id)

        planejado_cte = planejado_query.group_by(*planejado_group_by_cols).cte("planejado_cte")

        # --- CTE para Horas Realizadas (Apontadas) ---
        realizado_select_cols = [
            Apontamento.recurso_id,
            extract("year", Apontamento.data_apontamento).label("ano"),
            extract("month", Apontamento.data_apontamento).label("mes"),
            func.sum(Apontamento.horas_apontadas).label("horas_realizadas")
        ]
        realizado_group_by_cols = [
            Apontamento.recurso_id,
            extract("year", Apontamento.data_apontamento),
            extract("month", Apontamento.data_apontamento)
        ]

        if agrupar_por_projeto:
            realizado_select_cols.insert(1, Apontamento.projeto_id)
            realizado_group_by_cols.insert(1, Apontamento.projeto_id)

        realizado_query = select(*realizado_select_cols).filter(extract("year", Apontamento.data_apontamento) == ano)

        if mes:
            realizado_query = realizado_query.filter(extract("month", Apontamento.data_apontamento) == mes)
        if projeto_id:
            realizado_query = realizado_query.filter(Apontamento.projeto_id == projeto_id)
        if recurso_id:
            realizado_query = realizado_query.filter(Apontamento.recurso_id == recurso_id)

        if equipe_id or secao_id:
            realizado_query = realizado_query.join(Recurso, Apontamento.recurso_id == Recurso.id)
            if equipe_id:
                realizado_query = realizado_query.filter(Recurso.equipe_principal_id == equipe_id)
            if secao_id:
                realizado_query = realizado_query.join(Equipe, Recurso.equipe_principal_id == Equipe.id)
                realizado_query = realizado_query.filter(Equipe.secao_id == secao_id)

        realizado_cte = realizado_query.group_by(*realizado_group_by_cols).cte("realizado_cte")

        # --- Consulta principal com FULL OUTER JOIN ---
        join_conditions = [
            planejado_cte.c.recurso_id == realizado_cte.c.recurso_id,
            planejado_cte.c.ano == realizado_cte.c.ano,
            planejado_cte.c.mes == realizado_cte.c.mes,
        ]
        if agrupar_por_projeto:
            join_conditions.append(planejado_cte.c.projeto_id == realizado_cte.c.projeto_id)

        final_select_cols = [
            Recurso.id.label("recurso_id"),
            Recurso.nome.label("recurso_nome"),
            Equipe.nome.label("equipe_nome"),
            Secao.nome.label("secao_nome"),
            func.coalesce(planejado_cte.c.ano, realizado_cte.c.ano).label("ano"),
            func.coalesce(planejado_cte.c.mes, realizado_cte.c.mes).label("mes"),
            func.coalesce(planejado_cte.c.horas_planejadas, 0).label("horas_planejadas"),
            func.coalesce(realizado_cte.c.horas_realizadas, 0).label("horas_realizadas")
        ]

        if agrupar_por_projeto:
            final_select_cols.insert(2, Projeto.id.label("projeto_id"))
            final_select_cols.insert(3, Projeto.nome.label("projeto_nome"))

        final_query = select(*final_select_cols).select_from(
            join(
                planejado_cte,
                realizado_cte,
                and_(*join_conditions),
                full=True
            )
        ).join(
            Recurso, Recurso.id == func.coalesce(planejado_cte.c.recurso_id, realizado_cte.c.recurso_id)
        )

        if agrupar_por_projeto:
            final_query = final_query.join(
                Projeto, Projeto.id == func.coalesce(planejado_cte.c.projeto_id, realizado_cte.c.projeto_id)
            )
        
        final_query = final_query.join(
            Equipe, Recurso.equipe_principal_id == Equipe.id, isouter=True
        ).join(
            Secao, Equipe.secao_id == Secao.id, isouter=True
        )

        result = await self.db.execute(final_query)
        rows = result.mappings().all()

        response_data = []
        for row in rows:
            # Convert RowMapping to a mutable dictionary
            row_dict = dict(row)
            
            planejadas = float(row_dict.get("horas_planejadas", 0))
            realizadas = float(row_dict.get("horas_realizadas", 0))
            diferenca = planejadas - realizadas
            percentual = (realizadas / planejadas * 100) if planejadas > 0 else 0
            
            row_dict["horas_planejadas"] = planejadas
            row_dict["horas_realizadas"] = realizadas
            row_dict["diferenca"] = diferenca
            row_dict["percentual_realizado"] = round(percentual, 2)
            
            response_data.append(row_dict)
            
        return response_data
    
    async def get_disponibilidade_recursos(
        self,
        ano: int,
        mes: Optional[int] = None,
        recurso_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None,
        agrupar_por_mes: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Calcula e retorna a disponibilidade dos recursos, incluindo horas disponíveis,
        planejadas, realizadas, e métricas de utilização.
        """
        # 1. CTE para pré-filtrar os recursos com base nos filtros de equipe e seção
        recursos_query = select(Recurso.id, Recurso.nome, Recurso.equipe_principal_id)
        if secao_id or equipe_id:
            recursos_query = recursos_query.join(Equipe, Recurso.equipe_principal_id == Equipe.id)
            if secao_id:
                recursos_query = recursos_query.filter(Equipe.secao_id == secao_id)
            if equipe_id:
                recursos_query = recursos_query.filter(Equipe.id == equipe_id)
        if recurso_id:
            recursos_query = recursos_query.filter(Recurso.id == recurso_id)
        
        recursos_cte = recursos_query.cte("recursos_cte")

        # 2. CTE para horas planejadas, já filtrando pelos recursos corretos
        planejadas_select_cols = [
            AlocacaoRecursoProjeto.recurso_id,
            func.sum(HorasPlanejadas.horas_planejadas).label("total_horas_planejadas")
        ]
        planejadas_group_by_cols = [AlocacaoRecursoProjeto.recurso_id]

        if agrupar_por_mes and not mes:
            planejadas_select_cols.append(HorasPlanejadas.mes)
            planejadas_group_by_cols.append(HorasPlanejadas.mes)

        planejadas_query = (
            select(*planejadas_select_cols)
            .join(recursos_cte, AlocacaoRecursoProjeto.recurso_id == recursos_cte.c.id)
            .join(HorasPlanejadas, HorasPlanejadas.alocacao_id == AlocacaoRecursoProjeto.id)
            .filter(HorasPlanejadas.ano == ano)
        )
        if mes:
            planejadas_query = planejadas_query.filter(HorasPlanejadas.mes == mes)
        planejadas_query = planejadas_query.group_by(*planejadas_group_by_cols).cte("planejadas_cte")

        # 3. CTE para horas realizadas (apontadas), também filtrando pelos recursos
        realizadas_select_cols = [
            Apontamento.recurso_id,
            func.sum(Apontamento.horas_apontadas).label("total_horas_realizadas")
        ]
        realizadas_group_by_cols = [Apontamento.recurso_id]

        if agrupar_por_mes and not mes:
            realizadas_select_cols.append(extract("month", Apontamento.data_apontamento).label("mes"))
            realizadas_group_by_cols.append(extract("month", Apontamento.data_apontamento))

        realizadas_query = (
            select(*realizadas_select_cols)
            .join(recursos_cte, Apontamento.recurso_id == recursos_cte.c.id)
            .filter(extract("year", Apontamento.data_apontamento) == ano)
        )
        if mes:
            realizadas_query = realizadas_query.filter(extract("month", Apontamento.data_apontamento) == mes)
        realizadas_query = realizadas_query.group_by(*realizadas_group_by_cols).cte("realizadas_cte")

        # 4. Consulta principal que junta os dados de RH com os agregados
        final_query = (
            select(
                recursos_cte.c.id.label("recurso_id"),
                recursos_cte.c.nome.label("recurso_nome"),
                HorasDisponiveisRH.ano,
                HorasDisponiveisRH.mes,
                HorasDisponiveisRH.horas_disponiveis_mes.label("horas_disponiveis_rh"),
                func.coalesce(planejadas_query.c.total_horas_planejadas, 0).label("horas_planejadas"),
                func.coalesce(realizadas_query.c.total_horas_realizadas, 0).label("horas_realizadas")
            )
            .join(HorasDisponiveisRH, recursos_cte.c.id == HorasDisponiveisRH.recurso_id)
            .outerjoin(
                planejadas_query, 
                and_(
                    recursos_cte.c.id == planejadas_query.c.recurso_id,
                    (HorasDisponiveisRH.mes == planejadas_query.c.mes) if (agrupar_por_mes and not mes) else text('1=1')
                )
            )
            .outerjoin(
                realizadas_query, 
                and_(
                    recursos_cte.c.id == realizadas_query.c.recurso_id,
                    (HorasDisponiveisRH.mes == realizadas_query.c.mes) if (agrupar_por_mes and not mes) else text('1=1')
                )
            )
            .filter(HorasDisponiveisRH.ano == ano)
        )

        if mes:
            final_query = final_query.filter(HorasDisponiveisRH.mes == mes)

        if agrupar_por_mes and not mes:
            final_query = final_query.order_by(recursos_cte.c.nome, HorasDisponiveisRH.mes)
        else:
            final_query = final_query.order_by(recursos_cte.c.nome)

        result = await self.db.execute(final_query)
        rows = result.mappings().all()

        # 5. Processamento e cálculo final em Python
        response_data = []
        for row in rows:
            disponiveis = float(row.horas_disponiveis_rh or 0)
            planejadas = float(row.horas_planejadas or 0)
            realizadas = float(row.horas_realizadas or 0)

            horas_livres = disponiveis - realizadas

            percentual_alocacao_rh = (planejadas / disponiveis * 100) if disponiveis > 0 else 0
            percentual_utilizacao_sobre_planejado = (realizadas / planejadas * 100) if planejadas > 0 else 0
            percentual_utilizacao_sobre_disponivel_rh = (realizadas / disponiveis * 100) if disponiveis > 0 else 0

            response_data.append({
                "recurso_id": row.recurso_id,
                "recurso_nome": row.recurso_nome,
                "ano": row.ano,
                "mes": row.mes,
                "horas_disponiveis_rh": round(disponiveis, 2),
                "horas_planejadas": round(planejadas, 2),
                "horas_realizadas": round(realizadas, 2),
                "horas_livres": round(horas_livres, 2),
                "percentual_alocacao_rh": round(percentual_alocacao_rh, 2),
                "percentual_utilizacao_sobre_planejado": round(percentual_utilizacao_sobre_planejado, 2),
                "percentual_utilizacao_sobre_disponivel_rh": round(percentual_utilizacao_sobre_disponivel_rh, 2),
            })

        return response_data