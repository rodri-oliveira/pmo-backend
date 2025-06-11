import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import asyncio
from datetime import datetime, timedelta

# Data inicial padrão para carga completa de worklogs
DEFAULT_START_DATE = datetime(2024, 8, 1)

from app.services.sincronizacao_jira_service import SincronizacaoJiraService
from app.db.session import AsyncSessionLocal
from app.integrations.jira_client import JiraClient
from app.repositories.apontamento_repository import ApontamentoRepository
from app.repositories.secao_repository import SecaoRepository

# helper para extrair apenas o primeiro texto de comentário JIRA
def extract_comment_text(comment):
    if not comment or "content" not in comment:
        return None
    for block in comment["content"]:
        for frag in block.get("content", []):
            if "text" in frag:
                return frag["text"]
    return None

async def processar_periodo(data_inicio: datetime, data_fim: datetime):
    """
    Processa worklogs do Jira de data_inicio até data_fim:
    upsert de projeto, recurso e apontamento conforme regras definidas.
    """
    async with AsyncSessionLocal() as session:
        service = SincronizacaoJiraService(session)
        apont_repo = ApontamentoRepository(session)
        secao_repo = SecaoRepository(session)
        proj_repo = service.projeto_repository
        rec_repo = service.recurso_repository

        client = JiraClient()
        project_keys = ["SEG", "SGI", "DTIN", "TIN"]
        # busca todas as issues com worklogs no período
        project_keys_str = ", ".join(project_keys)
        # JQL original com filtro de data:
        # jql = (
        #     f"project IN ({project_keys_str}) "
        #     f"AND worklogDate >= '{data_inicio.date()}' "
        #     f"AND worklogDate <= '{data_fim.date()}'"
        # )

        jql = (
            f"project IN ({project_keys_str}) "
            f"AND worklogDate >= '{data_inicio.date()}' "
            f"AND worklogDate <= '{data_fim.date()}'"
        )
        print(f"[DIAGNOSTICO] Usando JQL com filtro de data: {jql}")
        issues = client.get_all_issues(jql, fields=["key","summary","assignee","worklog"], max_results=100)
        # Diagnóstico: quantas issues foram retornadas pelo JQL
        print(f"[PROCESSAR_PERIODO] Issues encontradas: {len(issues)}")
        # Você também pode filtrar por projeto específico
        total_count = 0
        for issue in issues:
            try:
                issue_key = issue.get("key", "")
                proj_key = issue_key.split("-")[0]
                secao = await secao_repo.get_by_jira_project_key(proj_key)

                # upsert projeto (summary é nome do projeto)
                resumo = issue["fields"].get("summary", "").strip() or issue_key
                projeto = await proj_repo.get_by_name(resumo)
                print(f"[DEBUG] Buscando projeto pelo nome: '{resumo}'. Encontrado: {projeto.id if projeto else 'Nenhum'}")
                if not projeto:
                    status_default = await proj_repo.get_status_default()
                    projeto = await proj_repo.create({
                        "nome": resumo,
                        "jira_project_key": proj_key,
                        "secao_id": secao.id if secao else None,
                        "status_projeto_id": status_default.id if status_default else None
                    })
                    print(f"[PROJECT_UPSERT] Created projeto {proj_key} -> id={projeto.id}")
                elif projeto.nome != resumo:
                    projeto.nome = resumo
                    await proj_repo.db.commit()
                    await proj_repo.db.refresh(projeto)
                    print(f"[PROJECT_UPSERT] Updated projeto {proj_key} -> id={projeto.id}")
                else:
                    print(f"[PROJECT_FOUND] projeto {proj_key} -> id={projeto.id}")

                # upsert recurso (assignee)
                ass = issue["fields"].get("assignee") or {}
                jira_user_id = ass.get("accountId")
                email = ass.get("emailAddress")
                nome_rec = ass.get("displayName")
                recurso = None
                if jira_user_id:
                    recurso = await rec_repo.get_by_jira_user_id(jira_user_id)
                if not recurso and email:
                    recurso = await rec_repo.get_by_email(email)
                if recurso:
                    # Se o recurso já existe, atualiza os dados se necessário
                    upd = {}
                    if nome_rec and recurso.nome != nome_rec:
                        upd["nome"] = nome_rec
                    if email and recurso.email != email:
                        upd["email"] = email
                    if not recurso.jira_user_id and jira_user_id:
                        upd["jira_user_id"] = jira_user_id
                    
                    if upd:
                        for k, v in upd.items():
                            setattr(recurso, k, v)
                        await rec_repo.db.commit()
                        await rec_repo.db.refresh(recurso)
                        print(f"[RECURSO_UPDATE] Updated recurso {recurso.email} -> id={recurso.id}")

                else:
                    # Se o recurso não existe, cria um novo (apenas se houver e-mail)
                    if email:
                        nome_para_criar = nome_rec or email  # Usa e-mail como fallback para o nome
                        recurso = await rec_repo.create({
                            "nome": nome_para_criar,
                            "email": email,
                            "jira_user_id": jira_user_id,
                            "ativo": ass.get("active", True)
                        })
                        print(f"[RECURSO_CREATE] Created recurso {nome_para_criar} -> id={recurso.id}")
                    else:
                        # Log de aviso se não for possível criar o recurso por falta de e-mail
                        print(f"[RECURSO_SKIP] Recurso para issue {issue_key} não processado por falta de e-mail.")

                # processa todos os worklogs da issue via paginação
                wlogs = client.get_all_worklogs(issue_key)
                # Diagnóstico: quantos worklogs para esta issue
                print(f"[PROCESSAR_PERIODO] Issue {issue_key}: {len(wlogs)} worklogs")
                for wl in wlogs:
                    wl_id = wl.get("id")
                    # parsing de datas sem timezone
                    def parse_dt(s): return datetime.fromisoformat(s[:-6]) if s else None
                    dt_c = parse_dt(wl.get("created"))
                    dt_u = parse_dt(wl.get("updated"))
                    dt_s = parse_dt(wl.get("started"))
                    horas = wl.get("timeSpentSeconds", 0) / 3600
                    # filtrar worklogs fora do período
                    if not dt_s or dt_s < data_inicio or dt_s > data_fim:
                        print(f"[SKIP_WORKLOG] Issue {issue_key} wl_id={wl_id}: fora do período, pulando")
                        continue
                    # pular apontamentos com horas inválidas (>24 ou <=0)
                    if horas <= 0 or horas > 24:
                        print(f"[SKIP_WORKLOG] Issue {issue_key} wl_id={wl_id}: horas_apontadas={horas} inválidas, pulando")
                        continue
                    
                    # Garantir que recurso e projeto existem antes de criar o apontamento
                    if not recurso or not projeto:
                        print(f"[SKIP_WORKLOG] Issue {issue_key} wl_id={wl_id}: recurso ou projeto não encontrado, pulando")
                        continue

                    data = {
                        "recurso_id": recurso.id,
                        "projeto_id": projeto.id,
                        "jira_issue_key": issue_key,
                        "data_hora_inicio_trabalho": dt_s,
                        "data_apontamento": dt_s.date() if dt_s else None,
                        "horas_apontadas": horas,
                        "descricao": extract_comment_text(wl.get("comment")),
                        "data_criacao": dt_c,
                        "data_atualizacao": dt_u,
                        "data_sincronizacao_jira": datetime.now(),
                    }
                    await apont_repo.sync_jira_apontamento(wl_id, data)
                    total_count += 1
            except Exception as e:
                # Log do erro e continua para a próxima issue
                issue_key_for_log = issue.get("key", "NO_KEY")
                print(f'\n--- ERRO AO PROCESSAR ISSUE: {issue_key_for_log} ---')
                import traceback
                traceback.print_exc()
                print("----------------------------------------------------\n")
                continue
                print("----------------------------------------------------\n")
                continue
        print(f"[PROCESSAR_PERIODO] Total worklogs processados: {total_count}")

async def carga_completa():
    """
    Executa a carga completa de worklogs do Jira desde 01/08/2024 até hoje.
    """
    data_inicio = DEFAULT_START_DATE
    data_fim = datetime.now()
    print(f"[CARGA COMPLETA] Iniciando de {data_inicio.date()} até {data_fim.date()}")
    await processar_periodo(data_inicio, data_fim)

async def carga_personalizada(start_str: str, end_str: str):
    from datetime import datetime
    try:
        data_inicio = datetime.fromisoformat(start_str)
        data_fim = datetime.fromisoformat(end_str)
    except Exception as e:
        print(f"[ERRO DATA] Formato inválido: {e}")
        return
    print(f"[CARGA PERSONALIZADA] Iniciando de {data_inicio.date()} até {data_fim.date()}")
    await processar_periodo(data_inicio, data_fim)

async def rotina_mensal():
    """
    Executa a rotina mensal de sincronização do Jira (mês anterior ao mês corrente).
    """
    hoje = datetime.now()
    primeiro_dia_mes_atual = hoje.replace(day=1)
    ultimo_dia_mes_anterior = primeiro_dia_mes_atual - timedelta(days=1)
    primeiro_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1)
    data_inicio = primeiro_dia_mes_anterior
    data_fim = ultimo_dia_mes_anterior
    print(f"[ROTINA MENSAL] Iniciando de {data_inicio.date()} até {data_fim.date()}")
    await processar_periodo(data_inicio, data_fim)

if __name__ == "__main__":
    import sys
    # uso: python sincronizar_jira.py <start> <end> | mensal | (sem args)
    if len(sys.argv) == 3:
        _, start_str, end_str = sys.argv
        asyncio.run(carga_personalizada(start_str, end_str))
    elif len(sys.argv) > 1 and sys.argv[1] == "mensal":
        asyncio.run(rotina_mensal())
    else:
        asyncio.run(carga_completa())
