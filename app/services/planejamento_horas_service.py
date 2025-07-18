from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.planejamento_horas_repository import PlanejamentoHorasRepository
import logging
from app.repositories.alocacao_repository import AlocacaoRepository
from app.repositories.horas_disponiveis_repository import HorasDisponiveisRepository
from app.schemas.matriz_planejamento_schemas import (
    MatrizPlanejamentoUpdate, 
    MatrizPlanejamentoResponse, 
    ProjetoPlanejamentoResponse, 
    PlanejamentoMensalResponse
)
from sqlalchemy import select
from app.db.orm_models import HorasPlanejadas
from fastapi import HTTPException

logger = logging.getLogger(__name__)

class PlanejamentoHorasService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PlanejamentoHorasRepository(db)
        self.alocacao_repository = AlocacaoRepository(db)
        self.horas_disponiveis_repository = HorasDisponiveisRepository(db)

    async def get_matriz_planejamento_by_recurso(self, recurso_id: int) -> Optional[MatrizPlanejamentoResponse]:
        """
        Busca e monta a matriz de planejamento completa para um recurso.
        """
        logger.info(f"Buscando dados da matriz para o recurso_id: {recurso_id}")
        

        
        raw_data = await self.repository.get_matriz_data_by_recurso(recurso_id)
        
        if not raw_data:
            logger.warning(f"Nenhum dado de planejamento encontrado para o recurso_id: {recurso_id}")
            return MatrizPlanejamentoResponse(recurso_id=recurso_id, projetos=[])

        projetos_dict: Dict[int, ProjetoPlanejamentoResponse] = {}
        
        logger.info(f"Dados brutos recebidos do repositório: {raw_data}")

        for row in raw_data:
            projeto_id = row['projeto_id']

            # Garante que o projeto seja adicionado ao dicionário com os dados da alocação
            if projeto_id not in projetos_dict:
                projetos_dict[projeto_id] = ProjetoPlanejamentoResponse(
                    projeto_id=projeto_id,
                    alocacao_id=row.get('alocacao_id'), # Usa .get() para segurança
                    status_alocacao_id=row.get('status_alocacao_id'),
                    observacao=row.get('observacao'),
                    esforco_estimado=float(row.get('esforco_estimado', 0.0)) if row.get('esforco_estimado') is not None else None,
                    planejamento_mensal=[]
                )

            # Adiciona o planejamento mensal se ele existir
            if row.get('ano') and row.get('mes') and row.get('horas_planejadas') is not None:
                planejamento = PlanejamentoMensalResponse(
                    ano=row['ano'],
                    mes=row['mes'],
                    horas_planejadas=float(row['horas_planejadas'])
                )
                projetos_dict[projeto_id].planejamento_mensal.append(planejamento)

        response = MatrizPlanejamentoResponse(
            recurso_id=recurso_id,
            projetos=list(projetos_dict.values())
        )
        
        logger.info(f"Matriz de planejamento montada com sucesso para o recurso_id: {recurso_id}")
        return response

    async def create_or_update_planejamento(self, alocacao_id: int, ano: int, mes: int, horas_planejadas: float) -> Dict[str, Any]:
        """
        Cria ou atualiza o planejamento de horas para uma alocação em um mês específico.
        """
        alocacao_ids = await self.alocacao_repository.get_ids_by_id(alocacao_id)
        if not alocacao_ids:
            raise ValueError(f"Alocação com ID {alocacao_id} não encontrada")

        if not 1 <= mes <= 12:
            raise ValueError(f"Mês deve estar entre 1 e 12, recebido: {mes}")
        if horas_planejadas < 0:
            raise ValueError(f"Horas planejadas devem ser positivas, recebido: {horas_planejadas}")

        planejamento_dict = await self.repository.create_or_update(
            alocacao_id, ano, mes, horas_planejadas
        )

        return {
            "id": planejamento_dict["id"],
            "alocacao_id": planejamento_dict["alocacao_id"],
            "projeto_id": alocacao_ids["projeto_id"],
            "recurso_id": alocacao_ids["recurso_id"],
            "ano": planejamento_dict["ano"],
            "mes": planejamento_dict["mes"],
            "horas_planejadas": planejamento_dict["horas_planejadas"]
        }
    
    async def get_planejamento(self, alocacao_id: int, ano: int, mes: int) -> Optional[dict]:
        """
        Obtém o planejamento de horas para uma alocação em um mês específico.
        """
        return await self.repository.get_by_alocacao_ano_mes(alocacao_id, ano, mes)
    
    async def list_by_alocacao(self, alocacao_id: int, ano: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Lista todos os planejamentos de uma alocação.
        """
        logger.info(f"[list_by_alocacao] Início: alocacao_id={alocacao_id}")
        try:
            alocacao = await self.alocacao_repository.get(alocacao_id)
            if not alocacao:
                logger.warning(f"[list_by_alocacao] Alocação com ID {alocacao_id} não encontrada")
                raise ValueError(f"Alocação com ID {alocacao_id} não encontrada")
            planejamentos = await self.repository.list_by_alocacao(alocacao_id, ano)
            result = [
                {
                    "id": p.id,
                    "alocacao_id": p.alocacao_id,
                    "projeto_id": alocacao.projeto_id,
                    "recurso_id": alocacao.recurso_id,
                    "ano": p.ano,
                    "mes": p.mes,
                    "horas_planejadas": float(p.horas_planejadas)
                }
                for p in planejamentos
            ]
            return result
        except ValueError as e:
            logger.warning(f"[list_by_alocacao] Valor inválido: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"[list_by_alocacao] Erro inesperado: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Erro inesperado ao listar planejamentos por alocação: {str(e)}")
    
    async def list_by_recurso_periodo(self, recurso_id: int, ano: int, mes_inicio: int = 1, mes_fim: int = 12) -> List[Dict[str, Any]]:
        """
        Lista planejamentos de um recurso em um período.
        """
        return await self.repository.list_by_recurso_periodo(recurso_id, ano, mes_inicio, mes_fim)
    
    async def delete_planejamento(self, planejamento_id: int) -> None:
        """
        Remove um planejamento de horas.
        """
        result = await self.repository.db.execute(select(HorasPlanejadas).filter(HorasPlanejadas.id == planejamento_id))
        planejamento = result.scalars().first()
        if not planejamento:
            raise ValueError(f"Planejamento com ID {planejamento_id} não encontrado")
        await self.repository.delete(planejamento_id)

    async def salvar_alteracoes_matriz(self, payload: MatrizPlanejamentoUpdate) -> None:
        logger.info("--- INICIANDO salvar_alteracoes_matriz ---")
        logger.info(f"Payload recebido: {payload.model_dump_json(indent=2)}") # Log do payload
        try:
            if not payload.alteracoes_projetos:
                logger.warning("A lista 'alteracoes_projetos' está vazia. Nenhuma alteração será salva.")

            for projeto_update in payload.alteracoes_projetos:
                alocacao_id = projeto_update.alocacao_id
                logger.info(f"Processando alocação ID: {alocacao_id} para o projeto ID: {projeto_update.projeto_id}")

                update_data = {}
                if projeto_update.status_alocacao_id is not None:
                    update_data['status_alocacao_id'] = projeto_update.status_alocacao_id
                if projeto_update.observacao is not None:
                    update_data['observacao'] = projeto_update.observacao
                if projeto_update.esforco_estimado is not None:
                    update_data['esforco_estimado'] = projeto_update.esforco_estimado
                
                if update_data:
                    logger.info(f"Atualizando alocação {alocacao_id} com dados: {update_data}")
                    await self.alocacao_repository.update(alocacao_id, update_data)

                # Verificar se a lista de planejamento mensal não está vazia antes de processá-la
                if projeto_update.planejamento_mensal:
                    logger.info(f"Processando {len(projeto_update.planejamento_mensal)} registros de planejamento mensal")
                    for planejamento_mensal in projeto_update.planejamento_mensal:
                        await self.create_or_update_planejamento(
                            alocacao_id=alocacao_id,
                            ano=planejamento_mensal.ano,
                            mes=planejamento_mensal.mes,
                            horas_planejadas=planejamento_mensal.horas_planejadas
                        )
                else:
                    logger.warning(f"Lista de planejamento mensal vazia para alocação {alocacao_id}")
            logger.info("--- FINALIZADO salvar_alteracoes_matriz com SUCESSO ---")
        except Exception as e:
            logger.error(f"ERRO FATAL em salvar_alteracoes_matriz: {e}", exc_info=True)
            raise