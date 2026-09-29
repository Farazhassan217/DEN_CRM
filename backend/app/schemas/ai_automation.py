from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


# 1. AI Prompt Version Schemas
class AIPromptVersionBase(BaseModel):
    feature_name: str
    version: int
    system_prompt: str
    user_prompt_template: str
    is_active: Optional[bool] = True


class AIPromptVersionCreate(AIPromptVersionBase):
    pass


class AIPromptVersionResponse(AIPromptVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# 2. AI Run Schemas
class AIRunBase(BaseModel):
    feature_name: str
    model_name: str
    prompt_version_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    organization_id: Optional[UUID] = None
    clinic_id: Optional[UUID] = None
    input_payload: Dict[str, Any]
    output_payload: Optional[Dict[str, Any]] = None
    latency_ms: Optional[int] = None
    prompt_tokens: Optional[int] = 0
    completion_tokens: Optional[int] = 0
    estimated_cost: Optional[float] = 0.0
    status: Optional[str] = "completed"
    error_message: Optional[str] = None


class AIRunCreate(AIRunBase):
    pass


class AIRunResponse(AIRunBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# 3. AI Feedback Schemas
class AIFeedbackBase(BaseModel):
    ai_run_id: UUID
    user_id: Optional[UUID] = None
    action: str  # 'accepted', 'edited', 'rejected'
    edited_output: Optional[Dict[str, Any]] = None
    feedback_text: Optional[str] = None


class AIFeedbackCreate(AIFeedbackBase):
    pass


class AIFeedbackResponse(AIFeedbackBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# 4. AI Usage Schemas
class AIUsageBase(BaseModel):
    organization_id: UUID
    clinic_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    feature_name: str
    input_tokens: int = 0
    output_tokens: int = 0
    total_cost: float = 0.0


class AIUsageCreate(AIUsageBase):
    pass


class AIUsageResponse(AIUsageBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# 5. Automation Rule Schemas
class AutomationRuleBase(BaseModel):
    organization_id: UUID
    clinic_id: Optional[UUID] = None
    name: str
    event_trigger: str
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict)
    actions: Dict[str, Any]
    is_active: Optional[bool] = True


class AutomationRuleCreate(AutomationRuleBase):
    pass


class AutomationRuleResponse(AutomationRuleBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# 6. Automation Run Schemas
class AutomationRunBase(BaseModel):
    rule_id: Optional[UUID] = None
    triggered_by_entity: Optional[str] = None
    triggered_by_id: Optional[UUID] = None
    status: Optional[str] = "success"
    execution_details: Optional[Dict[str, Any]] = None


class AutomationRunCreate(AutomationRunBase):
    pass


class AutomationRunResponse(AutomationRunBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    executed_at: datetime


# 7. Knowledge Document Schemas
class KnowledgeDocumentBase(BaseModel):
    organization_id: UUID
    title: str
    source_type: str
    metadata_info: Optional[Dict[str, Any]] = Field(default_factory=dict)


class KnowledgeDocumentCreate(KnowledgeDocumentBase):
    pass


class KnowledgeDocumentResponse(KnowledgeDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# 8. Knowledge Chunk Schemas
class KnowledgeChunkBase(BaseModel):
    document_id: UUID
    organization_id: UUID
    content: str
    embedding: Optional[List[float]] = None


class KnowledgeChunkCreate(KnowledgeChunkBase):
    pass


class KnowledgeChunkResponse(KnowledgeChunkBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


# 9. Knowledge RAG Search Schemas
class KnowledgeSearchRequest(BaseModel):
    """
    Request body for the RAG semantic search endpoint.
    Frontend sends the user's natural language query here.
    """
    query: str                              # User ka sawal / search text
    organization_id: UUID                   # Sirf is org ke chunks search ho
    document_id: Optional[UUID] = None      # Optional: sirf ek document mein search karo
    top_k: Optional[int] = Field(default=5, ge=1, le=20)  # Kitne results chahiye (1-20)


class KnowledgeSearchResultItem(BaseModel):
    """
    Single search result — one relevant chunk with its similarity score.
    """
    model_config = ConfigDict(from_attributes=True)

    chunk_id: UUID
    document_id: UUID
    content: str                            # The actual text chunk
    similarity_score: float                 # 0.0 = most similar, 2.0 = least similar (cosine distance)


class KnowledgeSearchResponse(BaseModel):
    """
    Full response from the RAG search endpoint.
    """
    query: str                              # Original query (for frontend reference)
    results: List[KnowledgeSearchResultItem]
    total_results: int