"""
Script de Sincronização Dashboard Jira
Baseado na estrutura do sincronizacao_jira_funcional_service.py
Responsável por sincronizar dados do Jira para a tabela dashboard_jira_snapshot
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import json

from app.db.session import AsyncSessionLocal
from app.integrations.jira_client import JiraClient
from app.services.dashboard_jira_service import DashboardJiraService
from app.services.dashboard_jira_sync_service import DashboardJiraSyncService
from app.models.schemas import DashboardFilters, SecaoEnum

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('dashboard_jira_sync.log')
    ]
)
logger = logging.getLogger(__name__)

class DashboardJiraSyncScript:
    """Script de sincronização dos dados do dashboard Jira"""
    
    def __init__(self):
        self.jira_client = JiraClient()
        self.stats = {
            'inicio': None,
            'fim': None,
            'duracao_segundos': 0,
            'secoes_processadas': [],
            'total_snapshots_criados': 0,
            'snapshots_removidos': 0,
            'erros': []
        }
    
    async def executar_sincronizacao_completa(self, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Executa sincronização completa de todas as seções
        
        Args:
            force_refresh: Se True, força nova sincronização mesmo se já existe snapshot recente
            
        Returns:
            Dict com resultado da sincronização
        """
        self.stats['inicio'] = datetime.now()
        logger.info(f"[SYNC_SCRIPT] Iniciando sincronização completa do dashboard Jira - force_refresh: {force_refresh}")
        
        try:
            async with AsyncSessionLocal() as session:
                # Criar serviços
                dashboard_service = DashboardJiraService()
                sync_service = DashboardJiraSyncService(dashboard_service, session)
                
                # Executar sincronização
                resultado = await sync_service.sync_all_dashboards(force_refresh=force_refresh)
                
                # Atualizar estatísticas
                self.stats['secoes_processadas'] = resultado.get('secoes_processadas', [])
                self.stats['total_snapshots_criados'] = resultado.get('total_registros', 0)
                self.stats['erros'] = resultado.get('erros', [])
                
                logger.info(f"[SYNC_SCRIPT_SUCCESS] Sincronização concluída com sucesso")
                return resultado
                
        except Exception as e:
            logger.error(f"[SYNC_SCRIPT_ERROR] Erro na sincronização: {str(e)}", exc_info=True)
            self.stats['erros'].append({
                'tipo': 'erro_geral',
                'mensagem': str(e),
                'timestamp': datetime.now()
            })
            raise
        finally:
            self.stats['fim'] = datetime.now()
            if self.stats['inicio']:
                self.stats['duracao_segundos'] = (self.stats['fim'] - self.stats['inicio']).total_seconds()
    
    async def executar_sincronizacao_secao(self, secao: str, force_refresh: bool = False, overwrite: bool = True) -> Dict[str, Any]:
        """
        Executa sincronização de uma seção específica
        
        Args:
            secao: Seção a ser sincronizada (DTIN, SEG, SGI)
            force_refresh: Se True, força nova sincronização
            overwrite: Se True, sobrecreve dados existentes (evita duplicação)
            
        Returns:
            Dict com resultado da sincronização
        """
        self.stats['inicio'] = datetime.now()
        logger.info(f"[SYNC_SECAO] Iniciando sincronização da seção {secao}")
        
        try:
            # Validar seção
            if secao not in ['DTIN', 'SEG', 'SGI']:
                raise ValueError(f"Seção inválida: {secao}. Deve ser DTIN, SEG ou SGI")
            
            secao_enum = SecaoEnum(secao)
            
            async with AsyncSessionLocal() as session:
                # Criar serviços
                dashboard_service = DashboardJiraService()
                sync_service = DashboardJiraSyncService(dashboard_service, session)
                
                # Executar sincronização da seção
                resultado = await sync_service.sync_secao_especifica(secao_enum, force_refresh=force_refresh)
                
                # Atualizar estatísticas
                if resultado.get('status') == 'success':
                    self.stats['secoes_processadas'].append(resultado)
                    self.stats['total_snapshots_criados'] = resultado.get('registros', 0)
                else:
                    self.stats['erros'].append(resultado)
                
                logger.info(f"[SYNC_SECAO_SUCCESS] Sincronização da seção {secao} concluída")
                return resultado
                
        except Exception as e:
            logger.error(f"[SYNC_SECAO_ERROR] Erro na sincronização da seção {secao}: {str(e)}", exc_info=True)
            erro = {
                'secao': secao,
                'tipo': 'erro_sincronizacao',
                'mensagem': str(e),
                'timestamp': datetime.now()
            }
            self.stats['erros'].append(erro)
            raise
        finally:
            self.stats['fim'] = datetime.now()
            if self.stats['inicio']:
                self.stats['duracao_segundos'] = (self.stats['fim'] - self.stats['inicio']).total_seconds()
    
    async def limpar_snapshots_antigos(self, dias_manter: int = 7) -> Dict[str, Any]:
        """
        Remove snapshots antigos do cache
        
        Args:
            dias_manter: Número de dias de snapshots para manter
            
        Returns:
            Dict com resultado da limpeza
        """
        logger.info(f"[CLEANUP] Iniciando limpeza de snapshots com mais de {dias_manter} dias")
        
        try:
            async with AsyncSessionLocal() as session:
                from app.services.dashboard_jira_query_service import DashboardJiraQueryService
                query_service = DashboardJiraQueryService(session)
                
                resultado = await query_service.limpar_cache_antigo(dias_manter=dias_manter)
                
                self.stats['snapshots_removidos'] = resultado.get('total_removidos', 0)
                
                logger.info(f"[CLEANUP_SUCCESS] Limpeza concluída: {resultado['total_removidos']} snapshots removidos")
                return resultado
                
        except Exception as e:
            logger.error(f"[CLEANUP_ERROR] Erro na limpeza: {str(e)}", exc_info=True)
            raise
    
    async def verificar_status_cache(self) -> Dict[str, Any]:
        """
        Verifica o status atual do cache
        
        Returns:
            Dict com informações do status do cache
        """
        logger.info("[STATUS_CHECK] Verificando status do cache")
        
        try:
            async with AsyncSessionLocal() as session:
                from app.services.dashboard_jira_query_service import DashboardJiraQueryService
                query_service = DashboardJiraQueryService(session)
                
                status = await query_service.get_status_cache()
                
                logger.info("[STATUS_CHECK_SUCCESS] Status do cache obtido com sucesso")
                return status
                
        except Exception as e:
            logger.error(f"[STATUS_CHECK_ERROR] Erro ao verificar status: {str(e)}", exc_info=True)
            raise
    
    def get_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas da última execução"""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reseta as estatísticas"""
        self.stats = {
            'inicio': None,
            'fim': None,
            'duracao_segundos': 0,
            'secoes_processadas': [],
            'total_snapshots_criados': 0,
            'snapshots_removidos': 0,
            'erros': []
        }

# Função para execução direta via linha de comando
async def main():
    """Função principal para execução via linha de comando"""
    import sys
    
    script = DashboardJiraSyncScript()
    
    if len(sys.argv) > 1:
        comando = sys.argv[1].lower()
        
        if comando == "sync-all":
            force = "--force" in sys.argv
            resultado = await script.executar_sincronizacao_completa(force_refresh=force)
            print(f"Sincronização completa: {resultado['total_registros']} registros criados")
            
        elif comando == "sync-secao" and len(sys.argv) > 2:
            secao = sys.argv[2].upper()
            force = "--force" in sys.argv
            resultado = await script.executar_sincronizacao_secao(secao, force_refresh=force)
            print(f"Sincronização {secao}: {resultado}")
            
        elif comando == "cleanup":
            dias = int(sys.argv[2]) if len(sys.argv) > 2 else 7
            resultado = await script.limpar_snapshots_antigos(dias_manter=dias)
            print(f"Limpeza: {resultado['total_removidos']} snapshots removidos")
            
        elif comando == "status":
            status = await script.verificar_status_cache()
            print("Status do cache:")
            for secao, info in status.items():
                print(f"  {secao}: {info}")
                
        else:
            print("Uso: python dashboard_jira_sync_script.py [sync-all|sync-secao SECAO|cleanup [DIAS]|status] [--force]")
    else:
        # Execução padrão: sincronização completa
        resultado = await script.executar_sincronizacao_completa()
        print(f"Sincronização padrão concluída: {resultado['total_registros']} registros")

if __name__ == "__main__":
    asyncio.run(main())
