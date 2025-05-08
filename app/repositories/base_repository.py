from typing import List, Optional, Dict, Any, Generic, TypeVar, Type
from sqlalchemy.orm import Session
from app.db.orm_models import Base

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Implementação base para repositórios."""
    
    def __init__(self, db: Session, model_class: Type[T]):
        self.db = db
        self.model_class = model_class
    
    def get(self, id: int) -> Optional[T]:
        """Obtém uma entidade pelo ID."""
        return self.db.query(self.model_class).filter(self.model_class.id == id).first()
    
    def list(self, skip: int = 0, limit: int = 100, **filters) -> List[T]:
        """Lista entidades com paginação e filtros opcionais."""
        query = self.db.query(self.model_class)
        
        # Aplicar filtros
        for field, value in filters.items():
            if value is not None and hasattr(self.model_class, field):
                query = query.filter(getattr(self.model_class, field) == value)
        
        # Aplicar paginação
        return query.offset(skip).limit(limit).all()
    
    def create(self, data: Dict[str, Any]) -> T:
        """Cria uma nova entidade."""
        entity = self.model_class(**data)
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def update(self, id: int, data: Dict[str, Any]) -> Optional[T]:
        """Atualiza uma entidade existente."""
        entity = self.get(id)
        if entity is None:
            return None
        
        # Atualizar os campos
        for key, value in data.items():
            if hasattr(entity, key) and value is not None:
                setattr(entity, key, value)
        
        self.db.commit()
        self.db.refresh(entity)
        return entity
    
    def delete(self, id: int) -> bool:
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