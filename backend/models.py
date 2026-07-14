from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    DateTime,
    ForeignKey,
    JSON,
)
from sqlalchemy.orm import relationship

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), default="agent")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tickets = relationship("Ticket", back_populates="assigned_agent")
    reply_drafts = relationship("ReplyDraft", back_populates="agent")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False, index=True)
    company = Column(String(255), nullable=True)
    subject = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String(100), default="General Question")
    status = Column(String(50), default="New", index=True)
    priority = Column(String(50), default="Medium", index=True)
    sentiment = Column(String(50), default="Neutral", index=True)
    ai_summary = Column(Text, nullable=True)
    ai_suggested_reply = Column(Text, nullable=True)
    escalation_recommendation = Column(Boolean, default=False)
    assigned_agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    first_response_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    first_response_time_minutes = Column(Float, nullable=True)
    resolution_time_minutes = Column(Float, nullable=True)

    assigned_agent = relationship("User", back_populates="tickets")
    analysis = relationship("TicketAnalysis", back_populates="ticket", uselist=False, cascade="all, delete-orphan")
    reply_drafts = relationship("ReplyDraft", back_populates="ticket", cascade="all, delete-orphan")
    escalations = relationship("Escalation", back_populates="ticket", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="ticket", cascade="all, delete-orphan")


class TicketAnalysis(Base):
    __tablename__ = "ticket_analyses"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), unique=True, nullable=False)
    summary = Column(Text, nullable=False)
    customer_intent = Column(String(255), nullable=True)
    sentiment = Column(String(50), nullable=False)
    priority = Column(String(50), nullable=False)
    category = Column(String(100), nullable=False)
    escalate = Column(Boolean, default=False)
    escalation_reason = Column(Text, nullable=True)
    suggested_reply_tone = Column(String(50), default="Professional")
    key_issue = Column(Text, nullable=True)
    risk_level = Column(String(50), default="Low")
    suggested_next_action = Column(Text, nullable=True)
    confidence = Column(Float, default=0.75)
    raw_response = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="analysis")


class ReplyDraft(Base):
    __tablename__ = "reply_drafts"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    agent_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    content = Column(Text, nullable=False)
    tone = Column(String(50), default="Professional")
    status = Column(String(50), default="drafted")  # drafted, edited, approved, sent
    ai_generated = Column(Boolean, default=True)
    citations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)
    sent_at = Column(DateTime, nullable=True)

    ticket = relationship("Ticket", back_populates="reply_drafts")
    agent = relationship("User", back_populates="reply_drafts")


class Escalation(Base):
    __tablename__ = "escalations"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    escalate = Column(Boolean, default=True)
    reason = Column(Text, nullable=False)
    recommended_team = Column(String(100), default="Manager")
    internal_note = Column(Text, nullable=True)
    status = Column(String(50), default="open")  # open, in_progress, resolved
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)

    ticket = relationship("Ticket", back_populates="escalations")


class KnowledgeBaseDocument(Base):
    __tablename__ = "kb_documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    filename = Column(String(500), nullable=False)
    file_type = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    chunk_count = Column(Integer, default=0)
    status = Column(String(50), default="indexed")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    chunks = relationship("KnowledgeBaseChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeBaseChunk(Base):
    __tablename__ = "kb_chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("kb_documents.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding_id = Column(String(255), nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("KnowledgeBaseDocument", back_populates="chunks")


class CopilotChatSession(Base):
    __tablename__ = "copilot_sessions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), default="Support Copilot Session")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    messages = relationship("CopilotChatMessage", back_populates="session", cascade="all, delete-orphan")


class CopilotChatMessage(Base):
    __tablename__ = "copilot_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("copilot_sessions.id"), nullable=False)
    role = Column(String(50), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    citations = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("CopilotChatSession", back_populates="messages")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    reply_draft_id = Column(Integer, ForeignKey("reply_drafts.id"), nullable=True)
    document_id = Column(Integer, ForeignKey("kb_documents.id"), nullable=True)
    chunk_id = Column(Integer, ForeignKey("kb_chunks.id"), nullable=True)
    snippet = Column(Text, nullable=False)
    score = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    ticket = relationship("Ticket", back_populates="citations")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False)
    priority = Column(String(50), default="Medium")
    action_items = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AppSettings(Base):
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, index=True)
    business_name = Column(String(255), default="Acme Support")
    support_email = Column(String(255), default="support@acme.com")
    default_reply_tone = Column(String(50), default="Professional")
    sla_urgent_hours = Column(Float, default=1.0)
    sla_high_hours = Column(Float, default=4.0)
    sla_medium_hours = Column(Float, default=12.0)
    sla_low_hours = Column(Float, default=24.0)
    ai_provider = Column(String(100), default="openai-compatible")
    api_key_placeholder = Column(String(255), default="")
    chat_model = Column(String(100), default="gpt-4o-mini")
    embedding_model = Column(String(100), default="text-embedding-3-small")
    default_escalation_team = Column(String(100), default="Manager")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
