from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict


# ---------- Auth / User ----------
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "agent"


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------- Tickets ----------
class TicketBase(BaseModel):
    customer_name: str
    customer_email: EmailStr
    company: Optional[str] = None
    subject: str
    message: str
    category: str = "General Question"
    status: str = "New"
    priority: str = "Medium"
    sentiment: str = "Neutral"
    assigned_agent_id: Optional[int] = None


class TicketCreate(TicketBase):
    pass


class TicketUpdate(BaseModel):
    customer_name: Optional[str] = None
    customer_email: Optional[EmailStr] = None
    company: Optional[str] = None
    subject: Optional[str] = None
    message: Optional[str] = None
    category: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    sentiment: Optional[str] = None
    ai_summary: Optional[str] = None
    ai_suggested_reply: Optional[str] = None
    escalation_recommendation: Optional[bool] = None
    assigned_agent_id: Optional[int] = None
    first_response_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class TicketOut(TicketBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ai_summary: Optional[str] = None
    ai_suggested_reply: Optional[str] = None
    escalation_recommendation: bool = False
    assigned_agent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    first_response_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    first_response_time_minutes: Optional[float] = None
    resolution_time_minutes: Optional[float] = None


# ---------- Analysis ----------
class TicketAnalysisOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: int
    summary: str
    customer_intent: Optional[str] = None
    sentiment: str
    priority: str
    category: str
    escalate: bool
    escalation_reason: Optional[str] = None
    suggested_reply_tone: str
    key_issue: Optional[str] = None
    risk_level: str
    suggested_next_action: Optional[str] = None
    confidence: float
    created_at: datetime
    updated_at: datetime


class BulkAnalyzeRequest(BaseModel):
    ticket_ids: Optional[list[int]] = None


# ---------- Replies ----------
class ReplyGenerateRequest(BaseModel):
    tone: str = "Professional"
    regenerate: bool = False


class ReplyUpdate(BaseModel):
    content: Optional[str] = None
    tone: Optional[str] = None
    status: Optional[str] = None


class ReplyDraftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: int
    agent_id: Optional[int] = None
    content: str
    tone: str
    status: str
    ai_generated: bool
    citations: Optional[list[Any]] = None
    created_at: datetime
    updated_at: datetime
    approved_at: Optional[datetime] = None
    sent_at: Optional[datetime] = None


# ---------- Escalations ----------
class EscalationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticket_id: int
    escalate: bool
    reason: str
    recommended_team: str
    internal_note: Optional[str] = None
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None


class EscalationUpdate(BaseModel):
    status: Optional[str] = None
    recommended_team: Optional[str] = None
    internal_note: Optional[str] = None
    reason: Optional[str] = None


# ---------- Knowledge Base ----------
class KBDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    filename: str
    file_type: str
    chunk_count: int
    status: str
    created_at: datetime
    updated_at: datetime


class KBDocumentDetail(KBDocumentOut):
    content: str


class KBSearchRequest(BaseModel):
    query: str
    limit: int = Field(default=5, ge=1, le=20)


class KBSearchResult(BaseModel):
    chunk_id: int
    document_id: int
    document_title: str
    content: str
    score: float


# ---------- Copilot ----------
class CopilotAskRequest(BaseModel):
    question: str
    session_id: Optional[int] = None


class CopilotMessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    session_id: int
    role: str
    content: str
    citations: Optional[list[Any]] = None
    created_at: datetime


class CopilotSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: list[CopilotMessageOut] = []


class CopilotAskResponse(BaseModel):
    session_id: int
    answer: str
    citations: list[KBSearchResult] = []
    message: CopilotMessageOut


# ---------- Analytics ----------
class DashboardAnalytics(BaseModel):
    total_tickets: int
    open_tickets: int
    pending_tickets: int
    resolved_tickets: int
    escalated_tickets: int
    new_tickets: int
    average_response_time_minutes: Optional[float] = None
    customer_satisfaction: float = 4.2
    sentiment_breakdown: dict[str, int]
    priority_breakdown: dict[str, int]
    category_breakdown: dict[str, int]
    status_breakdown: dict[str, int]
    recent_urgent: list[TicketOut] = []
    recent_replies: list[ReplyDraftOut] = []
    escalation_rate: float = 0.0
    resolution_rate: float = 0.0
    ai_approval_rate: float = 0.0
    overdue_tickets: int = 0
    sla_risk_tickets: int = 0


class ResponseTimeAnalytics(BaseModel):
    average_first_response_minutes: Optional[float] = None
    average_resolution_minutes: Optional[float] = None
    overdue_tickets: list[TicketOut] = []
    sla_risk_tickets: list[TicketOut] = []
    by_priority: dict[str, dict[str, Optional[float]]]


# ---------- Recommendations ----------
class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: str
    category: str
    priority: str
    action_items: Optional[list[Any]] = None
    created_at: datetime


# ---------- Settings ----------
class SettingsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    business_name: str
    support_email: str
    default_reply_tone: str
    sla_urgent_hours: float
    sla_high_hours: float
    sla_medium_hours: float
    sla_low_hours: float
    ai_provider: str
    api_key_placeholder: str
    chat_model: str
    embedding_model: str
    default_escalation_team: str
    updated_at: datetime


class SettingsUpdate(BaseModel):
    business_name: Optional[str] = None
    support_email: Optional[str] = None
    default_reply_tone: Optional[str] = None
    sla_urgent_hours: Optional[float] = None
    sla_high_hours: Optional[float] = None
    sla_medium_hours: Optional[float] = None
    sla_low_hours: Optional[float] = None
    ai_provider: Optional[str] = None
    api_key_placeholder: Optional[str] = None
    chat_model: Optional[str] = None
    embedding_model: Optional[str] = None
    default_escalation_team: Optional[str] = None


class MessageResponse(BaseModel):
    message: str
    detail: Optional[Any] = None
