import time
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from sqlalchemy.orm import Session

from ..services.openai_service import OpenAIService
from ..services.auth import get_current_user
from ..schemas.user import User
from ..database import get_db  # Database session dependency
from ..services.ai_automation import AIAutomationService
from ..core.config import settings
from ..core.rate_limiter import limiter, get_clinic_rate_limit_key
from ..schemas.ai_automation import (
    AIRunCreate,
    AIFeedbackCreate,
    AIPromptVersionCreate,
    AIUsageCreate,
    AutomationRuleCreate,
    AutomationRunCreate,
    KnowledgeDocumentCreate,
    KnowledgeChunkCreate,
)

router = APIRouter(prefix="/ai", tags=["AI Features"])

# Allowed management roles for administrative AI and Knowledge actions
MANAGEMENT_ROLES = ["super_admin", "org_admin", "clinic_manager"]


def _normalize_role(role) -> str:
    if hasattr(role, "value"):
        return str(role.value).lower()
    return str(role).lower()


# ==========================================
# ROLE-BASED ACCESS CONTROL (RBAC) HELPER
# ==========================================
def require_role(allowed_roles: list[str]):
    def role_checker(current_user: User = Depends(get_current_user)):
        user_role = _normalize_role(getattr(current_user, "role", None))
        normalized_allowed = [_normalize_role(role) for role in allowed_roles]
        if user_role not in normalized_allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Aapko is action ko perform karne ki ijazat nahi hai (Insufficient permissions)."
            )
        return current_user
    return role_checker


class SummaryRequest(BaseModel):
    lead_notes: str = Field(..., description="Lead notes or conversation thread to summarize")

class SummaryResponse(BaseModel):
    success: bool
    ai_summary: str
    intent: Optional[str] = None


# ==========================================
# 1. AI LEAD SUMMARIZATION & RUNS
# ==========================================

@router.post("/summarize-lead", response_model=SummaryResponse)
@limiter.limit("10/minute", key_func=get_clinic_rate_limit_key)
async def summarize_lead_notes(
    request: Request,
    payload: SummaryRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an AI summary for lead notes using OpenAI asynchronously 
    with governance tracking and database logging.
    Rate limited to 10 requests per minute per clinic context.
    """
    start_time = time.time()
    try:
        summary = await OpenAIService.generate_lead_summary(payload.lead_notes)
        latency_ms = int((time.time() - start_time) * 1000)

        run_data = AIRunCreate(
            feature_name="lead_summary",
            model_name=settings.AI_PRIMARY_MODEL,
            prompt_version_id=None,
            user_id=getattr(current_user, "id", None),
            organization_id=getattr(current_user, "organization_id", None),
            clinic_id=getattr(current_user, "clinic_id", None),
            input_payload={"lead_notes": payload.lead_notes},
            output_payload={"ai_summary": summary, "intent": "Follow-up required"},
            latency_ms=latency_ms,
            prompt_tokens=50,
            completion_tokens=30,
            estimated_cost=0.0005,
            status="completed",
            error_message=None
        )
        
        AIAutomationService.create_ai_run(db=db, schema=run_data)

        return {
            "success": True, 
            "ai_summary": summary,
            "intent": "Follow-up required"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"AI summarization failed: {str(e)}"
        )


# ==========================================
# 2. AI FEEDBACK ENDPOINT
# ==========================================

@router.post("/feedback")
async def create_feedback(
    feedback: AIFeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit feedback for an AI run result (accepted, edited, or rejected).
    """
    try:
        if feedback.user_id is None:
            feedback.user_id = getattr(current_user, "id", None)
            
        return AIAutomationService.create_ai_feedback(db=db, schema=feedback)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=f"Failed to submit feedback: {str(e)}"
        )


# ==========================================
# 3. PROMPT VERSIONING ENDPOINTS (Restricted)
# ==========================================

@router.post("/prompts")
async def create_prompt_version(
    schema: AIPromptVersionCreate,
    current_user: User = Depends(require_role(MANAGEMENT_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Create a new version of an AI prompt.
    """
    try:
        return AIAutomationService.create_prompt_version(db=db, schema=schema)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/prompts/active/{feature_name}")
async def get_active_prompt(
    feature_name: str,
    current_user: User = Depends(require_role(MANAGEMENT_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Fetch the currently active prompt version for a specific feature.
    """
    prompt = AIAutomationService.get_active_prompt_version(db=db, feature_name=feature_name)
    if not prompt:
        raise HTTPException(status_code=404, detail="Active prompt version not found")
    return prompt


# ==========================================
# 4. AI USAGE & TOKEN TRACKING ENDPOINT (Restricted)
# ==========================================

@router.post("/usage")
async def log_ai_usage(
    schema: AIUsageCreate,
    current_user: User = Depends(require_role(MANAGEMENT_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Log token consumption and cost against an organization or user.
    """
    try:
        if schema.user_id is None:
            schema.user_id = getattr(current_user, "id", None)
        return AIAutomationService.create_ai_usage(db=db, schema=schema)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 5. AUTOMATION RULES & RUNS ENDPOINTS (Restricted)
# ==========================================

@router.post("/automation-rules")
async def create_automation_rule(
    schema: AutomationRuleCreate,
    current_user: User = Depends(require_role(MANAGEMENT_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Create a new automation rule for an organization.
    """
    try:
        return AIAutomationService.create_automation_rule(db=db, schema=schema)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/automation-rules/{organization_id}")
async def get_automation_rules(
    organization_id: UUID,
    current_user: User = Depends(require_role(MANAGEMENT_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Fetch all automation rules belonging to a specific organization.
    """
    return AIAutomationService.get_automation_rules_by_org(db=db, organization_id=organization_id)


@router.post("/automation-runs")
async def log_automation_run(
    schema: AutomationRunCreate,
    current_user: User = Depends(require_role(MANAGEMENT_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Log execution results of an automation rule trigger.
    """
    try:
        return AIAutomationService.create_automation_run(db=db, schema=schema)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# 6. KNOWLEDGE BASE & VECTOR CHUNKS ENDPOINTS (Restricted)
# ==========================================

@router.post("/knowledge/documents")
async def create_knowledge_document(
    schema: KnowledgeDocumentCreate,
    current_user: User = Depends(require_role(MANAGEMENT_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Register a knowledge document metadata source.
    """
    try:
        return AIAutomationService.create_knowledge_document(db=db, schema=schema)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/knowledge/chunks")
async def create_knowledge_chunk(
    schema: KnowledgeChunkCreate,
    current_user: User = Depends(require_role(MANAGEMENT_ROLES)),
    db: Session = Depends(get_db)
):
    """
    Store text chunks along with their pgvector embeddings for RAG search.
    """
    try:
        return AIAutomationService.create_knowledge_chunk(db=db, schema=schema)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))