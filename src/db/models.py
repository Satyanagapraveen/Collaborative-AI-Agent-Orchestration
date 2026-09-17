import uuid
from sqlalchemy import Text, Column, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from src.db.database import Base

class Task(Base):
    __tablename__="tasks"
    id = Column(UUID(as_uuid=True), primary_key=True, default= uuid.uuid4)
    prompt = Column(Text, nullable=False)
    status= Column(String(50),nullable=False, default="PENDING")
    result= Column(Text, nullable=False)
    agent_logs=Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
