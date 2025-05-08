from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.db.orm_models import Projeto, StatusProjeto
from app.repositories.base_repository import BaseRepository

class ProjetoRepository(BaseRepository[Projeto]):
    """
    Repositório para operações com projetos.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o repositório com uma sessão do banco de dados.
        
        Args:
            db: Sessão do banco de dados
        """
        super().__init__(db, Projeto)
    
    def get_by_jira_project_key(self, project_key: str) -> Optional[Projeto]:
        """
        Busca um projeto pela chave do projeto no Jira.
        
        Args:
            project_key: Chave do projeto no Jira
            
        Returns:
            Projeto encontrado ou None
        """
        return self.db.query(self.model).filter(
            self.model.jira_project_key == project_key
        ).first()
    
    def get_by_jira_issue_id(self, issue_id: str) -> Optional[Projeto]:
        """
        Busca um projeto pelo ID da issue no Jira.
        Este método assume que existe um mapeamento entre issues e projetos.
        
        Args:
            issue_id: ID da issue no Jira
            
        Returns:
            Projeto encontrado ou None
        """
        return self.db.query(self.model).filter(
            self.model.jira_issue_id == issue_id
        ).first()
    
    def get_by_status(self, status_id: int) -> List[Projeto]:
        """
        Busca projetos por status.
        
        Args:
            status_id: ID do status
            
        Returns:
            Lista de projetos com o status
        """
        return self.db.query(self.model).filter(
            self.model.status_id == status_id
        ).all()
    
    def get_active_projects(self) -> List[Projeto]:
        """
        Busca projetos ativos.
        
        Returns:
            Lista de projetos ativos
        """
        return self.db.query(self.model).filter(
            self.model.ativo == True
        ).all()
    
    def search(
        self, 
        nome: Optional[str] = None,
        codigo: Optional[str] = None,
        status_id: Optional[int] = None,
        ativo: Optional[bool] = None
    ) -> List[Projeto]:
        """
        Busca projetos com base em critérios.
        
        Args:
            nome: Nome ou parte do nome
            codigo: Código do projeto
            status_id: ID do status
            ativo: Se o projeto está ativo
            
        Returns:
            Lista de projetos que atendem aos critérios
        """
        query = self.db.query(self.model)
        
        if nome:
            query = query.filter(self.model.nome.ilike(f"%{nome}%"))
            
        if codigo:
            query = query.filter(self.model.codigo.ilike(f"%{codigo}%"))
            
        if status_id:
            query = query.filter(self.model.status_id == status_id)
            
        if ativo is not None:
            query = query.filter(self.model.ativo == ativo)
            
        return query.all()
    
    def get_with_status(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um projeto com detalhes do status.
        
        Args:
            id: ID do projeto
            
        Returns:
            Dicionário com dados do projeto e status ou None
        """
        result = self.db.query(
            self.model,
            StatusProjeto.nome.label("status_nome")
        ).join(
            StatusProjeto, self.model.status_id == StatusProjeto.id
        ).filter(
            self.model.id == id
        ).first()
        
        if not result:
            return None
            
        projeto, status_nome = result
        
        return {
            "id": projeto.id,
            "nome": projeto.nome,
            "codigo": projeto.codigo,
            "descricao": projeto.descricao,
            "data_inicio": projeto.data_inicio,
            "data_fim_prevista": projeto.data_fim_prevista,
            "data_fim_real": projeto.data_fim_real,
            "status_id": projeto.status_id,
            "status_nome": status_nome,
            "ativo": projeto.ativo,
            "jira_project_key": projeto.jira_project_key
        }
    
    def list_with_status(self) -> List[Dict[str, Any]]:
        """
        Lista todos os projetos com detalhes do status.
        
        Returns:
            Lista de dicionários com dados dos projetos e status
        """
        results = self.db.query(
            self.model,
            StatusProjeto.nome.label("status_nome")
        ).join(
            StatusProjeto, self.model.status_id == StatusProjeto.id
        ).all()
        
        return [
            {
                "id": projeto.id,
                "nome": projeto.nome,
                "codigo": projeto.codigo,
                "descricao": projeto.descricao,
                "data_inicio": projeto.data_inicio,
                "data_fim_prevista": projeto.data_fim_prevista,
                "data_fim_real": projeto.data_fim_real,
                "status_id": projeto.status_id,
                "status_nome": status_nome,
                "ativo": projeto.ativo,
                "jira_project_key": projeto.jira_project_key
            }
            for projeto, status_nome in results
        ] 