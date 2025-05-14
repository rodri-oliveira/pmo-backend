from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete
from datetime import datetime, timezone
from sqlalchemy.orm import class_mapper
from fastapi import HTTPException
from app.domain.models.status_projeto_model import StatusProjeto as DomainStatusProjeto
from app.application.dtos.status_projeto_dtos import StatusProjetoCreateDTO, StatusProjetoUpdateDTO
from app.domain.repositories.status_projeto_repository import StatusProjetoRepository
from app.infrastructure.database.status_projeto_sql_model import StatusProjetoSQL
from app.utils.dependency_checker import check_dependents

class SQLAlchemyStatusProjetoRepository(StatusProjetoRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    def _to_dict(self, obj):
        """Converte um objeto SQLAlchemy para dicionário"""
        if obj is None:
            return None
        return {c.key: getattr(obj, c.key) for c in class_mapper(obj.__class__).columns}

    async def get_by_id(self, status_id: int) -> Optional[DomainStatusProjeto]:
        result = await self.db_session.execute(select(StatusProjetoSQL).filter(StatusProjetoSQL.id == status_id))
        status_sql = result.scalars().first()
        if status_sql:
            return DomainStatusProjeto.model_validate(self._to_dict(status_sql))
        return None

    async def get_by_nome(self, nome: str) -> Optional[DomainStatusProjeto]:
        result = await self.db_session.execute(select(StatusProjetoSQL).filter(StatusProjetoSQL.nome == nome))
        status_sql = result.scalars().first()
        if status_sql:
            return DomainStatusProjeto.model_validate(self._to_dict(status_sql))
        return None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[DomainStatusProjeto]:
        query = select(StatusProjetoSQL).order_by(StatusProjetoSQL.ordem_exibicao, StatusProjetoSQL.nome).offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        status_sql = result.scalars().all()
        return [DomainStatusProjeto.model_validate(self._to_dict(s)) for s in status_sql]

    async def create(self, status_create_dto: StatusProjetoCreateDTO) -> DomainStatusProjeto:
        # Extrair dados do DTO
        data = status_create_dto.model_dump()
        
        # Adicionar manualmente as datas
        now = datetime.now()
        data["data_criacao"] = now
        data["data_atualizacao"] = now
        
        # Criar o objeto SQL e salvá-lo
        new_status_sql = StatusProjetoSQL(**data)
        self.db_session.add(new_status_sql)
        await self.db_session.commit()
        await self.db_session.refresh(new_status_sql)
        
        # Converter para dicionário antes de validar
        status_dict = self._to_dict(new_status_sql)
        return DomainStatusProjeto.model_validate(status_dict)

    async def update(self, status_id: int, status_update_dto: StatusProjetoUpdateDTO) -> Optional[DomainStatusProjeto]:
        status_sql = await self.db_session.get(StatusProjetoSQL, status_id)
        if not status_sql:
            return None

        update_data = status_update_dto.model_dump(exclude_unset=True)
        # Atualizar a data de atualização manualmente
        update_data["data_atualizacao"] = datetime.now()
        
        for key, value in update_data.items():
            setattr(status_sql, key, value)
            
        await self.db_session.commit()
        await self.db_session.refresh(status_sql)
        
        # Converter para dicionário antes de validar
        status_dict = self._to_dict(status_sql)
        return DomainStatusProjeto.model_validate(status_dict)

    async def delete_status_projeto(status_id: int, db: AsyncSession, status_projeto_repository):
        # Checa dependentes usando a função utilitária (já lança exceção se houver projetos vinculados)
        await check_dependents(db, ProjetoSQL, "status_projeto_id", status_id, "projetos vinculados a este status")

        # Executa o soft delete normalmente
        await status_projeto_repository.delete(status_id, db)
