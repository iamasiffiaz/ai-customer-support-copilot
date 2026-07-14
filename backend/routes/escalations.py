from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Ticket, Escalation
from schemas import EscalationOut, EscalationUpdate
from services.escalation_service import check_and_persist_escalation

router = APIRouter(prefix="/api/escalations", tags=["escalations"])


@router.get("", response_model=list[EscalationOut])
def list_escalations(db: Session = Depends(get_db)):
    return db.query(Escalation).order_by(Escalation.created_at.desc()).all()


@router.post("/check/{ticket_id}", response_model=EscalationOut)
def check_escalation(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return check_and_persist_escalation(db, ticket)


@router.put("/{escalation_id}", response_model=EscalationOut)
def update_escalation(escalation_id: int, payload: EscalationUpdate, db: Session = Depends(get_db)):
    esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(esc, key, value)
    db.commit()
    db.refresh(esc)
    return esc


@router.post("/{escalation_id}/resolve", response_model=EscalationOut)
def resolve_escalation(escalation_id: int, db: Session = Depends(get_db)):
    esc = db.query(Escalation).filter(Escalation.id == escalation_id).first()
    if not esc:
        raise HTTPException(status_code=404, detail="Escalation not found")
    esc.status = "resolved"
    esc.resolved_at = datetime.utcnow()
    db.commit()
    db.refresh(esc)
    return esc
