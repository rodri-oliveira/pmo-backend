from typing import List, Optional
from sqlalchemy.orm import Session
from app.api.dtos.secao_schema import SecaoCreateSchema, SecaoUpdateSchema, SecaoResponseSchema
from app.repositories.secao_repository import SecaoRepository
from app.db.orm_models import Secao

class SecaoService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = SecaoRepository(db)
    
    def create(self, secao_data: SecaoCreateSchema) -> SecaoResponseSchema:
        """
        Cria uma nova seção.
        
        Args:
            secao_data: Dados da seção a ser criada
            
        Returns:
            SecaoResponseSchema: Dados da seção criada
            
        Raises:
            ValueError: Se o nome da seção já existir
        """
        # Verificar se já existe seção com esse nome
        if self.repository.get_by_nome(secao_data.nome):
            raise ValueError(f"Já existe uma seção com o nome '{secao_data.nome}'")
        
        # Criar nova seção
        secao = self.repository.create(secao_data)
        return SecaoResponseSchema.from_orm(secao)
    
    def get(self, id: int) -> Optional[SecaoResponseSchema]:
        """
        Obtém uma seção pelo ID.
        
        Args:
            id: ID da seção
            
        Returns:
            SecaoResponseSchema: Dados da seção, ou None se não encontrada
        """
        secao = self.repository.get(id)
        if not secao:
            return None
        return SecaoResponseSchema.from_orm(secao)
    
    def list(self, skip: int = 0, limit: int = 100, nome: Optional[str] = None, ativo: Optional[bool] = None) -> List[SecaoResponseSchema]:
        """
        Lista seções com opção de filtros.
        
        Args:
            skip: Registros para pular (paginação)
            limit: Limite de registros (paginação)
            nome: Filtro opcional por nome
            ativo: Filtro opcional por status ativo
            
        Returns:
            List[SecaoResponseSchema]: Lista de seções
        """
        secoes = self.repository.list(skip, limit, nome, ativo)
        return [SecaoResponseSchema.from_orm(secao) for secao in secoes]
    
    def update(self, id: int, secao_data: SecaoUpdateSchema) -> SecaoResponseSchema:
        """
        Atualiza uma seção.
        
        Args:
            id: ID da seção
            secao_data: Dados para atualização
            
        Returns:
            SecaoResponseSchema: Dados da seção atualizada
            
        Raises:
            ValueError: Se o nome da seção já existir para outra seção
        """
        # Verificar se a seção existe
        secao = self.repository.get(id)
        if not secao:
            raise ValueError(f"Seção com ID {id} não encontrada")
        
        # Verificar se o novo nome (se fornecido) já está em uso por outra seção
        if secao_data.nome and secao_data.nome != secao.nome:
            existing = self.repository.get_by_nome(secao_data.nome)
            if existing and existing.id != id:
                raise ValueError(f"Já existe uma seção com o nome '{secao_data.nome}'")
        
        # Atualizar seção
        secao = self.repository.update(id, secao_data)
        return SecaoResponseSchema.from_orm(secao)
    
    def delete(self, id: int) -> None:
        """
        Remove uma seção (exclusão lógica - apenas marca como inativo).
        
        Args:
            id: ID da seção
            
        Raises:
            ValueError: Se a seção não for encontrada
        """
        # Verificar se a seção existe
        secao = self.repository.get(id)
        if not secao:
            raise ValueError(f"Seção com ID {id} não encontrada")
        
        # Excluir logicamente a seção
        self.repository.delete(id) 