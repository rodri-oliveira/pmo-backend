from typing import List, Optional
from sqlalchemy.orm import Session
from app.api.dtos.projeto_schema import ProjetoCreateSchema, ProjetoUpdateSchema, ProjetoResponseSchema
from app.repositories.projeto_repository import ProjetoRepository
from app.repositories.status_projeto_repository import StatusProjetoRepository

class ProjetoService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = ProjetoRepository(db)
        self.status_repository = StatusProjetoRepository(db)
    
    def create(self, projeto_data: ProjetoCreateSchema) -> ProjetoResponseSchema:
        """
        Cria um novo projeto.
        
        Args:
            projeto_data: Dados do projeto a ser criado
            
        Returns:
            ProjetoResponseSchema: Dados do projeto criado
            
        Raises:
            ValueError: Se o status não existir ou código/jira_key duplicado
        """
        # Verificar se o status existe
        status = self.status_repository.get(projeto_data.status_projeto)
        if not status:
            raise ValueError(f"Status com ID {projeto_data.status_projeto} não encontrado")
        
        # Verificar se já existe projeto com o mesmo código empresa
        if projeto_data.codigo_empresa:
            existing = self.repository.get_by_codigo_empresa(projeto_data.codigo_empresa)
            if existing:
                raise ValueError(f"Já existe um projeto com o código '{projeto_data.codigo_empresa}'")
        
        # Verificar se já existe projeto com a mesma chave Jira
        if projeto_data.jira_project_key:
            existing = self.repository.get_by_jira_project_key(projeto_data.jira_project_key)
            if existing:
                raise ValueError(f"Já existe um projeto com a chave Jira '{projeto_data.jira_project_key}'")
        
        # Criar novo projeto
        projeto = self.repository.create(projeto_data.dict())
        return ProjetoResponseSchema.from_orm(projeto)
    
    def get(self, id: int) -> Optional[ProjetoResponseSchema]:
        """
        Obtém um projeto pelo ID.
        
        Args:
            id: ID do projeto
            
        Returns:
            ProjetoResponseSchema: Dados do projeto, ou None se não encontrado
        """
        projeto = self.repository.get(id)
        if not projeto:
            return None
        return ProjetoResponseSchema.from_orm(projeto)
    
    def list(self, skip: int = 0, limit: int = 100, nome: Optional[str] = None, 
             codigo_empresa: Optional[str] = None, status_projeto: Optional[int] = None, 
             ativo: Optional[bool] = None) -> List[ProjetoResponseSchema]:
        """
        Lista projetos com opção de filtros.
        
        Args:
            skip: Registros para pular (paginação)
            limit: Limite de registros (paginação)
            nome: Filtro opcional por nome
            codigo_empresa: Filtro opcional por código empresa
            status_projeto: Filtro opcional por status
            ativo: Filtro opcional por status ativo
            
        Returns:
            List[ProjetoResponseSchema]: Lista de projetos
        """
        projetos = self.repository.list(
            skip, limit, 
            nome=nome, 
            codigo_empresa=codigo_empresa, 
            status_projeto=status_projeto, 
            ativo=ativo
        )
        return [ProjetoResponseSchema.from_orm(projeto) for projeto in projetos]
    
    def update(self, id: int, projeto_data: ProjetoUpdateSchema) -> ProjetoResponseSchema:
        """
        Atualiza um projeto.
        
        Args:
            id: ID do projeto
            projeto_data: Dados para atualização
            
        Returns:
            ProjetoResponseSchema: Dados do projeto atualizado
            
        Raises:
            ValueError: Se o projeto não existir, status não existir, ou código/jira_key duplicado
        """
        # Verificar se o projeto existe
        projeto = self.repository.get(id)
        if not projeto:
            raise ValueError(f"Projeto com ID {id} não encontrado")
        
        # Verificar se o novo status (se fornecido) existe
        if projeto_data.status_projeto is not None and projeto_data.status_projeto != projeto.status_projeto:
            status = self.status_repository.get(projeto_data.status_projeto)
            if not status:
                raise ValueError(f"Status com ID {projeto_data.status_projeto} não encontrado")
        
        # Verificar se o novo código empresa (se fornecido) já está em uso
        if projeto_data.codigo_empresa is not None and projeto_data.codigo_empresa != projeto.codigo_empresa:
            existing = self.repository.get_by_codigo_empresa(projeto_data.codigo_empresa)
            if existing and existing.id != id:
                raise ValueError(f"Já existe um projeto com o código '{projeto_data.codigo_empresa}'")
        
        # Verificar se a nova chave Jira (se fornecida) já está em uso
        if projeto_data.jira_project_key is not None and projeto_data.jira_project_key != projeto.jira_project_key:
            existing = self.repository.get_by_jira_project_key(projeto_data.jira_project_key)
            if existing and existing.id != id:
                raise ValueError(f"Já existe um projeto com a chave Jira '{projeto_data.jira_project_key}'")
        
        # Atualizar projeto
        data_dict = projeto_data.dict(exclude_unset=True)
        projeto = self.repository.update(id, data_dict)
        return ProjetoResponseSchema.from_orm(projeto)
    
    def delete(self, id: int) -> None:
        """
        Remove um projeto (exclusão lógica - apenas marca como inativo).
        
        Args:
            id: ID do projeto
            
        Raises:
            ValueError: Se o projeto não for encontrado
        """
        # Verificar se o projeto existe
        projeto = self.repository.get(id)
        if not projeto:
            raise ValueError(f"Projeto com ID {id} não encontrado")
        
        # Excluir logicamente o projeto
        self.repository.delete(id) 