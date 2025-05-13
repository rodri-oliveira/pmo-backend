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
        super().__init__(db, Projeto)

    def get_active_projects(self) -> List[Dict[str, Any]]:
        results = self.db.query(
            self.model,
            StatusProjeto.id.label("status_id"),
            StatusProjeto.nome.label("status_nome")
        ).join(
            StatusProjeto, self.model.status_projeto_id == StatusProjeto.id
        ).filter(
            self.model.ativo == True
        ).all()

        return [
            {
                "id": projeto.id,
                "nome": projeto.nome,
                "codigo_empresa": projeto.codigo_empresa,
                "descricao": projeto.descricao,
                "data_inicio_prevista": projeto.data_inicio_prevista,
                "data_fim_prevista": projeto.data_fim_prevista,
                "status_projeto_id": status_id,
                "status_projeto": {
                    "id": status_id,
                    "nome": status_nome
                },
                "ativo": projeto.ativo,
                "jira_project_key": projeto.jira_project_key
            }
            for projeto, status_id, status_nome in results
        ]

    def get_by_status(self, status_projeto_id: int) -> List[Dict[str, Any]]:
        results = self.db.query(
            self.model,
            StatusProjeto.id.label("status_id"),
            StatusProjeto.nome.label("status_nome")
        ).join(
            StatusProjeto, self.model.status_projeto_id == StatusProjeto.id
        ).filter(
            self.model.status_projeto_id == status_projeto_id
        ).all()

        return [
            {
                "id": projeto.id,
                "nome": projeto.nome,
                "codigo_empresa": projeto.codigo_empresa,
                "descricao": projeto.descricao,
                "data_inicio_prevista": projeto.data_inicio_prevista,
                "data_fim_prevista": projeto.data_fim_prevista,
                "status_projeto_id": status_id,
                "status_projeto": {
                    "id": status_id,
                    "nome": status_nome
                },
                "ativo": projeto.ativo,
                "jira_project_key": projeto.jira_project_key
            }
            for projeto, status_id, status_nome in results
        ]

    def search(
        self, 
        nome: Optional[str] = None,
        codigo_empresa: Optional[str] = None,
        status_projeto_id: Optional[int] = None,
        ativo: Optional[bool] = None
    ) -> List[Dict[str, Any]]:
        query = self.db.query(
            self.model,
            StatusProjeto.id.label("status_id"),
            StatusProjeto.nome.label("status_nome")
        ).join(
            StatusProjeto, self.model.status_projeto_id == StatusProjeto.id
        )

        if nome:
            query = query.filter(self.model.nome.ilike(f"%{nome}%"))
        if codigo_empresa:
            query = query.filter(self.model.codigo_empresa.ilike(f"%{codigo_empresa}%"))
        if status_projeto_id:
            query = query.filter(self.model.status_projeto_id == status_projeto_id)
        if ativo is not None:
            query = query.filter(self.model.ativo == ativo)

        results = query.all()
        return [
            {
                "id": projeto.id,
                "nome": projeto.nome,
                "codigo_empresa": projeto.codigo_empresa,
                "descricao": projeto.descricao,
                "data_inicio_prevista": projeto.data_inicio_prevista,
                "data_fim_prevista": projeto.data_fim_prevista,
                "status_projeto_id": status_id,
                "status_projeto": {
                    "id": status_id,
                    "nome": status_nome
                },
                "ativo": projeto.ativo,
                "jira_project_key": projeto.jira_project_key
            }
            for projeto, status_id, status_nome in results
        ]

    def get_with_status(self, id: int) -> Optional[Dict[str, Any]]:
        result = self.db.query(
            self.model,
            StatusProjeto.id.label("status_id"),
            StatusProjeto.nome.label("status_nome")
        ).join(
            StatusProjeto, self.model.status_projeto_id == StatusProjeto.id
        ).filter(
            self.model.id == id
        ).first()

        if not result:
            return None

        projeto, status_id, status_nome = result

        return {
            "id": projeto.id,
            "nome": projeto.nome,
            "codigo_empresa": projeto.codigo_empresa,
            "descricao": projeto.descricao,
            "data_inicio_prevista": projeto.data_inicio_prevista,
            "data_fim_prevista": projeto.data_fim_prevista,
            "status_projeto_id": status_id,
            "status_projeto": {
                "id": status_id,
                "nome": status_nome
            },
            "ativo": projeto.ativo,
            "jira_project_key": projeto.jira_project_key
        }

    def list_with_status(self) -> List[Dict[str, Any]]:
        results = self.db.query(
            self.model,
            StatusProjeto.id.label("status_id"),
            StatusProjeto.nome.label("status_nome")
        ).join(
            StatusProjeto, self.model.status_projeto_id == StatusProjeto.id
        ).all()

        return [
            {
                "id": projeto.id,
                "nome": projeto.nome,
                "codigo_empresa": projeto.codigo_empresa,
                "descricao": projeto.descricao,
                "data_inicio_prevista": projeto.data_inicio_prevista,
                "data_fim_prevista": projeto.data_fim_prevista,
                "status_projeto_id": status_id,
                "status_projeto": {
                    "id": status_id,
                    "nome": status_nome
                },
                "ativo": projeto.ativo,
                "jira_project_key": projeto.jira_project_key
            }
            for projeto, status_id, status_nome in results
        ]

    def get_with_status_by_jira_project_key(self, project_key: str) -> Optional[Dict[str, Any]]:
        result = self.db.query(
            self.model,
            StatusProjeto.id.label("status_id"),
            StatusProjeto.nome.label("status_nome")
        ).join(
            StatusProjeto, self.model.status_projeto_id == StatusProjeto.id
        ).filter(
            self.model.jira_project_key == project_key
        ).first()

        if not result:
            return None

        projeto, status_id, status_nome = result
        return {
            "id": projeto.id,
            "nome": projeto.nome,
            "codigo_empresa": projeto.codigo_empresa,
            "descricao": projeto.descricao,
            "data_inicio_prevista": projeto.data_inicio_prevista,
            "data_fim_prevista": projeto.data_fim_prevista,
            "status_projeto_id": status_id,
            "status_projeto": {
                "id": status_id,
                "nome": status_nome
            },
            "ativo": projeto.ativo,
            "jira_project_key": projeto.jira_project_key
        }

    def get_with_status_by_jira_issue_id(self, issue_id: str) -> Optional[Dict[str, Any]]:
        result = self.db.query(
            self.model,
            StatusProjeto.id.label("status_id"),
            StatusProjeto.nome.label("status_nome")
        ).join(
            StatusProjeto, self.model.status_projeto_id == StatusProjeto.id
        ).filter(
            self.model.jira_issue_id == issue_id
        ).first()

        if not result:
            return None

        projeto, status_id, status_nome = result
        return {
            "id": projeto.id,
            "nome": projeto.nome,
            "codigo_empresa": projeto.codigo_empresa,
            "descricao": projeto.descricao,
            "data_inicio_prevista": projeto.data_inicio_prevista,
            "data_fim_prevista": projeto.data_fim_prevista,
            "status_projeto_id": status_id,
            "status_projeto": {
                "id": status_id,
                "nome": status_nome
            },
            "ativo": projeto.ativo,
            "jira_project_key": projeto.jira_project_key
        }