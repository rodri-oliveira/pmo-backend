from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.repositories.planejamento_horas_repository import PlanejamentoHorasRepository
from app.repositories.alocacao_repository import AlocacaoRepository
from app.repositories.horas_disponiveis_repository import HorasDisponiveisRepository

class PlanejamentoHorasService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = PlanejamentoHorasRepository(db)
        self.alocacao_repository = AlocacaoRepository(db)
        self.horas_disponiveis_repository = HorasDisponiveisRepository(db)
    
    def create_or_update_planejamento(self, alocacao_id: int, ano: int, mes: int, horas_planejadas: float) -> Dict[str, Any]:
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
        alocacao = self.alocacao_repository.get(alocacao_id)
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
        horas_disponiveis = self.horas_disponiveis_repository.get_by_recurso_ano_mes(recurso_id, ano, mes)
        
        if horas_disponiveis:
            # Se houver configuração de horas disponíveis, verificar limite
            total_planejado = self.repository.get_total_horas_planejadas_por_recurso_mes(recurso_id, ano, mes)
            total_planejado = total_planejado or 0
            
            # Subtrair horas do planejamento atual se for atualização
            planejamento_atual = self.repository.get_by_alocacao_ano_mes(alocacao_id, ano, mes)
            if planejamento_atual:
                total_planejado -= float(planejamento_atual.horas_planejadas)
            
            # Verificar se o novo total não excede o disponível
            if total_planejado + horas_planejadas > float(horas_disponiveis.horas_disponiveis_mes):
                raise ValueError(
                    f"Total de horas planejadas ({total_planejado + horas_planejadas}) excede "
                    f"o disponível para o recurso ({horas_disponiveis.horas_disponiveis_mes}) "
                    f"no mês {mes}/{ano}"
                )
        
        # Criar ou atualizar o planejamento
        planejamento = self.repository.create_or_update(alocacao_id, ano, mes, horas_planejadas)
        
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
    
    def get_planejamento(self, alocacao_id: int, ano: int, mes: int) -> Optional[dict]:
        """
        Obtém o planejamento de horas para uma alocação em um mês específico.
        
        Args:
            alocacao_id: ID da alocação
            ano: Ano do planejamento
            mes: Mês do planejamento (1-12)
            
        Returns:
            dict: Dados do planejamento, ou None se não encontrado
        """
        return self.repository.get_by_alocacao_ano_mes(alocacao_id, ano, mes)
    
    def list_by_alocacao(self, alocacao_id: int) -> List[Dict[str, Any]]:
        """
        Lista todos os planejamentos de uma alocação.
        
        Args:
            alocacao_id: ID da alocação
            
        Returns:
            List[Dict[str, Any]]: Lista de planejamentos
        """
        # Verificar se a alocação existe
        alocacao = self.alocacao_repository.get(alocacao_id)
        if not alocacao:
            raise ValueError(f"Alocação com ID {alocacao_id} não encontrada")
        
        planejamentos = self.repository.list_by_alocacao(alocacao_id)
        
        # Formatar resultado
        return [{
            "id": p.id,
            "alocacao_id": p.alocacao_id,
            "projeto_id": alocacao.projeto_id,
            "recurso_id": alocacao.recurso_id,
            "ano": p.ano,
            "mes": p.mes,
            "horas_planejadas": float(p.horas_planejadas)
        } for p in planejamentos]
    
    def list_by_recurso_periodo(self, recurso_id: int, ano: int, mes_inicio: int = 1, mes_fim: int = 12) -> List[Dict[str, Any]]:
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
        return self.repository.list_by_recurso_periodo(recurso_id, ano, mes_inicio, mes_fim)
    
    def delete_planejamento(self, planejamento_id: int) -> None:
        """
        Remove um planejamento de horas.
        
        Args:
            planejamento_id: ID do planejamento
            
        Raises:
            ValueError: Se o planejamento não for encontrado
        """
        planejamento = self.repository.get(planejamento_id)
        if not planejamento:
            raise ValueError(f"Planejamento com ID {planejamento_id} não encontrado")
        
        self.repository.delete(planejamento_id) 