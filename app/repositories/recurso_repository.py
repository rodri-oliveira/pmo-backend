from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, func, select

from app.db.orm_models import Recurso, Equipe, Secao
from app.repositories.base_repository import BaseRepository

class RecursoRepository(BaseRepository[Recurso]):
    async def get_by_id(self, recurso_id: int) -> Optional[Recurso]:
        """Obtém um recurso pelo ID (compatibilidade com ServiceLayer)."""
        return await self.get(recurso_id)

    """
    Repositório para operações com recursos.
    """
    
    def __init__(self, db: AsyncSession):
        """
        Inicializa o repositório com uma sessão do banco de dados assíncrona.
        
        Args:
            db: Sessão do banco de dados assíncrona
        """
        super().__init__(db, Recurso)
    
    async def get_by_jira_account_id(self, account_id: str) -> Optional[Recurso]:
        """
        Busca um recurso pelo ID da conta no Jira.
        
        Args:
            account_id: ID da conta no Jira
            
        Returns:
            Recurso encontrado ou None
        """
        query = select(self.model).where(self.model.jira_account_id == account_id)
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_by_jira_user_id(self, jira_user_id: str) -> Optional[Recurso]:
        """
        Busca um recurso pelo ID do usuário no Jira.
        
        Args:
            jira_user_id: ID do usuário no Jira
            
        Returns:
            Recurso encontrado ou None
        """
        query = select(self.model).where(self.model.jira_user_id == jira_user_id)
        result = await self.db.execute(query)
        return result.scalars().first()
        
    async def get_by_email(self, email: str) -> Optional[Recurso]:
        """
        Busca um recurso pelo email.
        
        Args:
            email: Email do recurso
            
        Returns:
            Recurso encontrado ou None
        """
        query = select(self.model).where(self.model.email == email)
        result = await self.db.execute(query)
        return result.scalars().first()
    
    async def get_by_equipe(self, equipe_id: int) -> List[Recurso]:
        """
        Busca recursos por equipe.
        
        Args:
            equipe_id: ID da equipe
            
        Returns:
            Lista de recursos da equipe
        """
        query = select(self.model).where(self.model.equipe_principal_id == equipe_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_by_secao(self, secao_id: int) -> List[Recurso]:
        """
        Busca recursos por seção.
        
        Args:
            secao_id: ID da seção
            
        Returns:
            Lista de recursos da seção
        """
        return self.db.query(self.model).filter(
            self.model.secao_id == secao_id
        ).all()
    
    def search(
        self, 
        nome: Optional[str] = None,
        equipe_id: Optional[int] = None,
        secao_id: Optional[int] = None,
        ativo: Optional[bool] = None
    ) -> List[Recurso]:
        """
        Busca recursos com base em critérios.
        
        Args:
            nome: Nome ou parte do nome
            equipe_id: ID da equipe
            secao_id: ID da seção
            ativo: Se o recurso está ativo
            
        Returns:
            Lista de recursos que atendem aos critérios
        """
        query = self.db.query(self.model)
        
        if nome:
            query = query.filter(self.model.nome.ilike(f"%{nome}%"))
            
        if equipe_id:
            query = query.filter(self.model.equipe_id == equipe_id)
            
        if secao_id:
            query = query.filter(self.model.secao_id == secao_id)
            
        if ativo is not None:
            query = query.filter(self.model.ativo == ativo)
            
        return query.all()
    
    def get_with_details(self, id: int) -> Optional[Dict[str, Any]]:
        """
        Busca um recurso com detalhes da equipe e seção.
        
        Args:
            id: ID do recurso
            
        Returns:
            Dicionário com dados do recurso e relacionamentos ou None
        """
        result = self.db.query(
            self.model,
            Equipe.nome.label("equipe_nome"),
            Secao.nome.label("secao_nome")
        ).join(
            Equipe, self.model.equipe_id == Equipe.id, isouter=True
        ).join(
            Secao, self.model.secao_id == Secao.id, isouter=True
        ).filter(
            self.model.id == id
        ).first()
        
        if not result:
            return None
            
        recurso, equipe_nome, secao_nome = result
        
        return {
            "id": recurso.id,
            "nome": recurso.nome,
            "matricula": recurso.matricula,
            "email": recurso.email,
            "equipe_id": recurso.equipe_id,
            "equipe_nome": equipe_nome,
            "secao_id": recurso.secao_id,
            "secao_nome": secao_nome,
            "ativo": recurso.ativo,
            "jira_account_id": recurso.jira_account_id
        }
    
    def list_with_details(self) -> List[Dict[str, Any]]:
        """
        Lista todos os recursos com detalhes da equipe e seção.
        
        Returns:
            Lista de dicionários com dados dos recursos e relacionamentos
        """
        results = self.db.query(
            self.model,
            Equipe.nome.label("equipe_nome"),
            Secao.nome.label("secao_nome")
        ).join(
            Equipe, self.model.equipe_id == Equipe.id, isouter=True
        ).join(
            Secao, self.model.secao_id == Secao.id, isouter=True
        ).all()
        
        return [
            {
                "id": recurso.id,
                "nome": recurso.nome,
                "matricula": recurso.matricula,
                "email": recurso.email,
                "equipe_id": recurso.equipe_id,
                "equipe_nome": equipe_nome,
                "secao_id": recurso.secao_id,
                "secao_nome": secao_nome,
                "ativo": recurso.ativo,
                "jira_account_id": recurso.jira_account_id
            }
            for recurso, equipe_nome, secao_nome in results
        ] 