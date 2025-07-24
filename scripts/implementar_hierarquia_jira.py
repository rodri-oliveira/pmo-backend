"""
Script para implementar a solução de hierarquia Jira
Este script contém as modificações necessárias para resolver o problema de subtarefas vs projetos pai
"""

# 1. MIGRAÇÃO DO BANCO DE DADOS
migration_sql = """
-- Adicionar campos de hierarquia Jira na tabela apontamento
ALTER TABLE apontamento ADD COLUMN jira_parent_key VARCHAR(50);
ALTER TABLE apontamento ADD COLUMN jira_issue_type VARCHAR(50);
ALTER TABLE apontamento ADD COLUMN nome_subtarefa VARCHAR(200);
ALTER TABLE apontamento ADD COLUMN projeto_pai_id INTEGER;

-- Adicionar foreign key para projeto pai
ALTER TABLE apontamento ADD CONSTRAINT fk_apontamento_projeto_pai 
    FOREIGN KEY (projeto_pai_id) REFERENCES projeto(id) 
    ON UPDATE CASCADE ON DELETE SET NULL;

-- Adicionar índices para performance
CREATE INDEX idx_apontamento_jira_parent_key ON apontamento(jira_parent_key);
CREATE INDEX idx_apontamento_jira_issue_type ON apontamento(jira_issue_type);
CREATE INDEX idx_apontamento_projeto_pai_id ON apontamento(projeto_pai_id);
"""

# 2. CÓDIGO PARA ADICIONAR AO apontamento_data NO SERVIÇO DE SINCRONIZAÇÃO
apontamento_data_hierarchy_fields = """
# Adicionar estes campos ao apontamento_data no método _extrair_dados_worklog:

"jira_parent_key": jira_parent_key,
"jira_issue_type": jira_issue_type,
"nome_subtarefa": nome_subtarefa,
"projeto_pai_id": projeto_pai_id,
"""

# 3. LÓGICA DE EXTRAÇÃO DE HIERARQUIA (já implementada no arquivo)
hierarchy_extraction_logic = """
# Esta lógica já foi adicionada ao método _extrair_dados_worklog:

# Buscar informações detalhadas da issue para obter hierarquia
issue_details = None
jira_parent_key = None
jira_issue_type = None
nome_subtarefa = None

try:
    # Buscar detalhes da issue incluindo parent e issueType
    issue_details = self.jira_client.get_issue(issue_key)
    
    # Extrair tipo da issue
    issue_type_info = issue_details.get("fields", {}).get("issuetype", {})
    jira_issue_type = issue_type_info.get("name")
    
    # Extrair informações do parent (Epic)
    parent_info = issue_details.get("fields", {}).get("parent")
    if parent_info:
        jira_parent_key = parent_info.get("key")
        nome_subtarefa = issue_details.get("fields", {}).get("summary")
        logger.info(f"[WORKLOG_EXTRACT] Issue {issue_key} é subtarefa de {jira_parent_key}")
    else:
        logger.info(f"[WORKLOG_EXTRACT] Issue {issue_key} é um Epic (sem parent)")
        
except Exception as e:
    logger.error(f"[WORKLOG_EXTRACT] Erro ao obter detalhes da issue {issue_key}: {str(e)}")
    # Continuar mesmo sem informações de hierarquia

# Buscar projeto pai se a issue for uma subtarefa
projeto_pai = None
projeto_pai_id = None

if jira_parent_key:
    # Extrair project_key do parent
    parent_project_key = jira_parent_key.split('-')[0] if '-' in jira_parent_key else None
    
    if parent_project_key:
        # Buscar projeto pai pelo jira_project_key
        projeto_pai = await self.projeto_repository.get_by_jira_project_key(parent_project_key)
        
        if not projeto_pai:
            # Criar projeto pai se não existir
            logger.info(f"[WORKLOG_EXTRACT] Projeto pai não encontrado para {parent_project_key}, criando novo")
            
            try:
                # Buscar detalhes do Epic pai no Jira
                parent_issue_details = self.jira_client.get_issue(jira_parent_key)
                parent_summary = parent_issue_details.get("fields", {}).get("summary", f"Epic {jira_parent_key}")
                
                # Buscar status padrão
                status_projeto = await self.projeto_repository.get_status_default()
                
                if status_projeto:
                    projeto_pai_data = {
                        "nome": parent_summary,
                        "jira_project_key": jira_parent_key,  # Usar a chave do Epic como identificador
                        "status_projeto_id": status_projeto.id,
                        "ativo": True
                    }
                    
                    # Vincular à seção se existir
                    secao = await self.secao_repository.get_by_jira_project_key(parent_project_key)
                    if secao:
                        projeto_pai_data["secao_id"] = secao.id
                    
                    projeto_pai = await self.projeto_repository.create(projeto_pai_data)
                    logger.info(f"[WORKLOG_EXTRACT] Projeto pai criado: {projeto_pai.nome} (id={projeto_pai.id})")
                
            except Exception as e:
                logger.error(f"[WORKLOG_EXTRACT] Erro ao criar projeto pai: {str(e)}")
        
        if projeto_pai:
            projeto_pai_id = projeto_pai.id
            logger.info(f"[WORKLOG_EXTRACT] Projeto pai encontrado: {projeto_pai.nome} (id={projeto_pai_id})")
"""

# 4. ESTRUTURA FINAL DOS DADOS
final_structure_explanation = """
ESTRUTURA FINAL DOS DADOS DE APONTAMENTO:

Para uma subtarefa DTIN-5343 "Consultoria PowerAutomate" filha do Epic DTIN-323 "DTI_Consultoria":

apontamento:
- id: 123
- jira_worklog_id: "12345"
- recurso_id: 37
- projeto_id: [ID do projeto DTIN] (projeto raiz)
- jira_issue_key: "DTIN-5343" (subtarefa)
- jira_parent_key: "DTIN-323" (Epic pai)
- jira_issue_type: "Sub-task"
- nome_subtarefa: "Consultoria PowerAutomate"
- projeto_pai_id: [ID do projeto Epic DTIN-323]
- data_apontamento: "2025-07-24"
- horas_apontadas: 8.00
- descricao: "Trabalho na consultoria"
- fonte_apontamento: "JIRA"

BENEFÍCIOS:
1. Mantém rastreabilidade da subtarefa (jira_issue_key, nome_subtarefa)
2. Vincula ao Epic pai (jira_parent_key, projeto_pai_id)
3. Permite comparação correta com planejamento de horas usando projeto_pai_id
4. Preserva dados originais para auditoria
"""

# 5. QUERIES PARA ANÁLISE APÓS IMPLEMENTAÇÃO
analysis_queries = """
-- Query para ver apontamentos com hierarquia
SELECT 
    a.id,
    r.nome AS recurso,
    a.jira_issue_key AS subtarefa,
    a.nome_subtarefa,
    a.jira_parent_key AS epic_pai,
    p_pai.nome AS projeto_pai,
    a.horas_apontadas,
    a.data_apontamento
FROM apontamento a
    INNER JOIN recursos r ON a.recurso_id = r.id
    LEFT JOIN projeto p_pai ON a.projeto_pai_id = p_pai.id
WHERE a.recurso_id = 37
    AND a.jira_parent_key IS NOT NULL
ORDER BY a.data_apontamento DESC;

-- Query para comparar apontamentos com planejamento (usando projeto pai)
SELECT 
    p_pai.nome AS projeto_pai,
    SUM(a.horas_apontadas) AS horas_apontadas_total,
    -- Adicionar JOIN com horas_planejadas usando projeto_pai_id
FROM apontamento a
    LEFT JOIN projeto p_pai ON a.projeto_pai_id = p_pai.id
WHERE a.jira_parent_key IS NOT NULL
GROUP BY p_pai.id, p_pai.nome;
"""

if __name__ == "__main__":
    print("=== IMPLEMENTAÇÃO DA HIERARQUIA JIRA ===")
    print("\n1. Execute a migração SQL no banco de dados")
    print("2. Adicione os campos de hierarquia ao apontamento_data")
    print("3. A lógica de extração já foi implementada")
    print("4. Execute as queries de análise para validar")
    print("\nEstrutura final dos dados:")
    print(final_structure_explanation)
