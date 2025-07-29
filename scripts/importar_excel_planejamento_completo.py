#!/usr/bin/env python3
"""
Script para importar dados de planejamento do Excel para o banco de dados.
"""

import os
import sys
import pandas as pd
import re
import logging
from datetime import date
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Adicionar o diretório raiz ao path para importar módulos do app
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from app.db.orm_models import (
    Recurso, Projeto, Equipe, StatusProjeto, AlocacaoRecursoProjeto, 
    HorasPlanejadas, Secao
)
from app.core.config import Settings

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('importacao_planejamento.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ImportadorExcelPlanejamento:
    """Classe para importar dados de planejamento do Excel."""
    
    def __init__(self, arquivo_excel: str, nome_aba: str):
        self.arquivo_excel = arquivo_excel
        self.nome_aba = nome_aba
        self.session = None
        self.estatisticas = {
            'projetos_inseridos': 0,
            'alocacoes_criadas': 0,
            'alocacoes_atualizadas': 0,
            'horas_planejadas_inseridas': 0,
            'erros': 0
        }
    
    def conectar_banco(self):
        """Conecta ao banco de dados."""
        try:
            settings = Settings()
            # Criar URL síncrona para SQLAlchemy
            from urllib.parse import quote_plus
            password = quote_plus(settings.DB_PASSWORD)
            database_url = f"postgresql://{settings.DB_USER}:{password}@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
            
            engine = create_engine(database_url)
            Session = sessionmaker(bind=engine)
            self.session = Session()
            logger.info("Conectado ao banco de dados")
        except Exception as e:
            logger.error(f"Erro ao conectar ao banco: {e}")
            raise
    
    def ler_planilha(self) -> pd.DataFrame:
        """Lê a planilha Excel."""
        try:
            df = pd.read_excel(
                self.arquivo_excel,
                sheet_name=self.nome_aba,
                engine='openpyxl',
                keep_default_na=False,
                na_values=[],
                dtype=str
            )
            logger.info(f"Planilha lida: {df.shape[0]} linhas x {df.shape[1]} colunas")
            return df
        except Exception as e:
            logger.error(f"Erro ao ler planilha: {e}")
            raise
    
    def extrair_equipe_do_arquivo(self) -> str:
        """Extrai nome da equipe do nome do arquivo."""
        nome_arquivo = os.path.basename(self.arquivo_excel)
        nome_sem_extensao = os.path.splitext(nome_arquivo)[0]
        return nome_sem_extensao.replace('SGI ', '').strip()
    
    def extrair_email_recurso(self, df: pd.DataFrame) -> str:
        """Extrai email do recurso da célula E7."""
        try:
            if len(df) > 6 and len(df.columns) > 4:
                email = str(df.iloc[6, 4]).strip()
                return email if email and email != 'nan' else None
        except:
            pass
        return None
    
    def buscar_equipe_por_nome(self, nome: str) -> Optional[Equipe]:
        """Busca equipe por nome."""
        try:
            return self.session.query(Equipe).filter(Equipe.nome.ilike(f'%{nome}%')).first()
        except Exception as e:
            logger.error(f"Erro ao buscar equipe: {e}")
            return None
    
    def buscar_status_por_nome(self, nome: str) -> Optional[StatusProjeto]:
        """Busca status por nome."""
        try:
            return self.session.query(StatusProjeto).filter(StatusProjeto.nome.ilike(f'%{nome}%')).first()
        except Exception as e:
            logger.error(f"Erro ao buscar status: {e}")
            return None
    
    def criar_ou_atualizar_recurso(self, nome: str, email: str, equipe: Equipe) -> Optional[Recurso]:
        """Cria ou atualiza recurso."""
        try:
            # Buscar recurso existente
            recurso = self.session.query(Recurso).filter(Recurso.nome == nome).first()
            
            if recurso:
                logger.info(f"Recurso encontrado: {nome}")
                return recurso
            
            # Criar novo recurso
            novo_recurso = Recurso(
                nome=nome,
                email=email,
                equipe_id=equipe.id if equipe else None,
                ativo=True
            )
            
            self.session.add(novo_recurso)
            self.session.flush()
            
            logger.info(f"Recurso criado: {nome}")
            return novo_recurso
            
        except Exception as e:
            logger.error(f"Erro ao criar/atualizar recurso: {e}")
            return None
    
    def inserir_projeto(self, nome_projeto: str) -> Optional[Projeto]:
        """Insere projeto se não existir."""
        try:
            # Verificar se projeto já existe
            projeto_existente = self.session.query(Projeto).filter(Projeto.nome == nome_projeto).first()
            if projeto_existente:
                logger.info(f"Projeto já existe: {nome_projeto}")
                return projeto_existente
            
            # Buscar seção padrão
            secao = self.session.query(Secao).first()
            if not secao:
                logger.error("Nenhuma seção encontrada no banco")
                return None
            
            # Buscar status padrão
            status_padrao = self.session.query(StatusProjeto).first()
            if not status_padrao:
                logger.error("Nenhum status encontrado no banco")
                return None
            
            # Criar novo projeto
            novo_projeto = Projeto(
                nome=nome_projeto.strip(),
                secao_id=secao.id,
                status_projeto_id=status_padrao.id,
                data_inicio_prevista=date(2025, 1, 1),
                ativo=True
            )
            
            self.session.add(novo_projeto)
            self.session.flush()
            
            logger.info(f"Projeto inserido: {nome_projeto}")
            self.estatisticas['projetos_inseridos'] += 1
            
            return novo_projeto
            
        except Exception as e:
            logger.error(f"Erro ao inserir projeto '{nome_projeto}': {e}")
            self.estatisticas['erros'] += 1
            return None
    
    def criar_alocacao(self, recurso: Recurso, projeto: Projeto, equipe: Equipe, 
                      status: StatusProjeto, esforco_estimado: float, observacao: str = None) -> Optional[AlocacaoRecursoProjeto]:
        """Cria alocação do recurso no projeto."""
        try:
            # Verificar se alocação já existe
            alocacao_existente = self.session.query(AlocacaoRecursoProjeto).filter(
                AlocacaoRecursoProjeto.recurso_id == recurso.id,
                AlocacaoRecursoProjeto.projeto_id == projeto.id,
                AlocacaoRecursoProjeto.data_inicio_alocacao == date(2025, 1, 1)
            ).first()

            if alocacao_existente:
                logger.info(f"Alocação já existe (ID: {alocacao_existente.id})")
                
                # Atualizar esforço estimado se necessário
                if esforco_estimado is not None:
                    novo_valor = Decimal(str(esforco_estimado))
                    valor_atual = alocacao_existente.esforco_estimado
                    if valor_atual != novo_valor:
                        logger.info(f"Atualizando esforço: {valor_atual} -> {novo_valor}")
                        alocacao_existente.esforco_estimado = novo_valor
                        self.session.flush()
                        self.estatisticas.setdefault('alocacoes_atualizadas', 0)
                        self.estatisticas['alocacoes_atualizadas'] += 1
                    else:
                        logger.info(f"Esforço já está correto: {valor_atual}")
                
                # Atualizar status se necessário
                novo_status_id = status.id if status else None
                logger.info(f"DEBUG STATUS - Atual: {alocacao_existente.status_alocacao_id}, Novo: {novo_status_id}")
                if alocacao_existente.status_alocacao_id != novo_status_id:
                    logger.info(f"Atualizando status: {alocacao_existente.status_alocacao_id} -> {novo_status_id}")
                    alocacao_existente.status_alocacao_id = novo_status_id
                    self.session.flush()
                    self.estatisticas.setdefault('alocacoes_atualizadas', 0)
                    self.estatisticas['alocacoes_atualizadas'] += 1
                else:
                    logger.info(f"Status já está correto: {alocacao_existente.status_alocacao_id}")
                
                # Atualizar observação se necessário
                nova_observacao = observacao if observacao and observacao.strip() else None
                if alocacao_existente.observacao != nova_observacao:
                    logger.info(f"Atualizando observação: '{alocacao_existente.observacao}' -> '{nova_observacao}'")
                    alocacao_existente.observacao = nova_observacao
                    self.session.flush()
                else:
                    logger.info(f"Observação já está correta: '{alocacao_existente.observacao}'")
                        
                return alocacao_existente
            
            # Criar nova alocação
            logger.info(f"Criando nova alocação com esforço: {esforco_estimado}")
            
            nova_alocacao = AlocacaoRecursoProjeto(
                recurso_id=recurso.id,
                projeto_id=projeto.id,
                equipe_id=equipe.id if equipe else None,
                status_alocacao_id=status.id if status else None,
                observacao=observacao if observacao and observacao.strip() else None,
                data_inicio_alocacao=date(2025, 1, 1),
                esforco_estimado=Decimal(str(esforco_estimado)) if esforco_estimado is not None else None
            )
            
            self.session.add(nova_alocacao)
            self.session.flush()
            
            logger.info(f"Alocação criada (ID: {nova_alocacao.id})")
            self.estatisticas['alocacoes_criadas'] += 1
            
            return nova_alocacao
            
        except Exception as e:
            logger.error(f"Erro ao criar alocação: {e}")
            self.estatisticas['erros'] += 1
            return None
    
    def processar_linha_projeto(self, linha: pd.Series, recurso: Recurso, 
                               equipe: Equipe, colunas_horas: List[str], 
                               df: pd.DataFrame, linha_index: int) -> bool:
        """Processa uma linha de projeto da planilha."""
        try:
            # Extrair dados da linha
            nome_projeto = str(linha.iloc[0]).strip()
            observacao = str(linha.iloc[1]).strip() if len(linha) > 1 else ''  # Coluna B
            status_nome = str(linha.iloc[2]).strip() if len(linha) > 2 else ''
            
            logger.info(f"Processando projeto: {nome_projeto} (linha {linha_index + 1})")
            logger.info(f"Observação (coluna B): '{observacao}'")
            logger.info(f"Status (coluna C): '{status_nome}'")
            
            # Extrair esforço estimado da coluna F (índice 5)
            esforco_estimado = None
            esforco_str = ''
            
            try:
                if len(df.columns) > 5:
                    esforco_str = str(df.iloc[linha_index, 5]).strip()
                    logger.info(f"Esforço bruto da coluna F: '{esforco_str}'")
                    
                    # USAR APENAS COLUNA F - NÃO FAZER FALLBACK
                    # Se coluna F estiver vazia, deixar esforço como NULL
                    if not esforco_str or esforco_str in ['', 'nan', 'NaN', 'None', 'null']:
                        logger.info("Coluna F vazia - esforço será NULL")
                        esforco_str = ''  # Forçar vazio para não processar
                    
                    if esforco_str and esforco_str not in ['', 'nan', 'NaN', 'None', 'null']:
                        # Limpar e converter
                        esforco_limpo = esforco_str.replace(',', '.').replace(' ', '')
                        esforco_limpo = re.sub(r'[^\d.]', '', esforco_limpo)
                        
                        if esforco_limpo:
                            esforco_estimado = float(esforco_limpo)
                            logger.info(f"[OK] Esforço estimado: {esforco_estimado}h")
                        else:
                            logger.debug(f"Valor vazio após limpeza: '{esforco_str}'")
                    else:
                        logger.debug(f"Esforço não informado para projeto: {nome_projeto}")
                        
            except Exception as e:
                logger.error(f"Erro ao extrair esforço: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
            
            # 1. Inserir projeto
            projeto = self.inserir_projeto(nome_projeto)
            if not projeto:
                return False
            
            # 2. Buscar status
            status = None
            if status_nome and status_nome.strip() and status_nome.strip().lower() not in ['', 'nan', 'none', 'null']:
                status = self.buscar_status_por_nome(status_nome.strip())
                if status:
                    logger.info(f"Status encontrado: {status.nome}")
                else:
                    logger.info(f"Status não encontrado para: '{status_nome}'")
            else:
                logger.info(f"Status vazio na planilha - será NULL no banco")
            
            # 3. Criar alocação
            alocacao = self.criar_alocacao(recurso, projeto, equipe, status, esforco_estimado, observacao)
            if not alocacao:
                return False
            
            # 4. Extrair horas mensais
            horas_mensais = {}
            for col_nome in colunas_horas:
                try:
                    valor_str = str(linha.get(col_nome, '')).strip()
                    base_nome = col_nome.split('.')[0]
                    # Corrigir jan/262 -> jan/26
                    if base_nome == 'jan/262':
                        base_nome = 'jan/26'
                    if valor_str and valor_str not in ['', 'nan', 'NaN']:
                        valor_limpo = valor_str.replace(',', '.')
                        horas = float(valor_limpo)
                        # Filtrar apenas valores negativos (manter zero)
                        if horas >= 0:
                            horas_mensais[base_nome] = horas
                            if horas == 0:
                                logger.debug(f"Incluindo valor zero para {col_nome}: {horas}")
                        else:
                            logger.debug(f"Ignorando valor negativo para {col_nome}: {horas}")
                except ValueError:
                    continue
            
            # 5. Inserir horas planejadas
            if horas_mensais:
                inseridas = self.inserir_horas_planejadas(alocacao, horas_mensais)
                logger.info(f"Horas planejadas inseridas: {inseridas}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar linha: {e}")
            self.estatisticas['erros'] += 1
            return False
    
    def inserir_horas_planejadas(self, alocacao: AlocacaoRecursoProjeto, horas_mensais: dict) -> int:
        """Insere horas planejadas."""
        inseridos = 0
        try:
            for mes_ano, horas in horas_mensais.items():
                try:
                    # Extrair mês e ano
                    mes_nome, ano_str = mes_ano.split('/')
                    ano = 2000 + int(ano_str)
                    
                    # Converter nome do mês para número
                    meses = {
                        'jan': 1, 'fev': 2, 'mar': 3, 'abr': 4, 'mai': 5, 'jun': 6,
                        'jul': 7, 'ago': 8, 'set': 9, 'out': 10, 'nov': 11, 'dez': 12
                    }
                    mes_num = meses.get(mes_nome.lower(), 1)
                    
                    # Verificar se já existe
                    horas_existente = self.session.query(HorasPlanejadas).filter(
                        HorasPlanejadas.alocacao_id == alocacao.id,
                        HorasPlanejadas.ano == ano,
                        HorasPlanejadas.mes == mes_num
                    ).first()
                    
                    if horas_existente:
                        logger.info(f"Horas já existem: {mes_ano} - {horas}h")
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
                    
                except ValueError as e:
                    logger.warning(f"Erro ao processar mês {mes_ano}: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Erro ao inserir horas planejadas: {e}")
            
        self.estatisticas['horas_planejadas_inseridas'] += inseridos
        return inseridos
    
    def processar_aba(self) -> bool:
        """Processa uma aba da planilha."""
        try:
            logger.info(f"Iniciando processamento da aba: {self.nome_aba}")
            
            # 1. Ler planilha
            df = self.ler_planilha()
            
            # 2. Extrair nome da equipe
            nome_equipe = self.extrair_equipe_do_arquivo()
            
            # 3. Extrair email do recurso
            email_recurso = self.extrair_email_recurso(df)
            
            # 4. Buscar equipe
            equipe = self.buscar_equipe_por_nome(nome_equipe)
            
            # 5. Criar ou atualizar recurso
            recurso = self.criar_ou_atualizar_recurso(self.nome_aba, email_recurso, equipe)
            if not recurso:
                logger.error(f"Falha ao criar/atualizar recurso: {self.nome_aba}")
                return False
            
            # 6. Extrair colunas de horas (considerar duplicatas e erros como 'jan/262')
            padrao_mes_base = re.compile(r'^[a-zA-Z]{3}/\d{2,3}$')  # 2 ou 3 dígitos
            colunas_horas = []
            for c in df.columns:
                base = str(c).strip().split('.')[0]
                if padrao_mes_base.match(base):
                    # Corrigir jan/262 -> jan/26
                    if base == 'jan/262':
                        base = 'jan/26'
                    colunas_horas.append(c)
            
            logger.info(f"Colunas de horas identificadas: {colunas_horas}")
            logger.info(f"TODAS AS COLUNAS: {list(df.columns)}")
            logger.info(f"COLUNAS QUE COMEÇAM COM 'jan': {[c for c in df.columns if 'jan' in str(c).lower()]}")
            
            # 7. Processar linhas de projetos
            projetos_processados = 0
            
            for index, linha in df.iterrows():
                # Logar nome da linha e amostra de horas (primeiras 3 colunas de horas) para debug de desalinhamento
                try:
                    sample_hours = [str(linha.get(c, '')).strip() for c in colunas_horas[:3]] if colunas_horas else []
                    logger.info(f"ROW_ORIG {index + 1}: '{str(linha.iloc[0]).strip()}' | sample_hours: {sample_hours}")
                except Exception:
                    pass
                # Nome do possível projeto na coluna A
                nome_projeto_temp = str(linha.iloc[0]).strip() if len(linha) > 0 else ''

                # Filtro para identificar projetos válidos
                cabecalhos_ignorar = {
                    '', 'nan', 'NaN', 'None', 'gap', 'epic', 'ações', 
                    'horas disponíveis', 'total de esforço (hrs)', 'total de esforço',
                    'seg - global infrastructure', 'sap basis & db'
                }
                
                # Verificar se é linha de projeto válido
                nome_lower = nome_projeto_temp.lower().strip()
                
                # Ignorar cabeçalhos conhecidos
                if nome_lower in cabecalhos_ignorar:
                    logger.debug(f"Linha {index + 1} ignorada (cabeçalho): '{nome_projeto_temp}'")
                    continue
                
                # NÃO ignorar por status vazio - projetos podem ter status NULL
                
                # Deve ter pelo menos 3 caracteres
                if len(nome_projeto_temp) < 3:
                    logger.debug(f"Linha {index + 1} ignorada (nome muito curto): '{nome_projeto_temp}'")
                    continue
                
                # Processar linha considerada projeto
                logger.info(f"\n--- Processando linha {index + 1} ---")
                logger.info(f"Projeto detectado: '{nome_projeto_temp}'")

                if self.processar_linha_projeto(linha, recurso, equipe, colunas_horas, df, index):
                    projetos_processados += 1
                    logger.info("[OK] Projeto processado com sucesso")
                else:
                    logger.error("[ERRO] Falha ao processar projeto")
            
            logger.info(f"Total de projetos processados: {projetos_processados}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar aba: {e}")
            return False
    
    def executar(self) -> bool:
        """Executa o processo completo de importação."""
        try:
            logger.info("=== INICIANDO IMPORTAÇÃO DE PLANEJAMENTO ===")
            logger.info(f"Arquivo: {self.arquivo_excel}")
            logger.info(f"Aba: {self.nome_aba}")
            
            # Conectar ao banco
            self.conectar_banco()
            
            # Processar aba
            sucesso = self.processar_aba()
            
            if sucesso:
                self.session.commit()
                logger.info("=== IMPORTAÇÃO CONCLUÍDA COM SUCESSO ===")
                logger.info(f"Estatísticas: {self.estatisticas}")
            else:
                self.session.rollback()
                logger.error("=== IMPORTAÇÃO FALHOU ===")
            
            return sucesso
            
        except Exception as e:
            logger.error(f"Erro na execução: {e}")
            if self.session:
                self.session.rollback()
            return False
        finally:
            if self.session:
                self.session.close()


def main():
    """Função principal."""
    if len(sys.argv) != 3:
        print("Uso: python importar_excel_planejamento_completo.py <arquivo_excel> <nome_aba>")
        sys.exit(1)
    
    arquivo_excel = sys.argv[1]
    nome_aba = sys.argv[2]
    
    if not os.path.exists(arquivo_excel):
        print(f"Arquivo não encontrado: {arquivo_excel}")
        sys.exit(1)
    
    importador = ImportadorExcelPlanejamento(arquivo_excel, nome_aba)
    sucesso = importador.executar()
    
    sys.exit(0 if sucesso else 1)


if __name__ == "__main__":
    main()
