from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Ticket, TicketAnalysis
from schemas import TicketAnalysisOut, BulkAnalyzeRequest, MessageResponse
from services.ticket_analysis_service import analyze_and_persist
from services.escalation_service import check_and_persist_escalation

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/analyze-ticket/{ticket_id}", response_model=TicketAnalysisOut)
def analyze_single(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    analysis = analyze_and_persist(db, ticket)
    if analysis.escalate:
        check_and_persist_escalation(db, ticket)
    return analysis


@router.post("/bulk-analyze", response_model=MessageResponse)
def bulk_analyze(payload: BulkAnalyzeRequest, db: Session = Depends(get_db)):
    query = db.query(Ticket)
    if payload.ticket_ids:
        query = query.filter(Ticket.id.in_(payload.ticket_ids))
    tickets = query.all()
    count = 0
    errors = []
    for ticket in tickets:
        try:
            analysis = analyze_and_persist(db, ticket)
            if analysis.escalate:
                check_and_persist_escalation(db, ticket)
            count += 1
        except Exception as exc:
            errors.append({"ticket_id": ticket.id, "error": str(exc)})
    return {
        "message": f"Analyzed {count}/{len(tickets)} tickets",
        "detail": {"count": count, "errors": errors},
    }


@router.get("/{ticket_id}", response_model=TicketAnalysisOut)
def get_analysis(ticket_id: int, db: Session = Depends(get_db)):
    analysis = db.query(TicketAnalysis).filter(TicketAnalysis.ticket_id == ticket_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis
