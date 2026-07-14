from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from database import get_db
from models import Ticket
from schemas import TicketCreate, TicketUpdate, TicketOut
from utils.date_utils import minutes_between

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


@router.get("", response_model=list[TicketOut])
def list_tickets(
    q: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    sentiment: Optional[str] = None,
    category: Optional[str] = None,
    escalated: Optional[bool] = None,
    sort_by: str = Query(default="created_at"),
    sort_dir: str = Query(default="desc"),
    db: Session = Depends(get_db),
):
    query = db.query(Ticket)
    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Ticket.subject.ilike(like),
                Ticket.message.ilike(like),
                Ticket.customer_name.ilike(like),
                Ticket.customer_email.ilike(like),
                Ticket.company.ilike(like),
            )
        )
    if status:
        query = query.filter(Ticket.status == status)
    if priority:
        query = query.filter(Ticket.priority == priority)
    if sentiment:
        query = query.filter(Ticket.sentiment == sentiment)
    if category:
        query = query.filter(Ticket.category == category)
    if escalated is not None:
        query = query.filter(Ticket.escalation_recommendation == escalated)

    sort_map = {
        "created_at": Ticket.created_at,
        "priority": Ticket.priority,
        "sentiment": Ticket.sentiment,
        "updated_at": Ticket.updated_at,
        "status": Ticket.status,
    }
    col = sort_map.get(sort_by, Ticket.created_at)
    query = query.order_by(col.desc() if sort_dir == "desc" else col.asc())
    return query.all()


@router.post("", response_model=TicketOut)
def create_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    ticket = Ticket(**payload.model_dump())
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}", response_model=TicketOut)
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.put("/{ticket_id}", response_model=TicketOut)
def update_ticket(ticket_id: int, payload: TicketUpdate, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    data = payload.model_dump(exclude_unset=True)

    if "status" in data and data["status"] == "Resolved" and not ticket.resolved_at:
        ticket.resolved_at = datetime.utcnow()
        ticket.resolution_time_minutes = minutes_between(ticket.created_at, ticket.resolved_at)
    if "status" in data and data["status"] != "Resolved":
        pass

    for key, value in data.items():
        setattr(ticket, key, value)
    ticket.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(ticket)
    return ticket


@router.delete("/{ticket_id}")
def delete_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    db.delete(ticket)
    db.commit()
    return {"message": "Ticket deleted"}
