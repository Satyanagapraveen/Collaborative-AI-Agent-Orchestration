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
