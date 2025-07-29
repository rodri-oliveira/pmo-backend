#!/usr/bin/env python3
"""
Script para importar dados de planejamento do Excel para o banco de dados.

Processa planilhas Excel com estrutura padronizada para:
- Inserir projetos na tabela 'projeto'
- Criar alocações na tabela 'alocacao_recurso_projeto'
- Inserir horas planejadas na tabela 'horas_planejadas_alocacao'

Autor: Sistema de Automação PMO
Data: 28/07/2025
"""

import sys
import os
import pandas as pd
import logging
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Optional, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Adicionar o diretório raiz ao path para importar módulos do app
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

from app.db.session import get_db_session
from app.db.orm_models import (
    Projeto, Recurso, Equipe, Secao, StatusProjeto,
    AlocacaoRecursoProjeto, HorasPlanejadas
)

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('importar_excel_planejamento.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ImportadorExcelPlanejamento:
    """Classe para importar dados de planejamento do Excel."""
    
    def __init__(self, arquivo_excel: str, nome_aba: str):
        """
        Inicializa o importador.
        
        Args:
            arquivo_excel: Caminho para o arquivo Excel
            nome_aba: Nome da aba a ser processada
        """
        self.arquivo_excel = arquivo_excel
        self.nome_aba = nome_aba
        self.session = None
        self.estatisticas = {
            'projetos_inseridos': 0,
            'projetos_existentes': 0,
            'alocacoes_criadas': 0,
            'horas_planejadas_inseridas': 0,
            'erros': 0
        }
        
        # Mapeamento de meses para números
        self.meses_map = {
            'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
            'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
        }
    
    def conectar_banco(self):
        """Conecta ao banco de dados."""
        try:
            self.session = next(get_db_session())
            logger.info("Conexão com banco de dados estabelecida")
        except Exception as e:
            logger.error(f"Erro ao conectar com banco: {e}")
            raise
    
    def desconectar_banco(self):
        """Desconecta do banco de dados."""
        if self.session:
            self.session.close()
            logger.info("Conexão com banco de dados fechada")
    
    def ler_planilha(self) -> pd.DataFrame:
        """
        Lê a planilha Excel.
        
        Returns:
            DataFrame com os dados da planilha
        """
        try:
            logger.info(f"Lendo planilha: {self.arquivo_excel}, aba: {self.nome_aba}")
            
            # Ler como CSV se for arquivo .csv
            if self.arquivo_excel.endswith('.csv'):
                df = pd.read_csv(self.arquivo_excel, sep=';', encoding='utf-8')
            else:
                df = pd.read_excel(self.arquivo_excel, sheet_name=self.nome_aba)
            
            logger.info(f"Planilha lida com sucesso. {len(df)} linhas encontradas")
            return df
            
        except Exception as e:
            logger.error(f"Erro ao ler planilha: {e}")
            raise
    
    def extrair_nome_equipe(self, df: pd.DataFrame) -> str:
        """
        Extrai o nome da equipe da célula A6.
        
        Args:
            df: DataFrame com os dados
            
        Returns:
            Nome da equipe
        """
        try:
            # A6 corresponde à linha 5 (índice 5) na coluna 0
            if len(df) > 5:
                nome_equipe = str(df.iloc[5, 0]).strip()
                logger.info(f"Nome da equipe extraído: {nome_equipe}")
                return nome_equipe
            else:
                raise ValueError("Planilha não possui linha A6")
                
        except Exception as e:
            logger.error(f"Erro ao extrair nome da equipe: {e}")
            raise
    
    def buscar_recurso_por_nome(self, nome_recurso: str) -> Optional[Recurso]:
        """
        Busca recurso pelo nome.
        
        Args:
            nome_recurso: Nome do recurso
            
        Returns:
            Objeto Recurso ou None se não encontrado
        """
        try:
            recurso = self.session.query(Recurso).filter(
                Recurso.nome.ilike(f"%{nome_recurso}%")
            ).first()
            
            if recurso:
                logger.info(f"Recurso encontrado: {recurso.nome} (ID: {recurso.id})")
            else:
                logger.warning(f"Recurso não encontrado: {nome_recurso}")
                
            return recurso
            
        except Exception as e:
            logger.error(f"Erro ao buscar recurso: {e}")
            return None
    
    def buscar_equipe_por_nome(self, nome_equipe: str) -> Optional[Equipe]:
        """
        Busca equipe pelo nome.
        
        Args:
            nome_equipe: Nome da equipe
            
        Returns:
            Objeto Equipe ou None se não encontrado
        """
        try:
            equipe = self.session.query(Equipe).filter(
                Equipe.nome.ilike(f"%{nome_equipe}%")
            ).first()
            
            if equipe:
                logger.info(f"Equipe encontrada: {equipe.nome} (ID: {equipe.id})")
            else:
                logger.warning(f"Equipe não encontrada: {nome_equipe}")
                
            return equipe
            
        except Exception as e:
            logger.error(f"Erro ao buscar equipe: {e}")
            return None
    
    def buscar_status_por_nome(self, nome_status: str) -> Optional[StatusProjeto]:
        """
        Busca status pelo nome.
        
        Args:
            nome_status: Nome do status
            
        Returns:
            Objeto StatusProjeto ou None se não encontrado
        """
        try:
            # Mapeamento de status da planilha para o banco
            mapeamento_status = {
                'em andamento': 'Em Andamento',
                'concluído': 'Concluído',
                'concluido': 'Concluído',
                'finalizado': 'Finalizado',
                'pausado': 'Pausado'
            }
            
            nome_normalizado = nome_status.lower().strip()
            nome_banco = mapeamento_status.get(nome_normalizado, nome_status)
            
            status = self.session.query(StatusProjeto).filter(
                StatusProjeto.nome.ilike(f"%{nome_banco}%")
            ).first()
            
            if status:
                logger.info(f"Status encontrado: {status.nome} (ID: {status.id})")
            else:
                logger.warning(f"Status não encontrado: {nome_status}")
                
            return status
            
        except Exception as e:
            logger.error(f"Erro ao buscar status: {e}")
            return None
    
    def inserir_projeto(self, nome_projeto: str, secao_id: int = None) -> Optional[Projeto]:
        """
        Insere projeto se não existir.
        
        Args:
            nome_projeto: Nome do projeto
            secao_id: ID da seção (opcional)
            
        Returns:
            Objeto Projeto criado ou existente
        """
        try:
            # Verificar se projeto já existe
            projeto_existente = self.session.query(Projeto).filter(
                Projeto.nome == nome_projeto.strip()
            ).first()
            
            if projeto_existente:
                logger.info(f"Projeto já existe: {nome_projeto} (ID: {projeto_existente.id})")
                self.estatisticas['projetos_existentes'] += 1
                return projeto_existente
            
            # Buscar status padrão (assumindo que existe um status "Em Andamento")
            status_padrao = self.session.query(StatusProjeto).filter(
                StatusProjeto.nome.ilike("%andamento%")
            ).first()
            
            if not status_padrao:
                # Se não encontrar, usar o primeiro status disponível
                status_padrao = self.session.query(StatusProjeto).first()
            
            if not status_padrao:
                logger.error("Nenhum status encontrado no banco de dados")
                return None
            
            # Criar novo projeto
            novo_projeto = Projeto(
                nome=nome_projeto.strip(),
                secao_id=secao_id,
                status_projeto_id=status_padrao.id,
                data_inicio_prevista=date(2025, 1, 1),  # jan/25 conforme especificado
                ativo=True
            )
            
            self.session.add(novo_projeto)
            self.session.flush()  # Para obter o ID
            
            logger.info(f"Projeto inserido: {nome_projeto} (ID: {novo_projeto.id})")
            self.estatisticas['projetos_inseridos'] += 1
            
            return novo_projeto
            
        except Exception as e:
            logger.error(f"Erro ao inserir projeto '{nome_projeto}': {e}")
            self.estatisticas['erros'] += 1
            return None
    
    def criar_alocacao(self, recurso: Recurso, projeto: Projeto, equipe: Equipe, 
                      status: StatusProjeto, esforco_estimado: float) -> Optional[AlocacaoRecursoProjeto]:
        """
        Cria alocação do recurso no projeto.
        
        Args:
            recurso: Objeto Recurso
            projeto: Objeto Projeto
            equipe: Objeto Equipe
            status: Objeto StatusProjeto
            esforco_estimado: Esforço estimado em horas
            
        Returns:
            Objeto AlocacaoRecursoProjeto criado
        """
        try:
            # Verificar se alocação já existe
            alocacao_existente = self.session.query(AlocacaoRecursoProjeto).filter(
                AlocacaoRecursoProjeto.recurso_id == recurso.id,
                AlocacaoRecursoProjeto.projeto_id == projeto.id,
                AlocacaoRecursoProjeto.data_inicio_alocacao == date(2025, 1, 1)
            ).first()
            
            if alocacao_existente:
                logger.info(f"Alocação já existe: Recurso {recurso.nome} -> Projeto {projeto.nome}")
                return alocacao_existente
            
            # Criar nova alocação
            nova_alocacao = AlocacaoRecursoProjeto(
                recurso_id=recurso.id,
                projeto_id=projeto.id,
                equipe_id=equipe.id if equipe else None,
                status_alocacao_id=status.id if status else None,
                data_inicio_alocacao=date(2025, 1, 1),  # jan/25
                esforco_estimado=Decimal(str(esforco_estimado)) if esforco_estimado else None
            )
            
            self.session.add(nova_alocacao)
            self.session.flush()  # Para obter o ID
            
            logger.info(f"Alocação criada: Recurso {recurso.nome} -> Projeto {projeto.nome} (ID: {nova_alocacao.id})")
            self.estatisticas['alocacoes_criadas'] += 1
            
            return nova_alocacao
            
        except Exception as e:
            logger.error(f"Erro ao criar alocação: {e}")
            self.estatisticas['erros'] += 1
            return None
    
    def inserir_horas_planejadas(self, alocacao: AlocacaoRecursoProjeto, 
                                horas_mensais: Dict[str, float]) -> int:
        """
        Insere horas planejadas para a alocação.
        
        Args:
            alocacao: Objeto AlocacaoRecursoProjeto
            horas_mensais: Dicionário com horas por mês
            
        Returns:
            Número de registros inseridos
        """
        try:
            inseridos = 0
            
            for mes_ano, horas in horas_mensais.items():
                if horas and horas > 0:
                    # Extrair mês e ano do formato "jan/25"
                    try:
                        mes_nome, ano_str = mes_ano.split('/')
                        mes_num = self.meses_map.get(mes_nome.lower())
                        ano = 2000 + int(ano_str)  # Converter 25 para 2025
                        
                        if not mes_num:
                            logger.warning(f"Mês inválido: {mes_nome}")
                            continue
                        
                        # Verificar se já existe
                        horas_existente = self.session.query(HorasPlanejadas).filter(
                            HorasPlanejadas.alocacao_id == alocacao.id,
                            HorasPlanejadas.ano == ano,
                            HorasPlanejadas.mes == mes_num
                        ).first()
                        
                        if horas_existente:
                            logger.info(f"Horas planejadas já existem: {mes_ano} - {horas}h")
                            continue
                        
                        # Inserir horas planejadas
                        novas_horas = HorasPlanejadas(
                            alocacao_id=alocacao.id,
                            ano=ano,
                            mes=mes_num,
                            horas_planejadas=Decimal(str(horas))
                        )
                        
                        self.session.add(novas_horas)
                        inseridos += 1
                        
                        logger.info(f"Horas planejadas inseridas: {mes_ano} - {horas}h")
                        
                    except ValueError as e:
                        logger.warning(f"Erro ao processar mês {mes_ano}: {e}")
                        continue
            
            self.estatisticas['horas_planejadas_inseridas'] += inseridos
            return inseridos
            
        except Exception as e:
            logger.error(f"Erro ao inserir horas planejadas: {e}")
            self.estatisticas['erros'] += 1
            return 0
    
    def processar_linha_projeto(self, linha: pd.Series, recurso: Recurso, 
                               equipe: Equipe, colunas_horas: List[str]) -> bool:
        """
        Processa uma linha de projeto da planilha.
        
        Args:
            linha: Série pandas com dados da linha
            recurso: Objeto Recurso
            equipe: Objeto Equipe
            colunas_horas: Lista com nomes das colunas de horas
            
        Returns:
            True se processado com sucesso, False caso contrário
        """
        try:
            # Extrair dados da linha
            nome_projeto = str(linha.iloc[0]).strip()  # Coluna A
            status_nome = str(linha.iloc[2]).strip()   # Coluna C
            esforco_str = str(linha.iloc[5]).strip()   # Coluna F
            
            # Validar nome do projeto
            if not nome_projeto or nome_projeto in ['', 'nan', 'NaN']:
                return False
            
            # Converter esforço estimado
            esforco_estimado = 0.0
            if esforco_str and esforco_str not in ['', 'nan', 'NaN']:
                try:
                    esforco_estimado = float(esforco_str.replace(',', '.'))
                except ValueError:
                    logger.warning(f"Esforço inválido para projeto {nome_projeto}: {esforco_str}")
            
            logger.info(f"Processando projeto: {nome_projeto}")
            
            # 1. Inserir projeto
            projeto = self.inserir_projeto(nome_projeto)
            if not projeto:
                return False
            
            # 2. Buscar status
            status = self.buscar_status_por_nome(status_nome) if status_nome else None
            
            # 3. Criar alocação
            alocacao = self.criar_alocacao(recurso, projeto, equipe, status, esforco_estimado)
            if not alocacao:
                return False
            
            # 4. Extrair horas mensais (a partir da coluna M - índice 12)
            horas_mensais = {}
            for i, col_nome in enumerate(colunas_horas):
                try:
                    col_index = 12 + i  # Coluna M é índice 12
                    if col_index < len(linha):
                        valor_str = str(linha.iloc[col_index]).strip()
                        if valor_str and valor_str not in ['', 'nan', 'NaN']:
                            horas = float(valor_str.replace(',', '.'))
                            horas_mensais[col_nome] = horas
                except (ValueError, IndexError):
                    continue
            
            # 5. Inserir horas planejadas
            if horas_mensais:
                self.inserir_horas_planejadas(alocacao, horas_mensais)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar linha do projeto: {e}")
            self.estatisticas['erros'] += 1
            return False
    
    def processar_aba(self) -> bool:
        """
        Processa uma aba da planilha.
        
        Returns:
            True se processado com sucesso, False caso contrário
        """
        try:
            logger.info(f"Iniciando processamento da aba: {self.nome_aba}")
            
            # 1. Ler planilha
            df = self.ler_planilha()
            
            # 2. Extrair nome da equipe (A6)
            nome_equipe = self.extrair_nome_equipe(df)
            
            # 3. Buscar recurso pelo nome da aba
            recurso = self.buscar_recurso_por_nome(self.nome_aba)
            if not recurso:
                logger.error(f"Recurso não encontrado para a aba: {self.nome_aba}")
                return False
            
            # 4. Buscar equipe
            equipe = self.buscar_equipe_por_nome(nome_equipe)
            
            # 5. Extrair nomes das colunas de horas (a partir da coluna M)
            colunas_horas = []
            if len(df.columns) > 12:  # Coluna M é índice 12
                for col in df.columns[12:]:  # A partir da coluna M
                    col_str = str(col).strip()
                    if '/' in col_str:  # Formato "jan/25"
                        colunas_horas.append(col_str)
            
            logger.info(f"Colunas de horas identificadas: {colunas_horas}")
            
            # 6. Processar linhas de projetos (a partir da linha 7 - índice 6)
            projetos_processados = 0
            for index, linha in df.iterrows():
                if index >= 6:  # Linha 7+ (índice 6+)
                    if self.processar_linha_projeto(linha, recurso, equipe, colunas_horas):
                        projetos_processados += 1
            
            logger.info(f"Processamento concluído. {projetos_processados} projetos processados")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar aba: {e}")
            return False
    
    def executar(self) -> bool:
        """
        Executa o processo completo de importação.
        
        Returns:
            True se executado com sucesso, False caso contrário
        """
        try:
            logger.info("=== INICIANDO IMPORTAÇÃO DE PLANEJAMENTO ===")
            logger.info(f"Arquivo: {self.arquivo_excel}")
            logger.info(f"Aba: {self.nome_aba}")
            
            # Conectar ao banco
            self.conectar_banco()
            
            # Processar aba
            sucesso = self.processar_aba()
            
            if sucesso:
                # Commit das transações
                self.session.commit()
                logger.info("Transações commitadas com sucesso")
            else:
                # Rollback em caso de erro
                self.session.rollback()
                logger.error("Rollback executado devido a erros")
            
            # Exibir estatísticas
            self.exibir_estatisticas()
            
            return sucesso
            
        except Exception as e:
            logger.error(f"Erro durante execução: {e}")
            if self.session:
                self.session.rollback()
            return False
            
        finally:
            self.desconectar_banco()
    
    def exibir_estatisticas(self):
        """Exibe estatísticas do processamento."""
        logger.info("=== ESTATÍSTICAS DO PROCESSAMENTO ===")
        logger.info(f"Projetos inseridos: {self.estatisticas['projetos_inseridos']}")
        logger.info(f"Projetos já existentes: {self.estatisticas['projetos_existentes']}")
        logger.info(f"Alocações criadas: {self.estatisticas['alocacoes_criadas']}")
        logger.info(f"Horas planejadas inseridas: {self.estatisticas['horas_planejadas_inseridas']}")
        logger.info(f"Erros encontrados: {self.estatisticas['erros']}")
        logger.info("=====================================")


def main():
    """Função principal."""
    # Configurações
    ARQUIVO_EXCEL = os.path.join(ROOT_DIR, "scripts", "excel", "SEG Blue Team.csv")
    NOME_ABA = "Blue Team & DevSecOps"  # Nome da aba = nome do recurso
    
    # Verificar se arquivo existe
    if not os.path.exists(ARQUIVO_EXCEL):
        logger.error(f"Arquivo não encontrado: {ARQUIVO_EXCEL}")
        return False
    
    # Executar importação
    importador = ImportadorExcelPlanejamento(ARQUIVO_EXCEL, NOME_ABA)
    sucesso = importador.executar()
    
    if sucesso:
        logger.info("Importação concluída com sucesso!")
        return True
    else:
        logger.error("Importação falhou!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
