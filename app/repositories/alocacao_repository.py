from typing import List, Optional
from datetime import date
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from app.db.orm_models import AlocacaoRecursoProjeto, Recurso, Projeto
from app.repositories.base_repository import BaseRepository

class AlocacaoRepository(BaseRepository[AlocacaoRecursoProjeto]):
    """Repositório para operações com a entidade AlocacaoRecursoProjeto."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, AlocacaoRecursoProjeto)
    
    async def get_by_recurso_projeto_data(self, recurso_id: int, projeto_id: int, data_inicio: date) -> Optional[AlocacaoRecursoProjeto]:
        """Obtém alocação pelo recurso, projeto e data de início."""
        query = select(AlocacaoRecursoProjeto).filter(
            AlocacaoRecursoProjeto.recurso_id == recurso_id,
            AlocacaoRecursoProjeto.projeto_id == projeto_id,
            AlocacaoRecursoProjeto.data_inicio_alocacao == data_inicio
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def list_by_recurso(self, recurso_id: int) -> List[AlocacaoRecursoProjeto]:
        """Lista alocações de um recurso."""
        query = select(AlocacaoRecursoProjeto).options(
            joinedload(AlocacaoRecursoProjeto.equipe),
            joinedload(AlocacaoRecursoProjeto.recurso),
            joinedload(AlocacaoRecursoProjeto.projeto)
        ).filter(
            AlocacaoRecursoProjeto.recurso_id == recurso_id
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def list_by_projeto(self, projeto_id: int) -> List[AlocacaoRecursoProjeto]:
        """Lista alocações de um projeto."""
        query = select(AlocacaoRecursoProjeto).options(
            joinedload(AlocacaoRecursoProjeto.equipe),
            joinedload(AlocacaoRecursoProjeto.recurso),
            joinedload(AlocacaoRecursoProjeto.projeto)
        ).filter(
            AlocacaoRecursoProjeto.projeto_id == projeto_id
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def list_by_periodo(self, data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> List[AlocacaoRecursoProjeto]:
        """
        Lista alocações em um período.
        Inclui alocações que: (começaram antes e terminaram depois) OU (começaram durante) OU (terminaram durante).
        """
        query = select(AlocacaoRecursoProjeto).options(
            joinedload(AlocacaoRecursoProjeto.equipe),
            joinedload(AlocacaoRecursoProjeto.recurso),
            joinedload(AlocacaoRecursoProjeto.projeto)
        )
        
        if data_inicio is not None and data_fim is not None:
            query = query.filter(
                or_(
                    # Começou antes e terminou depois (ou não terminou)
                    and_(
                        AlocacaoRecursoProjeto.data_inicio_alocacao <= data_fim,
                        or_(
                            AlocacaoRecursoProjeto.data_fim_alocacao == None,
                            AlocacaoRecursoProjeto.data_fim_alocacao >= data_inicio
                        )
                    ),
                    # Começou durante o período
                    and_(
                        AlocacaoRecursoProjeto.data_inicio_alocacao >= data_inicio,
                        AlocacaoRecursoProjeto.data_inicio_alocacao <= data_fim
                    ),
                    # Terminou durante o período
                    and_(
                        AlocacaoRecursoProjeto.data_fim_alocacao >= data_inicio,
                        AlocacaoRecursoProjeto.data_fim_alocacao <= data_fim
                    )
                )
            )
        elif data_inicio is not None:
            query = query.filter(
                or_(
                    AlocacaoRecursoProjeto.data_inicio_alocacao >= data_inicio,
                    AlocacaoRecursoProjeto.data_fim_alocacao >= data_inicio
                )
            )
        elif data_fim is not None:
            query = query.filter(
                or_(
                    AlocacaoRecursoProjeto.data_inicio_alocacao <= data_fim,
                    AlocacaoRecursoProjeto.data_fim_alocacao == None
                )
            )
        
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def list_active_with_details(self) -> List[AlocacaoRecursoProjeto]:
        """Lista alocações ativas com detalhes de recursos e projetos."""
        query = select(AlocacaoRecursoProjeto).options(
            joinedload(AlocacaoRecursoProjeto.equipe),
            joinedload(AlocacaoRecursoProjeto.recurso),
            joinedload(AlocacaoRecursoProjeto.projeto)
        ).filter(
            or_(
                AlocacaoRecursoProjeto.data_fim_alocacao == None,
                AlocacaoRecursoProjeto.data_fim_alocacao >= date.today()
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()