-- =====================================================================
-- QUERIES PARA TESTE DO ENDPOINT /backend/dashboard/disponibilidade-recurso
-- Execute no pgAdmin para validar os dados
-- =====================================================================

-- PARÂMETROS DE TESTE (ajuste conforme necessário)
-- recurso_id = 87
-- ano = 2025
-- mes_inicio = 1
-- mes_fim = 12

-- =====================================================================
-- QUERY 1: HORAS PLANEJADAS (Capacidade + Planejamento)
-- =====================================================================
SELECT
    hdr.ano,
    hdr.mes,
    hdr.horas_disponiveis_mes AS capacidade_rh,
    p.id AS projeto_id,
    p.nome AS projeto_nome,
    -- Normalizar nome do projeto para matching
    UPPER(TRIM(REPLACE(p.nome, '_', ''))) AS projeto_nome_normalizado,
    hpa.horas_planejadas
FROM
    horas_disponiveis_rh hdr
LEFT JOIN
    alocacao_recurso_projeto arp ON hdr.recurso_id = arp.recurso_id
LEFT JOIN
    horas_planejadas_alocacao hpa ON arp.id = hpa.alocacao_id
                                  AND hdr.ano = hpa.ano
                                  AND hdr.mes = hpa.mes
LEFT JOIN
    projeto p ON arp.projeto_id = p.id
WHERE
    hdr.recurso_id = 87  -- AJUSTE AQUI
    AND hdr.ano = 2025   -- AJUSTE AQUI
    AND hdr.mes BETWEEN 1 AND 12  -- AJUSTE AQUI
    -- Filtrar apenas projetos válidos das seções WEG
    AND (p.id IS NULL OR p.jira_project_key ~ '^(SEG|SGI|DTIN|TIN|WTMT|WENSAS|WTDPE|WTDQUO|WTDDMF|WPDREAC|WTDNS)-')
ORDER BY
    hdr.ano, hdr.mes;

-- =====================================================================
-- QUERY 2: HORAS APONTADAS (Agregação por Projeto Pai - Hierarquia Jira)
-- =====================================================================
SELECT
    EXTRACT(YEAR FROM a.data_apontamento) AS ano,
    EXTRACT(MONTH FROM a.data_apontamento) AS mes,
    -- Usar projeto pai quando disponível, senão usar projeto atual
    COALESCE(a.projeto_pai_id, a.projeto_id) AS projeto_id,
    -- Usar nome do projeto pai quando disponível, senão usar nome do projeto atual
    COALESCE(a.nome_projeto_pai, p.nome) AS projeto_nome,
    -- Normalizar nome do projeto (remover underscores, espaços extras, maiúsculas)
    UPPER(TRIM(REPLACE(COALESCE(a.nome_projeto_pai, p.nome), '_', ''))) AS projeto_nome_normalizado,
    SUM(a.horas_apontadas) AS horas_apontadas,
    -- Informações adicionais para debug
    COUNT(CASE WHEN a.jira_parent_key IS NOT NULL THEN 1 END) AS subtarefas_count,
    COUNT(CASE WHEN a.jira_parent_key IS NULL THEN 1 END) AS tarefas_principais_count
FROM
    apontamento a
LEFT JOIN
    projeto p ON a.projeto_id = p.id
WHERE
    a.recurso_id = 87  -- AJUSTE AQUI
    AND EXTRACT(YEAR FROM a.data_apontamento) = 2025  -- AJUSTE AQUI
    AND EXTRACT(MONTH FROM a.data_apontamento) BETWEEN 1 AND 12  -- AJUSTE AQUI
GROUP BY
    EXTRACT(YEAR FROM a.data_apontamento),
    EXTRACT(MONTH FROM a.data_apontamento),
    COALESCE(a.projeto_pai_id, a.projeto_id),
    COALESCE(a.nome_projeto_pai, p.nome),
    UPPER(TRIM(REPLACE(COALESCE(a.nome_projeto_pai, p.nome), '_', '')))
ORDER BY
    ano, mes, projeto_id;

-- =====================================================================
-- QUERY 3: ANÁLISE DE MATCHING (Para debug)
-- =====================================================================
-- Esta query mostra os nomes normalizados lado a lado para verificar o matching

WITH planejamento AS (
    SELECT DISTINCT
        UPPER(TRIM(REPLACE(p.nome, '_', ''))) AS nome_normalizado,
        p.nome AS nome_original,
        'PLANEJAMENTO' AS fonte
    FROM horas_disponiveis_rh hdr
    LEFT JOIN alocacao_recurso_projeto arp ON hdr.recurso_id = arp.recurso_id
    LEFT JOIN horas_planejadas_alocacao hpa ON arp.id = hpa.alocacao_id
    LEFT JOIN projeto p ON arp.projeto_id = p.id
    WHERE hdr.recurso_id = 87 AND hdr.ano = 2025 AND p.id IS NOT NULL
),
apontamentos AS (
    SELECT DISTINCT
        UPPER(TRIM(REPLACE(COALESCE(a.nome_projeto_pai, p.nome), '_', ''))) AS nome_normalizado,
        COALESCE(a.nome_projeto_pai, p.nome) AS nome_original,
        'APONTAMENTO' AS fonte
    FROM apontamento a
    LEFT JOIN projeto p ON a.projeto_id = p.id
    WHERE a.recurso_id = 87 AND EXTRACT(YEAR FROM a.data_apontamento) = 2025
)
SELECT 
    COALESCE(pl.nome_normalizado, ap.nome_normalizado) AS nome_normalizado,
    pl.nome_original AS planejamento_nome,
    ap.nome_original AS apontamento_nome,
    CASE 
        WHEN pl.nome_normalizado IS NOT NULL AND ap.nome_normalizado IS NOT NULL THEN '✅ MATCH EXATO'
        WHEN pl.nome_normalizado IS NOT NULL AND ap.nome_normalizado IS NULL THEN '❌ SÓ PLANEJAMENTO'
        WHEN pl.nome_normalizado IS NULL AND ap.nome_normalizado IS NOT NULL THEN '❌ SÓ APONTAMENTO'
        ELSE '❓ INDEFINIDO'
    END AS status_matching
FROM planejamento pl
FULL OUTER JOIN apontamentos ap ON pl.nome_normalizado = ap.nome_normalizado
ORDER BY nome_normalizado;

-- =====================================================================
-- QUERY 4: VERIFICAR DADOS DO RECURSO
-- =====================================================================
SELECT 
    r.id,
    r.nome,
    r.jira_user_id,
    r.ativo
FROM recurso r 
WHERE r.id = 87;  -- AJUSTE AQUI

-- =====================================================================
-- INSTRUÇÕES DE USO:
-- =====================================================================
-- 1. Ajuste os parâmetros no início do arquivo (recurso_id, ano, mes_inicio, mes_fim)
-- 2. Execute cada query separadamente no pgAdmin
-- 3. A Query 1 mostra as horas planejadas por mês/projeto
-- 4. A Query 2 mostra as horas apontadas agregadas por projeto pai
-- 5. A Query 3 mostra o status do matching entre nomes
-- 6. A Query 4 verifica se o recurso existe
-- 
-- PONTOS DE ATENÇÃO:
-- - Verifique se há dados nas tabelas horas_disponiveis_rh e apontamento
-- - Observe os nomes normalizados na Query 3 para identificar problemas de matching
-- - A Query 2 deve mostrar agregação correta de subtarefas no projeto pai
