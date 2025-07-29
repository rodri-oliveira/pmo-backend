    # Esquema do Banco de Dados - Sistema de Automação PMO

## Versão: 1.3 (Atualizado em 28/07/2025)

Este documento descreve a estrutura atual do banco de dados do sistema de automação PMO da WEG.

## Tabelas Principais

### Tabela: configuracao
```sql
Table configuracao {
  id int [pk, increment]
  chave varchar(100) [unique, not null]
  valor text
  descricao text
  data_criacao datetime [not null, default: now()]
  data_atualizacao datetime [not null, default: now(), onupdate: now()]
}
```

### Tabela: dim_tempo
```sql
Table dim_tempo {
  data_id int [pk]
  data date [unique, not null]
  ano smallint [not null]
  mes int [not null]
  dia int [not null]
  trimestre int [not null]
  dia_semana int [not null]
  nome_dia_semana varchar(20) [not null]
  nome_mes varchar(20) [not null]
  semana_ano int [not null]
  is_dia_util boolean [not null]
  is_feriado boolean [not null, default: false]
  nome_feriado varchar(100)
}
```

### Tabela: secao
```sql
Table secao {
  id int [pk, increment]
  nome varchar(100) [unique, not null]
  descricao text
  jira_project_key varchar(20) [unique, indexed]
  data_criacao datetime [not null, default: now()]
  data_atualizacao datetime [not null, default: now(), onupdate: now()]
  ativo boolean [not null, default: true]
}
```

### Tabela: equipe
```sql
Table equipe {
  id int [pk, increment]
  secao_id int [not null, fk: secao.id, indexed]
  nome varchar(100) [not null]
  descricao text
  data_criacao datetime [not null, default: now()]
  data_atualizacao datetime [not null, default: now(), onupdate: now()]
  ativo boolean [not null, default: true]
}
```

### Tabela: status_projeto
```sql
Table status_projeto {
  id int [pk, increment]
  nome varchar(50) [unique, not null]
  descricao varchar(255)
  is_final boolean [not null, default: false]
  ordem_exibicao int [unique]
  data_criacao datetime [not null, default: now()]
  data_atualizacao datetime [not null, default: now(), onupdate: now()]
}
```

### Tabela: projeto
```sql
Table projeto {
  id int [pk, increment]
  nome varchar(200) [not null]
  codigo_empresa varchar(50) [unique, indexed]
  descricao text
  jira_project_key varchar(100) [indexed]
  status_projeto_id int [not null, fk: status_projeto.id, indexed]
  secao_id int [fk: secao.id, indexed]
  data_inicio_prevista date
  data_fim_prevista date
  data_criacao datetime [not null, default: now()]
  data_atualizacao datetime [not null, default: now(), onupdate: now()]
  ativo boolean [not null, default: true]
}
```

### Tabela: recurso
```sql
Table recurso {
  id int [pk, increment]
  equipe_principal_id int [fk: equipe.id, indexed]
  nome varchar(150) [not null]
  email varchar(100) [unique, not null, indexed]
  matricula varchar(50) [unique, indexed]
  cargo varchar(100)
  jira_user_id varchar(100) [unique, indexed]
  data_admissao date
  data_criacao datetime [not null, default: now()]
  data_atualizacao datetime [not null, default: now(), onupdate: now()]
  ativo boolean [not null, default: true]
}
```

### Tabela: alocacao_recurso_projeto
```sql
Table alocacao_recurso_projeto {
  id int [pk, increment]
  recurso_id int [not null, fk: recurso.id, indexed]
  projeto_id int [not null, fk: projeto.id, indexed]
  equipe_id int [fk: equipe.id, indexed]
  status_alocacao_id int [fk: status_projeto.id, indexed]
  observacao text
  data_inicio_alocacao date [not null]
  data_fim_alocacao date
  data_criacao datetime [not null, default: now()]
  data_atualizacao datetime [not null, default: now(), onupdate: now()]
  esforco_estimado decimal(10,2)
  esforco_planejado decimal(10,2)
}
```

### Tabela: horas_disponiveis_rh
```sql
Table horas_disponiveis_rh {
  id int [pk, increment]
  recurso_id int [not null, fk: recurso.id, indexed]
  ano smallint [not null]
  mes int [not null]
  horas_disponiveis_mes decimal(5,2) [not null]
  data_criacao datetime [not null, default: now()]
  data_atualizacao datetime [not null, default: now(), onupdate: now()]
}
```

### Tabela: horas_planejadas_alocacao
```sql
Table horas_planejadas_alocacao {
  id int [pk, increment]
  alocacao_id int [not null, fk: alocacao_recurso_projeto.id, indexed]
  ano smallint [not null]
  mes int [not null]
  horas_planejadas decimal(5,2) [not null]
  data_criacao datetime [not null, default: now()]
  data_atualizacao datetime [not null, default: now(), onupdate: now()]
}
```

### Tabela: apontamento
```sql
Table apontamento {
  id int [pk, increment]
  jira_worklog_id varchar(255) [unique, indexed]
  recurso_id int [not null, fk: recurso.id, indexed]
  projeto_id int [not null, fk: projeto.id, indexed]
  jira_issue_key varchar(50) [indexed]
  jira_parent_key varchar(50) [indexed]
  jira_issue_type varchar(50)
  nome_subtarefa varchar(255)
  projeto_pai_id int [fk: projeto.id, indexed]
  nome_projeto_pai varchar(200)
  data_hora_inicio_trabalho datetime
  data_apontamento date [not null, indexed]
  horas_apontadas decimal(5,2) [not null]
  descricao text
  fonte_apontamento enum('JIRA', 'MANUAL') [not null, default: 'MANUAL', indexed]
  id_usuario_admin_criador int [fk: usuario.id, indexed]
  data_sincronizacao_jira datetime
  data_criacao datetime [not null, default: now()]
  data_atualizacao datetime [not null, default: now(), onupdate: now()]
}
```

### Tabela: usuario
```sql
Table usuario {
  id int [pk, increment]
  nome varchar(100) [not null]
  email varchar(100) [unique, not null, indexed]
  senha_hash varchar(255) [not null]
  role enum('admin', 'gestor', 'recurso') [not null]
  recurso_id int [unique, fk: recurso.id]
  data_criacao datetime [not null, default: now()]
  data_atualizacao datetime [not null, default: now(), onupdate: now()]
  ultimo_acesso datetime
  ativo boolean [not null, default: true]
}
```

### Tabela: log_atividade
```sql
Table log_atividade {
  id int [pk, increment]
  usuario_id int [fk: usuario.id, indexed]
  acao varchar(255) [not null]
  tabela_afetada varchar(100)
  registro_id varchar(255)
  detalhes text
  ip_origem varchar(45)
  data_hora timestamp(6) [not null, default: now(), indexed]
}
```

### Tabela: sincronizacao_jira
```sql
Table sincronizacao_jira {
  id int [pk, increment]
  data_inicio datetime [not null]
  data_fim datetime
  status varchar(50) [not null]
  mensagem text
  quantidade_apontamentos_processados int
  usuario_id int [fk: usuario.id]
}
```

### Tabela: equipe_projeto (Associação N:N)
```sql
Table equipe_projeto {
  equipe_id int [pk, fk: equipe.id]
  projeto_id int [pk, fk: projeto.id]
}
```

## Relacionamentos

### Chaves Estrangeiras
```sql
Ref: equipe.secao_id > secao.id [restrict, cascade]
Ref: recurso.equipe_principal_id > equipe.id [set null, cascade]
Ref: projeto.status_projeto_id > status_projeto.id [restrict, cascade]
Ref: projeto.secao_id > secao.id [restrict, cascade]
Ref: alocacao_recurso_projeto.recurso_id > recurso.id [cascade, cascade]
Ref: alocacao_recurso_projeto.projeto_id > projeto.id [cascade, cascade]
Ref: alocacao_recurso_projeto.equipe_id > equipe.id [set null, cascade]
Ref: alocacao_recurso_projeto.status_alocacao_id > status_projeto.id [set null, cascade]
Ref: horas_disponiveis_rh.recurso_id > recurso.id [cascade, cascade]
Ref: horas_planejadas_alocacao.alocacao_id > alocacao_recurso_projeto.id [cascade, cascade]
Ref: apontamento.recurso_id > recurso.id [restrict, cascade]
Ref: apontamento.projeto_id > projeto.id [restrict, cascade]
Ref: apontamento.projeto_pai_id > projeto.id [set null, cascade]
Ref: apontamento.id_usuario_admin_criador > usuario.id [set null, cascade]
Ref: usuario.recurso_id > recurso.id [set null, cascade]
Ref: log_atividade.usuario_id > usuario.id [set null, cascade]
Ref: sincronizacao_jira.usuario_id > usuario.id [set null, cascade]
Ref: equipe_projeto.equipe_id > equipe.id [cascade]
Ref: equipe_projeto.projeto_id > projeto.id [cascade]
```

## Constraints e Índices

### Unique Constraints
- `uq_equipe_secao_nome`: (secao_id, nome) na tabela equipe
- `uq_alocacao_recurso_projeto_data`: (recurso_id, projeto_id, data_inicio_alocacao) na tabela alocacao_recurso_projeto
- `uq_horas_disponveis_recurso_ano_mes`: (recurso_id, ano, mes) na tabela horas_disponiveis_rh
- `uq_horas_planejadas_alocacao_ano_mes`: (alocacao_id, ano, mes) na tabela horas_planejadas_alocacao

### Check Constraints
- `chk_alocacao_datas`: data_fim_alocacao IS NULL OR data_fim_alocacao >= data_inicio_alocacao
- `chk_horas_disponveis_mes`: mes >= 1 AND mes <= 12
- `chk_horas_disponveis_valor`: horas_disponiveis_mes >= 0
- `chk_horas_planejadas_mes`: mes >= 1 AND mes <= 12
- `chk_horas_planejadas_valor`: horas_planejadas >= 0
- `chk_apontamento_horas`: horas_apontadas > 0 AND horas_apontadas <= 24

## Enums

### FonteApontamento
- JIRA
- MANUAL

### UserRole
- admin
- gestor
- recurso

## Observações Importantes

1. **Hierarquia Jira**: A tabela `apontamento` possui campos específicos para tratar a hierarquia do Jira:
   - `jira_parent_key`: Chave do projeto pai quando é uma subtarefa
   - `jira_issue_type`: Tipo da issue (Task, Sub-task, etc.)
   - `nome_subtarefa`: Nome da subtarefa para rastreabilidade
   - `projeto_pai_id`: ID do projeto pai no banco local

2. **Sincronização**: O sistema possui controle de sincronização com o Jira através da tabela `sincronizacao_jira`

3. **Auditoria**: Todas as tabelas principais possuem campos de auditoria (`data_criacao`, `data_atualizacao`)

4. **Soft Delete**: Tabelas principais usam campo `ativo` para soft delete

5. **Planejamento vs Realizado**: 
   - Horas planejadas: tabela `horas_planejadas_alocacao`
   - Horas realizadas: tabela `apontamento`
   - Comparação feita através da alocação do recurso ao projeto