from typing import Dict, Any, List, Optional
from datetime import datetime, date
from sqlalchemy import select, func, case, and_, or_, cast, String, extract, literal, union_all, Float
from app.infrastructure.database.dim_tempo_sql_model import DimTempoSQL as DimTempo
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.orm_models import (
    Apontamento, 
    Recurso, 
    Projeto, 
    Equipe, 
    Secao, 
    AlocacaoRecursoProjeto, 
    HorasPlanejadas,
    HorasDisponiveisRH,
    StatusProjeto
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
            import logging
            logging.exception("Erro ao executar query de horas por recurso")
            raise

    # -------------------------------------------------------------------------
    # Relatório Planejado vs Realizado 2 (POST)
    # -------------------------------------------------------------------------
    async def get_planejado_vs_realizado_v2(
        self,
        recurso_id: int,
        status: Optional[str] = None,
        mes_inicio: Optional[str] = None,
        mes_fim: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Gera relatório Planejado vs Realizado consolidado por projeto e meses.

        - Garante retorno de todos os meses entre mes_inicio e mes_fim (YYYY-MM).
        - Calcula horas planejadas, realizadas e disponibilidade (RH).
        - Monta linhas_resumo (Gap, Disponível, Total Planejado) e lista de projetos.
        """
        from calendar import monthrange
        from datetime import datetime
        from dateutil.relativedelta import relativedelta

        # 1. Validar e construir intervalo de meses
        def parse_mes(m: Optional[str]) -> Optional[datetime]:
            if not m or m.lower() == 'string':
                return None
            try:
                return datetime.strptime(m, "%Y-%m")
            except ValueError:
                return None

        dt_inicio = parse_mes(mes_inicio)
        dt_fim = parse_mes(mes_fim)

        # Se datas não informadas, busca o intervalo completo no banco
        if not dt_inicio or not dt_fim:
            # Subquery para datas planejadas
            planned_dates_q = (
                select(
                    func.to_date(HorasPlanejadas.ano.cast(String) + '-' + HorasPlanejadas.mes.cast(String), 'YYYY-MM').label("data")
                )
                .join(AlocacaoRecursoProjeto, AlocacaoRecursoProjeto.id == HorasPlanejadas.alocacao_id)
                .where(AlocacaoRecursoProjeto.recurso_id == recurso_id)
            )

            # Subquery para datas realizadas
            realized_dates_q = (
                select(func.date_trunc('month', Apontamento.data_apontamento).label("data"))
                .where(Apontamento.recurso_id == recurso_id)
            )
            
            # União das fontes de data
            all_dates_q = union_all(planned_dates_q, realized_dates_q).alias("all_dates")

            min_max_q = select(func.min(all_dates_q.c.data).label("min_date"), func.max(all_dates_q.c.data).label("max_date"))
            date_range_result = await self.db.execute(min_max_q)
            min_max = date_range_result.one_or_none()

            db_min_date = min_max.min_date if min_max and min_max.min_date else datetime.utcnow().date()
            db_max_date = min_max.max_date if min_max and min_max.max_date else datetime.utcnow().date()
            
            dt_inicio = dt_inicio or db_min_date
            dt_fim = dt_fim or db_max_date

        if dt_fim < dt_inicio:
            raise ValueError("mes_fim não pode ser anterior ao mes_inicio")

        meses_intervalo = []
        cursor = dt_inicio
        while cursor <= dt_fim:
            meses_intervalo.append(cursor.strftime("%Y-%m"))
            cursor += relativedelta(months=1)

        # 2. Unificar consultas de horas planejadas e realizadas
        HP, ARP, AP, P, S = HorasPlanejadas, AlocacaoRecursoProjeto, Apontamento, Projeto, StatusProjeto

        planejado_subquery = (
            select(
                ARP.projeto_id,
                HP.ano,
                HP.mes,
                func.sum(HP.horas_planejadas).label("planejado"),
                literal(0).cast(Float).label("realizado")
            )
            .join(ARP, HP.alocacao_id == ARP.id)
            .where(ARP.recurso_id == recurso_id)
            .group_by(ARP.projeto_id, HP.ano, HP.mes)
        )

        realizado_subquery = (
            select(
                AP.projeto_id,
                extract("year", AP.data_apontamento).label("ano"),
                extract("month", AP.data_apontamento).label("mes"),
                literal(0).cast(Float).label("planejado"),
                func.sum(AP.horas_apontadas).label("realizado")
            )
            .where(AP.recurso_id == recurso_id)
            .group_by(AP.projeto_id, extract("year", AP.data_apontamento), extract("month", AP.data_apontamento))
        )
        
        unified_query = union_all(planejado_subquery, realizado_subquery).alias("unified")

        # Consulta principal agregada
        main_q = (
            select(
                unified_query.c.projeto_id,
                P.nome.label("projeto_nome"),
                P.codigo_empresa,
                S.nome.label("status_nome"),
                unified_query.c.ano,
                unified_query.c.mes,
                func.sum(unified_query.c.planejado).label("total_planejado"),
                func.sum(unified_query.c.realizado).label("total_realizado")
            )
            .join(P, P.id == unified_query.c.projeto_id)
            .join(S, S.id == P.status_projeto_id, isouter=True)
            .where(func.to_date(unified_query.c.ano.cast(String) + '-' + unified_query.c.mes.cast(String), 'YYYY-MM').between(dt_inicio, dt_fim))
            .group_by(unified_query.c.projeto_id, P.nome, P.codigo_empresa, S.nome, unified_query.c.ano, unified_query.c.mes)
        )

        result = await self.db.execute(main_q)
        rows = result.fetchall()

        # 3. Consultar disponibilidade de RH
        disp_q = select(HorasDisponiveisRH.ano, HorasDisponiveisRH.mes, HorasDisponiveisRH.horas_disponiveis_mes.label("disponivel"))\
            .where(HorasDisponiveisRH.recurso_id == recurso_id)
        disp_result = (await self.db.execute(disp_q)).fetchall()
        disponibilidade_mes = {(d.ano, d.mes): d.disponivel for d in disp_result}

        # 4. Estruturar resposta
        projetos_map = {}
        for row in rows:
            proj_id = row.projeto_id
            if proj_id not in projetos_map:
                projetos_map[proj_id] = {
                    "id": proj_id,
                    "nome": row.projeto_nome,
                    "codigo_empresa": row.codigo_empresa,
                    "status": row.status_nome,
                    "esforco_planejado": 0,
                    "esforco_realizado": 0,
                    "meses": {m: {"planejado": 0, "realizado": 0} for m in meses_intervalo}
                }
            
            mes_str = f"{int(row.ano):04d}-{int(row.mes):02d}"
            if mes_str in projetos_map[proj_id]["meses"]:
                projetos_map[proj_id]["meses"][mes_str]["planejado"] = float(row.total_planejado or 0)
                projetos_map[proj_id]["meses"][mes_str]["realizado"] = float(row.total_realizado or 0)

        # Calcular totais por projeto
        for proj in projetos_map.values():
            proj["esforco_planejado"] = sum(m["planejado"] for m in proj["meses"].values())
            proj["esforco_realizado"] = sum(m["realizado"] for m in proj["meses"].values())

        # 5. Montar linhas de resumo
        resumo_gap = {"label": "GAP", "meses": {m: {"planejado": 0, "realizado": None} for m in meses_intervalo}}
        resumo_disponivel = {"label": "Horas Disponíveis", "meses": {m: {"planejado": 0, "realizado": None} for m in meses_intervalo}}
        resumo_total = {"label": "Total de esforço (hrs)", "meses": {m: {"planejado": 0, "realizado": 0} for m in meses_intervalo}}

        for mes_str in meses_intervalo:
            ano, mes = map(int, mes_str.split('-'))

            disp_mes = float(disponibilidade_mes.get((ano, mes), 0) or 0)
            total_plano_mes = sum(p["meses"][mes_str]["planejado"] for p in projetos_map.values())
            total_real_mes = sum(p["meses"][mes_str]["realizado"] for p in projetos_map.values())

            resumo_disponivel["meses"][mes_str]["planejado"] = disp_mes
            resumo_total["meses"][mes_str]["planejado"] = total_plano_mes
            resumo_total["meses"][mes_str]["realizado"] = total_real_mes
            resumo_gap["meses"][mes_str]["planejado"] = disp_mes - total_plano_mes

        # 6. Calcular totais gerais para as linhas de resumo
        resumo_gap["esforco_planejado"] = sum(v["planejado"] for v in resumo_gap["meses"].values())
        resumo_disponivel["esforco_planejado"] = sum(v["planejado"] for v in resumo_disponivel["meses"].values())
        resumo_total["esforco_planejado"] = sum(v["planejado"] for v in resumo_total["meses"].values())
        resumo_total["esforco_realizado"] = sum(v["realizado"] for v in resumo_total["meses"].values())

        # 7. Filtrar e montar resposta final
        lista_projetos = list(projetos_map.values())
        if status and status.lower() != 'string':
            lista_projetos = [p for p in lista_projetos if p.get("status", "").lower() == status.lower()]

        return {
            "linhas_resumo": [resumo_gap, resumo_disponivel, resumo_total],
            "projetos": lista_projetos,
        }

        # Montar resposta final
        linhas_resumo = [
            {
                "label": "GAP",
                "esforco_planejado": sum(filter(None, resumo_gap.values())),
                "esforco_realizado": None,  # GAP não tem realizado
                "meses": {m: {"planejado": resumo_gap.get(m), "realizado": None} for m in meses_intervalo},
            },
            {
                "label": "Horas Disponíveis",
                "esforco_planejado": sum(filter(None, resumo_disp.values())),
                "esforco_realizado": None, # Disponibilidade não tem realizado
                "meses": {m: {"planejado": resumo_disp.get(m), "realizado": None} for m in meses_intervalo},
            },
            {
                "label": "Total de esforço (hrs)",
                "esforco_planejado": sum(filter(None, resumo_total_planejado.values())),
                "esforco_realizado": sum(filter(None, resumo_total_realizado.values())),
                "meses": {m: {"planejado": resumo_total_planejado.get(m), "realizado": resumo_total_realizado.get(m) if resumo_total_realizado.get(m, 0) > 0 else None} for m in meses_intervalo},
            },
        ]

        return {
            "linhas_resumo": linhas_resumo,
            "projetos": list(projetos_dict.values()),
        }

    # -------------------------------------------------------------------------
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
        Obtém análise comparativa entre horas planejadas e horas efetivamente apontadas,
        com filtros e opção de agrupamento.
        """
        # 1. Consulta para Horas Planejadas
        planejado_query = select(
            AlocacaoRecursoProjeto.recurso_id,
            AlocacaoRecursoProjeto.projeto_id,
            HorasPlanejadas.ano,
            HorasPlanejadas.mes,
            Recurso.nome.label("recurso_nome"),
            Projeto.nome.label("projeto_nome"),
            Equipe.nome.label("equipe_nome"),
            Secao.nome.label("secao_nome"),
            func.sum(HorasPlanejadas.horas_planejadas).label("horas_planejadas")
        ).join(
            HorasPlanejadas, HorasPlanejadas.alocacao_id == AlocacaoRecursoProjeto.id
        ).join(
            Recurso, AlocacaoRecursoProjeto.recurso_id == Recurso.id
        ).join(
            Projeto, AlocacaoRecursoProjeto.projeto_id == Projeto.id
        ).join(
            Equipe, Recurso.equipe_principal_id == Equipe.id, isouter=True
        ).join(
            Secao, Equipe.secao_id == Secao.id, isouter=True
        ).filter(HorasPlanejadas.ano == ano)

        if mes: planejado_query = planejado_query.filter(HorasPlanejadas.mes == mes)
        if projeto_id: planejado_query = planejado_query.filter(AlocacaoRecursoProjeto.projeto_id == projeto_id)
        if recurso_id: planejado_query = planejado_query.filter(AlocacaoRecursoProjeto.recurso_id == recurso_id)
        if equipe_id: planejado_query = planejado_query.filter(Recurso.equipe_principal_id == equipe_id)
        if secao_id: planejado_query = planejado_query.filter(Equipe.secao_id == secao_id)

        planejado_query = planejado_query.group_by(
            AlocacaoRecursoProjeto.recurso_id, AlocacaoRecursoProjeto.projeto_id, HorasPlanejadas.ano, 
            HorasPlanejadas.mes, Recurso.nome, Projeto.nome, Equipe.nome, Secao.nome
        )

        # 2. Consulta para Horas Realizadas
        realizado_query = select(
            Apontamento.recurso_id,
            Apontamento.projeto_id,
            extract('year', Apontamento.data_apontamento).label('ano'),
            extract('month', Apontamento.data_apontamento).label('mes'),
            func.sum(Apontamento.horas_apontadas).label("horas_realizadas")
        ).filter(extract('year', Apontamento.data_apontamento) == ano)

        realizado_query = realizado_query.join(Recurso, Recurso.id == Apontamento.recurso_id, isouter=True)
        realizado_query = realizado_query.join(Equipe, Equipe.id == Recurso.equipe_principal_id, isouter=True)
        realizado_query = realizado_query.join(Secao, Secao.id == Equipe.secao_id, isouter=True)

        if mes: realizado_query = realizado_query.filter(extract('month', Apontamento.data_apontamento) == mes)
        if projeto_id: realizado_query = realizado_query.filter(Apontamento.projeto_id == projeto_id)
        if recurso_id: realizado_query = realizado_query.filter(Apontamento.recurso_id == recurso_id)
        if equipe_id: realizado_query = realizado_query.filter(Recurso.equipe_principal_id == equipe_id)
        if secao_id: realizado_query = realizado_query.filter(Equipe.secao_id == secao_id)

        realizado_query = realizado_query.group_by(Apontamento.recurso_id, Apontamento.projeto_id, 'ano', 'mes')

        # 3. Executar consultas e combinar resultados
        planejado_result = await self.db.execute(planejado_query)
        realizado_result = await self.db.execute(realizado_query)

        combined_dict = {}
        for row in planejado_result.mappings().all():
            key = (row.recurso_id, row.projeto_id, row.ano, row.mes)
            combined_dict[key] = {
                **row,
                "horas_planejadas": float(row.get("horas_planejadas", 0) or 0),
                "horas_realizadas": 0
            }

        for row in realizado_result.mappings().all():
            key = (row.recurso_id, row.projeto_id, row.ano, row.mes)
            if key in combined_dict:
                combined_dict[key]["horas_realizadas"] = float(row.get("horas_realizadas", 0) or 0)
            else:
                info_recurso_q = select(
                    Recurso.nome.label("recurso_nome"), 
                    Equipe.nome.label("equipe_nome"), 
                    Secao.nome.label("secao_nome")
                ).select_from(Recurso).join(
                    Equipe, Equipe.id == Recurso.equipe_principal_id, isouter=True
                ).join(
                    Secao, Secao.id == Equipe.secao_id, isouter=True
                ).where(Recurso.id == row.recurso_id)
                
                info_projeto_q = select(Projeto.nome.label("projeto_nome")).where(Projeto.id == row.projeto_id)
                
                info_recurso_res = (await self.db.execute(info_recurso_q)).mappings().first()
                info_projeto_res = (await self.db.execute(info_projeto_q)).mappings().first()

                combined_dict[key] = {
                    "recurso_id": row.recurso_id, 
                    "recurso_nome": info_recurso_res.get("recurso_nome") if info_recurso_res else 'N/A',
                    "projeto_id": row.projeto_id, 
                    "projeto_nome": info_projeto_res.get("projeto_nome") if info_projeto_res else 'N/A',
                    "equipe_nome": info_recurso_res.get("equipe_nome") if info_recurso_res else 'N/A', 
                    "secao_nome": info_recurso_res.get("secao_nome") if info_recurso_res else 'N/A',
                    "ano": row.ano, "mes": row.mes,
                    "horas_planejadas": 0,
                    "horas_realizadas": float(row.get("horas_realizadas", 0) or 0)
                }

        # 4. Consolidar se agrupar_por_projeto for False
        if not agrupar_por_projeto:
            consolidado_dict = {}
            for item in combined_dict.values():
                key_consolidado = (item['recurso_id'], item['ano'], item['mes'])
                if key_consolidado not in consolidado_dict:
                    consolidado_dict[key_consolidado] = {
                        "recurso_id": item['recurso_id'],
                        "recurso_nome": item['recurso_nome'],
                        "projeto_id": None,
                        "projeto_nome": "Todos os Projetos",
                        "equipe_nome": item['equipe_nome'],
                        "secao_nome": item['secao_nome'],
                        "ano": item['ano'],
                        "mes": item['mes'],
                        "horas_planejadas": 0,
                        "horas_realizadas": 0
                    }
                consolidado_dict[key_consolidado]["horas_planejadas"] += item["horas_planejadas"]
                consolidado_dict[key_consolidado]["horas_realizadas"] += item["horas_realizadas"]
            
            final_list = list(consolidado_dict.values())
        else:
            final_list = list(combined_dict.values())

        # 5. Calcular diferença e percentual para a lista final
        for item in final_list:
            item["diferenca"] = item["horas_planejadas"] - item["horas_realizadas"]
            if item["horas_planejadas"] > 0:
                item["percentual_realizado"] = round((item["horas_realizadas"] / item["horas_planejadas"]) * 100, 2)
            else:
                item["percentual_realizado"] = 100 if item["horas_realizadas"] > 0 else 0

        return sorted(final_list, key=lambda x: (x['recurso_nome'], x.get('projeto_nome', ''), x['ano'], x['mes']))
    
    async def get_disponibilidade_recursos(
        self,
        ano: int,
        mes: Optional[int] = None,
        recurso_id: Optional[int] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Calcula e retorna a disponibilidade dos recursos, incluindo horas disponíveis,
        planejadas, realizadas, e métricas de utilização.

        Args:
            ano: Ano de referência.
            mes: Mês de referência (opcional, se não fornecido, retorna para o ano todo).
            recurso_id: ID do recurso específico (opcional).

        Returns:
            Lista de dicionários com os dados de disponibilidade por recurso e mês.
        """
        # Subconsulta para agregar horas planejadas por recurso, ano e mês
        subquery_planejadas = (
            select(
                AlocacaoRecursoProjeto.recurso_id,
                HorasPlanejadas.ano,
                HorasPlanejadas.mes,
                func.sum(HorasPlanejadas.horas_planejadas).label("total_horas_planejadas")
            )
            .join(HorasPlanejadas, HorasPlanejadas.alocacao_id == AlocacaoRecursoProjeto.id)
            .group_by(AlocacaoRecursoProjeto.recurso_id, HorasPlanejadas.ano, HorasPlanejadas.mes)
            .filter(HorasPlanejadas.ano == ano)
        )
        if mes:
            subquery_planejadas = subquery_planejadas.filter(HorasPlanejadas.mes == mes)
        if recurso_id:
            subquery_planejadas = subquery_planejadas.filter(AlocacaoRecursoProjeto.recurso_id == recurso_id)
        subquery_planejadas = subquery_planejadas.cte("planejadas_cte")

        # Subconsulta para agregar horas apontadas por recurso, ano e mês
        subquery_apontadas = (
            select(
                Apontamento.recurso_id,
                extract("year", Apontamento.data_apontamento).label("ano"),
                extract("month", Apontamento.data_apontamento).label("mes"),
                func.sum(Apontamento.horas_apontadas).label("total_horas_realizadas")
            )
            .group_by(Apontamento.recurso_id, extract("year", Apontamento.data_apontamento), extract("month", Apontamento.data_apontamento))
            .filter(extract("year", Apontamento.data_apontamento) == ano)
        )
        if mes:
            subquery_apontadas = subquery_apontadas.filter(extract("month", Apontamento.data_apontamento) == mes)
        if recurso_id:
            subquery_apontadas = subquery_apontadas.filter(Apontamento.recurso_id == recurso_id)
        subquery_apontadas = subquery_apontadas.cte("apontadas_cte")

        # Consulta principal
        query = (
            select(
                Recurso.id.label("recurso_id"),
                Recurso.nome.label("recurso_nome"),
                HorasDisponiveisRH.ano,
                HorasDisponiveisRH.mes,
                HorasDisponiveisRH.horas_disponiveis_mes,
                func.coalesce(subquery_planejadas.c.total_horas_planejadas, 0).label("total_horas_planejadas"),
                func.coalesce(subquery_apontadas.c.total_horas_realizadas, 0).label("total_horas_realizadas")
            )
            .join(Recurso, Recurso.id == HorasDisponiveisRH.recurso_id)
            .outerjoin(
                subquery_planejadas,
                and_(
                    subquery_planejadas.c.recurso_id == HorasDisponiveisRH.recurso_id,
                    subquery_planejadas.c.ano == HorasDisponiveisRH.ano,
                    subquery_planejadas.c.mes == HorasDisponiveisRH.mes
                )
            )
            .outerjoin(
                subquery_apontadas,
                and_(
                    subquery_apontadas.c.recurso_id == HorasDisponiveisRH.recurso_id,
                    subquery_apontadas.c.ano == HorasDisponiveisRH.ano,
                    subquery_apontadas.c.mes == HorasDisponiveisRH.mes
                )
            )
            .filter(HorasDisponiveisRH.ano == ano)
        )

        if mes:
            query = query.filter(HorasDisponiveisRH.mes == mes)
        if recurso_id:
            query = query.filter(HorasDisponiveisRH.recurso_id == recurso_id)

        query = query.order_by(Recurso.nome, HorasDisponiveisRH.mes)
        
        result = await self.db.execute(query)
        rows = result.fetchall()

        response_data = []
        for row in rows:
            horas_disponiveis = row.horas_disponiveis_mes if row.horas_disponiveis_mes else 0
            horas_planejadas = row.total_horas_planejadas if row.total_horas_planejadas else 0
            horas_realizadas = row.total_horas_realizadas if row.total_horas_realizadas else 0

            horas_livres = horas_disponiveis - horas_planejadas
            
            percentual_alocacao = (horas_planejadas / horas_disponiveis * 100) if horas_disponiveis > 0 else 0
            percentual_utilizacao_planejado = (horas_realizadas / horas_planejadas * 100) if horas_planejadas > 0 else 0
            percentual_utilizacao_disponivel = (horas_realizadas / horas_disponiveis * 100) if horas_disponiveis > 0 else 0

            response_data.append({
                "recurso_id": row.recurso_id,
                "recurso_nome": row.recurso_nome,
                "ano": row.ano,
                "mes": row.mes,
                "horas_disponiveis_rh": horas_disponiveis,
                "horas_planejadas": horas_planejadas,
                "horas_realizadas": horas_realizadas,
                "horas_livres": horas_livres,
                "percentual_alocacao_rh": round(percentual_alocacao, 2),
                "percentual_utilizacao_sobre_planejado": round(percentual_utilizacao_planejado, 2),
                "percentual_utilizacao_sobre_disponivel_rh": round(percentual_utilizacao_disponivel, 2)
            })
            
        return response_data