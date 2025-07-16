import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, func
from datetime import datetime, timezone
from sqlalchemy.orm import class_mapper
from fastapi import HTTPException
from app.domain.models.status_projeto_model import StatusProjeto as DomainStatusProjeto
from app.application.dtos.status_projeto_dtos import StatusProjetoCreateDTO, StatusProjetoUpdateDTO
from app.domain.repositories.status_projeto_repository import StatusProjetoRepository
from app.infrastructure.database.status_projeto_sql_model import StatusProjetoSQL
from app.utils.dependency_checker import check_dependents

logger = logging.getLogger(__name__)


class SQLAlchemyStatusProjetoRepository(StatusProjetoRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    def _to_dict(self, obj):
        """Converte um objeto SQLAlchemy para dicionário"""
        if obj is None:
            return None
        return {c.key: getattr(obj, c.key) for c in class_mapper(obj.__class__).columns}

    async def get_by_id(self, status_id: int) -> Optional[DomainStatusProjeto]:
        try:
            result = await self.db_session.execute(select(StatusProjetoSQL).filter(StatusProjetoSQL.id == status_id, StatusProjetoSQL.ativo == True))
            status_sql = result.scalars().first()
            if status_sql:
                return DomainStatusProjeto.model_validate(self._to_dict(status_sql))
            return None
        except Exception as e:
            # Log the error
            logger.error(f"Erro ao buscar status por ID: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar status de projeto: {str(e)}"
            )

    async def get_by_nome(self, nome: str) -> Optional[DomainStatusProjeto]:
        try:
            result = await self.db_session.execute(select(StatusProjetoSQL).filter(StatusProjetoSQL.nome == nome, StatusProjetoSQL.ativo == True))
            status_sql = result.scalars().first()
            if status_sql:
                return DomainStatusProjeto.model_validate(self._to_dict(status_sql))
            return None
        except Exception as e:
            # Log the error
            logger.error(f"Erro ao buscar status por nome: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar status de projeto por nome: {str(e)}"
            )

    async def get_all(self, skip: int = 0, limit: int = 100, ativo: Optional[bool] = None) -> List[DomainStatusProjeto]:
        try:
            query = select(StatusProjetoSQL)

            if ativo is not None:
                query = query.filter(StatusProjetoSQL.ativo == ativo)

            query = query.order_by(StatusProjetoSQL.ordem_exibicao, StatusProjetoSQL.nome).offset(skip).limit(limit)
            result = await self.db_session.execute(query)
            status_sql = result.scalars().all()
            return [DomainStatusProjeto.model_validate(self._to_dict(s)) for s in status_sql]
        except Exception as e:
            # Log the error
            logger.error(f"Erro ao listar status: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao listar status de projeto: {str(e)}"
            )

    async def create(self, status_create_dto: StatusProjetoCreateDTO) -> DomainStatusProjeto:
        try:
            agora = datetime.now(timezone.utc)
            new_status_sql = StatusProjetoSQL(
                **status_create_dto.model_dump(),
                data_criacao=agora,
                data_atualizacao=agora
            )
            self.db_session.add(new_status_sql)
            await self.db_session.commit()
            await self.db_session.refresh(new_status_sql)
            return DomainStatusProjeto.model_validate(self._to_dict(new_status_sql))
        except HTTPException as e:
            await self.db_session.rollback()
            raise e
        except Exception as e:
            await self.db_session.rollback()
            # Log the error
            logger.error(f"Erro ao criar status: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao criar status de projeto: {str(e)}"
            )

    async def update(self, status_id: int, status_update_dto: StatusProjetoUpdateDTO) -> Optional[DomainStatusProjeto]:
        try:
            status_sql = await self.db_session.get(StatusProjetoSQL, status_id)
            if not status_sql:
                return None

            # Verificar se o nome já existe (se estiver sendo atualizado)
            if status_update_dto.nome is not None and status_update_dto.nome != status_sql.nome:
                existing_status = await self.get_by_nome(status_update_dto.nome)
                if existing_status:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Já existe um status de projeto com o nome '{status_update_dto.nome}'."
                    )

            # Verificar se a ordem_exibicao já existe (se estiver sendo atualizada)
            if status_update_dto.ordem_exibicao is not None and status_update_dto.ordem_exibicao != status_sql.ordem_exibicao:
                query = select(StatusProjetoSQL).filter(
                    StatusProjetoSQL.ordem_exibicao == status_update_dto.ordem_exibicao,
                    StatusProjetoSQL.id != status_id,
                    StatusProjetoSQL.ativo == True
                )
                result = await self.db_session.execute(query)
                existing_order = result.scalars().first()
                
                if existing_order:
                    # Opção 1: Encontrar a próxima ordem disponível
                    max_order_query = select(StatusProjetoSQL).order_by(StatusProjetoSQL.ordem_exibicao.desc())
                    max_order_result = await self.db_session.execute(max_order_query)
                    max_order_status = max_order_result.scalars().first()
                    
                    next_order = 1
                    if max_order_status and max_order_status.ordem_exibicao:
                        next_order = max_order_status.ordem_exibicao + 1
                    
                    # Atualizar o DTO com a nova ordem
                    status_update_dto.ordem_exibicao = next_order

            update_data = status_update_dto.model_dump(exclude_unset=True)
            # Atualizar a data de atualização manualmente
            update_data["data_atualizacao"] = datetime.now(timezone.utc)
            
            for key, value in update_data.items():
                setattr(status_sql, key, value)
                
            await self.db_session.commit()
            await self.db_session.refresh(status_sql)
            
            # Converter para dicionário antes de validar
            status_dict = self._to_dict(status_sql)
            return DomainStatusProjeto.model_validate(status_dict)
        except HTTPException:
            # Repassar exceções HTTP
            raise
        except Exception as e:
            # Log the error
            logger.error(f"Erro ao atualizar status: {str(e)}")
            # Rollback da transação em caso de erro
            await self.db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao atualizar status de projeto: {str(e)}"
            )

    async def get_max_ordem_exibicao(self) -> Optional[int]:
        try:
            result = await self.db_session.execute(select(func.max(StatusProjetoSQL.ordem_exibicao)).where(StatusProjetoSQL.ativo == True))
            max_order = result.scalar_one_or_none()
            return max_order
        except Exception as e:
            logger.error(f"Erro ao buscar a ordem de exibição máxima: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar a ordem de exibição máxima: {str(e)}"
            )

    async def get_by_nome_including_inactive(self, nome: str) -> Optional[DomainStatusProjeto]:
        try:
            result = await self.db_session.execute(select(StatusProjetoSQL).filter(StatusProjetoSQL.nome == nome))
            status_sql = result.scalars().first()
            if status_sql:
                return DomainStatusProjeto.model_validate(self._to_dict(status_sql))
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar status por nome (incluindo inativos): {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar status de projeto por nome: {str(e)}"
            )

    async def get_by_ordem_exibicao_including_inactive(self, ordem_exibicao: int) -> Optional[DomainStatusProjeto]:
        try:
            result = await self.db_session.execute(select(StatusProjetoSQL).filter(StatusProjetoSQL.ordem_exibicao == ordem_exibicao))
            status_sql = result.scalars().first()
            if status_sql:
                return DomainStatusProjeto.model_validate(self._to_dict(status_sql))
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar status por ordem_exibicao (incluindo inativos): {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao buscar status de projeto por ordem de exibição: {str(e)}"
            )

    async def delete(self, status_id: int) -> Optional[DomainStatusProjeto]:
        try:
            # Importar ProjetoSQL aqui para evitar importação circular
            from app.infrastructure.database.projeto_sql_model import ProjetoSQL

            # Opcional: Verificar dependências. Com soft delete, isso pode ser um aviso em vez de um bloqueio.
            await check_dependents(
                self.db_session,
                ProjetoSQL,
                "status_projeto_id",
                status_id,
                "projetos vinculados a este status"
            )

            # Buscar o status ativo pelo ID
            result = await self.db_session.execute(
                select(StatusProjetoSQL).filter(StatusProjetoSQL.id == status_id)
            )
            status_sql = result.scalars().first()

            if not status_sql or not status_sql.ativo:
                return None

            # Marcar como inativo (soft delete)
            status_sql.ativo = False
            status_sql.data_atualizacao = datetime.now(timezone.utc)

            await self.db_session.commit()
            await self.db_session.refresh(status_sql)

            return DomainStatusProjeto.model_validate(self._to_dict(status_sql))
        except HTTPException:
            await self.db_session.rollback()
            raise
        except Exception as e:
            await self.db_session.rollback()
            logger.error(f"Erro ao excluir status: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao excluir status de projeto: {str(e)}"
            )
            await self.db_session.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Erro ao excluir status de projeto: {str(e)}"
            )
