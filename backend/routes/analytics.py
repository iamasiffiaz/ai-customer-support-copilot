from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from schemas import DashboardAnalytics, ResponseTimeAnalytics
from services.analytics_service import get_dashboard_analytics, get_ticket_analytics, get_response_time_analytics

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/dashboard", response_model=DashboardAnalytics)
def dashboard(db: Session = Depends(get_db)):
    return get_dashboard_analytics(db)


@router.get("/tickets")
def tickets_analytics(db: Session = Depends(get_db)):
    return get_ticket_analytics(db)


@router.get("/response-times", response_model=ResponseTimeAnalytics)
def response_times(db: Session = Depends(get_db)):
    return get_response_time_analytics(db)
