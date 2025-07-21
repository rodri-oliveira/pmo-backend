#!/usr/bin/env python3
"""
Script para testar o serviço de sincronização melhorado do Jira.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Adicionar o diretório raiz do projeto ao PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import async_engine
from sqlalchemy.orm import sessionmaker
from sincronizacao_jira_melhorada import SincronizacaoJiraMelhorada

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('sincronizacao_teste.log')
    ]
)

logger = logging.getLogger(__name__)

async def testar_sincronizacao():
    """
    Testa o serviço de sincronização melhorado.
    Período: 01/08/2024 até data atual
    """
    logger.info("=" * 60)
    logger.info("TESTE DE SINCRONIZAÇÃO JIRA - 01/08/2024 ATÉ HOJE")
    logger.info("=" * 60)
    
    # Criar sessão assíncrona
    async_session = sessionmaker(
        async_engine, 
        expire_on_commit=False, 
        class_=AsyncSession
    )
    
    async with async_session() as session:
        try:
            # Inicializar serviço de sincronização melhorado
            logger.info("📋 Inicializando serviço de sincronização melhorado...")
            sync_service = SincronizacaoJiraMelhorada(session)
            
            # Calcular dias desde 01/08/2024
            data_inicio = datetime(2024, 8, 1)
            data_atual = datetime.now()
            dias_total = (data_atual - data_inicio).days
            
            logger.info(f"📅 Período: 01/08/2024 até {data_atual.strftime('%d/%m/%Y')}")
            logger.info(f"📊 Total de dias: {dias_total}")
            logger.info("🔄 Iniciando sincronização...")
            
            inicio = datetime.now()
            
            resultado = await sync_service.sincronizar_com_paginacao_robusta(dias=dias_total)
            
            fim = datetime.now()
            duracao = fim - inicio
            
            # Exibir resultados
            logger.info("=" * 60)
            logger.info("RESULTADO DA SINCRONIZAÇÃO")
            logger.info("=" * 60)
            logger.info(f"⏱️  Duração: {duracao.total_seconds():.2f} segundos")
            logger.info(f"📊 Status: {resultado.get('status', 'N/A')}")
            logger.info(f"📝 Apontamentos processados: {resultado.get('apontamentos_processados', 0)}")
            logger.info(f"👥 Recursos criados: {resultado.get('recursos_criados', 0)}")
            logger.info(f"❌ Erros: {resultado.get('erros', 0)}")
            logger.info(f"🎯 Issues processadas: {resultado.get('issues_processadas', 0)}")
            
            if resultado.get('status') == 'ERRO':
                logger.error(f"💥 Mensagem de erro: {resultado.get('mensagem', 'N/A')}")
            
            logger.info("=" * 60)
            logger.info("TESTE CONCLUÍDO COM SUCESSO!")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error("ERRO NO TESTE DE SINCRONIZAÇÃO")
            logger.error("=" * 60)
            logger.error(f"💥 Erro: {str(e)}")
            logger.error("=" * 60)
            raise

async def testar_sincronizacao_detalhada():
    """
    Testa o serviço com diagnósticos básicos.
    Período: 01/08/2024 até data atual
    """
    logger.info("=" * 60)
    logger.info("TESTE COM DIAGNÓSTICOS - 01/08/2024 ATÉ HOJE")
    logger.info("=" * 60)
    
    async_session = sessionmaker(
        async_engine, 
        expire_on_commit=False, 
        class_=AsyncSession
    )
    
    async with async_session() as session:
        try:
            sync_service = SincronizacaoJiraMelhorada(session)
            
            # 1. Testar conexão com Jira
            logger.info("🔌 Testando conexão com Jira...")
            try:
                # Fazer uma requisição simples para testar
                response = sync_service.jira_client._make_request("GET", "/rest/api/3/myself")
                logger.info(f"✅ Conexão OK! Usuário: {response.get('displayName', 'N/A')}")
            except Exception as e:
                logger.error(f"❌ Erro na conexão: {str(e)}")
                return
            
            # 2. Testar busca de issues (preview)
            logger.info("🔍 Testando busca de issues desde 01/08/2024...")
            jql_query = "worklogDate >= '2024-08-01'"
            
            try:
                # Buscar apenas uma página para preview
                endpoint = "/rest/api/3/search"
                params = {
                    'jql': jql_query,
                    'startAt': 0,
                    'maxResults': 5,  # Apenas 5 para preview
                    'fields': 'key,summary,assignee,timetracking,timespent,project'
                }
                
                response = sync_service.jira_client._make_request("GET", endpoint, params=params)
                issues = response.get('issues', [])
                total = response.get('total', 0)
                
                logger.info(f"✅ Busca OK! Encontradas {len(issues)} issues de {total} total")
                
                # Mostrar detalhes das primeiras issues
                for i, issue in enumerate(issues[:3]):
                    issue_key = issue.get('key', 'N/A')
                    summary = issue.get('fields', {}).get('summary', 'N/A')
                    assignee = issue.get('fields', {}).get('assignee', {})
                    assignee_name = assignee.get('displayName', 'Não atribuído') if assignee else 'Não atribuído'
                    
                    timetracking = issue.get('fields', {}).get('timetracking', {})
                    time_spent = timetracking.get('timeSpentSeconds', 0)
                    horas = time_spent / 3600 if time_spent > 0 else 0
                    
                    logger.info(f"  📋 Issue {i+1}: {issue_key} - {assignee_name} - {horas:.2f}h")
                    logger.info(f"      📝 {summary[:50]}...")
                
            except Exception as e:
                logger.error(f"❌ Erro na busca: {str(e)}")
                return
            
            # 3. Executar sincronização completa
            data_inicio = datetime(2024, 8, 1)
            data_atual = datetime.now()
            dias_total = (data_atual - data_inicio).days
            
            logger.info(f"🚀 Executando sincronização completa ({dias_total} dias)...")
            resultado = await sync_service.sincronizar_com_paginacao_robusta(dias=dias_total)
            
            # Exibir resultados
            logger.info("=" * 60)
            logger.info("RESULTADO DETALHADO")
            logger.info("=" * 60)
            for key, value in resultado.items():
                logger.info(f"📊 {key}: {value}")
            
        except Exception as e:
            logger.error(f"💥 Erro no teste detalhado: {str(e)}")
            raise

def main():
    """
    Função principal para executar o teste.
    Período fixo: 01/08/2024 até data atual
    """
    print("🚀 TESTE DE SINCRONIZAÇÃO JIRA MELHORADA")
    print("=" * 60)
    
    data_inicio = datetime(2024, 8, 1)
    data_atual = datetime.now()
    dias_total = (data_atual - data_inicio).days
    
    print(f"📅 Período: 01/08/2024 até {data_atual.strftime('%d/%m/%Y')}")
    print(f"📊 Total de dias: {dias_total}")
    print("=" * 60)
    print("Escolha o tipo de teste:")
    print("1. Teste direto (sem diagnósticos)")
    print("2. Teste com diagnósticos")
    print("=" * 60)
    
    try:
        escolha = input("Digite sua escolha (1 ou 2): ").strip()
        
        if escolha == "1":
            print("🔄 Executando teste direto...")
            asyncio.run(testar_sincronizacao())
        elif escolha == "2":
            print("🔍 Executando teste com diagnósticos...")
            asyncio.run(testar_sincronizacao_detalhada())
        else:
            print("❌ Escolha inválida!")
            return
        
        print("\n🎉 TODOS OS TESTES CONCLUÍDOS!")
        print("📋 Verifique o arquivo 'sincronizacao_teste.log' para detalhes completos.")
        
    except KeyboardInterrupt:
        print("\n⏹️  Teste interrompido pelo usuário.")
    except Exception as e:
        print(f"\n💥 Erro durante o teste: {str(e)}")
        print("📋 Verifique o arquivo 'sincronizacao_teste.log' para detalhes completos.")

if __name__ == "__main__":
    main()
