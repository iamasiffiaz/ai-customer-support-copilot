from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models import Recommendation, Ticket
from schemas import RecommendationOut
from services.ai_service import generate_support_recommendations
from services.analytics_service import get_dashboard_analytics, ticket_to_dict
from services.ticket_analysis_service import get_business_settings

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("", response_model=list[RecommendationOut])
def list_recommendations(db: Session = Depends(get_db)):
    return db.query(Recommendation).order_by(Recommendation.created_at.desc()).all()


@router.post("/generate", response_model=list[RecommendationOut])
def generate(db: Session = Depends(get_db)):
    tickets = db.query(Ticket).all()
    ticket_payloads = [ticket_to_dict(t) for t in tickets]
    # serialize datetimes
    for t in ticket_payloads:
        for k, v in list(t.items()):
            if hasattr(v, "isoformat"):
                t[k] = v.isoformat()
    analytics = get_dashboard_analytics(db)
    # strip ORM objects from analytics for AI prompt
    clean_analytics = {
        k: v
        for k, v in analytics.items()
        if k not in ("recent_urgent", "recent_replies")
    }
    recs = generate_support_recommendations(ticket_payloads, clean_analytics, get_business_settings(db))
    db.query(Recommendation).delete()
    saved = []
    for rec in recs:
        row = Recommendation(
            title=rec.get("title", "Recommendation"),
            description=rec.get("description", ""),
            category=rec.get("category", "General"),
            priority=rec.get("priority", "Medium"),
            action_items=rec.get("action_items") or [],
        )
        db.add(row)
        saved.append(row)
    db.commit()
    for row in saved:
        db.refresh(row)
    return saved
