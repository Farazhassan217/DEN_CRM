import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Boolean, DateTime, 
    Numeric, Text, ForeignKey
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector  # pgvector-python package

from ..database import Base


class AIPromptVersion(Base):
    __tablename__ = "ai_prompt_versions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_name = Column(String(100), nullable=False)
    version = Column(Integer, nullable=False)
    system_prompt = Column(Text, nullable=False)
    user_prompt_template = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AIRun(Base):
    __tablename__ = "ai_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    feature_name = Column(String(100), nullable=False)
    model_name = Column(String(100), nullable=False)
    prompt_version_id = Column(UUID(as_uuid=True), ForeignKey("ai_prompt_versions.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Removed ForeignKey to avoid NoReferencedTableError
    organization_id = Column(UUID(as_uuid=True), nullable=True)
    clinic_id = Column(UUID(as_uuid=True), nullable=True)
    input_payload = Column(JSONB, nullable=False)
    output_payload = Column(JSONB, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    estimated_cost = Column(Numeric(10, 6), default=0.0)
    status = Column(String(50), nullable=False, default="completed")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    feedbacks = relationship("AIFeedback", back_populates="ai_run", cascade="all, delete-orphan")


class AIFeedback(Base):
    __tablename__ = "ai_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ai_run_id = Column(UUID(as_uuid=True), ForeignKey("ai_runs.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Removed ForeignKey to avoid NoReferencedTableError
    action = Column(String(50), nullable=False)  # 'accepted', 'edited', 'rejected'
    edited_output = Column(JSONB, nullable=True)
    feedback_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)

    ai_run = relationship("AIRun", back_populates="feedbacks")


class AIUsage(Base):
    __tablename__ = "ai_usage"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    clinic_id = Column(UUID(as_uuid=True), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Removed ForeignKey to avoid NoReferencedTableError
    feature_name = Column(String(100), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    total_cost = Column(Numeric(10, 6), nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    clinic_id = Column(UUID(as_uuid=True), nullable=True)
    name = Column(String(255), nullable=False)
    event_trigger = Column(String(100), nullable=False)
    conditions = Column(JSONB, default={})
    actions = Column(JSONB, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AutomationRun(Base):
    __tablename__ = "automation_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_id = Column(UUID(as_uuid=True), ForeignKey("automation_rules.id", ondelete="CASCADE"), nullable=True)
    triggered_by_entity = Column(String(100), nullable=True)
    triggered_by_id = Column(UUID(as_uuid=True), nullable=True)
    status = Column(String(50), nullable=False, default="success")
    execution_details = Column(JSONB, nullable=True)
    executed_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    title = Column(String(255), nullable=False)
    source_type = Column(String(50), nullable=False)
    metadata_info = Column(JSONB, default={})
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class KnowledgeChunk(Base):
    __tablename__ = "knowledge_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536), nullable=True)  # pgvector column
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)