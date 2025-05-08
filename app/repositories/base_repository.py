from typing import Any, Dict, Generic, List, Optional, Type, TypeVar, Union
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.db.orm_models import Base

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """
    Repositório base com operações comuns para todos os modelos.
    """
    
    def __init__(self, db: Session, model: Type[T]):
        """
        Inicializa o repositório com uma sessão do banco de dados e o modelo.
        
        Args:
            db: Sessão do banco de dados
            model: Classe do modelo SQLAlchemy
        """
        self.db = db
        self.model = model
    
    def get(self, id: Any) -> Optional[T]:
        """
        Busca um registro pelo ID.
        
        Args:
            id: ID do registro
            
        Returns:
            Registro encontrado ou None
        """
        return self.db.query(self.model).filter(self.model.id == id).first()
    
    def get_all(self) -> List[T]:
        """
        Busca todos os registros.
        
        Returns:
            Lista de registros
        """
        return self.db.query(self.model).all()
    
    def create(self, obj_in: Dict[str, Any]) -> T:
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
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def update(self, id: Any, obj_in: Dict[str, Any]) -> Optional[T]:
        """
        Atualiza um registro existente.
        
        Args:
            id: ID do registro
            obj_in: Dados atualizados
            
        Returns:
            Registro atualizado ou None se não encontrado
            
        Raises:
            SQLAlchemyError: Se ocorrer um erro ao atualizar o registro
        """
        try:
            obj = self.get(id)
            if obj is None:
                return None
                
            for key, value in obj_in.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
                    
            self.db.add(obj)
            self.db.commit()
            self.db.refresh(obj)
            return obj
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def delete(self, id: Any) -> bool:
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
            obj = self.get(id)
            if obj is None:
                return False
                
            self.db.delete(obj)
            self.db.commit()
            return True
        except SQLAlchemyError as e:
            self.db.rollback()
            raise e
    
    def filter_by(self, **kwargs) -> List[T]:
        """
        Filtra registros por condições específicas.
        
        Args:
            **kwargs: Condições de filtro
            
        Returns:
            Lista de registros que atendem às condições
        """
        return self.db.query(self.model).filter_by(**kwargs).all()

    def list(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Lista entidades com paginação e filtros opcionais."""
        query = self.db.query(self.model)
        
        # Aplicar filtros
        for field, value in filters.items():
            if value is not None and hasattr(self.model, field):
                query = query.filter(getattr(self.model, field) == value)
        
        # Aplicar paginação
        return query.offset(skip).limit(limit).all()
    
    def delete_logic(self, id: int) -> bool:
        """
        Remove uma entidade.
        Se a entidade tiver um campo 'ativo', faz exclusão lógica.
        Caso contrário, faz exclusão física.
        
        Returns:
            bool: True se a operação foi bem-sucedida, False se a entidade não foi encontrada
        """
        entity = self.get(id)
        if entity is None:
            return False
        
        # Verificar se o modelo suporta exclusão lógica
        if hasattr(entity, "ativo"):
            # Exclusão lógica
            setattr(entity, "ativo", False)
            self.db.commit()
        else:
            # Exclusão física
            self.db.delete(entity)
            self.db.commit()
        
        return True 