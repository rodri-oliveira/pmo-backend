"""
Script para testar os novos endpoints de Dashboard Jira
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from datetime import datetime
from app.services.dashboard_jira_service import DashboardJiraService, DashboardFilters

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def testar_demandas():
    """Testa o dashboard de demandas"""
    logger.info("=== TESTANDO DASHBOARD DE DEMANDAS ===")
    
    try:
        service = DashboardJiraService()
        
        # Filtros de teste para DTIN em 2025
        filters = DashboardFilters(
            secao="DTIN",
            ano=2025
        )
        
        result = await service.get_demandas_dashboard(filters)
        
        logger.info(f"✅ DEMANDAS - Total: {result.total}")
        for item in result.items:
            logger.info(f"  - {item.status}: {item.quantidade} ({item.percentual}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERRO no teste de demandas: {str(e)}")
        return False

async def testar_melhorias():
    """Testa o dashboard de melhorias"""
    logger.info("=== TESTANDO DASHBOARD DE MELHORIAS ===")
    
    try:
        service = DashboardJiraService()
        
        # Filtros de teste para DTIN em 2025
        filters = DashboardFilters(
            secao="DTIN",
            ano=2025
        )
        
        result = await service.get_melhorias_dashboard(filters)
        
        logger.info(f"✅ MELHORIAS - Total: {result.total}")
        for item in result.items:
            logger.info(f"  - {item.status}: {item.quantidade} ({item.percentual}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERRO no teste de melhorias: {str(e)}")
        return False

async def testar_recursos_alocados():
    """Testa o dashboard de recursos alocados"""
    logger.info("=== TESTANDO DASHBOARD DE RECURSOS ALOCADOS ===")
    
    try:
        service = DashboardJiraService()
        
        # Filtros de teste para DTIN em 2025 (sem filtro de recursos específicos)
        filters = DashboardFilters(
            secao="DTIN",
            ano=2025
        )
        
        result = await service.get_recursos_alocados_dashboard(filters)
        
        logger.info(f"✅ RECURSOS ALOCADOS - Total: {result.total}")
        for item in result.items:
            logger.info(f"  - {item.status}: {item.quantidade} ({item.percentual}%)")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERRO no teste de recursos alocados: {str(e)}")
        return False

async def testar_recursos_disponiveis():
    """Testa a busca de recursos disponíveis"""
    logger.info("=== TESTANDO RECURSOS DISPONÍVEIS ===")
    
    try:
        service = DashboardJiraService()
        
        # Buscar recursos para DTIN
        recursos = await service.get_recursos_disponiveis("DTIN")
        
        logger.info(f"✅ RECURSOS DISPONÍVEIS - Total: {len(recursos)}")
        for i, recurso in enumerate(recursos[:5]):  # Mostrar apenas os primeiros 5
            logger.info(f"  - {recurso['display_name']} ({recurso['account_id']})")
        
        if len(recursos) > 5:
            logger.info(f"  ... e mais {len(recursos) - 5} recursos")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERRO no teste de recursos disponíveis: {str(e)}")
        return False

async def testar_jql_construcao():
    """Testa a construção dos JQLs"""
    logger.info("=== TESTANDO CONSTRUÇÃO DE JQLs ===")
    
    try:
        service = DashboardJiraService()
        
        # Teste 1: Filtros básicos
        filters = DashboardFilters(
            secao="DTIN",
            ano=2025
        )
        
        demandas_jql = service._build_demandas_jql(filters)
        melhorias_jql = service._build_melhorias_jql(filters)
        recursos_jql = service._build_recursos_alocados_jql(filters)
        
        logger.info("✅ JQLs construídos com sucesso:")
        logger.info(f"  DEMANDAS: {demandas_jql}")
        logger.info(f"  MELHORIAS: {melhorias_jql}")
        logger.info(f"  RECURSOS: {recursos_jql}")
        
        # Teste 2: Filtros com datas específicas
        filters_com_data = DashboardFilters(
            secao="DTIN",
            data_inicio=datetime(2025, 1, 1),
            data_fim=datetime(2025, 12, 31)
        )
        
        demandas_jql_data = service._build_demandas_jql(filters_com_data)
        logger.info(f"  DEMANDAS COM DATA: {demandas_jql_data}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ ERRO no teste de construção de JQLs: {str(e)}")
        return False

async def main():
    """Executa todos os testes"""
    logger.info("🚀 INICIANDO TESTES DOS DASHBOARDS JIRA")
    
    testes = [
        ("Construção de JQLs", testar_jql_construcao),
        ("Recursos Disponíveis", testar_recursos_disponiveis),
        ("Dashboard de Demandas", testar_demandas),
        ("Dashboard de Melhorias", testar_melhorias),
        ("Dashboard de Recursos Alocados", testar_recursos_alocados),
    ]
    
    resultados = []
    
    for nome_teste, funcao_teste in testes:
        logger.info(f"\n{'='*50}")
        logger.info(f"EXECUTANDO: {nome_teste}")
        logger.info(f"{'='*50}")
        
        try:
            sucesso = await funcao_teste()
            resultados.append((nome_teste, sucesso))
        except Exception as e:
            logger.error(f"❌ ERRO CRÍTICO no teste {nome_teste}: {str(e)}")
            resultados.append((nome_teste, False))
    
    # Relatório final
    logger.info(f"\n{'='*50}")
    logger.info("RELATÓRIO FINAL DOS TESTES")
    logger.info(f"{'='*50}")
    
    sucessos = 0
    for nome, sucesso in resultados:
        status = "✅ SUCESSO" if sucesso else "❌ FALHOU"
        logger.info(f"{status}: {nome}")
        if sucesso:
            sucessos += 1
    
    logger.info(f"\nRESUMO: {sucessos}/{len(resultados)} testes passaram")
    
    if sucessos == len(resultados):
        logger.info("🎉 TODOS OS TESTES PASSARAM!")
    else:
        logger.warning("⚠️  ALGUNS TESTES FALHARAM")

if __name__ == "__main__":
    asyncio.run(main())
