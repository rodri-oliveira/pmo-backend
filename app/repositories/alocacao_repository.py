from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy import select, or_, update, func
from sqlalchemy.orm import noload, joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.orm_models import AlocacaoRecursoProjeto, Recurso, Projeto
from app.repositories.base_repository import BaseRepository

class AlocacaoRepository(BaseRepository[AlocacaoRecursoProjeto]):

    async def update(self, id: int, data: dict) -> None:
        """
        Sobrescreve o método base para usar uma instrução de atualização direta
        e não retornar o objeto ORM, evitando problemas de greenlet.
        """
        if not data:
            return

        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
        )
        await self.db.execute(query)
        await self.db.flush()

    """Repositório para operações com a entidade AlocacaoRecursoProjeto."""

    async def count(self, apenas_ativos: bool = True):
        """Conta alocações com opção de apenas ativos (data_fim >= hoje ou NULL)."""
        query = select(func.count()).select_from(AlocacaoRecursoProjeto)
        if apenas_ativos:
            query = query.filter(or_(
                AlocacaoRecursoProjeto.data_fim_alocacao == None,
                AlocacaoRecursoProjeto.data_fim_alocacao >= date.today()
            ))
        result = await self.db.execute(query)
        return result.scalar_one()

    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = True):
        """Retorna lista paginada de alocações."""
        query = select(AlocacaoRecursoProjeto).options(
            joinedload(AlocacaoRecursoProjeto.equipe),
            joinedload(AlocacaoRecursoProjeto.recurso),
            joinedload(AlocacaoRecursoProjeto.projeto),
            joinedload(AlocacaoRecursoProjeto.status_alocacao)
        )
        if apenas_ativos:
            query = query.filter(or_(
                AlocacaoRecursoProjeto.data_fim_alocacao == None,
                AlocacaoRecursoProjeto.data_fim_alocacao >= date.today()
            ))
        query = query.order_by(AlocacaoRecursoProjeto.data_inicio_alocacao.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    """Repositório para operações com a entidade AlocacaoRecursoProjeto."""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, AlocacaoRecursoProjeto)
    
    async def update(self, id: int, data: dict) -> AlocacaoRecursoProjeto:
        """
        Sobrescreve o método base para usar uma instrução de atualização direta,
        evitando problemas de sessão com greenlet.
        """
        if not data:
            # Retorna o objeto existente sem fazer nada se não houver dados
            return await self.get_by_id(id)

        query = (
            update(self.model)
            .where(self.model.id == id)
            .values(**data)
            .returning(self.model)
        )
        result = await self.db.execute(query)
        await self.db.flush()
        return result.scalars().first()
    
    async def get_by_recurso_projeto_data(self, recurso_id: int, projeto_id: int, data_inicio: date) -> Optional[AlocacaoRecursoProjeto]:
        """Obtém alocação pelo recurso, projeto e data de início."""
        query = select(AlocacaoRecursoProjeto).filter(
            AlocacaoRecursoProjeto.recurso_id == recurso_id,
            AlocacaoRecursoProjeto.projeto_id == projeto_id,
            AlocacaoRecursoProjeto.data_inicio_alocacao == data_inicio
        )
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def find_overlapping_allocations(
        self, recurso_id: int, data_inicio: date, data_fim: date, exclude_alocacao_id: Optional[int] = None
    ) -> List[AlocacaoRecursoProjeto]:
        """Encontra alocações para um recurso que se sobrepõem a um determinado período."""
        # Condição base: a nova alocação começa antes que a existente termine,
        # E a nova alocação termina depois que a existente começa.
        # Isso cobre todos os casos de sobreposição.
        query = select(self.model).filter(
            self.model.recurso_id == recurso_id,
            # A nova alocação deve começar antes do fim da existente.
            # Se a existente não tem data de fim (NULL), ela é contínua.
            self.model.data_inicio_alocacao <= data_fim,
            # A nova alocação deve terminar após o início da existente.
            or_(
                self.model.data_fim_alocacao == None,
                self.model.data_fim_alocacao >= data_inicio
            )
        )

        # Se estivermos atualizando uma alocação, devemos excluí-la da verificação
        # para não conflitar com ela mesma.
        if exclude_alocacao_id is not None:
            query = query.filter(self.model.id != exclude_alocacao_id)

        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def list_by_recurso(self, recurso_id: int) -> List[AlocacaoRecursoProjeto]:
        """Lista alocações de um recurso."""
        query = select(AlocacaoRecursoProjeto).options(
            joinedload(AlocacaoRecursoProjeto.equipe),
            joinedload(AlocacaoRecursoProjeto.recurso),
            joinedload(AlocacaoRecursoProjeto.projeto),
            joinedload(AlocacaoRecursoProjeto.status_alocacao)
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
            joinedload(AlocacaoRecursoProjeto.projeto),
            joinedload(AlocacaoRecursoProjeto.status_alocacao)
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
            joinedload(AlocacaoRecursoProjeto.projeto),
            joinedload(AlocacaoRecursoProjeto.status_alocacao)
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
            joinedload(AlocacaoRecursoProjeto.projeto),
            joinedload(AlocacaoRecursoProjeto.status_alocacao)
        ).filter(
            or_(
                AlocacaoRecursoProjeto.data_fim_alocacao == None,
                AlocacaoRecursoProjeto.data_fim_alocacao >= date.today()
            )
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_latest_by_recurso_projeto(self, recurso_id: int, projeto_id: int) -> Optional[Dict[str, Any]]:
        """Obtém a alocação mais recente para um recurso e projeto, independentemente de estar ativa."""
        query = select(self.model).filter(
            self.model.recurso_id == recurso_id,
            self.model.projeto_id == projeto_id
        ).order_by(self.model.data_inicio_alocacao.desc())
        
        result = await self.db.execute(query)
        instance = result.scalars().first()
        return instance.to_dict() if instance else None

    async def get_active_by_recurso_projeto(self, recurso_id: int, projeto_id: int) -> Optional[Dict[str, Any]]:
        """Obtém a alocação ativa mais recente para um recurso e projeto e retorna como dict."""
        query = select(self.model).filter(
            self.model.recurso_id == recurso_id,
            self.model.projeto_id == projeto_id,
            or_(
                self.model.data_fim_alocacao == None,
                self.model.data_fim_alocacao >= date.today()
            )
        ).order_by(self.model.data_inicio_alocacao.desc())

        result = await self.db.execute(query)
        instance = result.scalars().first()
        return instance.to_dict() if instance else None

    async def get_ids_by_id(self, alocacao_id: int) -> Optional[Dict[str, int]]:
        """ Obtém os IDs de recurso e projeto de uma alocação pelo seu ID. """
        query = select(
            self.model.recurso_id,
            self.model.projeto_id
        ).filter(self.model.id == alocacao_id)
        
        result = await self.db.execute(query)
        record = result.first()
        
        if record:
            return {
                "recurso_id": record.recurso_id,
                "projeto_id": record.projeto_id
            }
        return None