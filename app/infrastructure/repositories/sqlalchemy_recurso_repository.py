from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update as sqlalchemy_update, delete as sqlalchemy_delete, and_, or_
import traceback # Adicionado para logging detalhado
from datetime import datetime, timezone
from app.domain.models.recurso_model import Recurso as DomainRecurso
from app.application.dtos.recurso_dtos import RecursoCreateDTO, RecursoUpdateDTO
from app.domain.repositories.recurso_repository import RecursoRepository
from app.db.orm_models import Recurso
from app.utils.dependency_checker import check_dependents
from fastapi import HTTPException
from sqlalchemy import func
from app.db.orm_models import AlocacaoRecursoProjeto, HorasDisponiveisRH, Usuario, Apontamento

class SQLAlchemyRecursoRepository(RecursoRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def autocomplete(
        self,
        search: str,
        skip: int = 0,
        limit: int = 20,
        apenas_ativos: bool = False,
        equipe_id: Optional[int] = None
    ):
        from sqlalchemy import or_
        query = select(Recurso)
        search_filter = or_(
            Recurso.nome.ilike(f"%{search}%"),
            Recurso.email.ilike(f"%{search}%"),
            Recurso.matricula.ilike(f"%{search}%")
        )
        query = query.filter(search_filter)
        if apenas_ativos:
            query = query.filter(Recurso.ativo == True)
        if equipe_id is not None:
            query = query.filter(Recurso.equipe_principal_id == equipe_id)
        query = query.order_by(Recurso.nome.asc())
        query = query.offset(skip).limit(limit)
        result = await self.db_session.execute(query)
        recursos_sql = result.scalars().all()
        return [DomainRecurso.model_validate(recurso) for recurso in recursos_sql]

    async def get_by_id(self, recurso_id: int) -> Optional[DomainRecurso]:
        result = await self.db_session.execute(select(Recurso).filter(Recurso.id == recurso_id))
        recurso_sql = result.scalars().first()
        if recurso_sql:
            return DomainRecurso.model_validate(recurso_sql)
        return None

    async def get_by_email(self, email: str) -> Optional[DomainRecurso]:
        result = await self.db_session.execute(select(Recurso).filter(Recurso.email == email))
        recurso_sql = result.scalars().first()
        if recurso_sql:
            return DomainRecurso.model_validate(recurso_sql)
        return None

    async def get_by_matricula(self, matricula: str) -> Optional[DomainRecurso]:
        result = await self.db_session.execute(select(Recurso).filter(Recurso.matricula == matricula))
        recurso_sql = result.scalars().first()
        if recurso_sql:
            return DomainRecurso.model_validate(recurso_sql)
        return None

    async def get_by_jira_user_id(self, jira_user_id: str) -> Optional[DomainRecurso]:
        result = await self.db_session.execute(select(Recurso).filter(Recurso.jira_user_id == jira_user_id))
        recurso_sql = result.scalars().first()
        if recurso_sql:
            return DomainRecurso.model_validate(recurso_sql)
        return None

    async def get_all(self, skip: int = 0, limit: int = 100, apenas_ativos: bool = False, equipe_id: Optional[int] = None) -> List[DomainRecurso]:
        query = select(Recurso).filter(Recurso.equipe_principal_id.isnot(None)).order_by(Recurso.nome)
        if apenas_ativos:
            query = query.filter(Recurso.ativo == True)
        if equipe_id is not None:
            query = query.filter(Recurso.equipe_principal_id == equipe_id)
        
        query = query.offset(skip).limit(limit)
        
        try:
            result = await self.db_session.execute(query)
            recursos_sql = result.scalars().all()
            return [DomainRecurso.model_validate(recurso) for recurso in recursos_sql]
        except Exception as e:
            print(f"Erro ao executar query no get_all: {e}")
            traceback.print_exc()
            raise

    async def create(self, recurso_create_dto: RecursoCreateDTO) -> DomainRecurso:
        try:
            # Converter strings vazias para None (NULL no banco)
            data = recurso_create_dto.model_dump()
            for key, value in data.items():
                if isinstance(value, str) and (value == "" or value.upper() == "NULL"):
                    data[key] = None
                    
            now_naive = datetime.now().replace(microsecond=0, tzinfo=None)
            new_recurso_sql = Recurso(
                **data,
                data_criacao=now_naive,
                data_atualizacao=now_naive,
                ativo=True
            )
            self.db_session.add(new_recurso_sql)
            await self.db_session.commit()
            await self.db_session.refresh(new_recurso_sql)
            
            return DomainRecurso.model_validate(new_recurso_sql)
        except Exception as e:
            await self.db_session.rollback()
            print(f"Error creating recurso: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Erro ao criar recurso: {str(e)}")

    async def update(self, recurso_id: int, recurso_update_dto: RecursoUpdateDTO) -> Optional[DomainRecurso]:
        try:
            recurso_sql = await self.db_session.get(Recurso, recurso_id)
            if not recurso_sql:
                return None

            # Converter strings vazias para None (NULL no banco)
            update_data = recurso_update_dto.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                if isinstance(value, str) and (value == "" or value.upper() == "NULL"):
                    update_data[key] = None
            
            # Atualizar os campos
            for key, value in update_data.items():
                setattr(recurso_sql, key, value)
            
            recurso_sql.data_atualizacao = datetime.now().replace(microsecond=0, tzinfo=None)
            await self.db_session.commit()
            await self.db_session.refresh(recurso_sql)
            return DomainRecurso.model_validate(recurso_sql)
        except Exception as e:
            await self.db_session.rollback()
            print(f"Error updating recurso: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Erro ao atualizar recurso: {str(e)}")

    async def delete(self, recurso_id: int) -> Optional[DomainRecurso]:
        try:
            # Verificar dependências manualmente com consultas SQL diretas
            # Verificar alocações
            result = await self.db_session.execute(
                select(func.count()).select_from(AlocacaoRecursoProjeto).where(
                    AlocacaoRecursoProjeto.recurso_id == recurso_id
                )
            )
            if result.scalar_one() > 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Não é possível excluir pois existem alocações de recurso em projeto vinculados."
                )
                
            # Verificar horas disponíveis
            result = await self.db_session.execute(
                select(func.count()).select_from(HorasDisponiveisRH).where(
                    HorasDisponiveisRH.recurso_id == recurso_id
                )
            )
            if result.scalar_one() > 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Não é possível excluir pois existem horas disponíveis RH vinculadas."
                )
                
            # Verificar usuários
            result = await self.db_session.execute(
                select(func.count()).select_from(Usuario).where(
                    Usuario.recurso_id == recurso_id
                )
            )
            if result.scalar_one() > 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Não é possível excluir pois existem usuários vinculados."
                )
                
            # Verificar apontamentos
            result = await self.db_session.execute(
                select(func.count()).select_from(Apontamento).where(
                    Apontamento.recurso_id == recurso_id
                )
            )
            if result.scalar_one() > 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Não é possível excluir pois existem apontamentos vinculados."
                )

            # Buscar o recurso
            recurso_to_delete_sql = await self.db_session.get(Recurso, recurso_id)
            if not recurso_to_delete_sql:
                return None

            # Inativar o recurso em vez de deletar
            recurso_to_delete_sql.ativo = False
            recurso_to_delete_sql.data_atualizacao = datetime.now().replace(microsecond=0, tzinfo=None)
            await self.db_session.commit()
            await self.db_session.refresh(recurso_to_delete_sql)
            
            return DomainRecurso.model_validate(recurso_to_delete_sql)
        except HTTPException as e:
            # Propagar exceções HTTP (como 409 Conflict) para o service/rota
            raise e
        except Exception as e:
            # Logar e tratar outros erros
            await self.db_session.rollback()
            print(f"Error deleting recurso: {e}")
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Erro ao deletar recurso: {str(e)}")
