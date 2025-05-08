from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session

from app.repositories.log_atividade_repository import LogAtividadeRepository
from app.models.usuario import UsuarioInDB

class LogService:
    """
    Serviço para gerenciamento de logs de atividade do sistema.
    """
    
    def __init__(self, db: Session):
        """
        Inicializa o serviço com uma sessão do banco de dados.
        
        Args:
            db: Sessão do banco de dados
        """
        self.db = db
        self.log_repository = LogAtividadeRepository(db)
    
    def registrar_acao(
        self, 
        acao: str, 
        entidade: str, 
        entidade_id: Optional[int] = None,
        usuario: Optional[UsuarioInDB] = None,
        detalhes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra uma ação realizada no sistema.
        
        Args:
            acao: Tipo de ação (CRIAR, ATUALIZAR, EXCLUIR, etc.)
            entidade: Nome da entidade afetada
            entidade_id: ID da entidade afetada
            usuario: Usuário que realizou a ação
            detalhes: Detalhes adicionais sobre a ação
            
        Returns:
            Dados do log criado
        """
        usuario_id = usuario.id if usuario else None
        
        log = self.log_repository.log_action(
            acao=acao,
            entidade=entidade,
            entidade_id=entidade_id,
            usuario_id=usuario_id,
            detalhes=detalhes
        )
        
        return {
            "id": log.id,
            "acao": log.acao,
            "entidade": log.entidade,
            "entidade_id": log.entidade_id,
            "usuario_id": log.usuario_id,
            "detalhes": log.detalhes,
            "data_hora": log.data_hora
        }
    
    def buscar_logs(
        self,
        entidade: Optional[str] = None,
        entidade_id: Optional[int] = None,
        usuario_id: Optional[int] = None,
        acao: Optional[str] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        limite: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Busca logs com base em critérios.
        
        Args:
            entidade: Filtrar por entidade
            entidade_id: Filtrar por ID da entidade
            usuario_id: Filtrar por usuário
            acao: Filtrar por tipo de ação
            data_inicio: Data inicial do período
            data_fim: Data final do período
            limite: Número máximo de logs a retornar
            
        Returns:
            Lista de logs encontrados
        """
        # Buscar logs no repositório
        if entidade and entidade_id:
            logs = self.log_repository.get_logs_by_entity(entidade, entidade_id)
        elif usuario_id:
            logs = self.log_repository.get_logs_by_user(usuario_id)
        else:
            logs = self.log_repository.get_all()
        
        # Aplicar filtros adicionais na memória
        resultados = []
        for log in logs:
            # Filtrar por ação
            if acao and log.acao != acao:
                continue
                
            # Filtrar por entidade
            if entidade and log.entidade != entidade:
                continue
                
            # Filtrar por data
            if data_inicio and log.data_hora < data_inicio:
                continue
                
            if data_fim and log.data_hora > data_fim:
                continue
                
            resultados.append({
                "id": log.id,
                "acao": log.acao,
                "entidade": log.entidade,
                "entidade_id": log.entidade_id,
                "usuario_id": log.usuario_id,
                "detalhes": log.detalhes,
                "data_hora": log.data_hora
            })
            
            # Limitar número de resultados
            if len(resultados) >= limite:
                break
                
        return resultados
    
    def limpar_logs_antigos(self, dias: int = 90) -> int:
        """
        Remove logs mais antigos que o período especificado.
        
        Args:
            dias: Idade máxima dos logs em dias
            
        Returns:
            Número de logs removidos
        """
        # Implementação a ser feita quando houver repositório com método adequado
        # Placeholder para desenvolvimento futuro
        return 0 