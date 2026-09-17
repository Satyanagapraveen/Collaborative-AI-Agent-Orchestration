import sqlalchemy
import os
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio.engine import create_async_engine, AsyncSession

load_dotenv()

DATABASE_URL=os.getenv("DATABASE_URL")
engine=create_async_engine(
    DATABASE_URL,
    echo=False,
    flush=True
)
AsyncSessionLocal=sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base=declarative_base()
async def get_db():
    async with AsyncSessionLocal as session:
        yield session