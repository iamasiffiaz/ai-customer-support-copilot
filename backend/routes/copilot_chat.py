from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from database import get_db
from models import CopilotChatSession, CopilotChatMessage
from schemas import CopilotAskRequest, CopilotAskResponse, CopilotSessionOut
from services.ai_service import answer_support_question
from services.rag_service import search_knowledge_base
from utils.text_utils import truncate

router = APIRouter(prefix="/api/copilot-chat", tags=["copilot-chat"])


@router.post("/ask", response_model=CopilotAskResponse)
def ask(payload: CopilotAskRequest, db: Session = Depends(get_db)):
    session = None
    if payload.session_id:
        session = db.query(CopilotChatSession).filter(CopilotChatSession.id == payload.session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = CopilotChatSession(title=truncate(payload.question, 80))
        db.add(session)
        db.commit()
        db.refresh(session)

    user_msg = CopilotChatMessage(session_id=session.id, role="user", content=payload.question)
    db.add(user_msg)

    citations = search_knowledge_base(db, payload.question, limit=5)
    result = answer_support_question(payload.question, citations)
    assistant_msg = CopilotChatMessage(
        session_id=session.id,
        role="assistant",
        content=result["answer"],
        citations=citations,
    )
    db.add(assistant_msg)
    db.commit()
    db.refresh(assistant_msg)

    return {
        "session_id": session.id,
        "answer": result["answer"],
        "citations": citations,
        "message": assistant_msg,
    }


@router.get("/sessions", response_model=list[CopilotSessionOut])
def list_sessions(db: Session = Depends(get_db)):
    sessions = (
        db.query(CopilotChatSession)
        .options(joinedload(CopilotChatSession.messages))
        .order_by(CopilotChatSession.updated_at.desc())
        .all()
    )
    return sessions


@router.get("/sessions/{session_id}", response_model=CopilotSessionOut)
def get_session(session_id: int, db: Session = Depends(get_db)):
    session = (
        db.query(CopilotChatSession)
        .options(joinedload(CopilotChatSession.messages))
        .filter(CopilotChatSession.id == session_id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session
