# Substitua APENAS os métodos abaixo na classe ImportadorExcelPlanejamento

def processar_linha_projeto(self, linha: pd.Series, recurso: Recurso, 
                           equipe: Equipe, colunas_horas: List[str], df: pd.DataFrame = None, linha_index: int = None) -> bool:
    """
    Processa uma linha de projeto da planilha.
    
    Args:
        linha: Série pandas com dados da linha
        recurso: Objeto Recurso
        equipe: Objeto Equipe
        colunas_horas: Lista com nomes das colunas de horas
        df: DataFrame completo (para acessar por posição absoluta)
        linha_index: Índice da linha no DataFrame
        
    Returns:
        True se processado com sucesso, False caso contrário
    """
    try:
        # Extrair dados da linha
        nome_projeto = str(linha.iloc[0]).strip()  # Coluna A
        status_nome = str(linha.iloc[2]).strip()   # Coluna C
        
        logger.info(f"Processando projeto: {nome_projeto} (linha {linha_index + 1})")
        
        # === CORREÇÃO PRINCIPAL: Extração do Esforço Estimado ===
        esforco_estimado = None
        esforco_str = ''
        
        try:
            # Método 1: Tentar extrair da coluna F usando o DataFrame completo
            if df is not None and linha_index is not None:
                # Verificar se temos colunas suficientes
                if len(df.columns) > 5:  # Coluna F = índice 5
                    valor_bruto = df.iloc[linha_index, 5]
                    esforco_str = str(valor_bruto).strip()
                    logger.debug(f"Método 1 - DataFrame[{linha_index}, 5]: '{esforco_str}' (tipo: {type(valor_bruto)})")
                else:
                    logger.warning(f"DataFrame tem apenas {len(df.columns)} colunas, coluna F não existe!")
            
            # Método 2 (fallback): Tentar extrair da linha atual
            if not esforco_str or esforco_str in ['', 'nan', 'NaN', 'None']:
                if len(linha) > 5:
                    valor_bruto_linha = linha.iloc[5]
                    esforco_str = str(valor_bruto_linha).strip()
                    logger.debug(f"Método 2 - linha.iloc[5]: '{esforco_str}' (tipo: {type(valor_bruto_linha)})")
            
            # Método 3 (última tentativa): Buscar por nome de coluna
            if not esforco_str or esforco_str in ['', 'nan', 'NaN', 'None']:
                # Procurar colunas que possam conter esforço estimado
                possiveis_colunas = ['esforco', 'estimado', 'total', 'horas', 'esforço']
                for col in df.columns if df is not None else []:
                    col_lower = str(col).lower()
                    if any(termo in col_lower for termo in possiveis_colunas):
                        try:
                            valor_col = df.iloc[linha_index, df.columns.get_loc(col)]
                            esforco_str = str(valor_col).strip()
                            logger.debug(f"Método 3 - Coluna '{col}': '{esforco_str}'")
                            break
                        except:
                            continue
            
            # Processar o valor extraído
            if esforco_str and esforco_str not in ['', 'nan', 'NaN', 'None', 'null']:
                # Limpar e normalizar o valor
                esforco_limpo = esforco_str.replace(',', '.').replace(' ', '').replace('\n', '').replace('\r', '')
                
                # Remover caracteres não numéricos (exceto ponto decimal)
                import re
                esforco_limpo = re.sub(r'[^\d.]', '', esforco_limpo)
                
                logger.debug(f"Valor após limpeza: '{esforco_limpo}' (original: '{esforco_str}')")
                
                # Tentar converter para float
                if esforco_limpo and esforco_limpo != '':
                    try:
                        esforco_estimado = float(esforco_limpo)
                        if esforco_estimado < 0:
                            logger.warning(f"Esforço negativo convertido para positivo: {esforco_estimado} -> {abs(esforco_estimado)}")
                            esforco_estimado = abs(esforco_estimado)
                        logger.info(f"✓ Esforço estimado extraído: {esforco_estimado}h")
                    except ValueError as e:
                        logger.warning(f"Erro na conversão final para float: '{esforco_limpo}' - {e}")
                        esforco_estimado = None
                else:
                    logger.debug(f"Valor vazio após limpeza para projeto '{nome_projeto}'")
            else:
                logger.debug(f"Projeto '{nome_projeto}': Esforço estimado não informado")
                
        except Exception as e:
            logger.error(f"Erro ao extrair esforço estimado para projeto '{nome_projeto}': {e}")
            esforco_estimado = None
        
        # === DEBUG: Log detalhado dos valores encontrados ===
        logger.info(f"RESULTADO EXTRAÇÃO - Projeto: {nome_projeto}")
        logger.info(f"  - Esforço bruto: '{esforco_str}'")
        logger.info(f"  - Esforço final: {esforco_estimado}")
        logger.info(f"  - Status: {status_nome}")
        
        # 1. Inserir projeto
        projeto = self.inserir_projeto(nome_projeto)
        if not projeto:
            return False
        
        # 2. Buscar status
        status = self.buscar_status_por_nome(status_nome) if status_nome else None
        
        # 3. Criar alocação (com esforço estimado corrigido)
        alocacao = self.criar_alocacao(recurso, projeto, equipe, status, esforco_estimado)
        if not alocacao:
            return False
        
        # 4. Extrair horas mensais (a partir da coluna M - índice 12)
        horas_mensais = {}
        for col_nome in colunas_horas:
            try:
                valor_str = str(linha.get(col_nome, '')).strip()
                if valor_str and valor_str not in ['', 'nan', 'NaN']:
                    # Aplicar mesma limpeza das horas mensais
                    valor_limpo = valor_str.replace(',', '.')
                    horas = float(valor_limpo)
                    horas_mensais[col_nome] = horas
                    logger.debug(f"Horas mensais {col_nome}: {horas}")
            except ValueError as e:
                logger.warning(f"Erro ao processar horas mensais {col_nome}: {valor_str} - {e}")
                continue
        
        # 5. Inserir horas planejadas
        if horas_mensais:
            inseridas = self.inserir_horas_planejadas(alocacao, horas_mensais)
            logger.info(f"Horas planejadas inseridas: {inseridas}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao processar linha do projeto '{nome_projeto}': {e}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        self.estatisticas['erros'] += 1
        return False


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
        logger.info(f"=== CRIANDO ALOCAÇÃO ===")
        logger.info(f"Recurso: {recurso.nome} (ID: {recurso.id})")
        logger.info(f"Projeto: {projeto.nome} (ID: {projeto.id})")
        logger.info(f"Esforço estimado recebido: {esforco_estimado} (tipo: {type(esforco_estimado)})")
        
        # Verificar se alocação já existe
        alocacao_existente = self.session.query(AlocacaoRecursoProjeto).filter(
            AlocacaoRecursoProjeto.recurso_id == recurso.id,
            AlocacaoRecursoProjeto.projeto_id == projeto.id,
            AlocacaoRecursoProjeto.data_inicio_alocacao == date(2025, 1, 1)
        ).first()

        # Converter esforço estimado para Decimal de forma segura
        esforco_decimal = None
        if esforco_estimado is not None:
            try:
                esforco_decimal = Decimal(str(esforco_estimado))
                logger.info(f"Esforço convertido para Decimal: {esforco_decimal}")
            except (ValueError, TypeError) as e:
                logger.error(f"Erro ao converter esforço para Decimal: {esforco_estimado} - {e}")
                esforco_decimal = None

        if alocacao_existente:
            logger.info(f"Alocação já existe (ID: {alocacao_existente.id})")
            
            # Atualizar esforço estimado se necessário
            if esforco_decimal is not None:
                valor_atual = alocacao_existente.esforco_estimado
                if valor_atual != esforco_decimal:
                    logger.info(f"Atualizando esforço: {valor_atual} -> {esforco_decimal}")
                    alocacao_existente.esforco_estimado = esforco_decimal
                    self.session.flush()  # Garantir que a atualização seja salva
                    self.estatisticas.setdefault('alocacoes_atualizadas', 0)
                    self.estatisticas['alocacoes_atualizadas'] += 1
                else:
                    logger.info(f"Esforço já está correto: {valor_atual}")
            elif alocacao_existente.esforco_estimado is not None:
                logger.info(f"Mantendo esforço existente: {alocacao_existente.esforco_estimado}")
                
            return alocacao_existente
        
        # Criar nova alocação
        logger.info(f"Criando nova alocação com esforço: {esforco_decimal}")
        
        nova_alocacao = AlocacaoRecursoProjeto(
            recurso_id=recurso.id,
            projeto_id=projeto.id,
            equipe_id=equipe.id if equipe else None,
            status_alocacao_id=status.id if status else None,
            data_inicio_alocacao=date(2025, 1, 1),  # jan/25
            esforco_estimado=esforco_decimal
        )
        
        self.session.add(nova_alocacao)
        self.session.flush()  # Para obter o ID
        
        logger.info(f"✓ Alocação criada com sucesso!")
        logger.info(f"  - ID: {nova_alocacao.id}")
        logger.info(f"  - Esforço salvo: {nova_alocacao.esforco_estimado}")
        
        self.estatisticas['alocacoes_criadas'] += 1
        
        return nova_alocacao
        
    except Exception as e:
        logger.error(f"Erro ao criar alocação: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        self.estatisticas['erros'] += 1
        return None


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
        
        # === DEBUG MELHORADO: Análise detalhada da estrutura ===
        logger.info(f"=== ANÁLISE DA ESTRUTURA DO ARQUIVO ===")
        logger.info(f"Dimensões: {df.shape[0]} linhas x {df.shape[1]} colunas")
        logger.info(f"Tipo do arquivo: {'CSV' if self.arquivo_excel.endswith('.csv') else 'Excel'}")
        
        # Mostrar cabeçalhos das colunas com seus índices
        logger.info(f"Colunas encontradas:")
        for i, col in enumerate(df.columns):
            logger.info(f"  [{i}] '{col}'")
        
        # Análise específica da coluna F (esforço estimado)
        logger.info(f"=== ANÁLISE DA COLUNA F (ESFORÇO ESTIMADO) ===")
        if len(df.columns) > 5:
            col_f_nome = df.columns[5]
            logger.info(f"Nome da coluna F: '{col_f_nome}'")
            
            # Mostrar primeiras 15 linhas da coluna F com mais detalhes
            for i in range(min(15, len(df))):
                valor_a = df.iloc[i, 0] if len(df.columns) > 0 else 'N/A'
                valor_f = df.iloc[i, 5]
                
                # Informações detalhadas sobre o valor
                tipo_valor = type(valor_f).__name__
                repr_valor = repr(valor_f)
                str_valor = str(valor_f).strip()
                
                logger.info(f"  Linha {i+1:2d} | A='{valor_a[:20]}...' | F='{str_valor}' | tipo={tipo_valor} | repr={repr_valor}")
                
                # Destacar linhas que podem conter projetos (a partir da linha 7)
                if i >= 6 and str_valor not in ['', 'nan', 'NaN', 'None']:
                    logger.info(f"    ^^^ POSSÍVEL ESFORÇO ESTIMADO DETECTADO ^^^")
        else:
            logger.error(f"ERRO: DataFrame tem apenas {len(df.columns)} colunas, coluna F não existe!")
            
        # 2. Extrair nome da equipe do nome da planilha
        nome_equipe = self.extrair_equipe_do_arquivo()
        
        # 3. Extrair email do recurso (E7)
        email_recurso = self.extrair_email_recurso(df)
        
        # 4. Buscar equipe
        equipe = self.buscar_equipe_por_nome(nome_equipe)
        
        # 5. Criar ou atualizar recurso conforme regra de negócio
        recurso = self.criar_ou_atualizar_recurso(self.nome_aba, email_recurso, equipe)
        if not recurso:
            logger.error(f"Falha ao criar/atualizar recurso: {self.nome_aba}")
            return False
        
        # 6. Extrair nomes das colunas de horas (a partir da coluna M)
        padrao_mes = re.compile(r'^[a-zA-Z]{3}/\d{2}$')
        colunas_horas = [c for c in df.columns if padrao_mes.match(str(c).strip())]
        
        logger.info(f"Colunas de horas identificadas: {colunas_horas}")
        
        # 7. Processar linhas de projetos (a partir da linha 7 - índice 6)
        logger.info(f"=== PROCESSANDO PROJETOS (A PARTIR DA LINHA 7) ===")
        projetos_processados = 0
        
        for index, linha in df.iterrows():
            if index >= 6:  # Linha 7+ (índice 6+)
                # Verificar se há nome de projeto
                nome_projeto_temp = str(linha.iloc[0]).strip() if len(linha) > 0 else ''
                
                if nome_projeto_temp and nome_projeto_temp not in ['', 'nan', 'NaN']:
                    logger.info(f"\n--- Processando linha {index + 1} ---")
                    logger.info(f"Projeto detectado: '{nome_projeto_temp}'")
                    
                    if self.processar_linha_projeto(linha, recurso, equipe, colunas_horas, df, index):
                        projetos_processados += 1
                        logger.info(f"✓ Projeto processado com sucesso")
                    else:
                        logger.error(f"✗ Falha ao processar projeto")
                else:
                    logger.debug(f"Linha {index + 1} ignorada (sem projeto): '{nome_projeto_temp}'")
        
        logger.info(f"=== RESUMO DO PROCESSAMENTO ===")
        logger.info(f"Total de projetos processados: {projetos_processados}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao processar aba: {e}")
        import traceback
        logger.error(f"Traceback completo: {traceback.format_exc()}")
        return False