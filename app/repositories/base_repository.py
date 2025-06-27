from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError
from app.db.orm_models import Base

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """
    Repositório base com operações comuns para todos os modelos.
    """
    
    def __init__(self, db: AsyncSession, model: Type[T]):
        """
        Inicializa o repositório com uma sessão do banco de dados e o modelo.
        
        Args:
            db: Sessão do banco de dados assíncrona
            model: Classe do modelo SQLAlchemy
        """
        self.db = db
        self.model = model
    
    async def get(self, id: Any) -> Optional[T]:
        """
        Busca um registro pelo ID.
        
        Args:
            id: ID do registro
            
        Returns:
            Optional[T]: O registro encontrado ou None
        """
        return await self.db.get(self.model, id)
    
    async def get_all(self) -> List[T]:
        """
        Busca todos os registros.
        
        Returns:
            Lista de registros
        """
        query = select(self.model)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def create(self, obj_in: Dict[str, Any]) -> T:
        """
        Cria um novo registro.
        
        Args:
            obj_in: Dados do novo registro
            
        Returns:
            Registro criado
            
        Raises:
            SQLAlchemyError: Se ocorrer um erro ao criar o registro
        """
        try:
            obj = self.model(**obj_in)
            self.db.add(obj)
            # Em cenários onde a transação é controlada externamente (service layer
            # usando `async with db.begin()`), não devemos fazer commit/rollback aqui.
            # Apenas flush para obter PK e refresh para garantir dados atualizados.
            await self.db.flush()
            await self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            # O rollback será conduzido pela camada de serviço se ela estiver
            # gerenciando a transação.
            raise e
    
    async def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[dict]:
        """
        Atualiza um registro existente e retorna um dicionário simples (evita problemas de ORM async).
        
        Args:
            id: ID do registro
            obj_in: Dados atualizados
            
        Returns:
            Dicionário com os dados atualizados ou None se não encontrado
        """
        try:
            obj = await self.get(id)
            if obj is None:
                return None
                
            for key, value in obj_in.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
                    
            await self.db.commit()
            # Recarrega o objeto 
            await self.db.refresh(obj)
            return obj
        except Exception as e:
            await self.db.rollback()
            raise e
    
    async def delete(self, id: Any) -> bool:
        """
        Remove um registro.
        
        Args:
            id: ID do registro
            
        Returns:
            True se removido com sucesso, False se não encontrado
            
        Raises:
            SQLAlchemyError: Se ocorrer um erro ao remover o registro
        """
        try:
            obj = await self.get(id)
            if obj is None:
                return False
                
            await self.db.delete(obj)
            await self.db.commit()
            return True
        except SQLAlchemyError as e:
            await self.db.rollback()
            raise e
    
    async def filter_by(self, **kwargs) -> List[T]:
        """
        Filtra registros por condições específicas.
        
        Args:
            **kwargs: Condições de filtro
            
        Returns:
            Lista de registros que atendem às condições
        """
        query = select(self.model).filter_by(**kwargs)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def list(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Lista entidades com paginação e filtros opcionais."""
        query = select(self.model)
        
        # Aplicar filtros
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        
        # Aplicar paginação
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def delete_logic(self, id: int) -> bool:
        """
        Remove uma entidade.
        Se a entidade tiver um campo 'ativo', faz exclusão lógica.
        Caso contrário, faz exclusão física.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False se a entidade não foi encontrada
        """
        entity = await self.get(id)
        if entity is None:
            return False
        
        # Verificar se o modelo suporta exclusão lógica
        if hasattr(entity, "ativo"):
            # Exclusão lógica
            setattr(entity, "ativo", False)
            await self.db.commit()
        else:
            # Exclusão física
            await self.db.delete(entity)
            await self.db.commit()
        
        return True