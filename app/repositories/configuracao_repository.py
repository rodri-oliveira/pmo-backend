from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.db.orm_models import Configuracao
from app.repositories.base_repository import BaseRepository

class ConfiguracaoRepository(BaseRepository[Configuracao]):
    """
    Repositório para operações com configurações do sistema.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o repositório com uma sessão do banco de dados.
        
        Args:
            db: Sessão do banco de dados
        """
        super().__init__(db, Configuracao)
    
    def get_by_chave(self, chave: str) -> Optional[Configuracao]:
        """
        Busca uma configuração pela chave.
        
        Args:
            chave: Chave da configuração
            
        Returns:
            Configuração encontrada ou None
        """
        return self.db.query(self.model).filter(
            self.model.chave == chave
        ).first()
    
    def set_valor(self, chave: str, valor: str, descricao: Optional[str] = None) -> Configuracao:
        """
        Define o valor de uma configuração, criando-a se não existir.
        
        Args:
            chave: Chave da configuração
            valor: Valor da configuração
            descricao: Descrição opcional da configuração
            
        Returns:
            Configuração atualizada ou criada
        """
        configuracao = self.get_by_chave(chave)
        
        if configuracao:
            # Atualizar configuração existente
            update_data = {"valor": valor}
            if descricao:
                update_data["descricao"] = descricao
                
            return self.update(configuracao.id, update_data)
        else:
            # Criar nova configuração
            create_data = {
                "chave": chave,
                "valor": valor,
                "descricao": descricao if descricao else f"Configuração {chave}"
            }
            
            return self.create(create_data)
    
    def get_valor(self, chave: str, default: Optional[str] = None) -> str:
        """
        Obtém o valor de uma configuração.
        
        Args:
            chave: Chave da configuração
            default: Valor padrão se a configuração não existir
            
        Returns:
            Valor da configuração ou valor padrão
        """
        configuracao = self.get_by_chave(chave)
        
        if configuracao:
            return configuracao.valor
            
        return default
    
    def get_all_as_dict(self) -> Dict[str, str]:
        """
        Obtém todas as configurações como um dicionário.
        
        Returns:
            Dicionário com chaves e valores das configurações
        """
        configuracoes = self.get_all()
        
        return {
            configuracao.chave: configuracao.valor
            for configuracao in configuracoes
        } 