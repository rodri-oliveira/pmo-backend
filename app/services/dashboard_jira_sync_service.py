"""
Serviço de Sincronização para Dashboard Jira
Responsável por executar sincronização periódica dos dados do Jira para a tabela local.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select
from sqlalchemy.sql import func

from app.db.orm_models import DashboardJiraSnapshot
from app.services.dashboard_jira_service import DashboardJiraService, DashboardFilters
from app.models.schemas import SecaoEnum

logger = logging.getLogger(__name__)

class DashboardJiraSyncService:
    """Serviço para sincronização periódica dos dados do dashboard Jira"""
    
    def __init__(self, jira_service: DashboardJiraService, db_session: AsyncSession):
        self.jira_service = jira_service
        self.db_session = db_session
    
    async def sync_all_dashboards(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Sincroniza todos os dashboards para todas as seções
        
        Args:
            force_refresh: Se True, força nova sincronização mesmo se já existe snapshot recente
            
        Returns:
            Dict com resultado da sincronização
        """
        logger.info("[SYNC_ALL] Iniciando sincronização completa dos dashboards Jira")
        
        resultado = {
            "inicio": datetime.now(),
            "secoes_processadas": [],
            "total_registros": 0,
            "erros": []
        }
        
        # Seções para sincronizar
        secoes = [SecaoEnum.DTIN, SecaoEnum.SEG, SecaoEnum.SGI]
        
        for secao in secoes:
            try:
                logger.info(f"[SYNC_SECAO] Processando seção: {secao}")
                
                # Verificar se precisa sincronizar
                if not force_refresh and await self._tem_snapshot_recente(secao):
                    logger.info(f"[SYNC_SKIP] Seção {secao} já tem snapshot recente, pulando")
                    continue
                
                # Sincronizar cada tipo de dashboard
                registros_secao = await self._sync_secao_completa(secao)
                
                resultado["secoes_processadas"].append({
                    "secao": secao,
                    "registros": registros_secao,
                    "sucesso": True
                })
                resultado["total_registros"] += registros_secao
                
            except Exception as e:
                logger.error(f"[SYNC_ERROR] Erro ao sincronizar seção {secao}: {str(e)}")
                resultado["erros"].append({
                    "secao": secao,
                    "erro": str(e)
                })
        
        resultado["fim"] = datetime.now()
        resultado["duracao"] = (resultado["fim"] - resultado["inicio"]).total_seconds()
        
        logger.info(f"[SYNC_COMPLETE] Sincronização concluída: {resultado['total_registros']} registros em {resultado['duracao']:.2f}s")
        
        return resultado
    
    async def _tem_snapshot_recente(self, secao: SecaoEnum, horas_limite: int = 6) -> bool:
        """Verifica se já existe snapshot recente para a seção"""
        limite_tempo = datetime.now() - timedelta(hours=horas_limite)
        
        stmt = select(func.count(DashboardJiraSnapshot.id)).where(
            DashboardJiraSnapshot.secao == secao.value,
            DashboardJiraSnapshot.data_snapshot >= limite_tempo
        )
        
        result = await self.db_session.execute(stmt)
        count = result.scalar()
        
        return count > 0
    
    async def _sync_secao_completa(self, secao: SecaoEnum, overwrite: bool = True) -> int:
        """Sincroniza todos os tipos de dashboard para uma seção
        
        Args:
            secao: Seção a ser sincronizada
            overwrite: Se True, limpa dados existentes antes de salvar (padrão: True)
        """
        logger.info(f"[SYNC_SECAO_COMPLETA] Iniciando sincronização completa da seção {secao} - overwrite: {overwrite}")
        
        # SOBRECREVER: Limpar snapshots atuais da seção inteira
        if overwrite:
            removidos = await self._limpar_snapshots_secao_atual(secao.value)
            logger.info(f"[OVERWRITE] Removidos {removidos} snapshots existentes da seção {secao}")
        
        # Limpar snapshots antigos (mais de 7 dias)
        await self._limpar_snapshots_antigos(secao)
        
        total_registros = 0
        data_snapshot = datetime.now()
        
        # Filtros base para a seção
        filtros = DashboardFilters(
            secao=secao,
            ano=2025  # Ano atual
        )
        
        # Sincronizar cada tipo de dashboard
        tipos_dashboard = [
            ("demandas", self.jira_service.get_demandas_dashboard),
            ("melhorias", self.jira_service.get_melhorias_dashboard),
            ("recursos_alocados", self.jira_service.get_recursos_alocados_dashboard)
        ]
        
        for tipo, metodo in tipos_dashboard:
            try:
                logger.info(f"[SYNC_TIPO] Sincronizando {tipo} para seção {secao}")
                
                # Obter dados do Jira
                dashboard_data = await metodo(filtros)
                
                # Salvar no banco
                registros_salvos = await self._salvar_snapshot(
                    secao=secao.value,
                    dashboard_tipo=tipo,
                    dashboard_data=dashboard_data,
                    data_snapshot=data_snapshot,
                    filtros=filtros
                )
                
                total_registros += registros_salvos
                logger.info(f"[SYNC_TIPO_OK] {tipo} sincronizado: {registros_salvos} registros")
                
            except Exception as e:
                logger.error(f"[SYNC_TIPO_ERROR] Erro ao sincronizar {tipo} para {secao}: {str(e)}")
                raise
        
        return total_registros
    
    async def _limpar_snapshots_secao_atual(self, secao: str, dashboard_tipo: str = None):
        """Remove snapshots atuais da seção para evitar duplicação (SOBRECREVER)"""
        try:
            if dashboard_tipo:
                # Limpar apenas um tipo específico
                stmt = delete(DashboardJiraSnapshot).where(
                    DashboardJiraSnapshot.secao == secao,
                    DashboardJiraSnapshot.dashboard_tipo == dashboard_tipo
                )
                logger.info(f"[OVERWRITE] Limpando snapshots: {secao} - {dashboard_tipo}")
            else:
                # Limpar toda a seção
                stmt = delete(DashboardJiraSnapshot).where(
                    DashboardJiraSnapshot.secao == secao
                )
                logger.info(f"[OVERWRITE] Limpando TODOS os snapshots da seção: {secao}")
            
            result = await self.db_session.execute(stmt)
            await self.db_session.commit()
            
            logger.info(f"[OVERWRITE] Removidos {result.rowcount} snapshots para sobrecrever")
            return result.rowcount
            
        except Exception as e:
            logger.error(f"[OVERWRITE_ERROR] Erro ao limpar snapshots: {str(e)}")
            await self.db_session.rollback()
            raise

    async def _limpar_snapshots_antigos(self, secao: SecaoEnum, dias_manter: int = 7):
        """Remove snapshots antigos para liberar espaço"""
        limite_tempo = datetime.now() - timedelta(days=dias_manter)
        
        stmt = delete(DashboardJiraSnapshot).where(
            DashboardJiraSnapshot.secao == secao.value,
            DashboardJiraSnapshot.data_snapshot < limite_tempo
        )
        
        result = await self.db_session.execute(stmt)
        await self.db_session.commit()
        
        if result.rowcount > 0:
            logger.info(f"[CLEANUP] Removidos {result.rowcount} snapshots antigos da seção {secao}")
    
    async def _salvar_snapshot(
        self, 
        secao: str, 
        dashboard_tipo: str, 
        dashboard_data: Any,
        data_snapshot: datetime,
        filtros: DashboardFilters
    ) -> int:
        """Salva dados do dashboard na tabela de snapshot"""
        
        registros_salvos = 0
        filtros_json = json.dumps(filtros.__dict__, default=str)
        
        # Iterar pelos itens do dashboard
        for item in dashboard_data.items:
            snapshot = DashboardJiraSnapshot(
                secao=secao,
                dashboard_tipo=dashboard_tipo,
                status=item.status,
                quantidade=item.quantidade,
                percentual=float(item.percentual),
                data_snapshot=data_snapshot,
                filtros_aplicados=filtros_json
            )
            
            self.db_session.add(snapshot)
            registros_salvos += 1
        
        await self.db_session.commit()
        return registros_salvos
    
    async def sync_secao_especifica(self, secao: SecaoEnum, force_refresh: bool = False, overwrite: bool = True) -> Dict[str, Any]:
        """Sincroniza apenas uma seção específica
        
        Args:
            secao: Seção a ser sincronizada
            force_refresh: Se True, força sincronização mesmo com cache recente
            overwrite: Se True, sobrecreve dados existentes (evita duplicação)
        """
        logger.info(f"[SYNC_ESPECIFICA] Sincronizando seção específica: {secao} - overwrite: {overwrite}")
        
        # Se overwrite=True, sempre executa (ignora snapshot recente)
        # Se overwrite=False, só executa se force_refresh=True ou não tem snapshot recente
        if not overwrite and not force_refresh and await self._tem_snapshot_recente(secao):
            return {
                "secao": secao,
                "status": "skipped",
                "motivo": "snapshot_recente_existe"
            }
        
        try:
            registros = await self._sync_secao_completa(secao, overwrite=overwrite)
            return {
                "secao": secao,
                "status": "success",
                "registros": registros,
                "timestamp": datetime.now()
            }
        except Exception as e:
            logger.error(f"[SYNC_ESPECIFICA_ERROR] Erro: {str(e)}")
            return {
                "secao": secao,
                "status": "error",
                "erro": str(e),
                "timestamp": datetime.now()
            }
    
    async def get_status_sincronizacao(self) -> Dict[str, Any]:
        """Retorna status da última sincronização para cada seção"""
        status = {}
        
        for secao in [SecaoEnum.DTIN, SecaoEnum.SEG, SecaoEnum.SGI]:
            # Buscar último snapshot da seção
            stmt = select(
                DashboardJiraSnapshot.data_snapshot,
                func.count(DashboardJiraSnapshot.id).label('total_registros')
            ).where(
                DashboardJiraSnapshot.secao == secao.value
            ).group_by(
                DashboardJiraSnapshot.data_snapshot
            ).order_by(
                DashboardJiraSnapshot.data_snapshot.desc()
            ).limit(1)
            
            result = await self.db_session.execute(stmt)
            row = result.first()
            
            if row:
                status[secao.value] = {
                    "ultima_sincronizacao": row.data_snapshot,
                    "total_registros": row.total_registros,
                    "idade_horas": (datetime.now() - row.data_snapshot).total_seconds() / 3600,
                    "status": "ok" if (datetime.now() - row.data_snapshot).total_seconds() < 21600 else "desatualizado"  # 6h
                }
            else:
                status[secao.value] = {
                    "ultima_sincronizacao": None,
                    "total_registros": 0,
                    "idade_horas": None,
                    "status": "nunca_sincronizado"
                }
        
        return status
