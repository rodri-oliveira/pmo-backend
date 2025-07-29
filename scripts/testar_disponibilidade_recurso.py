"""
Script de teste para validar o endpoint /backend/dashboard/disponibilidade-recurso
Testa especificamente o matching por similaridade entre horas planejadas e apontadas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import logging
from datetime import datetime
import httpx

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('teste_disponibilidade_recurso.log')
    ]
)
logger = logging.getLogger(__name__)

async def testar_disponibilidade_recurso():
    """Testa o endpoint de disponibilidade de recurso"""
    logger.info("=" * 80)
    logger.info("TESTE DO ENDPOINT /backend/dashboard/disponibilidade-recurso")
    logger.info("Testando matching por similaridade entre planejamento e apontamentos")
    logger.info("=" * 80)
    
    # Configurações do teste
    base_url = "http://localhost:8000"
    endpoint = "/backend/dashboard/disponibilidade-recurso"
    
    # Parâmetros de teste - ajuste conforme necessário
    test_params = {
        "recurso_id": 87,  # ID do recurso a ser testado
        "ano": 2025,
        "mes_inicio": 1,
        "mes_fim": 12
    }
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            logger.info(f"Fazendo requisição para: {base_url}{endpoint}")
            logger.info(f"Parâmetros: {test_params}")
            
            response = await client.get(
                f"{base_url}{endpoint}",
                params=test_params
            )
            
            logger.info(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Analisar resultado
                recurso_info = data.get("recurso", {})
                disponibilidade_mensal = data.get("disponibilidade_mensal", [])
                
                logger.info(f"Recurso: {recurso_info.get('nome')} (ID: {recurso_info.get('id')})")
                logger.info(f"Meses com dados: {len(disponibilidade_mensal)}")
                
                for mes_data in disponibilidade_mensal:
                    mes = mes_data.get("mes")
                    ano = mes_data.get("ano")
                    capacidade = mes_data.get("capacidade_rh", 0)
                    total_planejadas = mes_data.get("total_horas_planejadas", 0)
                    total_apontadas = mes_data.get("total_horas_apontadas", 0)
                    alocacoes = mes_data.get("alocacoes_detalhadas", [])
                    
                    logger.info(f"\n--- MÊS {mes}/{ano} ---")
                    logger.info(f"Capacidade RH: {capacidade}h")
                    logger.info(f"Total Planejadas: {total_planejadas}h")
                    logger.info(f"Total Apontadas: {total_apontadas}h")
                    logger.info(f"Projetos: {len(alocacoes)}")
                    
                    for alocacao in alocacoes:
                        projeto = alocacao.get("projeto", {})
                        horas_planejadas = alocacao.get("horas_planejadas", 0)
                        horas_apontadas = alocacao.get("horas_apontadas", 0)
                        
                        match_status = "✅ MATCH" if horas_apontadas > 0 else "❌ SEM MATCH"
                        
                        logger.info(f"  • {projeto.get('nome')}: "
                                   f"Planejadas={horas_planejadas}h, "
                                   f"Apontadas={horas_apontadas}h {match_status}")
                
                logger.info("\n" + "=" * 80)
                logger.info("TESTE CONCLUÍDO COM SUCESSO")
                logger.info("=" * 80)
                
            else:
                logger.error(f"Erro na requisição: {response.status_code}")
                logger.error(f"Resposta: {response.text}")
                
    except Exception as e:
        logger.error(f"ERRO NO TESTE: {str(e)}")
        logger.error("Traceback completo:", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(testar_disponibilidade_recurso())
