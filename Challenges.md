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

## Lesson learned

- PostgreSQL connection issues usually mean a missing database driver or a wrong database URL format.
- Import errors like this usually mean a wrong module was used.
- For SQLAlchemy, the correct pattern is to import Column from sqlalchemy, and data types from sqlalchemy or the specific dialect package when needed.
