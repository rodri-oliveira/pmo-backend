from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.planejamento_horas_repository import PlanejamentoHorasRepository
import logging
from app.repositories.alocacao_repository import AlocacaoRepository
from app.repositories.horas_disponiveis_repository import HorasDisponiveisRepository
from app.schemas.matriz_planejamento_schemas import MatrizPlanejamentoUpdate
from sqlalchemy import select
from app.db.orm_models import HorasPlanejadas

logger = logging.getLogger(__name__)


class PlanejamentoHorasService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PlanejamentoHorasRepository(db)
        self.alocacao_repository = AlocacaoRepository(db)
        self.horas_disponiveis_repository = HorasDisponiveisRepository(db)
    
    async def create_or_update_planejamento(self, alocacao_id: int, ano: int, mes: int, horas_planejadas: float) -> Dict[str, Any]:
        """
        Cria ou atualiza o planejamento de horas para uma alocação em um mês específico.
        """
        # 1. Obter IDs de forma segura, sem carregar o objeto ORM
        alocacao_ids = await self.alocacao_repository.get_ids_by_id(alocacao_id)
        if not alocacao_ids:
            raise ValueError(f"Alocação com ID {alocacao_id} não encontrada")

        # 2. Validações
        if not 1 <= mes <= 12:
            raise ValueError(f"Mês deve estar entre 1 e 12, recebido: {mes}")
        if horas_planejadas < 0:
            raise ValueError(f"Horas planejadas devem ser positivas, recebido: {horas_planejadas}")

        # 3. Criar ou atualizar o planejamento (o repositório já é seguro)
        planejamento_dict = await self.repository.create_or_update(
            alocacao_id, ano, mes, horas_planejadas
        )

        # 4. Montar o retorno apenas com dados primitivos
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
        
        Args:
            alocacao_id: ID da alocação
            ano: Ano do planejamento
            mes: Mês do planejamento (1-12)
            
        Returns:
            dict: Dados do planejamento, ou None se não encontrado
        """
        return await self.repository.get_by_alocacao_ano_mes(alocacao_id, ano, mes)
    
    async def list_by_alocacao(self, alocacao_id: int, ano: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Lista todos os planejamentos de uma alocação.
        """
        logger = logging.getLogger("app.services.planejamento_horas_service")
        logger.info(f"[list_by_alocacao] Início: alocacao_id={alocacao_id}")
        try:
            alocacao = await self.alocacao_repository.get(alocacao_id)
            logger.debug(f"[list_by_alocacao] Alocação encontrada: {alocacao}")
            if not alocacao:
                logger.warning(f"[list_by_alocacao] Alocação com ID {alocacao_id} não encontrada")
                raise ValueError(f"Alocação com ID {alocacao_id} não encontrada")
            planejamentos = await self.repository.list_by_alocacao(alocacao_id, ano)
            logger.info(f"[list_by_alocacao] {len(planejamentos)} planejamentos encontrados para alocacao_id={alocacao_id}")
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
            logger.debug(f"[list_by_alocacao] Resultado formatado: {result}")
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
        
        Args:
            recurso_id: ID do recurso
            ano: Ano dos planejamentos
            mes_inicio: Mês inicial (1-12)
            mes_fim: Mês final (1-12)
            
        Returns:
            List[Dict[str, Any]]: Lista de planejamentos
        """
        return await self.repository.list_by_recurso_periodo(recurso_id, ano, mes_inicio, mes_fim)
    
    async def delete_planejamento(self, planejamento_id: int) -> None:
        """
        Remove um planejamento de horas.
        
        Args:
            planejamento_id: ID do planejamento
            
        Raises:
            ValueError: Se o planejamento não for encontrado
        """
        logger.debug(f"[DELETE DEBUG] Conectando ao banco para deletar planejamento_id={planejamento_id}")
        logger.info(f"[delete_planejamento] Tentando deletar planejamento_id={planejamento_id}")
        result = await self.repository.db.execute(select(HorasPlanejadas).filter(HorasPlanejadas.id == planejamento_id))
        planejamento = result.scalars().first()
        if not planejamento:
            logger.warning(f"[delete_planejamento] Planejamento com ID {planejamento_id} não encontrado usando filtro!")
            raise ValueError(f"Planejamento com ID {planejamento_id} não encontrado")
        logger.info(f"[delete_planejamento] Planejamento encontrado via filtro: {planejamento}")
        await self.repository.delete(planejamento_id)
        logger.info(f"[delete_planejamento] Planejamento deletado com sucesso!")

    async def salvar_alteracoes_matriz(self, payload: MatrizPlanejamentoUpdate) -> None:
        logger = logging.getLogger(__name__)
        logger.info("--- INICIANDO salvar_alteracoes_matriz ---")
        try:
            for i, projeto_update in enumerate(payload.alteracoes_projetos):
                logger.info(f"--- Processando projeto {i+1}/{len(payload.alteracoes_projetos)}: ID {projeto_update.projeto_id} ---")

                # 1. Encontrar a alocação ativa
                logger.info(f"Buscando alocação ativa para recurso {payload.recurso_id} e projeto {projeto_update.projeto_id}")
                alocacao = await self.alocacao_repository.get_active_by_recurso_projeto(
                    recurso_id=payload.recurso_id,
                    projeto_id=projeto_update.projeto_id
                )
                logger.info(f"Alocação encontrada: {alocacao}")

                if not alocacao:
                    logger.error(f"Alocação ativa não encontrada para o recurso ID {payload.recurso_id} e projeto ID {projeto_update.projeto_id}")
                    raise ValueError(f"Alocação ativa não encontrada para o recurso ID {payload.recurso_id} e projeto ID {projeto_update.projeto_id}")

                alocacao_id = alocacao["id"]
                logger.info(f"ID da alocação: {alocacao_id}")

                # 2. Atualizar os dados da alocação
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
                    logger.info(f"Alocação {alocacao_id} atualizada.")

                # 3. Criar ou atualizar as horas planejadas para cada mês
                for j, planejamento_mensal in enumerate(projeto_update.planejamento_mensal):
                    logger.info(f"Processando planejamento {j+1}/{len(projeto_update.planejamento_mensal)}: Ano {planejamento_mensal.ano}, Mês {planejamento_mensal.mes}")
                    await self.create_or_update_planejamento(
                        alocacao_id=alocacao_id,
                        ano=planejamento_mensal.ano,  # <-- ALTERAÇÃO PRINCIPAL AQUI
                        mes=planejamento_mensal.mes,
                        horas_planejadas=planejamento_mensal.horas_planejadas
                    )
                    logger.info(f"Planejamento para o ano/mês {planejamento_mensal.ano}/{planejamento_mensal.mes} concluído.")
            logger.info("--- FINALIZADO salvar_alteracoes_matriz com SUCESSO ---")
        except Exception as e:
            logger.error(f"ERRO FATAL em salvar_alteracoes_matriz: {e}", exc_info=True)
            raise