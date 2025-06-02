-- Migração para adicionar a coluna secao_id à tabela projeto
-- Primeiro verifica se a coluna já existe para evitar erros
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'projeto' AND column_name = 'secao_id'
    ) THEN
        -- Adiciona a coluna secao_id como FK para a tabela secao
        ALTER TABLE projeto ADD COLUMN secao_id INTEGER;
        
        -- Adiciona o índice para melhorar performance de consultas
        CREATE INDEX idx_projeto_secao_id ON projeto(secao_id);
        
        -- Adiciona a constraint de chave estrangeira
        ALTER TABLE projeto 
        ADD CONSTRAINT fk_projeto_secao 
        FOREIGN KEY (secao_id) 
        REFERENCES secao(id) ON DELETE RESTRICT;
        
        -- Atualiza os projetos existentes com base no prefixo do jira_project_key
        -- Esta parte é opcional e depende da lógica de negócio
        UPDATE projeto p
        SET secao_id = s.id
        FROM secao s
        WHERE p.jira_project_key LIKE s.jira_project_key || '-%' 
           OR p.jira_project_key = s.jira_project_key;
    END IF;
END $$;
