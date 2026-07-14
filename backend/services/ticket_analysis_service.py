from __future__ import annotations

from sqlalchemy.orm import Session

from models import Ticket, TicketAnalysis, AppSettings
from services.ai_service import analyze_ticket


def get_business_settings(db: Session) -> dict:
    settings = db.query(AppSettings).first()
    if not settings:
        return {"business_name": "Acme Support"}
    return {
        "business_name": settings.business_name,
        "support_email": settings.support_email,
        "default_reply_tone": settings.default_reply_tone,
        "default_escalation_team": settings.default_escalation_team,
    }


def analyze_and_persist(db: Session, ticket: Ticket) -> TicketAnalysis:
    ticket_data = {
        "customer_name": ticket.customer_name,
        "customer_email": ticket.customer_email,
        "company": ticket.company,
        "subject": ticket.subject,
        "message": ticket.message,
        "category": ticket.category,
        "status": ticket.status,
        "priority": ticket.priority,
        "sentiment": ticket.sentiment,
    }
    result = analyze_ticket(ticket_data, get_business_settings(db))

    analysis = db.query(TicketAnalysis).filter(TicketAnalysis.ticket_id == ticket.id).first()
    if not analysis:
        analysis = TicketAnalysis(ticket_id=ticket.id)
        db.add(analysis)

    analysis.summary = result.get("summary", "")
    analysis.customer_intent = result.get("customer_intent")
    analysis.sentiment = result.get("sentiment", ticket.sentiment)
    analysis.priority = result.get("priority", ticket.priority)
    analysis.category = result.get("category", ticket.category)
    analysis.escalate = bool(result.get("escalate"))
    analysis.escalation_reason = result.get("escalation_reason")
    analysis.suggested_reply_tone = result.get("suggested_reply_tone", "Professional")
    analysis.key_issue = result.get("key_issue")
    analysis.risk_level = result.get("risk_level", "Low")
    analysis.suggested_next_action = result.get("suggested_next_action")
    analysis.confidence = float(result.get("confidence", 0.75))
    analysis.raw_response = result

    ticket.ai_summary = analysis.summary
    ticket.sentiment = analysis.sentiment
    ticket.priority = analysis.priority
    ticket.category = analysis.category
    ticket.escalation_recommendation = analysis.escalate

    db.commit()
    db.refresh(analysis)
    db.refresh(ticket)
    return analysis
