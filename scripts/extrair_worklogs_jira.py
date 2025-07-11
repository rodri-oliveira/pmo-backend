import csv
import sys
import os

# Ajuste o path para importar o app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.integrations.jira_client import JiraClient

CSV_PATH = "scripts/worklog_jira_map.csv"
PROJECT_KEYS = ["TIN", "SGI", "SEG"]

def main():
    jira = JiraClient()
    worklog_map = {}

    for project_key in PROJECT_KEYS:
        print(f"Buscando issues do projeto {project_key}...")
        jql = f"project={project_key}"
        issues = jira.search_issues(jql, fields=["key"], max_results=1000)
        print(f"Total de issues em {project_key}: {len(issues)}")
        for idx, issue in enumerate(issues, 1):
            issue_key = issue.get("key")
            print(f"[{project_key}] Issue {idx}/{len(issues)}: {issue_key}")
            try:
                worklogs = jira.get_worklogs(issue_key)
                for wl in worklogs:
                    worklog_id = str(wl.get("id"))
                    author = wl.get("author", {})
                    jira_user_id = author.get("accountId")
                    if worklog_id and jira_user_id:
                        worklog_map[worklog_id] = jira_user_id
            except Exception as e:
                print(f"Erro ao buscar worklogs da issue {issue_key}: {e}")

    print(f"Total de worklogs extraídos: {len(worklog_map)}")
    with open(CSV_PATH, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["jira_worklog_id", "jira_user_id"])
        writer.writeheader()
        for worklog_id, user_id in worklog_map.items():
            writer.writerow({"jira_worklog_id": worklog_id, "jira_user_id": user_id})
    print(f"Arquivo CSV gerado em: {CSV_PATH}")

if __name__ == "__main__":
    main()