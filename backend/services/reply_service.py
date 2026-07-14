from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from models import Ticket, TicketAnalysis, ReplyDraft, Citation, AppSettings
from services.ai_service import generate_reply
from services.rag_service import search_knowledge_base
from config import get_settings


def generate_and_persist_reply(db: Session, ticket: Ticket, tone: str | None = None) -> ReplyDraft:
    settings = get_settings()
    app_settings = db.query(AppSettings).first()
    analysis = db.query(TicketAnalysis).filter(TicketAnalysis.ticket_id == ticket.id).first()
    analysis_data = None
    if analysis:
        analysis_data = {
            "summary": analysis.summary,
            "customer_intent": analysis.customer_intent,
            "sentiment": analysis.sentiment,
            "priority": analysis.priority,
            "category": analysis.category,
            "escalate": analysis.escalate,
            "escalation_reason": analysis.escalation_reason,
            "recommended_team": (analysis.raw_response or {}).get("recommended_team", "Manager"),
            "suggested_reply_tone": analysis.suggested_reply_tone,
            "key_issue": analysis.key_issue,
            "risk_level": analysis.risk_level,
            "suggested_next_action": analysis.suggested_next_action,
            "confidence": analysis.confidence,
            "priority_reason": (analysis.raw_response or {}).get("priority_reason"),
        }
        tone = tone or analysis.suggested_reply_tone
    if not tone:
        tone = (app_settings.default_reply_tone if app_settings else None) or "Professional"

    query = f"{ticket.subject} {ticket.message}"
    context = search_knowledge_base(db, query, limit=settings.rag_top_k)
    ticket_data = {
        "customer_name": ticket.customer_name,
        "customer_email": ticket.customer_email,
        "company": ticket.company,
        "subject": ticket.subject,
        "message": ticket.message,
        "status": ticket.status,
    }
    result = generate_reply(ticket_data, analysis_data, tone=tone, retrieved_context=context)

    draft = ReplyDraft(
        ticket_id=ticket.id,
        content=result["reply"],
        tone=tone,
        status="drafted",
        ai_generated=True,
        citations=context,
    )
    db.add(draft)
    ticket.ai_suggested_reply = result["reply"]

    # Replace prior citation rows for this ticket on regenerate
    db.query(Citation).filter(Citation.ticket_id == ticket.id).delete()
    for c in context:
        db.add(
            Citation(
                ticket_id=ticket.id,
                document_id=c.get("document_id"),
                chunk_id=c.get("chunk_id"),
                snippet=c.get("content", "")[:500],
                score=c.get("score", 0),
            )
        )
    db.commit()
    db.refresh(draft)
    return draft


def update_reply_status(db: Session, draft: ReplyDraft, status: str) -> ReplyDraft:
    draft.status = status
    if status == "approved":
        draft.approved_at = datetime.utcnow()
    if status == "sent":
        draft.sent_at = datetime.utcnow()
        ticket = db.query(Ticket).filter(Ticket.id == draft.ticket_id).first()
        if ticket and not ticket.first_response_at:
            ticket.first_response_at = datetime.utcnow()
            from utils.date_utils import minutes_between

            ticket.first_response_time_minutes = minutes_between(ticket.created_at, ticket.first_response_at)
            if ticket.status in ("New", "Open"):
                ticket.status = "Pending"
    db.commit()
    db.refresh(draft)
    return draft
