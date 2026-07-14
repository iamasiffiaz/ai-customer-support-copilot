from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from models import Ticket, TicketAnalysis, Escalation, AppSettings
from services.ai_service import generate_escalation_recommendation
from utils.date_utils import is_overdue, is_sla_risk


def _sla_hours(db: Session, priority: str) -> float:
    s = db.query(AppSettings).first()
    defaults = {"Urgent": 1.0, "High": 4.0, "Medium": 12.0, "Low": 24.0}
    if not s:
        return defaults.get(priority, 12.0)
    mapping = {
        "Urgent": s.sla_urgent_hours,
        "High": s.sla_high_hours,
        "Medium": s.sla_medium_hours,
        "Low": s.sla_low_hours,
    }
    return mapping.get(priority, 12.0)


def check_and_persist_escalation(db: Session, ticket: Ticket) -> Escalation:
    analysis = db.query(TicketAnalysis).filter(TicketAnalysis.ticket_id == ticket.id).first()
    analysis_data = None
    if analysis:
        analysis_data = {
            "summary": analysis.summary,
            "sentiment": analysis.sentiment,
            "priority": analysis.priority,
            "category": analysis.category,
            "escalate": analysis.escalate,
            "escalation_reason": analysis.escalation_reason,
            "recommended_team": (analysis.raw_response or {}).get("recommended_team", "Manager"),
            "key_issue": analysis.key_issue,
            "confidence": analysis.confidence,
            "suggested_next_action": analysis.suggested_next_action,
            "risk_level": analysis.risk_level,
        }

    settings = db.query(AppSettings).first()
    default_team = settings.default_escalation_team if settings else "Manager"
    hours = _sla_hours(db, ticket.priority)
    overdue = is_overdue(ticket.created_at, hours, ticket.first_response_at) if ticket.status != "Resolved" else False
    risk = is_sla_risk(ticket.created_at, hours, ticket.first_response_at) if ticket.status != "Resolved" else False

    ticket_data = {
        "customer_name": ticket.customer_name,
        "subject": ticket.subject,
        "message": ticket.message,
        "status": ticket.status,
        "priority": ticket.priority,
        "sentiment": ticket.sentiment,
    }
    result = generate_escalation_recommendation(ticket_data, analysis_data, sla_risk=risk, overdue=overdue)
    team = result.get("recommended_team") or default_team

    existing = (
        db.query(Escalation)
        .filter(Escalation.ticket_id == ticket.id, Escalation.status == "open")
        .order_by(Escalation.created_at.desc())
        .first()
    )

    if not result.get("escalate"):
        if existing:
            existing.escalate = False
            existing.reason = result.get("escalation_reason") or existing.reason
            existing.internal_note = result.get("suggested_internal_note")
            existing.status = "resolved"
            existing.resolved_at = datetime.utcnow()
            db.commit()
            db.refresh(existing)
            return existing
        escalation = Escalation(
            ticket_id=ticket.id,
            escalate=False,
            reason=result.get("escalation_reason") or "No escalation required",
            recommended_team=team,
            internal_note=result.get("suggested_internal_note"),
            status="resolved",
            resolved_at=datetime.utcnow(),
        )
        db.add(escalation)
        ticket.escalation_recommendation = False
        db.commit()
        db.refresh(escalation)
        return escalation

    if existing:
        existing.escalate = True
        existing.reason = result.get("escalation_reason") or existing.reason
        existing.recommended_team = team
        existing.internal_note = result.get("suggested_internal_note")
        existing.status = "open"
        existing.resolved_at = None
        escalation = existing
    else:
        escalation = Escalation(
            ticket_id=ticket.id,
            escalate=True,
            reason=result.get("escalation_reason") or "Review recommended",
            recommended_team=team,
            internal_note=result.get("suggested_internal_note"),
            status="open",
        )
        db.add(escalation)

    ticket.escalation_recommendation = True
    if ticket.status not in ("Resolved", "Escalated"):
        ticket.status = "Escalated"
    db.commit()
    db.refresh(escalation)
    return escalation
