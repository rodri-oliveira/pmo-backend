from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.alocacao_repository import AlocacaoRepository
from app.repositories.recurso_repository import RecursoRepository
from app.repositories.projeto_repository import ProjetoRepository
from app.db.orm_models import AlocacaoRecursoProjeto

class AlocacaoService:
    async def get_all_alocacoes(self, skip: int = 0, limit: int = 100, include_inactive: bool = False):
        apenas_ativos = not include_inactive
        alocacoes = await self.repository.get_all(skip=skip, limit=limit, apenas_ativos=apenas_ativos)
        return [self._format_response(a) for a in alocacoes]

    async def count_alocacoes(self, include_inactive: bool = False):
        apenas_ativos = not include_inactive
        return await self.repository.count(apenas_ativos=apenas_ativos)


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
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"[ALOCACAO_CREATE] Iniciando criação de alocação: {alocacao_data}")
        logger.info(f"[ALOCACAO_CREATE] REGRA: Recurso pode estar em vários projetos, apenas não pode haver alocações idênticas")
        
        try:
            # Verificar se o recurso existe
            logger.info(f"[ALOCACAO_CREATE] Verificando recurso ID: {alocacao_data['recurso_id']}")
            recurso = await self.recurso_repository.get(alocacao_data["recurso_id"])
            if not recurso:
                raise ValueError(f"Recurso com ID {alocacao_data['recurso_id']} não encontrado")
            logger.info(f"[ALOCACAO_CREATE] Recurso encontrado: {recurso.id}")
            
            # Verificar se o projeto existe
            logger.info(f"[ALOCACAO_CREATE] Verificando projeto ID: {alocacao_data['projeto_id']}")
            projeto = await self.projeto_repository.get(alocacao_data["projeto_id"])
            if not projeto:
                raise ValueError(f"Projeto com ID {alocacao_data['projeto_id']} não encontrado")
            logger.info(f"[ALOCACAO_CREATE] Projeto encontrado: {projeto.id}")
            
            # Verificar se já existe uma alocação idêntica (mesmo recurso + mesmo projeto + mesma data de início)
            data_inicio = alocacao_data["data_inicio_alocacao"]
            logger.info(f"[ALOCACAO_CREATE] Verificando se já existe alocação idêntica: recurso {alocacao_data['recurso_id']}, projeto {alocacao_data['projeto_id']}, data {data_inicio}")

            alocacao_existente = await self.repository.get_by_recurso_projeto_data(
                recurso_id=alocacao_data["recurso_id"],
                projeto_id=alocacao_data["projeto_id"],
                data_inicio=data_inicio
            )
            if alocacao_existente:
                logger.info(f"[ALOCACAO_CREATE] Alocação existente encontrada: ID={alocacao_existente.id}, recurso={alocacao_existente.recurso_id}, projeto={alocacao_existente.projeto_id}, data={alocacao_existente.data_inicio_alocacao}")
            else:
                logger.info(f"[ALOCACAO_CREATE] Nenhuma alocação existente encontrada")

            if alocacao_existente:
                # Mostrar mensagem de erro simples com IDs para evitar inconsistências
                logger.info(f"[ALOCACAO_CREATE] Alocação duplicada detectada - bloqueando criação")
                raise ValueError(f"Já existe uma alocação idêntica: recurso {alocacao_data['recurso_id']}, projeto {alocacao_existente.projeto_id}, data {data_inicio}. Alocação existente ID: {alocacao_existente.id}.")

            # Preencher equipe_id automaticamente
            alocacao_data = dict(alocacao_data)
            equipe_id = getattr(recurso, "equipe_principal_id", None)
            alocacao_data["equipe_id"] = equipe_id
            logger.info(f"[ALOCACAO_CREATE] Equipe ID definida: {equipe_id}")
            
            # Criar a alocação
            logger.info(f"[ALOCACAO_CREATE] Chamando repository.create...")
            alocacao = await self.repository.create(alocacao_data)
            logger.info(f"[ALOCACAO_CREATE] Alocação criada com ID: {alocacao.id}")

            # Usar uma nova sessão isolada para buscar o objeto completo
            logger.info(f"[ALOCACAO_CREATE] Iniciando busca com nova sessão...")
            from sqlalchemy import select
            from sqlalchemy.orm import joinedload
            from app.db.orm_models import AlocacaoRecursoProjeto, Equipe
            from app.db.session import AsyncSessionLocal

            async with AsyncSessionLocal() as new_session:
                logger.info(f"[ALOCACAO_CREATE] Nova sessão criada, montando query...")
                query = (
                    select(AlocacaoRecursoProjeto)
                    .options(
                        joinedload(AlocacaoRecursoProjeto.equipe).joinedload(Equipe.secao),
                        joinedload(AlocacaoRecursoProjeto.recurso),
                        joinedload(AlocacaoRecursoProjeto.projeto),
                        joinedload(AlocacaoRecursoProjeto.status_alocacao)
                    )
                    .filter(AlocacaoRecursoProjeto.id == alocacao.id)
                )
                logger.info(f"[ALOCACAO_CREATE] Executando query na nova sessão...")
                result = await new_session.execute(query)
                logger.info(f"[ALOCACAO_CREATE] Query executada, obtendo resultado...")
                alocacao_completa = result.scalars().first()
                logger.info(f"[ALOCACAO_CREATE] Alocação completa obtida: {alocacao_completa.id if alocacao_completa else 'None'}")

            logger.info(f"[ALOCACAO_CREATE] Formatando resposta...")
            response = self._format_response(alocacao_completa)
            logger.info(f"[ALOCACAO_CREATE] Resposta formatada com sucesso")
            return response
            
        except Exception as e:
            logger.error(f"[ALOCACAO_CREATE] ERRO: {type(e).__name__}: {str(e)}")
            logger.error(f"[ALOCACAO_CREATE] Stack trace:", exc_info=True)
            raise
    
    async def get(self, alocacao_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtém uma alocação pelo ID.
        
        Args:
            alocacao_id: ID da alocação
            
        Returns:
            Dict: Dados da alocação, ou None se não encontrada
        """
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload
        from app.db.orm_models import AlocacaoRecursoProjeto, Equipe

        query = (
            select(AlocacaoRecursoProjeto)
            .options(
                joinedload(AlocacaoRecursoProjeto.equipe).joinedload(Equipe.secao),
                joinedload(AlocacaoRecursoProjeto.recurso),
                joinedload(AlocacaoRecursoProjeto.projeto),
                joinedload(AlocacaoRecursoProjeto.status_alocacao)
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
        from sqlalchemy import select
        from sqlalchemy.orm import joinedload
        from app.db.orm_models import AlocacaoRecursoProjeto, Equipe

        query = (
            select(AlocacaoRecursoProjeto)
            .options(
                joinedload(AlocacaoRecursoProjeto.equipe).joinedload(Equipe.secao),
                joinedload(AlocacaoRecursoProjeto.recurso),
                joinedload(AlocacaoRecursoProjeto.projeto),
                joinedload(AlocacaoRecursoProjeto.status_alocacao)
            )
            .filter(AlocacaoRecursoProjeto.id == alocacao_id)
        )
        result = await self.db.execute(query)
        alocacao_completa = result.scalars().first()

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
            "status_alocacao_id": alocacao.status_alocacao_id,
            "status_alocacao_nome": getattr(alocacao.status_alocacao, "nome", None) if hasattr(alocacao, "status_alocacao") and alocacao.status_alocacao else None,
            "data_criacao": alocacao.data_criacao,
            "data_atualizacao": alocacao.data_atualizacao,
            "recurso_nome": getattr(alocacao.recurso, "nome", None) if hasattr(alocacao, "recurso") and alocacao.recurso else None,
            "projeto_nome": getattr(alocacao.projeto, "nome", None) if hasattr(alocacao, "projeto") and alocacao.projeto else None,
        "observacao": getattr(alocacao, "observacao", None)
        }
        return result
