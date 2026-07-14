from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from database import init_db
from routes import (
    auth,
    tickets,
    analysis,
    replies,
    escalations,
    knowledge_base,
    copilot_chat,
    analytics,
    recommendations,
    settings as settings_routes,
)

app_settings = get_settings()

app = FastAPI(
    title=app_settings.app_name,
    description="AI-powered customer support copilot with ticket analysis, RAG, and human approval workflows.",
    version="1.0.0",
)

origins = [o.strip() for o in app_settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or [
        "http://127.0.0.1:5180",
        "http://localhost:5180",
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(tickets.router)
app.include_router(analysis.router)
app.include_router(replies.router)
app.include_router(escalations.router)
app.include_router(knowledge_base.router)
app.include_router(copilot_chat.router)
app.include_router(analytics.router)
app.include_router(recommendations.router)
app.include_router(settings_routes.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root():
    return {
        "name": app_settings.app_name,
        "status": "ok",
        "docs": "/docs",
    }


@app.get("/api/health")
def health():
    from sqlalchemy import text
    from database import engine

    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        db_ok = False
    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "unavailable",
        "ai_configured": bool(app_settings.openai_api_key),
        "rag_top_k": app_settings.rag_top_k,
    }