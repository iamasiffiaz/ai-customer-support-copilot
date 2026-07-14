from datetime import datetime, timedelta
from typing import Optional


def utcnow() -> datetime:
    return datetime.utcnow()


def minutes_between(start: datetime, end: Optional[datetime] = None) -> float:
    end = end or datetime.utcnow()
    return max(0.0, (end - start).total_seconds() / 60.0)


def hours_to_minutes(hours: float) -> float:
    return hours * 60.0


def is_overdue(created_at: datetime, sla_hours: float, first_response_at: Optional[datetime] = None) -> bool:
    if first_response_at:
        return False
    deadline = created_at + timedelta(hours=sla_hours)
    return datetime.utcnow() > deadline


def is_sla_risk(created_at: datetime, sla_hours: float, first_response_at: Optional[datetime] = None) -> bool:
    if first_response_at:
        return False
    elapsed = minutes_between(created_at)
    threshold = hours_to_minutes(sla_hours) * 0.75
    return elapsed >= threshold and elapsed < hours_to_minutes(sla_hours)


SLA_HOURS = {
    "Urgent": 1.0,
    "High": 4.0,
    "Medium": 12.0,
    "Low": 24.0,
}
