from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, and_

from app.domain.models.equipe_model import Equipe as DomainEquipe
from app.application.dtos.equipe_dtos import EquipeCreateDTO, EquipeUpdateDTO
from app.domain.repositories.equipe_repository import EquipeRepository
from app.infrastructure.database.equipe_sql_model import EquipeSQL
from datetime import datetime

class SQLAlchemyEquipeRepository(EquipeRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def get_by_id(self, equipe_id: int) -> Optional[DomainEquipe]:
        result = await self.db_session.execute(select(EquipeSQL).filter(EquipeSQL.id == equipe_id))
        equipe_sql = result.scalars().first()
        if equipe_sql:
            return DomainEquipe.model_validate(equipe_sql)
        return None

    async def get_by_nome_and_secao_id(self, nome: str, secao_id: int) -> Optional[DomainEquipe]:
        result = await self.db_session.execute(
            select(EquipeSQL).filter(and_(EquipeSQL.nome == nome, EquipeSQL.secao_id == secao_id))
        )
        equipe_sql = result.scalars().first()
        if equipe_sql:
            return DomainEquipe.model_validate(equipe_sql)
        return None

    async def get_all_by_secao_id(self, secao_id: int, skip: int = 0, limit: int = 100, apenas_ativos: bool = False) -> List[DomainEquipe]:
        query = select(EquipeSQL).filter(EquipeSQL.secao_id == secao_id)
        if apenas_ativos:
            query = query.filter(EquipeSQL.ativo == True)
        query = query.offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        equipes_sql = result.scalars().all()
        return [DomainEquipe.model_validate(equipe) for equipe in equipes_sql]

    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False) -> List[DomainEquipe]:
        query = select(EquipeSQL)
        if apenas_ativos:
            query = query.filter(EquipeSQL.ativo == True)
        query = query.offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        equipes_sql = result.scalars().all()
        return [DomainEquipe.model_validate(equipe) for equipe in equipes_sql]

    async def create(self, equipe_create_dto: EquipeCreateDTO) -> DomainEquipe:
        new_equipe_sql = EquipeSQL(
            nome=equipe_create_dto.nome,
            descricao=equipe_create_dto.descricao,
            secao_id=equipe_create_dto.secao_id,
            data_criacao=datetime.utcnow(),
            data_atualizacao=datetime.utcnow(),
            ativo=True
        )
        self.db_session.add(new_equipe_sql)
        await self.db_session.commit()
        await self.db_session.refresh(new_equipe_sql)
        return DomainEquipe.model_validate(new_equipe_sql)

    async def update(self, equipe_id: int, equipe_update_dto: EquipeUpdateDTO) -> Optional[DomainEquipe]:
        equipe_sql = await self.db_session.get(EquipeSQL, equipe_id)
        if not equipe_sql:
            return None

        update_data = equipe_update_dto.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(equipe_sql, key, value)
            
        await self.db_session.commit()
        await self.db_session.refresh(equipe_sql)
        return DomainEquipe.model_validate(equipe_sql)

    async def delete(self, equipe_id: int) -> Optional[DomainEquipe]:
        equipe_to_delete_sql = await self.db_session.get(EquipeSQL, equipe_id)
        if not equipe_to_delete_sql:
            return None
        
        equipe_domain = DomainEquipe.model_validate(equipe_to_delete_sql)
        await self.db_session.delete(equipe_to_delete_sql)
        await self.db_session.commit()
        return equipe_domain

