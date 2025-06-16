Table configuracao {
  id int [pk, increment]
  chave varchar(100) [unique, not null]
  valor text
  descricao text
  data_criacao datetime [not null]
  data_atualizacao datetime [not null]
}

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
  is_feriado boolean [not null]
  nome_feriado varchar(100)
}

Table secao {
  id int [pk, increment]
  nome varchar(100) [unique, not null]
  jira_project_key varchar(100) [unique]
  descricao text
  data_criacao datetime [not null]
  data_atualizacao datetime [not null]
  ativo boolean [not null]
}

Table status_projeto {
  id int [pk, increment]
  nome varchar(50) [unique, not null]
  descricao text
  is_final boolean [not null]
  ordem_exibicao int [unique]
  data_criacao datetime [not null]
  data_atualizacao datetime [not null]
}

Table equipe {
  id int [pk, increment]
  secao_id int [not null]
  nome varchar(100) [not null]
  descricao text
  data_criacao datetime [not null]
  data_atualizacao datetime [not null]
  ativo boolean [not null]
}

Table projeto {
  id int [pk, increment]
  nome varchar(200) [not null]
  codigo_empresa varchar(50) [unique]
  secao_id int
  descricao text
  jira_project_key varchar(100) [unique]
  status_projeto_id int [not null]
  data_inicio_prevista date
  data_fim_prevista date
  data_criacao datetime [not null]
  data_atualizacao datetime [not null]
  ativo boolean [not null]
}

Table recurso {
  id int [pk, increment]
  equipe_principal_id int
  nome varchar(150) [not null]
  email varchar(100) [unique, not null]
  matricula varchar(50) [unique]
  cargo varchar(100)
  jira_user_id varchar(100) [unique]
  data_admissao date
  data_criacao datetime [not null]
  data_atualizacao datetime [not null]
  ativo boolean [not null]
}

Table alocacao_recurso_projeto {
  id int [pk, increment]
  recurso_id int [not null]
  projeto_id int [not null]
  data_inicio_alocacao date [not null]
  data_fim_alocacao date
  periodo tsrange
  equipe_id int
  status_alocacao_id int
  observacao text
  data_criacao datetime [not null]
  data_atualizacao datetime [not null]
}

Table horas_disponiveis_rh {
  id int [pk, increment]
  recurso_id int [not null]
  ano smallint [not null]
  mes int [not null]
  horas_disponiveis_mes decimal(5,2) [not null]
  data_criacao datetime [not null]
  data_atualizacao datetime [not null]
}

Table usuario {
  id int [pk, increment]
  nome varchar(100) [not null]
  email varchar(100) [unique, not null]
  senha_hash varchar(255) [not null]
  role enum('ADMIN','GESTOR','RECURSO') [not null]
  recurso_id int
  data_criacao datetime [not null]
  data_atualizacao datetime [not null]
  ultimo_acesso datetime
  ativo boolean [not null]
}

Table apontamento {
  id int [pk, increment]
  jira_worklog_id varchar(255) [unique]
  recurso_id int [not null]
  projeto_id int [not null]
  jira_issue_key varchar(50)
  data_hora_inicio_trabalho datetime
  data_apontamento date [not null]
  horas_apontadas decimal(5,2) [not null]
  descricao text
  fonte_apontamento enum('JIRA','MANUAL') [not null]
  id_usuario_admin_criador int
  data_sincronizacao_jira datetime
  data_criacao datetime [not null]
  data_atualizacao datetime [not null]
}

Table horas_planejadas_alocacao {
  id int [pk, increment]
  alocacao_id int [not null]
  ano smallint [not null]
  mes int [not null]
  horas_planejadas decimal(5,2) [not null]
  data_criacao datetime [not null]
  data_atualizacao datetime [not null]
}

Table log_atividade {
  id int [pk, increment]
  usuario_id int
  acao varchar(255) [not null]
  tabela_afetada varchar(100)
  registro_id varchar(255)
  detalhes text
  ip_origem varchar(45)
  data_hora datetime [not null]
}

Table sincronizacao_jira {
  id int [pk, increment]
  data_inicio datetime [not null]
  data_fim datetime [not null]
  status varchar(50) [not null]
  mensagem text
  quantidade_apontamentos_processados int
  usuario_id int
}

Ref: equipe.secao_id > secao.id  
Ref: projeto.secao_id > secao.id  
Ref: projeto.status_projeto_id > status_projeto.id  
Ref: recurso.equipe_principal_id > equipe.id  
Ref: alocacao_recurso_projeto.recurso_id > recurso.id  
Ref: alocacao_recurso_projeto.projeto_id > projeto.id  
Ref: alocacao_recurso_projeto.equipe_id > equipe.id  
Ref: alocacao_recurso_projeto.status_alocacao_id > status_projeto.id  
Ref: horas_disponiveis_rh.recurso_id > recurso.id  
Ref: usuario.recurso_id > recurso.id  
Ref: apontamento.recurso_id > recurso.id  
Ref: apontamento.projeto_id > projeto.id  
Ref: apontamento.id_usuario_admin_criador > usuario.id  
Ref: horas_planejadas_alocacao.alocacao_id > alocacao_recurso_projeto.id  
Ref: log_atividade.usuario_id > usuario.id  
Ref: sincronizacao_jira.usuario_id > usuario.id  