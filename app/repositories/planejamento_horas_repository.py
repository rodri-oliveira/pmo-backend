from typing import List, Optional, Dict, Any
from sqlalchemy import func, extract, and_, or_
from sqlalchemy.orm import Session, joinedload
from app.db.orm_models import HorasPlanejadas, AlocacaoRecursoProjeto
from app.repositories.base_repository import BaseRepository

class PlanejamentoHorasRepository(BaseRepository[HorasPlanejadas, int]):
    """Repositório para operações com a entidade HorasPlanejadas."""
    
    def __init__(self, db: Session):
        super().__init__(db, HorasPlanejadas)
    
    def get_by_alocacao_ano_mes(self, alocacao_id: int, ano: int, mes: int) -> Optional[HorasPlanejadas]:
        """Obtém planejamento por alocação, ano e mês."""
        return self.db.query(HorasPlanejadas).filter(
            HorasPlanejadas.alocacao_id == alocacao_id,
            HorasPlanejadas.ano == ano,
            HorasPlanejadas.mes == mes
        ).first()
    
    def create_or_update(self, alocacao_id: int, ano: int, mes: int, horas_planejadas: float) -> HorasPlanejadas:
        """Cria ou atualiza um planejamento de horas."""
        existing = self.get_by_alocacao_ano_mes(alocacao_id, ano, mes)
        
        if existing:
            # Atualizar existente
            existing.horas_planejadas = horas_planejadas
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Criar novo
            return self.create({
                "alocacao_id": alocacao_id,
                "ano": ano,
                "mes": mes,
                "horas_planejadas": horas_planejadas
            })
    
    def list_by_alocacao(self, alocacao_id: int) -> List[HorasPlanejadas]:
        """Lista todos os planejamentos de uma alocação."""
        return self.db.query(HorasPlanejadas).filter(
            HorasPlanejadas.alocacao_id == alocacao_id
        ).order_by(HorasPlanejadas.ano, HorasPlanejadas.mes).all()
    
    def list_by_recurso_periodo(self, recurso_id: int, ano: int, mes_inicio: int = 1, mes_fim: int = 12) -> List[Dict[str, Any]]:
        """Lista planejamentos de um recurso em um período."""
        query = self.db.query(
            HorasPlanejadas,
            AlocacaoRecursoProjeto
        ).join(
            AlocacaoRecursoProjeto,
            HorasPlanejadas.alocacao_id == AlocacaoRecursoProjeto.id
        ).filter(
            AlocacaoRecursoProjeto.recurso_id == recurso_id,
            HorasPlanejadas.ano == ano,
            HorasPlanejadas.mes >= mes_inicio,
            HorasPlanejadas.mes <= mes_fim
        ).order_by(
            HorasPlanejadas.mes
        )
        
        result = query.all()
        
        # Converter para formato mais amigável
        return [{
            "id": plano.id,
            "alocacao_id": plano.alocacao_id,
            "projeto_id": alocacao.projeto_id,
            "recurso_id": alocacao.recurso_id,
            "ano": plano.ano,
            "mes": plano.mes,
            "horas_planejadas": plano.horas_planejadas
        } for plano, alocacao in result]
    
    def get_total_horas_planejadas_por_recurso_mes(self, recurso_id: int, ano: int, mes: int) -> Optional[float]:
        """Obtém o total de horas planejadas para um recurso em um mês específico."""
        result = self.db.query(
            func.sum(HorasPlanejadas.horas_planejadas).label("total_horas")
        ).join(
            AlocacaoRecursoProjeto,
            HorasPlanejadas.alocacao_id == AlocacaoRecursoProjeto.id
        ).filter(
            AlocacaoRecursoProjeto.recurso_id == recurso_id,
            HorasPlanejadas.ano == ano,
            HorasPlanejadas.mes == mes
        ).scalar()
        
        return result 