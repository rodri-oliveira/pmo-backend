SELECT p.nome
FROM alocacao_recurso_projeto a
JOIN projeto p ON p.id = a.projeto_id
WHERE a.recurso_id = 82
  AND a.data_inicio_alocacao = DATE '2025-01-01'
ORDER BY p.nome;-- create_horas_function.sql
-- Cria a função inserir_horas_planejadas_json isoladamente

CREATE OR REPLACE FUNCTION public.inserir_horas_planejadas_json(
    _year INT,
    _data JSONB
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
  WITH raw AS (
    SELECT (d->>'recurso_id')::INT AS recurso_id,
           d->>'nome_projeto'          AS nome_projeto,
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
    SELECT a.alocacao_id,
           _year             AS ano,
           t.mes             AS mes,
           t.horas_planejadas AS horas_planejadas
    FROM allocs a
    CROSS JOIN LATERAL unnest(ARRAY[
        a.h1, a.h2, a.h3, a.h4, a.h5, a.h6,
        a.h7, a.h8, a.h9, a.h10, a.h11, a.h12
    ])
      WITH ORDINALITY AS t(horas_planejadas, mes)
  )
  INSERT INTO horas_planejadas_alocacao (
    alocacao_id, ano, mes, horas_planejadas, data_criacao, data_atualizacao
  )
  SELECT alocacao_id, ano, mes, horas_planejadas, NOW(), NOW()
  FROM monthly
  ON CONFLICT (alocacao_id, ano, mes) DO UPDATE
    SET horas_planejadas = EXCLUDED.horas_planejadas;
END;
$$;
