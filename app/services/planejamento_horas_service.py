from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.planejamento_horas_repository import PlanejamentoHorasRepository
import logging
from app.repositories.alocacao_repository import AlocacaoRepository
from app.repositories.horas_disponiveis_repository import HorasDisponiveisRepository

class PlanejamentoHorasService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repository = PlanejamentoHorasRepository(db)
        self.alocacao_repository = AlocacaoRepository(db)
        self.horas_disponiveis_repository = HorasDisponiveisRepository(db)
    
    async def create_or_update_planejamento(self, alocacao_id: int, ano: int, mes: int, horas_planejadas: float) -> Dict[str, Any]:
        """
        Cria ou atualiza o planejamento de horas para uma alocação em um mês específico.
        
        Args:
            alocacao_id: ID da alocação
            ano: Ano do planejamento
            mes: Mês do planejamento (1-12)
            horas_planejadas: Horas planejadas para o mês
            
        Returns:
            Dict[str, Any]: Dados do planejamento criado/atualizado
            
        Raises:
            ValueError: Se a alocação não existir ou se as horas excederem o disponível
        """
        # Verificar se a alocação existe
        alocacao = await self.alocacao_repository.get(alocacao_id)
        if not alocacao:
            raise ValueError(f"Alocação com ID {alocacao_id} não encontrada")
        
        # Verificar limites do mês (1-12)
        if mes < 1 or mes > 12:
            raise ValueError(f"Mês deve estar entre 1 e 12, recebido: {mes}")
        
        # Verificar se as horas planejadas são positivas
        if horas_planejadas < 0:
            raise ValueError(f"Horas planejadas devem ser positivas, recebido: {horas_planejadas}")
        
        # Verificar se as horas planejadas não excedem as horas disponíveis do recurso
        recurso_id = alocacao.recurso_id
        horas_disponiveis = await self.horas_disponiveis_repository.get_by_recurso_ano_mes(recurso_id, ano, mes)
        
        # Removido o bloqueio de excedente de horas disponíveis. Planejamentos podem ultrapassar o disponível.
        
        # Criar ou atualizar o planejamento
        planejamento = await self.repository.create_or_update(alocacao_id, ano, mes, horas_planejadas)
        
        # Retornar com dados adicionais
        return {
            "id": planejamento.id,
            "alocacao_id": planejamento.alocacao_id,
            "projeto_id": alocacao.projeto_id,
            "recurso_id": alocacao.recurso_id,
            "ano": planejamento.ano,
            "mes": planejamento.mes,
            "horas_planejadas": float(planejamento.horas_planejadas)
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
        planejamento = await self.repository.get(planejamento_id)
        if not planejamento:
            raise ValueError(f"Planejamento com ID {planejamento_id} não encontrado")
        
        await self.repository.delete(planejamento_id) 