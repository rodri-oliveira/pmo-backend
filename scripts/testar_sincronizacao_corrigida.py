#!/usr/bin/env python3
"""
Script para testar a sincronização JIRA corrigida.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime, timedelta

# Adicionar o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_engine
from sqlalchemy.orm import sessionmaker
from sincronizacao_jira_corrigida import SincronizacaoJiraCorrigida

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('teste_sincronizacao_corrigida.log')
    ]
)

logger = logging.getLogger(__name__)

async def testar_sincronizacao_pequena():
    """
    Testa a sincronização com um período pequeno (últimos 7 dias).
    """
    logger.info("=" * 80)
    logger.info("TESTE DE SINCRONIZAÇÃO JIRA CORRIGIDA - ÚLTIMOS 7 DIAS")
    logger.info("=" * 80)
    
    # Criar sessão assíncrona
    async_session = sessionmaker(
        async_engine, 
        expire_on_commit=False, 
        class_=AsyncSession
    )
    
    async with async_session() as session:
        try:
            # Período de teste: últimos 7 dias
            data_fim = datetime.now()
            data_inicio = data_fim - timedelta(days=7)
            
            logger.info(f"Período de teste: {data_inicio.date()} até {data_fim.date()}")
            
            # Inicializar sincronizador
            sincronizador = SincronizacaoJiraCorrigida(session)
            
            # Executar sincronização
            await sincronizador.processar_periodo(data_inicio, data_fim)
            
            logger.info("✅ Teste concluído com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro no teste: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

async def testar_sincronizacao_completa():
    """
    Testa a sincronização completa desde 01/08/2024.
    """
    logger.info("=" * 80)
    logger.info("TESTE DE SINCRONIZAÇÃO JIRA CORRIGIDA - CARGA COMPLETA")
    logger.info("=" * 80)
    
    # Criar sessão assíncrona
    async_session = sessionmaker(
        async_engine, 
        expire_on_commit=False, 
        class_=AsyncSession
    )
    
    async with async_session() as session:
        try:
            # Período completo: 01/08/2024 até hoje
            data_inicio = datetime(2024, 8, 1)
            data_fim = datetime.now()
            
            logger.info(f"Período completo: {data_inicio.date()} até {data_fim.date()}")
            
            # Inicializar sincronizador
            sincronizador = SincronizacaoJiraCorrigida(session)
            
            # Executar sincronização
            await sincronizador.processar_periodo(data_inicio, data_fim)
            
            logger.info("✅ Teste completo concluído com sucesso!")
            
        except Exception as e:
            logger.error(f"❌ Erro no teste completo: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

async def verificar_dados_inseridos():
    """
    Verifica se os dados foram inseridos corretamente no banco.
    """
    logger.info("=" * 80)
    logger.info("VERIFICAÇÃO DE DADOS INSERIDOS")
    logger.info("=" * 80)
    
    # Criar sessão assíncrona
    async_session = sessionmaker(
        async_engine, 
        expire_on_commit=False, 
        class_=AsyncSession
    )
    
    async with async_session() as session:
        try:
            from app.repositories.apontamento_repository import ApontamentoRepository
            from app.repositories.recurso_repository import RecursoRepository
            from app.repositories.projeto_repository import ProjetoRepository
            from app.repositories.secao_repository import SecaoRepository
            
            # Inicializar repositórios
            apontamento_repo = ApontamentoRepository(session)
            recurso_repo = RecursoRepository(session)
            projeto_repo = ProjetoRepository(session)
            secao_repo = SecaoRepository(session)
            
            # Contar registros
            from sqlalchemy import text
            
            # Apontamentos do JIRA
            result = await session.execute(text("""
                SELECT COUNT(*) as total 
                FROM apontamento 
                WHERE fonte_apontamento = 'JIRA'
                AND data_sincronizacao_jira IS NOT NULL
            """))
            apontamentos_jira = result.scalar()
            
            # Recursos com jira_user_id
            result = await session.execute(text("""
                SELECT COUNT(*) as total 
                FROM recurso 
                WHERE jira_user_id IS NOT NULL
            """))
            recursos_jira = result.scalar()
            
            # Projetos com jira_project_key
            result = await session.execute(text("""
                SELECT COUNT(*) as total 
                FROM projeto 
                WHERE jira_project_key IS NOT NULL
            """))
            projetos_jira = result.scalar()
            
            # Seções com jira_project_key
            result = await session.execute(text("""
                SELECT COUNT(*) as total 
                FROM secao 
                WHERE jira_project_key IS NOT NULL
            """))
            secoes_jira = result.scalar()
            
            # Últimos apontamentos
            result = await session.execute(text("""
                SELECT 
                    a.id,
                    a.jira_issue_key,
                    a.horas_apontadas,
                    a.data_apontamento,
                    r.nome as recurso_nome,
                    p.nome as projeto_nome
                FROM apontamento a
                JOIN recurso r ON a.recurso_id = r.id
                JOIN projeto p ON a.projeto_id = p.id
                WHERE a.fonte_apontamento = 'JIRA'
                ORDER BY a.data_sincronizacao_jira DESC
                LIMIT 10
            """))
            ultimos_apontamentos = result.fetchall()
            
            # Relatório
            logger.info(f"📊 APONTAMENTOS JIRA: {apontamentos_jira}")
            logger.info(f"👤 RECURSOS COM JIRA: {recursos_jira}")
            logger.info(f"📁 PROJETOS COM JIRA: {projetos_jira}")
            logger.info(f"🏢 SEÇÕES COM JIRA: {secoes_jira}")
            
            logger.info("\n🔄 ÚLTIMOS 10 APONTAMENTOS:")
            for apt in ultimos_apontamentos:
                logger.info(f"  ID {apt.id}: {apt.jira_issue_key} | {apt.recurso_nome} | {apt.horas_apontadas}h | {apt.data_apontamento}")
            
            if apontamentos_jira == 0:
                logger.warning("⚠️  NENHUM APONTAMENTO ENCONTRADO! Verifique a sincronização.")
            else:
                logger.info(f"✅ Sincronização funcionando: {apontamentos_jira} apontamentos encontrados")
            
        except Exception as e:
            logger.error(f"❌ Erro na verificação: {str(e)}")
            import traceback
            traceback.print_exc()
            raise

def main():
    """
    Função principal para executar os testes.
    """
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "pequeno":
            # Teste pequeno: python script.py pequeno
            asyncio.run(testar_sincronizacao_pequena())
        elif sys.argv[1] == "completo":
            # Teste completo: python script.py completo
            asyncio.run(testar_sincronizacao_completa())
        elif sys.argv[1] == "verificar":
            # Verificar dados: python script.py verificar
            asyncio.run(verificar_dados_inseridos())
        else:
            print("Uso: python testar_sincronizacao_corrigida.py [pequeno|completo|verificar]")
    else:
        # Padrão: teste pequeno + verificação
        print("Executando teste pequeno...")
        asyncio.run(testar_sincronizacao_pequena())
        print("\nVerificando dados inseridos...")
        asyncio.run(verificar_dados_inseridos())

if __name__ == "__main__":
    main()
