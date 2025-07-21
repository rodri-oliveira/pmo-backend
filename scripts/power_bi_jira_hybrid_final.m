let
    // 1. DEFINIÇÕES — DELIVERABLES (JQL CORRIGIDO)
    jqlQuery =
        "project = ""TIN Seção Tecnologia de Infraestrutura"" " &
        "AND cf[10014] IN (DTIN-8315, DTIN-8433, DTIN-9226, DTIN-9237, " &
        "DTIN-9251, DTIN-9266, DTIN-9300, DTIN-9331, DTIN-9365, DTIN-9392, " &
        "DTIN-15259, DTIN-15260)",

    baseUrl = "https://jiracloudweg.atlassian.net/rest/api/3/search",
    
    // 2. FUNÇÃO PARA BUSCAR DADOS (BASEADA NO CÓDIGO QUE FUNCIONA)
    fetchPage = (offset as number) as record =>
        let
            source = Json.Document(
                Web.Contents(
                    baseUrl,
                    [
                        Query = [
                            jql        = jqlQuery,
                            startAt    = Text.From(offset),
                            maxResults = "100",
                            fields     = "key,summary,status,assignee,creator,reporter,created,updated,project,timetracking,timespent,customfield_10014"
                        ],
                        Headers = [
                            Authorization = "Basic cm9saXZlaXJhQHdlZy5uZXQ6QVRBVFQzeEZmR0YwZG0xUzdSSHNReGFSTDZkNmZiaEZUMFNxSjZLbE9ScWRXQzg1M1Jlb3hFMUpnM0dSeXRUVTN4dG5McjdGVWg3WWFKZ2M1RDZwd3J5bjhQc3lHVDNrSklyRUlyVHpmNF9lMGJYLUdJdmxOOFIxanhyMV9GVGhLY1h3V1N0dU9VbE5ucEY2eFlhclhfWFpRb3RhTzlXeFhVaXlIWkdHTDFaMEx5cmJ4VzVyNVYwPUYxMDA3MDNF",
                            Accept = "application/json"
                        ]
                    ]
                )
            )
        in
            source,
    
    // 3. FUNÇÃO PARA BUSCAR TODAS AS PÁGINAS (BASEADA NO CÓDIGO QUE FUNCIONA)
    getAllPages = () as list =>
        let
            firstPage = fetchPage(0),
            totalIssues = firstPage[total],
            maxResults = 100,
            totalPages = Number.RoundUp(totalIssues / maxResults),
            pageNumbers = List.Numbers(0, totalPages, maxResults),
            allPages = List.Transform(pageNumbers, each fetchPage(_)),
            allIssues = List.Combine(List.Transform(allPages, each _[issues]))
        in
            allIssues,
    
    // 4. BUSCAR TODAS AS ISSUES
    allIssues = getAllPages(),
    issuesTable = Table.FromList(allIssues, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    
    // 5. EXPANDIR CAMPOS DA ISSUE
    expandIssue = Table.ExpandRecordColumn(
        issuesTable,
        "Column1",
        {"key", "fields"},
        {"key", "fields"}
    ),
    
    // 6. EXPANDIR CAMPOS ANINHADOS (TODOS OS CAMPOS NECESSÁRIOS)
    expandFields = Table.ExpandRecordColumn(
        expandIssue,
        "fields",
        {"summary", "status", "assignee", "creator", "reporter", "created", "updated", "project", "timetracking", "timespent", "customfield_10014"},
        {"summary", "status", "assignee", "creator", "reporter", "created", "updated", "project", "timetracking", "timespent", "EpicKey"}
    ),
    
    // 7. EXPANDIR STATUS
    expandStatus = Table.ExpandRecordColumn(
        expandFields,
        "status",
        {"name"},
        {"Status"}
    ),
    
    // 8. EXPANDIR ASSIGNEE
    expandAssignee = Table.ExpandRecordColumn(
        expandStatus,
        "assignee",
        {"displayName"},
        {"Responsável"}
    ),
    
    // 9. EXPANDIR CREATOR
    expandCreator = Table.ExpandRecordColumn(
        expandAssignee,
        "creator",
        {"displayName"},
        {"Criador"}
    ),
    
    // 10. EXPANDIR REPORTER
    expandReporter = Table.ExpandRecordColumn(
        expandCreator,
        "reporter",
        {"displayName"},
        {"Relator"}
    ),
    
    // 11. EXPANDIR PROJECT
    expandProject = Table.ExpandRecordColumn(
        expandReporter,
        "project",
        {"name"},
        {"Projeto"}
    ),
    
    // 12. EXPANDIR TIMETRACKING (CAMPO CRÍTICO)
    expandTimetracking = Table.ExpandRecordColumn(
        expandProject,
        "timetracking",
        {"timeSpentSeconds"},
        {"timeSpentSeconds"}
    ),
    
    // 13. RENOMEAR COLUNAS
    renameColumns = Table.RenameColumns(
        expandTimetracking,
        {
            {"key", "Chave"},
            {"summary", "Resumo"},
            {"created", "Data de Criação"},
            {"updated", "Última Atualização"}
        }
    ),
    
    // 14. ADICIONAR COLUNA DE HORAS CALCULADAS (LÓGICA QUE FUNCIONA)
    addHoursColumn = Table.AddColumn(
        renameColumns,
        "Horas Gastas",
        each
            let
                // Priorizar timetracking.timeSpentSeconds (soma correta de TODOS os worklogs)
                timeSpentSec = try [timeSpentSeconds] otherwise null,
                timeSpentDirect = try [timespent] otherwise null,
                finalHours = 
                    if timeSpentSec <> null and timeSpentSec > 0 then timeSpentSec / 3600
                    else if timeSpentDirect <> null and timeSpentDirect > 0 then timeSpentDirect / 3600
                    else 0
            in
                finalHours,
        type number
    ),
    
    // 15. SUBSTITUIR NULL EM RESPONSÁVEL
    replaceNullResponsavel = Table.ReplaceValue(
        addHoursColumn, 
        null, 
        "Não Atribuído", 
        Replacer.ReplaceValue, 
        {"Responsável"}
    ),
    
    // 16. SELECIONAR COLUNAS FINAIS
    selectColumns = Table.SelectColumns(
        replaceNullResponsavel,
        {"Chave", "Resumo", "Status", "Responsável", "Horas Gastas", "Projeto", "EpicKey", "Criador", "Relator", "Data de Criação", "Última Atualização"}
    ),
    
    // 17. ALTERAR TIPOS
    changeTypes = Table.TransformColumnTypes(
        selectColumns,
        {
            {"Data de Criação", type datetimezone},
            {"Última Atualização", type datetimezone},
            {"Horas Gastas", type number}
        }
    ),
    
    // 18. FILTROS FINAIS
    #"Linhas Filtradas" = Table.SelectRows(changeTypes, each true),
    #"Tipo Alterado" = Table.TransformColumnTypes(#"Linhas Filtradas",{{"Data de Criação", type date}, {"Última Atualização", type date}}),
    #"Linhas Filtradas1" = Table.SelectRows(#"Tipo Alterado", each ([Responsável] = "Thomas da Rosa"))
in
    #"Linhas Filtradas1"
