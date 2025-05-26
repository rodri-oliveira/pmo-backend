from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.alocacao_repository import AlocacaoRepository
from app.repositories.recurso_repository import RecursoRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.db.orm_models import AlocacaoRecursoProjeto

class AlocacaoService:
    """Serviço para gerenciamento de alocações de recursos em projetos."""

    async def list(
        self,
        recurso_id: Optional[int] = None,
        projeto_id: Optional[int] = None,
        data_inicio: Optional[str] = None,
        data_fim: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lista alocações com filtros opcionais por recurso, projeto e período.
        """
        # Conversão de datas se necessário
        from datetime import datetime
        data_inicio_dt = None
        data_fim_dt = None
        if data_inicio:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, "%Y-%m-%d").date()
            except ValueError:
                try:
                    data_inicio_dt = datetime.strptime(data_inicio, "%d/%m/%Y").date()
                except ValueError:
                    raise ValueError("Formato de data_inicio inválido. Use YYYY-MM-DD ou DD/MM/YYYY.")
        if data_fim:
            try:
                data_fim_dt = datetime.strptime(data_fim, "%Y-%m-%d").date()
            except ValueError:
                try:
                    data_fim_dt = datetime.strptime(data_fim, "%d/%m/%Y").date()
                except ValueError:
                    raise ValueError("Formato de data_fim inválido. Use YYYY-MM-DD ou DD/MM/YYYY.")

        # Prioridade: recurso_id > projeto_id > periodo > all
        if recurso_id is not None:
            return await self.list_by_recurso(recurso_id)
        elif projeto_id is not None:
            return await self.list_by_projeto(projeto_id)
        elif data_inicio_dt or data_fim_dt:
            return await self.list_by_periodo(data_inicio_dt, data_fim_dt)
        else:
            return await self.list_all()

    def __init__(self, db: AsyncSession):
        """
        Inicializa o serviço com uma sessão do banco de dados.
        
        Args:
            db: Sessão assíncrona do banco de dados
        """
        self.db = db
        self.repository = AlocacaoRepository(db)
        self.recurso_repository = RecursoRepository(db)
        self.projeto_repository = ProjetoRepository(db)
    
    async def create(self, alocacao_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Cria uma nova alocação de recurso em projeto.
        
        Args:
            alocacao_data: Dados da alocação a ser criada
            
        Returns:
            Dict: Dados da alocação criada
            
        Raises:
            ValueError: Se o recurso ou projeto não existir, ou se houver conflito de datas
        """
        # Verificar se o recurso existe
        recurso = await self.recurso_repository.get(alocacao_data["recurso_id"])
        if not recurso:
            raise ValueError(f"Recurso com ID {alocacao_data['recurso_id']} não encontrado")
        
        # Verificar se o projeto existe
        projeto = await self.projeto_repository.get(alocacao_data["projeto_id"])
        if not projeto:
            raise ValueError(f"Projeto com ID {alocacao_data['projeto_id']} não encontrado")
        
        # Verificar se já existe uma alocação para o mesmo recurso, projeto e data de início
        alocacao_existente = await self.repository.get_by_recurso_projeto_data(
            alocacao_data["recurso_id"],
            alocacao_data["projeto_id"],
            alocacao_data["data_inicio_alocacao"]
        )
        
        if alocacao_existente:
            raise ValueError(f"Já existe uma alocação para este recurso neste projeto com a mesma data de início")
        
        # Preencher equipe_id automaticamente (snapshot do momento)
        alocacao_data = dict(alocacao_data)
        # Use apenas o campo direto, nunca relacionamento
        equipe_id = getattr(recurso, "equipe_principal_id", None)
        alocacao_data["equipe_id"] = equipe_id
        # Criar a alocação
        alocacao = await self.repository.create(alocacao_data)

        # Buscar a alocacao novamente, agora com os relacionamentos carregados
        from sqlalchemy.future import select
        from sqlalchemy.orm import joinedload
        from app.db.orm_models import AlocacaoRecursoProjeto, Equipe

        query = (
            select(AlocacaoRecursoProjeto)
            .options(
                joinedload(AlocacaoRecursoProjeto.equipe).joinedload(Equipe.secao),
                joinedload(AlocacaoRecursoProjeto.recurso),
                joinedload(AlocacaoRecursoProjeto.projeto)
            )
            .filter(AlocacaoRecursoProjeto.id == alocacao.id)
        )
        result = await self.db.execute(query)
        alocacao_completa = result.scalars().first()

        # Formatar a resposta
        return self._format_response(alocacao_completa)
    
    async def get(self, alocacao_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém uma alocação pelo ID.
        
        Args:
            alocacao_id: ID da alocação
            
        Returns:
            Dict: Dados da alocação, ou None se não encontrada
        """
        from sqlalchemy.future import select
        from sqlalchemy.orm import joinedload
        from app.db.orm_models import AlocacaoRecursoProjeto, Equipe

        query = (
            select(AlocacaoRecursoProjeto)
            .options(
                joinedload(AlocacaoRecursoProjeto.equipe).joinedload(Equipe.secao),
                joinedload(AlocacaoRecursoProjeto.recurso),
                joinedload(AlocacaoRecursoProjeto.projeto)
            )
            .filter(AlocacaoRecursoProjeto.id == alocacao_id)
        )
        result = await self.db.execute(query)
        alocacao = result.scalars().first()
        if not alocacao:
            return None

        return self._format_response(alocacao)
    
    async def list_all(self) -> List[Dict[str, Any]]:
        """
        Lista todas as alocações ativas com detalhes de recursos e projetos.
        
        Returns:
            List[Dict]: Lista de alocações
        """
        alocacoes = await self.repository.list_active_with_details()
        return [self._format_response(a) for a in alocacoes]
    
    async def list_by_recurso(self, recurso_id: int) -> List[Dict[str, Any]]:
        """
        Lista alocações de um recurso.
        
        Args:
            recurso_id: ID do recurso
            
        Returns:
            List[Dict]: Lista de alocações do recurso
        """
        alocacoes = await self.repository.list_by_recurso(recurso_id)
        return [self._format_response(a) for a in alocacoes]
    
    async def list_by_projeto(self, projeto_id: int) -> List[Dict[str, Any]]:
        """
        Lista alocações de um projeto.
        
        Args:
            projeto_id: ID do projeto
            
        Returns:
            List[Dict]: Lista de alocações do projeto
        """
        alocacoes = await self.repository.list_by_projeto(projeto_id)
        return [self._format_response(a) for a in alocacoes]
    
    async def list_by_periodo(self, data_inicio: Optional[date] = None, data_fim: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Lista alocações em um período.
        
        Args:
            data_inicio: Data inicial do período
            data_fim: Data final do período
            
        Returns:
            List[Dict]: Lista de alocações no período
        """
        alocacoes = await self.repository.list_by_periodo(data_inicio, data_fim)
        return [self._format_response(a) for a in alocacoes]
    
    async def update(self, alocacao_id: int, alocacao_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza uma alocação existente.
        
        Args:
            alocacao_id: ID da alocação a ser atualizada
            alocacao_data: Dados para atualização
            
        Returns:
            Dict: Dados da alocação atualizada
            
        Raises:
            ValueError: Se a alocação não existir ou se houver conflito de datas
        """
        # Verificar se a alocação existe
        alocacao = await self.repository.get(alocacao_id)
        if not alocacao:
            raise ValueError(f"Alocação com ID {alocacao_id} não encontrada")
        
        # Se estiver atualizando o recurso, verificar se existe
        if "recurso_id" in alocacao_data and alocacao_data["recurso_id"] != alocacao.recurso_id:
            recurso = await self.recurso_repository.get(alocacao_data["recurso_id"])
            if not recurso:
                raise ValueError(f"Recurso com ID {alocacao_data['recurso_id']} não encontrado")
        
        # Se estiver atualizando o projeto, verificar se existe
        if "projeto_id" in alocacao_data and alocacao_data["projeto_id"] != alocacao.projeto_id:
            projeto = await self.projeto_repository.get(alocacao_data["projeto_id"])
            if not projeto:
                raise ValueError(f"Projeto com ID {alocacao_data['projeto_id']} não encontrado")
        
        # Se estiver atualizando a data de início, verificar conflitos
        if "data_inicio_alocacao" in alocacao_data and alocacao_data["data_inicio_alocacao"] != alocacao.data_inicio_alocacao:
            # Verificar se já existe outra alocação com a mesma combinação
            recurso_id = alocacao_data.get("recurso_id", alocacao.recurso_id)
            projeto_id = alocacao_data.get("projeto_id", alocacao.projeto_id)
            data_inicio = alocacao_data["data_inicio_alocacao"]
            
            alocacao_existente = await self.repository.get_by_recurso_projeto_data(
                recurso_id, projeto_id, data_inicio
            )
            if alocacao_existente and alocacao_existente.id != alocacao_id:
                raise ValueError(f"Já existe uma alocação para este recurso neste projeto com a mesma data de início")

        # Atualizar a alocação
        alocacao_atualizada = await self.repository.update(alocacao_id, alocacao_data)

        # Buscar novamente com relacionamentos carregados
        from sqlalchemy.future import select
        from sqlalchemy.orm import joinedload
        from app.db.orm_models import AlocacaoRecursoProjeto, Equipe

        query = (
            select(AlocacaoRecursoProjeto)
            .options(
                joinedload(AlocacaoRecursoProjeto.equipe).joinedload(Equipe.secao),
                joinedload(AlocacaoRecursoProjeto.recurso),
                joinedload(AlocacaoRecursoProjeto.projeto)
            )
            .filter(AlocacaoRecursoProjeto.id == alocacao_id)
        )
        result = await self.db.execute(query)
        alocacao_completa = result.scalars().first()

        # Formatar a resposta
        return self._format_response(alocacao_completa)

    async def delete(self, alocacao_id: int) -> None:
        """
        Remove uma alocação.
        
        Args:
            alocacao_id: ID da alocação a ser removida
        
        Raises:
            ValueError: Se a alocação não existir
        """
        # Verificar se a alocação existe
        alocacao = await self.repository.get(alocacao_id)
        if not alocacao:
            raise ValueError(f"Alocação com ID {alocacao_id} não encontrada")
        
        # Remover a alocação
        await self.repository.delete(alocacao_id)
    
    def _format_response(self, alocacao: AlocacaoRecursoProjeto) -> Dict[str, Any]:
        """
        Formata uma alocação para resposta da API.
        Inclui equipe_id e equipe_nome (se possível).
        """
        result = {
            "id": alocacao.id,
            "recurso_id": alocacao.recurso_id,
            "projeto_id": alocacao.projeto_id,
            "equipe_id": getattr(alocacao, "equipe_id", None),
            "equipe_nome": getattr(alocacao.equipe, "nome", None) if hasattr(alocacao, "equipe") and alocacao.equipe else None,
            "data_inicio_alocacao": alocacao.data_inicio_alocacao,
            "data_fim_alocacao": alocacao.data_fim_alocacao,
            "data_criacao": alocacao.data_criacao,
            "data_atualizacao": alocacao.data_atualizacao,
            "recurso_nome": getattr(alocacao.recurso, "nome", None) if hasattr(alocacao, "recurso") and alocacao.recurso else None,
            "projeto_nome": getattr(alocacao.projeto, "nome", None) if hasattr(alocacao, "projeto") and alocacao.projeto else None
        }
        return result
