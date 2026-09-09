from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from fastapi import HTTPException, status

from app.models.ai_automation import (
    AIPromptVersion,
    AIRun,
    AIFeedback,
    AIUsage,
    AutomationRule,
    AutomationRun,
    KnowledgeDocument,
    KnowledgeChunk,
)
from app.schemas.ai_automation import (
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
        db_obj = KnowledgeChunk(**schema.dict())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj