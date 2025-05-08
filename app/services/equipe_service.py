from typing import List, Optional
from sqlalchemy.orm import Session
from app.api.dtos.equipe_schema import EquipeCreateSchema, EquipeUpdateSchema, EquipeResponseSchema
from app.repositories.equipe_repository import EquipeRepository
from app.repositories.secao_repository import SecaoRepository

class EquipeService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = EquipeRepository(db)
        self.secao_repository = SecaoRepository(db)
    
    def create(self, equipe_data: EquipeCreateSchema) -> EquipeResponseSchema:
        """
        Cria uma nova equipe.
        
        Args:
            equipe_data: Dados da equipe a ser criada
            
        Returns:
            EquipeResponseSchema: Dados da equipe criada
            
        Raises:
            ValueError: Se a seção não existir ou nome duplicado
        """
        # Verificar se a seção existe
        secao = self.secao_repository.get(equipe_data.secao_id)
        if not secao:
            raise ValueError(f"Seção com ID {equipe_data.secao_id} não encontrada")
        
        # Verificar se já existe equipe com esse nome na mesma seção
        existing = self.repository.get_by_nome_and_secao(equipe_data.nome, equipe_data.secao_id)
        if existing:
            raise ValueError(f"Já existe uma equipe com o nome '{equipe_data.nome}' na seção {equipe_data.secao_id}")
        
        # Criar nova equipe
        equipe = self.repository.create(equipe_data.dict())
        return EquipeResponseSchema.from_orm(equipe)
    
    def get(self, id: int) -> Optional[EquipeResponseSchema]:
        """
        Obtém uma equipe pelo ID.
        
        Args:
            id: ID da equipe
            
        Returns:
            EquipeResponseSchema: Dados da equipe, ou None se não encontrada
        """
        equipe = self.repository.get(id)
        if not equipe:
            return None
        return EquipeResponseSchema.from_orm(equipe)
    
    def list(self, skip: int = 0, limit: int = 100, nome: Optional[str] = None, 
             secao_id: Optional[int] = None, ativo: Optional[bool] = None) -> List[EquipeResponseSchema]:
        """
        Lista equipes com opção de filtros.
        
        Args:
            skip: Registros para pular (paginação)
            limit: Limite de registros (paginação)
            nome: Filtro opcional por nome
            secao_id: Filtro opcional por seção
            ativo: Filtro opcional por status ativo
            
        Returns:
            List[EquipeResponseSchema]: Lista de equipes
        """
        equipes = self.repository.list(skip, limit, nome=nome, secao_id=secao_id, ativo=ativo)
        return equipes 