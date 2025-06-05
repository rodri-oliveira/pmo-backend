-- seed_data.sql
-- Script para povoar tabelas finais: horas_disponiveis_rh, horas_planejadas_alocacao e apontamento
-- Utilize este template e substitua os placeholders pelos valores reais.

-- 1) Horas Disponíveis RH
-- Insere quantas horas cada recurso tem disponível por ano e mês
INSERT INTO horas_disponiveis_rh (
  recurso_id,
  ano,
  mes,
  horas_disponiveis_mes,
  data_criacao,
  data_atualizacao
) VALUES
  ( /*recurso_id*/, /*ano*/, /*mes*/, /*horas_disponiveis_mes decimal*/, NOW(), NOW() )
-- Exemplo:
--, (1, 2025, 6, 160.00, NOW(), NOW())
;

-- 2) Horas Planejadas por Alocação
-- Insere quantas horas estão planejadas para cada alocação por ano e mês
INSERT INTO horas_planejadas_alocacao (
  alocacao_id,
  ano,
  mes,
  horas_planejadas,
  data_criacao,
  data_atualizacao
) VALUES
  ( /*alocacao_id*/, /*ano*/, /*mes*/, /*horas_planejadas decimal*/, NOW(), NOW() )
-- Exemplo:
--, (10, 2025, 6, 120.00, NOW(), NOW())
;

-- 3) Apontamento de Horas
-- Insere registros de apontamento de trabalho (worklogs)
INSERT INTO apontamento (
  jira_worklog_id,
  recurso_id,
  projeto_id,
  jira_issue_key,
  data_hora_inicio_trabalho,
  data_hora_fim_trabalho,
  data_criacao,
  data_atualizacao
) VALUES
  ('WORKLOG-KEY', /*recurso_id*/, /*projeto_id*/, 'ISSUE-123',
   'YYYY-MM-DD HH24:MI', 'YYYY-MM-DD HH24:MI',
   NOW(), NOW() )
-- Exemplo:
--, ('WL-1001', 32, 101, 'PROJ-45', '2025-06-03 08:00', '2025-06-03 12:00', NOW(), NOW())
;

-- 4) Função para inserção dinâmica de horas planejadas via JSON
CREATE OR REPLACE FUNCTION inserir_horas_planejadas_json(_year INT, _data JSONB)
RETURNS VOID AS $$
BEGIN
  WITH raw AS (
    SELECT (d->>'recurso_id')::INT        AS recurso_id,
           d->>'nome_projeto'             AS nome_projeto,
           (d->'h')->>0  ::NUMERIC AS h1,
           (d->'h')->>1  ::NUMERIC AS h2,
           (d->'h')->>2  ::NUMERIC AS h3,
           (d->'h')->>3  ::NUMERIC AS h4,
           (d->'h')->>4  ::NUMERIC AS h5,
           (d->'h')->>5  ::NUMERIC AS h6,
           (d->'h')->>6  ::NUMERIC AS h7,
           (d->'h')->>7  ::NUMERIC AS h8,
           (d->'h')->>8  ::NUMERIC AS h9,
           (d->'h')->>9  ::NUMERIC AS h10,
           (d->'h')->>10 ::NUMERIC AS h11,
           (d->'h')->>11 ::NUMERIC AS h12
    FROM JSONB_ARRAY_ELEMENTS(_data) AS t(d)
  ), allocs AS (
    SELECT r.*, a.id AS alocacao_id
    FROM raw r
    JOIN projeto p
      ON p.nome = r.nome_projeto
    JOIN alocacao_recurso_projeto a
      ON a.projeto_id = p.id
     AND a.recurso_id = r.recurso_id
  ), monthly AS (
    SELECT alocacao_id,
           _year      AS ano,
           unnest(ARRAY[h1,h2,h3,h4,h5,h6,h7,h8,h9,h10,h11,h12])
             WITH ORDINALITY AS (horas_planejadas, mes)
    FROM allocs
  )
  INSERT INTO horas_planejadas_alocacao (
    alocacao_id, ano, mes, horas_planejadas, data_criacao, data_atualizacao
  )
  SELECT alocacao_id, ano, mes, horas_planejadas, NOW(), NOW()
  FROM monthly
  ON CONFLICT (alocacao_id, ano, mes) DO UPDATE
    SET horas_planejadas = EXCLUDED.horas_planejadas;
END;
$$ LANGUAGE plpgsql;

-- Exemplo de uso:
-- SELECT inserir_horas_planejadas_json(
--   2025,
--   '[
--     {"recurso_id":14,"nome_projeto":"Project A","h":[0,0,49,0,100,0,0,0,23,115,57,60]},
--     {"recurso_id":14,"nome_projeto":"Project B","h":[...12 valores...]}
--   ]'::jsonb
-- );
