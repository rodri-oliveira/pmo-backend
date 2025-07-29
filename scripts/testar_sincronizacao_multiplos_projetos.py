"""
Script de teste para validar sincronização JIRA com múltiplos projetos
Testa especificamente SEG, SGI e DTIN para identificar problemas de gravação
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime, timedelta

from app.db.session import AsyncSessionLocal
from sincronizacao_jira_funcional import SincronizacaoJiraFuncional

# Configurar logging detalhado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('teste_multiplos_projetos.log')
    ]
)
logger = logging.getLogger(__name__)

async def testar_sincronizacao_multiplos_projetos():
    """Testa sincronização com SEG, SGI e DTIN"""
    logger.info("=" * 80)
    logger.info("TESTE DE SINCRONIZAÇÃO COM MÚLTIPLOS PROJETOS")
    logger.info("Projetos: SEG, SGI, DTIN")
    logger.info("=" * 80)
    
    async with AsyncSessionLocal() as session:
        try:
            # Criar instância do sincronizador
            sincronizador = SincronizacaoJiraFuncional(session)
            
            # Período de teste: últimos 7 dias
            data_fim = datetime.now()
            data_inicio = data_fim - timedelta(days=7)
            
            logger.info(f"Período de teste: {data_inicio.date()} até {data_fim.date()}")
            
            # Executar sincronização
            await sincronizador.processar_periodo(data_inicio, data_fim)
            
            logger.info("=" * 80)
            logger.info("TESTE CONCLUÍDO COM SUCESSO")
            logger.info("=" * 80)
            
        except Exception as e:
            logger.error(f"ERRO NO TESTE: {str(e)}")
            logger.error("Traceback completo:", exc_info=True)
            raise

if __name__ == "__main__":
    asyncio.run(testar_sincronizacao_multiplos_projetos())
