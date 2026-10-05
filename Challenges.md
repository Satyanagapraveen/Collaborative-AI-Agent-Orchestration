# Challenges and Fixes Log

## Challenge 1:

PostgreSQL driver missing while starting the FastAPI app

### Error logs when I try to run or do something

File "/api/src/main.py", line 2, in <module>

    from src.db.database import engine, Base

File "/api/src/db/database.py", line 10, in <module>

    engine = create_async_engine(

             ^^^^^^^^^^^^^^^^^^^^

File "/usr/local/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/engine.py", line 120, in create_async_engine

    sync_engine = _create_engine(url, **kw)

                  ^^^^^^^^^^^^^^^^^^^^^^^^^

File "<string>", line 2, in create_engine

File "/usr/local/lib/python3.11/site-packages/sqlalchemy/util/deprecations.py", line 281, in warned

    return fn(*args, **kwargs)  # type: ignore[no-any-return]

           ^^^^^^^^^^^^^^^^^^^^^^

File "/usr/local/lib/python3.11/site-packages/sqlalchemy/engine/create.py", line 617, in create_engine

    dbapi = dbapi_meth(**dbapi_args)

            ^^^^^^^^^^^^^^^^^^^^^^

File "/usr/local/lib/python3.11/site-packages/sqlalchemy/dialects/postgresql/psycopg2.py", line 697, in import_dbapi

    import psycopg2

ModuleNotFoundError: No module named 'psycopg2'

### Problem

The app is connecting to PostgreSQL, but the required Python driver for PostgreSQL is not installed. SQLAlchemy tries to import psycopg2 when the database URL points to PostgreSQL, and since it is missing, the app crashes during import.

### Fix

Install the correct PostgreSQL driver package for the type of database URL you are using.

For an async SQLAlchemy app, the best setup is usually:

- use a URL like postgresql+asyncpg://...
- install asyncpg

If you choose the sync PostgreSQL driver instead:

- use a URL like postgresql://...
- install psycopg2-binary

This project was using async SQLAlchemy, so the correct fix is to make sure the PostgreSQL async driver is installed and the DATABASE_URL matches it.

---

## Challenge 2:

Wrong import for the Column object in SQLAlchemy model definitions

### Error logs when I try to run or do something

from src.db import models

File "/api/src/db/models.py", line 2, in <module>

    from sqlalchemy.types import Text, Column, String, DateTime

ImportError: cannot import name 'Column' from 'sqlalchemy.types' (/usr/local/lib/python3.11/site-packages/sqlalchemy/types.py)

### Problem

The developer imported Column from sqlalchemy.types. That module contains data types like String, Text, and DateTime, but not the Column class used to define table columns in SQLAlchemy models.

### Fix

Import Column from the main SQLAlchemy package instead:

from sqlalchemy import Column, String, Text, DateTime

This is the correct pattern for SQLAlchemy ORM models. The types like Text and String still come from sqlalchemy, while Column is a separate SQLAlchemy construct used in model declarations.

---

## Challenge 3:

Celery task unregistered: worker receives message but task is not registered

### Error logs when I try to run or do something

worker-1 | [2026-09-17 12:24:47,443: ERROR/MainProcess] Received unregistered task of type 'run*agent_workflow'.
api-1 | INFO: 172.29.0.1:57858 - "POST /api/v1/tasks HTTP/1.1" 202 Accepted
worker-1 | The message has been ignored and discarded.
worker-1 |
worker-1 | Did you remember to import the module containing this task?
worker-1 | Or maybe you're using relative imports?
worker-1 |
worker-1 | Please see
worker-1 | https://docs.celeryq.dev/en/latest/internals/protocol.html
worker-1 | for more information.
worker-1 |
worker-1 | The full contents of the message body was:
worker-1 | b'[["c1e0f712-4436-4be6-b02f-62249ddabb54", "Async test"], {}, {"callbacks": null, "errbacks": null, "chain": null, "chord": null}]' (129b)
worker-1 |
worker-1 | The full contents of the message headers:
worker-1 | {'lang': 'py', 'task': 'run_agent_workflow', 'id': '5a68ae30-cc21-4f45-a78a-197c85a9524d', 'shadow': None, 'eta': None, 'expires': None, 'group': None, 'group_index': None, 'retries': 0, 'timelimit': [None, None], 'root_id': '5a68ae30-cc21-4f45-a78a-197c85a9524d', 'parent_id': None, 'origin': 'gen14@4158ed53bdbc', 'ignore_result': False, 'replaced_task_nesting': 0, 'stamped_headers': None, 'stamps': {}}
worker-1 |
worker-1 | The delivery info for this task is:
worker-1 | {'exchange': '', 'routing_key': 'celery'}
worker-1 | Traceback (most recent call last):
worker-1 | File "/usr/local/lib/python3.11/site-packages/celery/worker/consumer/consumer.py", line 668, in on_task_received
worker-1 | strategy = strategies[type*]
worker-1 | ~^^^^^^^
worker-1 | KeyError: 'run_agent_workflow'

### Problem

The API successfully sent the job to Redis/Broker, but the Celery worker did not know about the task definition. The task name was `run_agent_workflow`, but the worker's task registry never had that function registered. This usually happens when the task module is not imported when the Celery worker starts.

### Fix

Register the task module when creating the Celery app, using include.

Example:

from celery import Celery

celery_app = Celery(
"agent_worker",
broker=os.getenv("CELERY_BROKER_URL"),
backend=os.getenv("CELERY_RESULT_BACKEND"),
include=["src.worker.tasks"]
)

This tells Celery to import the module containing the decorated task before accepting jobs.

### Alternative fix

Use autodiscover_tasks so Celery imports tasks from your app packages automatically:

celery_app = Celery(
"agent_worker",
broker=os.getenv("CELERY_BROKER_URL"),
backend=os.getenv("CELERY_RESULT_BACKEND")
)

celery_app.autodiscover_tasks(["src"])

This works when your tasks are organized under a package structure and you want Celery to discover them automatically.

---

## Lesson learned

- PostgreSQL connection issues usually mean a missing database driver or a wrong database URL format.
- Import errors like this usually mean a wrong module was used.
- For SQLAlchemy, the correct pattern is to import Column from sqlalchemy, and data types from sqlalchemy or the specific dialect package when needed.
- Celery task registration errors happen when the worker does not import the task module. The fix is to register the task with include or autodiscover_tasks.

---

## Challenge 4:

asyncpg InterfaceError: "cannot perform operation: another operation is in progress"

### Error logs when I try to run or do something

sqlalchemy.exc.InterfaceError: (sqlalchemy.dialects.postgresql.asyncpg.InterfaceError) <class 'asyncpg.exceptions.\_base.InterfaceError'>: cannot perform operation: another operation is in progress

[SQL: SELECT tasks.id, tasks.prompt, tasks.status, tasks.result, tasks.agent_logs, tasks.created_at, tasks.updated_at

FROM tasks

WHERE tasks.id = $1::UUID]

[parameters: ('8b00bdc4-e5a9-4953-b25b-a53878d6ba89',)]

##(Background on this error at: https://sqlalche.me/e/20/rvf5)

Trace shows SQLAlchemy/asyncpg raised the InterfaceError while trying to start a transaction for a SELECT — the underlying message from asyncpg is that the connection was already executing another operation.

### Problem

asyncpg (the async Postgres driver) does not allow overlapping operations on the same physical connection. This error means your code attempted to run a DB operation while a previous operation was still in progress on the same connection/session. Common causes:

- sharing a single `AsyncSession` or connection across concurrent coroutines
- holding a transaction open while doing long non-DB work (sleeps, external I/O) and then attempting more DB work on the same session
- reusing session/connection objects across thread/worker boundaries (Celery tasks vs API coroutines)

In this project the worker `run_agent_workflow` created DB work while also invoking async orchestration (`agent_app.ainvoke`) and used the same session/connection for multiple awaits. The fix implemented was to create an isolated engine + session for the task so the task gets its own dedicated connection.

### Fix (what I implemented)

I created a brand-new isolated async engine and sessionmaker for each Celery task run, used that session for all DB work inside the task, and disposed the engine when finished. Key points from the implementation:

- Create an isolated async engine using `create_async_engine(os.getenv("DATABASE_URL"))` inside the task function.
- Build a dedicated `async_sessionmaker(engine, expire_on_commit=False)` and `async with` that session for all DB calls in the workflow.
- Commit and close the session before long non-DB waits, and `await engine.dispose()` in `finally` to clean up connections.

This prevents concurrent operations from colliding on a shared connection because each task gets its own connection pool/engine.

### Alternative / better patterns

- Prefer creating a shared `Engine` once (module-level) and then making isolated sessions per task: `async_sessionmaker(shared_engine)` — this reuses the connection pool while guaranteeing each task uses its own session/connection.
- Ensure transactions are short: commit or close the session before long sleeps or network calls.
- If you must run concurrent DB queries within one coroutine, use separate sessions for each concurrent subtask.

---

## Challenge 5:

SQLAlchemy asyncio module missing dependency: greenlet

### Error logs when I try to run or do something

Traceback (most recent call last):

File "/usr/local/lib/python3.11/site-packages/sqlalchemy/util/concurrency.py", line 70, in \_initialize

from greenlet import getcurrent

ModuleNotFoundError: No module named 'greenlet'

The above exception was the direct cause of the following exception:
Traceback (most recent call last):

File "/usr/local/bin/celery", line 8, in <module>

sys.exit(main())

File "/api/src/worker/tasks.py", line 5, in <module>
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
File "/usr/local/lib/python3.11/site-packages/sqlalchemy/ext/asyncio/**init**.py", line 28, in <module>

concurrency.\_concurrency_shim.\_initialize()

File "/usr/local/lib/python3.11/site-packages/sqlalchemy/util/concurrency.py", line 79, in \_initialize

raise ImportError(\_ERROR_MESSAGE) from e

ImportError: The SQLAlchemy asyncio module requires that the Python 'greenlet' library is installed. In order to ensure this dependency is available, use the 'sqlalchemy[asyncio]' install target: 'pip install sqlalchemy[asyncio]'

### Problem

We were using SQLAlchemy's async features (`create_async_engine`, `async_sessionmaker`) inside Celery workers. SQLAlchemy's asyncio support depends on a package called `greenlet`. The worker booted, imported the async SQLAlchemy module, and immediately detected that `greenlet` was missing. This is not a PostgreSQL problem; it is a Python dependency problem for SQLAlchemy async support.

### Fix

Update the dependency list so Docker installs the async support for SQLAlchemy. In this project, the fix is to add the extra dependency in `requirements.txt`:

sqlalchemy[asyncio]

This tells pip to install `greenlet` automatically along with SQLAlchemy's async support.

We also needed to rebuild the container so the new dependency gets installed:

```bash
docker-compose up --build -d
```

### What greenlet is

SQLAlchemy was originally built as a mostly synchronous library. When async Python became common, the library needed a way to bridge its older sync internals with the new async database driver. That bridge is `greenlet`.

`greenlet` enables Python code to pause in one context and resume in another, so SQLAlchemy can coordinate async behavior without rewriting the entire framework. Without it, SQLAlchemy's async engine module cannot initialize correctly, and `create_async_engine` fails early.

### Lesson learned

- PostgreSQL connection issues usually mean a missing database driver or a wrong database URL format.
- Import errors like this usually mean a wrong module was used.
- For SQLAlchemy async work, the missing dependency may be `greenlet`, not just `asyncpg`.
- Always install SQLAlchemy async extras when using `create_async_engine` and async sessions.
- For Docker-based projects, rebuild the image after updating `requirements.txt` so the dependency is actually installed.

---

## Challenge 6:

FastAPI reload triggered a deadlock because the WebSocket loop did not stop gracefully

### Error logs when I try to run or do something

```bash
python test_ws.py
Creating new task...
```

Docker logs:

```text
INFO:     connection open
api
INFO:     172.29.0.1:41478 - "POST /api/v1/tasks/a1e6c2fe-5117-4c6e-9080-f593536343d7/approve HTTP/1.1" 200 OK
worker
[2026-10-05 05:31:43,393: INFO/MainProcess] Task resume_agent_workflow[1eb80161-0b4f-4852-98a8-97f3eb10a4fd] received
[2026-10-05 05:31:43,436: INFO/ForkPoolWorker-15] Human approval received. Publishing final result.
[2026-10-05 05:31:43,450: INFO/ForkPoolWorker-15] Task resume_agent_workflow[1eb80161-0b4f-4852-98a8-97f3eb10a4fd] succeeded in 0.055953772999600915s: None
api
WARNING:  WatchFiles detected changes in 'test_ws.py'. Reloading...
INFO:     Shutting down
INFO:     Waiting for background tasks to complete. (CTRL+C to force quit)
```

### Problem

The server was reloading because Docker detected a file change. During reload, FastAPI began shutdown. But the WebSocket loop in `websocket_task_status` kept running forever in a `while True` loop and did not catch the shutdown signal. Because of that, the server got stuck in a shutdown state and could not complete the request cleanly. The client script appeared to hang at `Creating new task...` because the server never responded.

### Fix

Add graceful shutdown handling in the WebSocket endpoint. The key fix is to catch `asyncio.CancelledError` (and still unsubscribe from Redis), then break the loop cleanly.

Example:

```python
            await asyncio.sleep(0.1)
    except WebSocketDisconnect:
        await pubsub.unsubscribe(channel_name)
    except asyncio.CancelledError:
        await pubsub.unsubscribe(channel_name)
        raise
```

This prevents the WebSocket loop from keeping the server alive during shutdown, so the app can reload cleanly without deadlocking.

---

## Lesson learned

- PostgreSQL connection issues usually mean a missing database driver or a wrong database URL format.
- Import errors like this usually mean a wrong module was used.
- For SQLAlchemy, the correct pattern is to import Column from sqlalchemy, and data types from sqlalchemy or the specific dialect package when needed.
- Celery task registration errors happen when the worker does not import the task module. The fix is to register the task with include or autodiscover_tasks.
- asyncpg InterfaceError typically indicates overlapping DB operations on the same connection; use isolated sessions/connections and keep transactions short.
- SQLAlchemy async support requires `greenlet`; install `sqlalchemy[asyncio]` or `greenlet` explicitly.
- WebSocket loops must handle shutdown and cancellation gracefully; otherwise a server reload can hang and look like a deadlock.
