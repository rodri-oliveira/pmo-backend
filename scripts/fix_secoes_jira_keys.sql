-- fix_secoes_jira_keys.sql
-- Script para corrigir mapeamento de jira_project_key na tabela secao

-- 1) Inspeção atual
SELECT id, nome, jira_project_key
  FROM secao
  ORDER BY id;

-- 2) Correção: seção 3 estava com jira_project_key errado
BEGIN;
  UPDATE secao
  SET jira_project_key = 'TIN'
  WHERE id = 3;
COMMIT;        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1637, in _execute_clauseelement     
    ret = self._execute_context(
        dialect,
    ...<8 lines>...
        cache_hit=cache_hit,
    )
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1842, in _execute_context
    return self._exec_single_context(
           ~~~~~~~~~~~~~~~~~~~~~~~~~^
        dialect, context, statement, parameters
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1982, in _exec_single_context       
    self._handle_dbapi_exception(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        e, str_statement, effective_parameters, cursor, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 2351, in _handle_dbapi_exception    
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1963, in _exec_single_context       
    self.dialect.do_execute(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        cursor, str_statement, effective_parameters, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\default.py", line 943, in do_execute
    cursor.execute(statement, parameters)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 580, in execute     
    self._adapt_connection.await_(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self._prepare_and_execute(operation, parameters)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 132, in await_only       
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 196, in greenlet_spawn   
    value = await result
            ^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 558, in _prepare_and_execute
    self._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 508, in _handle_exception
    self._adapt_connection._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 792, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.IntegrityError: (sqlalchemy.dialects.postgresql.asyncpg.IntegrityError) <class 'asyncpg.exceptions.UniqueViolationError'>: duplicate key value violates unique constraint "ix_projeto_jira_project_key"
DETAIL:  Key (jira_project_key)=(SEG) already exists.
[SQL: INSERT INTO projeto (nome, codigo_empresa, descricao, jira_project_key, status_projeto_id, secao_id, data_inicio_prevista, data_fim_prevista, data_criacao, data_atualizacao, ativo) VALUES ($1::VARCHAR, $2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::INTEGER, $6::INTEGER, $7::DATE, $8::DATE, now(), now(), $9::BOOLEAN) RETURNING projeto.id, projeto.data_criacao, projeto.data_atualizacao]
[parameters: ('RITM8268769 - ifrs-za.weg.net', None, None, 'SEG', 3, 1, None, None, True)]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
----------------------------------------------------

[DEBUG] Buscando projeto pelo nome: 'RITM8430932 - solarportal-api.weg.net'. Encontrado: Nenhum

--- ERRO AO PROCESSAR ISSUE: SEG-3853 ---
Traceback (most recent call last):
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 545, in _prepare_and_execute
    self._rows = deque(await prepared_stmt.fetch(*parameters))
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\asyncpg\prepared_stmt.py", line 176, in fetch
    data = await self.__bind_execute(args, 0, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\asyncpg\prepared_stmt.py", line 267, in __bind_execute
    data, status, _ = await self.__do_execute(
                      ^^^^^^^^^^^^^^^^^^^^^^^^
        lambda protocol: protocol.bind_execute(
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            self._state, args, '', limit, True, timeout))
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\asyncpg\prepared_stmt.py", line 256, in __do_execute
    return await executor(protocol)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "asyncpg\\protocol\\protocol.pyx", line 206, in bind_execute
asyncpg.exceptions.UniqueViolationError: duplicate key value violates unique constraint "ix_projeto_jira_project_key"
DETAIL:  Key (jira_project_key)=(SEG) already exists.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1963, in _exec_single_context
    self.dialect.do_execute(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        cursor, str_statement, effective_parameters, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\default.py", line 943, in do_execute
    cursor.execute(statement, parameters)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 580, in execute     
    self._adapt_connection.await_(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self._prepare_and_execute(operation, parameters)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 132, in await_only       
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 196, in greenlet_spawn   
    value = await result
            ^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 558, in _prepare_and_execute
    self._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 508, in _handle_exception
    self._adapt_connection._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 792, in _handle_exception
    raise translated_error from error
sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.IntegrityError: <class 'asyncpg.exceptions.UniqueViolationError'>: duplicate key value violates unique constraint "ix_projeto_jira_project_key"
DETAIL:  Key (jira_project_key)=(SEG) already exists.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\weg\automacaopmobackend\scripts\sincronizar_jira.py", line 71, in processar_periodo
    projeto = await proj_repo.create({
              ^^^^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
    })
    ^^
  File "C:\weg\automacaopmobackend\app\repositories\base_repository.py", line 69, in create
    raise e
  File "C:\weg\automacaopmobackend\app\repositories\base_repository.py", line 64, in create
    await self.db.commit()
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\ext\asyncio\session.py", line 1014, in commit
    await greenlet_spawn(self.sync_session.commit)
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 203, in greenlet_spawn   
    result = context.switch(value)
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 2032, in commit
    trans.commit(_to_root=True)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "<string>", line 2, in commit
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\state_changes.py", line 139, in _go
    ret_value = fn(self, *arg, **kw)
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 1313, in commit
    self._prepare_impl()
    ~~~~~~~~~~~~~~~~~~^^
  File "<string>", line 2, in _prepare_impl
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\state_changes.py", line 139, in _go
    ret_value = fn(self, *arg, **kw)
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 1288, in _prepare_impl
    self.session.flush()
    ~~~~~~~~~~~~~~~~~~^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 4345, in flush
    self._flush(objects)
    ~~~~~~~~~~~^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 4480, in _flush
    with util.safe_reraise():
         ~~~~~~~~~~~~~~~~~^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py", line 224, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 4441, in _flush
    flush_context.execute()
    ~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py", line 466, in execute
    rec.execute(self)
    ~~~~~~~~~~~^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py", line 642, in execute
    util.preloaded.orm_persistence.save_obj(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self.mapper,
        ^^^^^^^^^^^^
        uow.states_for_mapper_hierarchy(self.mapper, False, False),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        uow,
        ^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\persistence.py", line 93, in save_obj
    _emit_insert_statements(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        base_mapper,
        ^^^^^^^^^^^^
    ...<3 lines>...
        insert,
        ^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\persistence.py", line 1233, in _emit_insert_statements
    result = connection.execute(
        statement,
        params,
        execution_options=execution_options,
    )
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1415, in execute
    return meth(
        self,
        distilled_parameters,
        execution_options or NO_OPTIONS,
    )
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\sql\elements.py", line 523, in _execute_on_connection     
    return connection._execute_clauseelement(
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self, distilled_params, execution_options
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1637, in _execute_clauseelement     
    ret = self._execute_context(
        dialect,
    ...<8 lines>...
        cache_hit=cache_hit,
    )
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1842, in _execute_context
    return self._exec_single_context(
           ~~~~~~~~~~~~~~~~~~~~~~~~~^
        dialect, context, statement, parameters
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1982, in _exec_single_context       
    self._handle_dbapi_exception(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        e, str_statement, effective_parameters, cursor, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 2351, in _handle_dbapi_exception    
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1963, in _exec_single_context       
    self.dialect.do_execute(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        cursor, str_statement, effective_parameters, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\default.py", line 943, in do_execute
    cursor.execute(statement, parameters)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 580, in execute     
    self._adapt_connection.await_(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self._prepare_and_execute(operation, parameters)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 132, in await_only       
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 196, in greenlet_spawn   
    value = await result
            ^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 558, in _prepare_and_execute
    self._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 508, in _handle_exception
    self._adapt_connection._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 792, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.IntegrityError: (sqlalchemy.dialects.postgresql.asyncpg.IntegrityError) <class 'asyncpg.exceptions.UniqueViolationError'>: duplicate key value violates unique constraint "ix_projeto_jira_project_key"
DETAIL:  Key (jira_project_key)=(SEG) already exists.
[SQL: INSERT INTO projeto (nome, codigo_empresa, descricao, jira_project_key, status_projeto_id, secao_id, data_inicio_prevista, data_fim_prevista, data_criacao, data_atualizacao, ativo) VALUES ($1::VARCHAR, $2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::INTEGER, $6::INTEGER, $7::DATE, $8::DATE, now(), now(), $9::BOOLEAN) RETURNING projeto.id, projeto.data_criacao, projeto.data_atualizacao]
[parameters: ('RITM8430932 - solarportal-api.weg.net', None, None, 'SEG', 3, 1, None, None, True)]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
----------------------------------------------------

[DEBUG] Buscando projeto pelo nome: 'Assessment'. Encontrado: Nenhum

--- ERRO AO PROCESSAR ISSUE: SEG-3852 ---
Traceback (most recent call last):
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 545, in _prepare_and_execute
    self._rows = deque(await prepared_stmt.fetch(*parameters))
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\asyncpg\prepared_stmt.py", line 176, in fetch
    data = await self.__bind_execute(args, 0, timeout)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\asyncpg\prepared_stmt.py", line 267, in __bind_execute
    data, status, _ = await self.__do_execute(
                      ^^^^^^^^^^^^^^^^^^^^^^^^
        lambda protocol: protocol.bind_execute(
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
            self._state, args, '', limit, True, timeout))
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\asyncpg\prepared_stmt.py", line 256, in __do_execute
    return await executor(protocol)
           ^^^^^^^^^^^^^^^^^^^^^^^^
  File "asyncpg\\protocol\\protocol.pyx", line 206, in bind_execute
asyncpg.exceptions.UniqueViolationError: duplicate key value violates unique constraint "ix_projeto_jira_project_key"
DETAIL:  Key (jira_project_key)=(SEG) already exists.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1963, in _exec_single_context       
    self.dialect.do_execute(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        cursor, str_statement, effective_parameters, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\default.py", line 943, in do_execute
    cursor.execute(statement, parameters)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 580, in execute     
    self._adapt_connection.await_(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self._prepare_and_execute(operation, parameters)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 132, in await_only       
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 196, in greenlet_spawn
    value = await result
            ^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 558, in _prepare_and_execute
    self._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 508, in _handle_exception
    self._adapt_connection._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 792, in _handle_exception
    raise translated_error from error
sqlalchemy.dialects.postgresql.asyncpg.AsyncAdapt_asyncpg_dbapi.IntegrityError: <class 'asyncpg.exceptions.UniqueViolationError'>: duplicate key value violates unique constraint "ix_projeto_jira_project_key"
DETAIL:  Key (jira_project_key)=(SEG) already exists.

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "C:\weg\automacaopmobackend\scripts\sincronizar_jira.py", line 71, in processar_periodo
    projeto = await proj_repo.create({
              ^^^^^^^^^^^^^^^^^^^^^^^^
    ...<4 lines>...
    })
    ^^
  File "C:\weg\automacaopmobackend\app\repositories\base_repository.py", line 69, in create
    raise e
  File "C:\weg\automacaopmobackend\app\repositories\base_repository.py", line 64, in create
    await self.db.commit()
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\ext\asyncio\session.py", line 1014, in commit
    await greenlet_spawn(self.sync_session.commit)
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 203, in greenlet_spawn   
    result = context.switch(value)
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 2032, in commit
    trans.commit(_to_root=True)
    ~~~~~~~~~~~~^^^^^^^^^^^^^^^
  File "<string>", line 2, in commit
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\state_changes.py", line 139, in _go
    ret_value = fn(self, *arg, **kw)
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 1313, in commit
    self._prepare_impl()
    ~~~~~~~~~~~~~~~~~~^^
  File "<string>", line 2, in _prepare_impl
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\state_changes.py", line 139, in _go
    ret_value = fn(self, *arg, **kw)
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 1288, in _prepare_impl
    self.session.flush()
    ~~~~~~~~~~~~~~~~~~^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 4345, in flush
    self._flush(objects)
    ~~~~~~~~~~~^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 4480, in _flush
    with util.safe_reraise():
         ~~~~~~~~~~~~~~~~~^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\langhelpers.py", line 224, in __exit__
    raise exc_value.with_traceback(exc_tb)
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\session.py", line 4441, in _flush
    flush_context.execute()
    ~~~~~~~~~~~~~~~~~~~~~^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py", line 466, in execute
    rec.execute(self)
    ~~~~~~~~~~~^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\unitofwork.py", line 642, in execute
    util.preloaded.orm_persistence.save_obj(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self.mapper,
        ^^^^^^^^^^^^
        uow.states_for_mapper_hierarchy(self.mapper, False, False),
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        uow,
        ^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\persistence.py", line 93, in save_obj
    _emit_insert_statements(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        base_mapper,
        ^^^^^^^^^^^^
    ...<3 lines>...
        insert,
        ^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\orm\persistence.py", line 1233, in _emit_insert_statements
    result = connection.execute(
        statement,
        params,
        execution_options=execution_options,
    )
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1415, in execute
    return meth(
        self,
        distilled_parameters,
        execution_options or NO_OPTIONS,
    )
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\sql\elements.py", line 523, in _execute_on_connection     
    return connection._execute_clauseelement(
           ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self, distilled_params, execution_options
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1637, in _execute_clauseelement     
    ret = self._execute_context(
        dialect,
    ...<8 lines>...
        cache_hit=cache_hit,
    )
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1842, in _execute_context
    return self._exec_single_context(
           ~~~~~~~~~~~~~~~~~~~~~~~~~^
        dialect, context, statement, parameters
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1982, in _exec_single_context       
    self._handle_dbapi_exception(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        e, str_statement, effective_parameters, cursor, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 2351, in _handle_dbapi_exception    
    raise sqlalchemy_exception.with_traceback(exc_info[2]) from e
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\base.py", line 1963, in _exec_single_context       
    self.dialect.do_execute(
    ~~~~~~~~~~~~~~~~~~~~~~~^
        cursor, str_statement, effective_parameters, context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\engine\default.py", line 943, in do_execute
    cursor.execute(statement, parameters)
    ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 580, in execute     
    self._adapt_connection.await_(
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^
        self._prepare_and_execute(operation, parameters)
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 132, in await_only       
    return current.parent.switch(awaitable)  # type: ignore[no-any-return,attr-defined] # noqa: E501
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\util\_concurrency_py3k.py", line 196, in greenlet_spawn   
    value = await result
            ^^^^^^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 558, in _prepare_and_execute
    self._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 508, in _handle_exception
    self._adapt_connection._handle_exception(error)
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^
  File "C:\weg\automacaopmobackend\.venv\Lib\site-packages\sqlalchemy\dialects\postgresql\asyncpg.py", line 792, in _handle_exception
    raise translated_error from error
sqlalchemy.exc.IntegrityError: (sqlalchemy.dialects.postgresql.asyncpg.IntegrityError) <class 'asyncpg.exceptions.UniqueViolationError'>: duplicate key value violates unique constraint "ix_projeto_jira_project_key"
DETAIL:  Key (jira_project_key)=(SEG) already exists.
[SQL: INSERT INTO projeto (nome, codigo_empresa, descricao, jira_project_key, status_projeto_id, secao_id, data_inicio_prevista, data_fim_prevista, data_criacao, data_atualizacao, ativo) VALUES ($1::VARCHAR, $2::VARCHAR, $3::VARCHAR, $4::VARCHAR, $5::INTEGER, $6::INTEGER, $7::DATE, $8::DATE, now(), now(), $9::BOOLEAN) RETURNING projeto.id, projeto.data_criacao, projeto.data_atualizacao]
[parameters: ('Assessment', None, None, 'SEG', 3, 1, None, None, True)]
(Background on this error at: https://sqlalche.me/e/20/gkpj)
----------------------------------------------------

-- 3) Verificação pós-correção
SELECT id, nome, jira_project_key
  FROM secao
  ORDER BY id;
