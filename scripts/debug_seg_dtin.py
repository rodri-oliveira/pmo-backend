"""
Script para debugar por que SEG e DTIN param de gravar no banco
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime
from app.db.session import AsyncSessionLocal
from app.repositories.secao_repository import SecaoRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.recurso_repository import RecursoRepository
from app.repositories.apontamento_repository import ApontamentoRepository

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def debug_secoes():
    """Verifica se as seções SEG, SGI, DTIN existem no banco"""
    async with AsyncSessionLocal() as session:
        secao_repo = SecaoRepository(session)
        
        projetos_teste = ["SEG", "SGI", "DTIN", "TIN"]
        
        logger.info("=== VERIFICANDO SEÇÕES NO BANCO ===")
        for projeto in projetos_teste:
            # Mapeamento correto: DTIN (Jira) → TIN (Seção)
            secao_key = projeto
            if projeto == "DTIN":
                secao_key = "TIN"
                
            secao = await secao_repo.get_by_jira_project_key(secao_key)
            
            if secao:
                logger.info(f"✅ {projeto} -> Seção {secao_key} EXISTE (id={secao.id}, nome={secao.nome})")
            else:
                logger.error(f"❌ {projeto} -> Seção {secao_key} NÃO EXISTE!")
                
                # Tentar criar a seção
                try:
                    secao_data = {
                        "nome": f"Seção {secao_key}",
                        "jira_project_key": secao_key,
                        "descricao": f"Seção criada automaticamente para projeto Jira {projeto}",
                        "ativo": True
                    }
                    
                    secao = await secao_repo.create(secao_data)
                    logger.info(f"✅ CRIADA: Seção {secao_key} (id={secao.id})")
                    
                except Exception as e:
                    logger.error(f"❌ ERRO ao criar seção {secao_key}: {str(e)}")

async def debug_status_projeto():
    """Verifica se existe status padrão para projetos"""
    async with AsyncSessionLocal() as session:
        projeto_repo = ProjetoRepository(session)
        
        logger.info("=== VERIFICANDO STATUS PADRÃO ===")
        try:
            status_default = await projeto_repo.get_status_default()
            if status_default:
                logger.info(f"✅ Status padrão EXISTE (id={status_default.id}, nome={status_default.nome})")
            else:
                logger.error("❌ Status padrão NÃO EXISTE!")
        except Exception as e:
            logger.error(f"❌ ERRO ao buscar status padrão: {str(e)}")

async def debug_teste_completo():
    """Teste completo de criação de apontamento para SEG"""
    async with AsyncSessionLocal() as session:
        secao_repo = SecaoRepository(session)
        projeto_repo = ProjetoRepository(session)
        recurso_repo = RecursoRepository(session)
        apontamento_repo = ApontamentoRepository(session)
        
        logger.info("=== TESTE COMPLETO PARA SEG ===")
        
        try:
            # 1. Verificar/criar seção SEG
            secao = await secao_repo.get_by_jira_project_key("SEG")
            if not secao:
                secao_data = {
                    "nome": "Seção SEG",
                    "jira_project_key": "SEG",
                    "descricao": "Seção Segurança da Informação",
                    "ativo": True
                }
                secao = await secao_repo.create(secao_data)
                logger.info(f"✅ Seção SEG criada (id={secao.id})")
            else:
                logger.info(f"✅ Seção SEG existe (id={secao.id})")
            
            # 2. Verificar status padrão
            status_default = await projeto_repo.get_status_default()
            if not status_default:
                logger.error("❌ Status padrão não existe - PARANDO TESTE")
                return
            
            # 3. Criar projeto teste SEG
            issue_key = "SEG-9999"
            projeto = await projeto_repo.get_by_jira_project_key(issue_key)
            
            if not projeto:
                projeto_data = {
                    "nome": "Projeto Teste SEG",
                    "jira_project_key": issue_key,
                    "secao_id": secao.id,
                    "status_projeto_id": status_default.id,
                    "ativo": True,
                    "data_criacao": datetime.now()
                }
                projeto = await projeto_repo.create(projeto_data)
                logger.info(f"✅ Projeto SEG criado (id={projeto.id})")
            else:
                logger.info(f"✅ Projeto SEG existe (id={projeto.id})")
            
            # 4. Buscar/criar recurso teste
            recurso = await recurso_repo.get_by_email("teste@weg.net")
            if not recurso:
                recurso_data = {
                    "nome": "Usuário Teste",
                    "email": "teste@weg.net",
                    "jira_user_id": "teste123",
                    "ativo": True
                }
                recurso = await recurso_repo.create(recurso_data)
                logger.info(f"✅ Recurso teste criado (id={recurso.id})")
            else:
                logger.info(f"✅ Recurso teste existe (id={recurso.id})")
            
            # 5. Tentar criar apontamento
            apontamento_data = {
                "recurso_id": recurso.id,
                "projeto_id": projeto.id,
                "jira_issue_key": issue_key,
                "data_hora_inicio_trabalho": datetime.now(),
                "data_apontamento": datetime.now().date(),
                "horas_apontadas": 2.0,
                "descricao": "Teste de apontamento SEG",
                "fonte_apontamento": "JIRA",
                "data_criacao": datetime.now(),
                "data_atualizacao": datetime.now(),
                "data_sincronizacao_jira": datetime.now(),
            }
            
            worklog_id = f"teste_seg_{int(datetime.now().timestamp())}"
            apontamento = await apontamento_repo.sync_jira_apontamento(worklog_id, apontamento_data)
            
            logger.info(f"✅ SUCESSO! Apontamento SEG criado (id={apontamento.id})")
            
        except Exception as e:
            logger.error(f"❌ ERRO no teste SEG: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")

async def main():
    """Executa todos os testes de debug"""
    logger.info("🔍 INICIANDO DEBUG SEG/DTIN")
    
    await debug_secoes()
    await debug_status_projeto()
    await debug_teste_completo()
    
    logger.info("🔍 DEBUG CONCLUÍDO")

if __name__ == "__main__":
    asyncio.run(main())
