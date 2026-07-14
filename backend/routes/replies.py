from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from models import Ticket, ReplyDraft
from schemas import ReplyDraftOut, ReplyGenerateRequest, ReplyUpdate
from services.reply_service import generate_and_persist_reply, update_reply_status

router = APIRouter(prefix="/api/replies", tags=["replies"])


@router.post("/generate/{ticket_id}", response_model=ReplyDraftOut)
def generate_reply(ticket_id: int, payload: ReplyGenerateRequest, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return generate_and_persist_reply(db, ticket, tone=payload.tone)


@router.get("", response_model=list[ReplyDraftOut])
def list_replies(
    ticket_id: Optional[int] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ReplyDraft).order_by(ReplyDraft.created_at.desc())
    if ticket_id:
        query = query.filter(ReplyDraft.ticket_id == ticket_id)
    if status:
        query = query.filter(ReplyDraft.status == status)
    return query.all()


@router.get("/{reply_id}", response_model=ReplyDraftOut)
def get_reply(reply_id: int, db: Session = Depends(get_db)):
    draft = db.query(ReplyDraft).filter(ReplyDraft.id == reply_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Reply not found")
    return draft


@router.put("/{reply_id}", response_model=ReplyDraftOut)
def update_reply(reply_id: int, payload: ReplyUpdate, db: Session = Depends(get_db)):
    draft = db.query(ReplyDraft).filter(ReplyDraft.id == reply_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Reply not found")
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(draft, key, value)
    if "content" in data and draft.status == "drafted":
        draft.status = "edited"
    db.commit()
    db.refresh(draft)
    return draft


@router.delete("/{reply_id}")
def delete_reply(reply_id: int, db: Session = Depends(get_db)):
    draft = db.query(ReplyDraft).filter(ReplyDraft.id == reply_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Reply not found")
    db.delete(draft)
    db.commit()
    return {"message": "Reply deleted"}


@router.post("/{reply_id}/approve", response_model=ReplyDraftOut)
def approve_reply(reply_id: int, db: Session = Depends(get_db)):
    draft = db.query(ReplyDraft).filter(ReplyDraft.id == reply_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Reply not found")
    return update_reply_status(db, draft, "approved")


@router.post("/{reply_id}/mark-sent", response_model=ReplyDraftOut)
def mark_sent(reply_id: int, db: Session = Depends(get_db)):
    draft = db.query(ReplyDraft).filter(ReplyDraft.id == reply_id).first()
    if not draft:
        raise HTTPException(status_code=404, detail="Reply not found")
    if draft.status not in ("approved", "edited", "drafted", "sent"):
        raise HTTPException(status_code=400, detail="Reply cannot be marked sent")
    return update_reply_status(db, draft, "sent")
