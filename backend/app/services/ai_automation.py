from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status
from pgvector.sqlalchemy import Vector

from ..models.ai_automation import (
    AIPromptVersion,
    AIRun,
    AIFeedback,
    AIUsage,
    AutomationRule,
    AutomationRun,
    KnowledgeDocument,
    KnowledgeChunk,
)
from ..schemas.ai_automation import (
    AIPromptVersionCreate,
    AIRunCreate,
    AIFeedbackCreate,
    AIUsageCreate,
    AutomationRuleCreate,
    AutomationRunCreate,
    KnowledgeDocumentCreate,
    KnowledgeChunkCreate,
)


class AIAutomationService:
    """Service handling AI prompts, runs, feedback, usage, automation rules, and knowledge base"""

    @staticmethod
    def create_prompt_version(db: Session, schema: AIPromptVersionCreate) -> AIPromptVersion:
        db_obj = AIPromptVersion(**schema.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_active_prompt_version(db: Session, feature_name: str) -> Optional[AIPromptVersion]:
        return (
            db.query(AIPromptVersion)
            .filter(AIPromptVersion.feature_name == feature_name, AIPromptVersion.is_active == True)
            .order_by(AIPromptVersion.version.desc())
            .first()
        )

    @staticmethod
    def create_ai_run(db: Session, schema: AIRunCreate) -> AIRun:
        db_obj = AIRun(**schema.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def create_ai_feedback(db: Session, schema: AIFeedbackCreate) -> AIFeedback:
        db_obj = AIFeedback(**schema.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def create_ai_usage(db: Session, schema: AIUsageCreate) -> AIUsage:
        db_obj = AIUsage(**schema.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def create_automation_rule(db: Session, schema: AutomationRuleCreate) -> AutomationRule:
        db_obj = AutomationRule(**schema.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_automation_rules_by_org(db: Session, organization_id: UUID) -> List[AutomationRule]:
        return db.query(AutomationRule).filter(AutomationRule.organization_id == organization_id).all()

    @staticmethod
    def create_automation_run(db: Session, schema: AutomationRunCreate) -> AutomationRun:
        db_obj = AutomationRun(**schema.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def create_knowledge_document(db: Session, schema: KnowledgeDocumentCreate) -> KnowledgeDocument:
        db_obj = KnowledgeDocument(**schema.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def create_knowledge_chunk(db: Session, schema: KnowledgeChunkCreate) -> KnowledgeChunk:
        """
        Store a knowledge chunk in the database.
        Embedding should be pre-generated and passed in schema.embedding.
        The API layer (ai.py) handles auto-generation via OpenAIService.generate_embedding().
        """
        db_obj = KnowledgeChunk(**schema.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def search_similar_chunks(
        db: Session,
        query_embedding: List[float],
        organization_id: UUID,
        top_k: int = 5,
        document_id: Optional[UUID] = None
    ) -> List[KnowledgeChunk]:
        """
        RAG Retriever: Find the most semantically similar chunks
        to a query embedding using pgvector cosine distance.

        Lower cosine distance = more similar.
        Filters by organization_id (data isolation between clinics).
        Optionally filter by document_id to search within a specific document.

        Args:
            db: SQLAlchemy session
            query_embedding: 1536-dim float list from OpenAIService.generate_embedding()
            organization_id: Only search chunks belonging to this org
            top_k: Number of top results to return (default 5)
            document_id: Optional — restrict search to one document

        Returns:
            List of KnowledgeChunk objects ordered by similarity (most relevant first)
        """
        query = (
            db.query(KnowledgeChunk)
            .filter(
                KnowledgeChunk.organization_id == organization_id,
                KnowledgeChunk.embedding.isnot(None)  # Skip chunks with no embedding
            )
        )

        if document_id:
            query = query.filter(KnowledgeChunk.document_id == document_id)

        # pgvector cosine_distance: 0 = identical, 2 = opposite
        results = (
            query
            .order_by(KnowledgeChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
            .all()
        )
        return results

    @staticmethod
    def get_chunks_by_document(db: Session, document_id: UUID) -> List[KnowledgeChunk]:
        """
        List all chunks belonging to a specific knowledge document.
        Useful for frontend to show what chunks are stored under a document.
        """
        return (
            db.query(KnowledgeChunk)
            .filter(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.created_at.asc())
            .all()
        )