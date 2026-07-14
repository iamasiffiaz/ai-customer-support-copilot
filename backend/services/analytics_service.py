from __future__ import annotations

from collections import Counter
from typing import Optional

from sqlalchemy.orm import Session

from models import Ticket, ReplyDraft, Escalation, AppSettings
from utils.date_utils import SLA_HOURS, is_overdue, is_sla_risk, minutes_between


def _settings_sla(db: Session) -> dict[str, float]:
    s = db.query(AppSettings).first()
    if not s:
        return SLA_HOURS
    return {
        "Urgent": s.sla_urgent_hours,
        "High": s.sla_high_hours,
        "Medium": s.sla_medium_hours,
        "Low": s.sla_low_hours,
    }


def ticket_to_dict(t: Ticket) -> dict:
    return {
        "id": t.id,
        "customer_name": t.customer_name,
        "customer_email": t.customer_email,
        "company": t.company,
        "subject": t.subject,
        "message": t.message,
        "category": t.category,
        "status": t.status,
        "priority": t.priority,
        "sentiment": t.sentiment,
        "ai_summary": t.ai_summary,
        "ai_suggested_reply": t.ai_suggested_reply,
        "escalation_recommendation": t.escalation_recommendation,
        "assigned_agent_id": t.assigned_agent_id,
        "created_at": t.created_at,
        "updated_at": t.updated_at,
        "first_response_at": t.first_response_at,
        "resolved_at": t.resolved_at,
        "first_response_time_minutes": t.first_response_time_minutes,
        "resolution_time_minutes": t.resolution_time_minutes,
    }


def get_dashboard_analytics(db: Session) -> dict:
    tickets = db.query(Ticket).all()
    replies = db.query(ReplyDraft).order_by(ReplyDraft.created_at.desc()).limit(8).all()
    sla = _settings_sla(db)

    status_counts = Counter(t.status for t in tickets)
    priority_counts = Counter(t.priority for t in tickets)
    sentiment_counts = Counter(t.sentiment for t in tickets)
    category_counts = Counter(t.category for t in tickets)

    response_times = [t.first_response_time_minutes for t in tickets if t.first_response_time_minutes is not None]
    avg_response = sum(response_times) / len(response_times) if response_times else None

    escalated = status_counts.get("Escalated", 0) + sum(1 for t in tickets if t.escalation_recommendation)
    resolved = status_counts.get("Resolved", 0)
    total = len(tickets) or 1

    approved = db.query(ReplyDraft).filter(ReplyDraft.status.in_(["approved", "sent"])).count()
    all_replies = db.query(ReplyDraft).count() or 1

    overdue = []
    sla_risk = []
    for t in tickets:
        if t.status == "Resolved":
            continue
        hours = sla.get(t.priority, 12.0)
        if is_overdue(t.created_at, hours, t.first_response_at):
            overdue.append(t)
        elif is_sla_risk(t.created_at, hours, t.first_response_at):
            sla_risk.append(t)

    urgent = (
        db.query(Ticket)
        .filter(Ticket.priority == "Urgent")
        .order_by(Ticket.created_at.desc())
        .limit(6)
        .all()
    )

    return {
        "total_tickets": len(tickets),
        "open_tickets": status_counts.get("Open", 0),
        "pending_tickets": status_counts.get("Pending", 0),
        "resolved_tickets": resolved,
        "escalated_tickets": status_counts.get("Escalated", 0),
        "new_tickets": status_counts.get("New", 0),
        "average_response_time_minutes": avg_response,
        "customer_satisfaction": 4.2,
        "sentiment_breakdown": dict(sentiment_counts),
        "priority_breakdown": dict(priority_counts),
        "category_breakdown": dict(category_counts),
        "status_breakdown": dict(status_counts),
        "recent_urgent": urgent,
        "recent_replies": replies,
        "escalation_rate": round(escalated / total, 3),
        "resolution_rate": round(resolved / total, 3),
        "ai_approval_rate": round(approved / all_replies, 3),
        "overdue_tickets": len(overdue),
        "sla_risk_tickets": len(sla_risk),
    }


def get_ticket_analytics(db: Session) -> dict:
    data = get_dashboard_analytics(db)
    tickets = db.query(Ticket).all()
    subjects = [t.subject for t in tickets]
    # crude recurring issue extraction by keyword
    keywords = ["refund", "login", "payment", "cancel", "bug", "invoice", "password", "api"]
    recurring = []
    for kw in keywords:
        count = sum(1 for s in subjects if kw in (s or "").lower()) + sum(
            1 for t in tickets if kw in (t.message or "").lower()
        )
        if count:
            recurring.append({"issue": kw, "count": count})
    recurring.sort(key=lambda x: x["count"], reverse=True)
    data["top_recurring_issues"] = recurring[:8]
    data["recent_urgent_table"] = (
        db.query(Ticket).filter(Ticket.priority.in_(["Urgent", "High"])).order_by(Ticket.created_at.desc()).limit(10).all()
    )
    return data


def get_response_time_analytics(db: Session) -> dict:
    tickets = db.query(Ticket).all()
    sla = _settings_sla(db)
    frt = [t.first_response_time_minutes for t in tickets if t.first_response_time_minutes is not None]
    res = [t.resolution_time_minutes for t in tickets if t.resolution_time_minutes is not None]

    by_priority: dict = {}
    for priority, hours in sla.items():
        subset = [t for t in tickets if t.priority == priority]
        frts = [t.first_response_time_minutes for t in subset if t.first_response_time_minutes is not None]
        by_priority[priority] = {
            "sla_hours": hours,
            "avg_first_response_minutes": (sum(frts) / len(frts)) if frts else None,
            "ticket_count": len(subset),
        }

    overdue = []
    risk = []
    for t in tickets:
        if t.status == "Resolved":
            continue
        hours = sla.get(t.priority, 12.0)
        if is_overdue(t.created_at, hours, t.first_response_at):
            overdue.append(t)
        elif is_sla_risk(t.created_at, hours, t.first_response_at):
            risk.append(t)

    return {
        "average_first_response_minutes": (sum(frt) / len(frt)) if frt else None,
        "average_resolution_minutes": (sum(res) / len(res)) if res else None,
        "overdue_tickets": overdue,
        "sla_risk_tickets": risk,
        "by_priority": by_priority,
    }
