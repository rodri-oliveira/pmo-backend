"""
Serviço de Consulta para Dashboard Jira
Responsável por consultar dados do dashboard a partir da tabela local (cache).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.sql import func

from app.db.orm_models import DashboardJiraSnapshot
from app.models.schemas import DashboardResponse, DashboardItem, DashboardFilters, SecaoEnum

logger = logging.getLogger(__name__)

class DashboardJiraQueryService:
    """Serviço para consultas rápidas dos dados do dashboard Jira a partir do cache local"""
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def get_demandas_dashboard_cached(self, filters: DashboardFilters) -> DashboardResponse:
        """Obtém dados do dashboard de Demandas a partir do cache"""
        return await self._get_dashboard_cached("demandas", filters)
    
    async def get_melhorias_dashboard_cached(self, filters: DashboardFilters) -> DashboardResponse:
        """Obtém dados do dashboard de Melhorias a partir do cache"""
        return await self._get_dashboard_cached("melhorias", filters)
    
    async def get_recursos_alocados_dashboard_cached(self, filters: DashboardFilters) -> DashboardResponse:
        """Obtém dados do dashboard de Recursos Alocados a partir do cache"""
        return await self._get_dashboard_cached("recursos_alocados", filters)
    
    async def _get_dashboard_cached(self, dashboard_tipo: str, filters: DashboardFilters) -> DashboardResponse:
        """Método genérico para obter dados do dashboard a partir do cache"""
        logger.info(f"[CACHE_QUERY] Consultando {dashboard_tipo} com filtros: {filters}")
        
        # Construir query base
        query = select(DashboardJiraSnapshot).where(
            DashboardJiraSnapshot.dashboard_tipo == dashboard_tipo
        )
        
        # Aplicar filtros
        if filters.secao:
            query = query.where(DashboardJiraSnapshot.secao == filters.secao)
        
        # Buscar snapshot mais recente
        query = query.order_by(DashboardJiraSnapshot.data_snapshot.desc())
        
        # Limitar por data se necessário (pegar apenas snapshots recentes)
        limite_tempo = datetime.now() - timedelta(hours=24)  # Máximo 24h de idade
        query = query.where(DashboardJiraSnapshot.data_snapshot >= limite_tempo)
        
        # Executar query
        result = await self.db_session.execute(query)
        snapshots = result.scalars().all()
        
        if not snapshots:
            logger.warning(f"[CACHE_EMPTY] Nenhum snapshot encontrado para {dashboard_tipo} com filtros {filters}")
            return DashboardResponse(
                tipo=dashboard_tipo,
                total=0,
                items=[],
                filtros_aplicados=filters.__dict__
            )
        
        # Agrupar por data_snapshot mais recente
        snapshot_mais_recente = snapshots[0].data_snapshot
        snapshots_recentes = [s for s in snapshots if s.data_snapshot == snapshot_mais_recente]
        
        # Converter para DashboardItem
        items = []
        total_issues = 0
        
        for snapshot in snapshots_recentes:
            items.append(DashboardItem(
                status=snapshot.status,
                quantidade=snapshot.quantidade,
                percentual=float(snapshot.percentual)
            ))
            total_issues += snapshot.quantidade
        
        logger.info(f"[CACHE_SUCCESS] {dashboard_tipo} retornado do cache: {len(items)} status, {total_issues} issues")
        
        return DashboardResponse(
            tipo=dashboard_tipo,
            total=total_issues,
            items=items,
            filtros_aplicados=filters.__dict__
        )
    
    async def get_dashboard_completo_cached(self, filters: DashboardFilters) -> Dict[str, DashboardResponse]:
        """Obtém todos os dashboards de uma vez a partir do cache"""
        logger.info(f"[CACHE_COMPLETO] Consultando dashboard completo com filtros: {filters}")
        
        # Executar consultas em paralelo seria ideal, mas por simplicidade vamos fazer sequencial
        demandas = await self.get_demandas_dashboard_cached(filters)
        melhorias = await self.get_melhorias_dashboard_cached(filters)
        recursos_alocados = await self.get_recursos_alocados_dashboard_cached(filters)
        
        return {
            "demandas": demandas,
            "melhorias": melhorias,
            "recursos_alocados": recursos_alocados
        }
    
    async def get_status_cache(self) -> Dict[str, Any]:
        """Retorna informações sobre o status do cache"""
        logger.info("[CACHE_STATUS] Consultando status do cache")
        
        status = {}
        
        # Para cada seção
        for secao in [SecaoEnum.DTIN, SecaoEnum.SEG, SecaoEnum.SGI]:
            # Buscar informações do cache
            query = select(
                DashboardJiraSnapshot.dashboard_tipo,
                func.max(DashboardJiraSnapshot.data_snapshot).label('ultima_atualizacao'),
                func.count(DashboardJiraSnapshot.id).label('total_registros')
            ).where(
                DashboardJiraSnapshot.secao == secao.value
            ).group_by(
                DashboardJiraSnapshot.dashboard_tipo
            )
            
            result = await self.db_session.execute(query)
            rows = result.all()
            
            secao_status = {}
            for row in rows:
                idade_horas = (datetime.now() - row.ultima_atualizacao).total_seconds() / 3600
                secao_status[row.dashboard_tipo] = {
                    "ultima_atualizacao": row.ultima_atualizacao,
                    "total_registros": row.total_registros,
                    "idade_horas": round(idade_horas, 2),
                    "status": "ok" if idade_horas < 6 else "desatualizado"
                }
            
            status[secao.value] = secao_status
        
        return status
    
    async def limpar_cache_antigo(self, dias_manter: int = 7) -> Dict[str, int]:
        """Remove snapshots antigos do cache"""
        logger.info(f"[CACHE_CLEANUP] Limpando cache com mais de {dias_manter} dias")
        
        limite_tempo = datetime.now() - timedelta(days=dias_manter)
        
        # Contar registros que serão removidos por seção
        count_query = select(
            DashboardJiraSnapshot.secao,
            func.count(DashboardJiraSnapshot.id).label('count')
        ).where(
            DashboardJiraSnapshot.data_snapshot < limite_tempo
        ).group_by(
            DashboardJiraSnapshot.secao
        )
        
        result = await self.db_session.execute(count_query)
        counts_antes = {row.secao: row.count for row in result.all()}
        
        # Remover registros antigos
        from sqlalchemy import delete
        delete_stmt = delete(DashboardJiraSnapshot).where(
            DashboardJiraSnapshot.data_snapshot < limite_tempo
        )
        
        result = await self.db_session.execute(delete_stmt)
        await self.db_session.commit()
        
        total_removidos = result.rowcount
        
        logger.info(f"[CACHE_CLEANUP_OK] Removidos {total_removidos} registros antigos")
        
        return {
            "total_removidos": total_removidos,
            "por_secao": counts_antes,
            "limite_tempo": limite_tempo
        }
    
    async def verificar_necessidade_sync(self, horas_limite: int = 6) -> Dict[str, bool]:
        """Verifica quais seções precisam de sincronização"""
        logger.info(f"[SYNC_CHECK] Verificando necessidade de sync (limite: {horas_limite}h)")
        
        limite_tempo = datetime.now() - timedelta(hours=horas_limite)
        necessita_sync = {}
        
        for secao in [SecaoEnum.DTIN, SecaoEnum.SEG, SecaoEnum.SGI]:
            # Verificar se tem snapshot recente
            query = select(func.count(DashboardJiraSnapshot.id)).where(
                and_(
                    DashboardJiraSnapshot.secao == secao.value,
                    DashboardJiraSnapshot.data_snapshot >= limite_tempo
                )
            )
            
            result = await self.db_session.execute(query)
            count = result.scalar()
            
            necessita_sync[secao.value] = count == 0
        
        logger.info(f"[SYNC_CHECK_RESULT] Seções que precisam sync: {[k for k, v in necessita_sync.items() if v]}")
        
        return necessita_sync
    
    async def get_historico_snapshots(self, secao: Optional[str] = None, dias: int = 7) -> List[Dict[str, Any]]:
        """Retorna histórico de snapshots para análise"""
        logger.info(f"[HISTORICO] Consultando histórico de {dias} dias para seção: {secao or 'todas'}")
        
        limite_tempo = datetime.now() - timedelta(days=dias)
        
        query = select(
            DashboardJiraSnapshot.secao,
            DashboardJiraSnapshot.dashboard_tipo,
            DashboardJiraSnapshot.data_snapshot,
            func.sum(DashboardJiraSnapshot.quantidade).label('total_issues')
        ).where(
            DashboardJiraSnapshot.data_snapshot >= limite_tempo
        ).group_by(
            DashboardJiraSnapshot.secao,
            DashboardJiraSnapshot.dashboard_tipo,
            DashboardJiraSnapshot.data_snapshot
        ).order_by(
            DashboardJiraSnapshot.data_snapshot.desc()
        )
        
        if secao:
            query = query.where(DashboardJiraSnapshot.secao == secao)
        
        result = await self.db_session.execute(query)
        rows = result.all()
        
        historico = []
        for row in rows:
            historico.append({
                "secao": row.secao,
                "dashboard_tipo": row.dashboard_tipo,
                "data_snapshot": row.data_snapshot,
                "total_issues": row.total_issues
            })
        
        logger.info(f"[HISTORICO_OK] Retornados {len(historico)} registros de histórico")
        
        return historico
    
    async def get_secao_status(self, secao: str) -> Dict[str, Any]:
        """Retorna status detalhado de uma seção específica"""
        logger.info(f"[SECAO_STATUS] Consultando status da seção: {secao}")
        
        try:
            # Buscar snapshot mais recente da seção
            query = select(
                DashboardJiraSnapshot.dashboard_tipo,
                DashboardJiraSnapshot.data_snapshot,
                func.sum(DashboardJiraSnapshot.quantidade).label('total_registros')
            ).where(
                DashboardJiraSnapshot.secao == secao
            ).group_by(
                DashboardJiraSnapshot.dashboard_tipo,
                DashboardJiraSnapshot.data_snapshot
            ).order_by(
                DashboardJiraSnapshot.data_snapshot.desc()
            ).limit(10)  # Últimos 10 snapshots
            
            result = await self.db_session.execute(query)
            snapshots = result.all()
            
            if not snapshots:
                return {
                    "status": "empty",
                    "dados_disponiveis": False,
                    "ultima_sincronizacao": None,
                    "total_registros": 0,
                    "dashboards": []
                }
            
            # Agrupar por data_snapshot mais recente
            snapshot_mais_recente = snapshots[0].data_snapshot
            snapshots_recentes = [s for s in snapshots if s.data_snapshot == snapshot_mais_recente]
            
            # Calcular totais
            total_registros = sum(s.total_registros for s in snapshots_recentes)
            dashboards_disponiveis = [s.dashboard_tipo for s in snapshots_recentes]
            
            # Verificar se dados são recentes (menos de 24h)
            agora = datetime.now()
            idade_horas = (agora - snapshot_mais_recente).total_seconds() / 3600
            dados_recentes = idade_horas < 24
            
            return {
                "status": "active" if dados_recentes else "stale",
                "dados_disponiveis": True,
                "ultima_sincronizacao": snapshot_mais_recente,
                "idade_horas": round(idade_horas, 1),
                "total_registros": total_registros,
                "dashboards": dashboards_disponiveis,
                "dados_recentes": dados_recentes
            }
            
        except Exception as e:
            logger.error(f"[SECAO_STATUS_ERROR] Erro ao consultar status da seção {secao}: {str(e)}")
            return {
                "status": "error",
                "dados_disponiveis": False,
                "erro": str(e),
                "ultima_sincronizacao": None,
                "total_registros": 0
            }
