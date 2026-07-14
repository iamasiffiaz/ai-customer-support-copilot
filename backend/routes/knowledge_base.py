import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from config import get_settings
from database import get_db
from models import KnowledgeBaseDocument, KnowledgeBaseChunk
from schemas import KBDocumentOut, KBDocumentDetail, KBSearchRequest, KBSearchResult
from services.chunking_service import chunk_text
from services.document_processor import extract_text_from_file
from services.embedding_service import embed_texts
from services.rag_service import search_knowledge_base
from services.vector_service import upsert_embeddings, delete_by_document
from utils.file_utils import ensure_upload_dir, safe_filename, is_allowed_file, get_file_type

router = APIRouter(prefix="/api/knowledge-base", tags=["knowledge-base"])
settings = get_settings()


def _index_document(db: Session, doc: KnowledgeBaseDocument, content: str) -> KnowledgeBaseDocument:
    chunks = chunk_text(content)
    # clear old
    db.query(KnowledgeBaseChunk).filter(KnowledgeBaseChunk.document_id == doc.id).delete()
    delete_by_document(doc.id)

    vectors = embed_texts(chunks) if chunks else []
    points = []
    for idx, chunk_content in enumerate(chunks):
        chunk = KnowledgeBaseChunk(
            document_id=doc.id,
            chunk_index=idx,
            content=chunk_content,
            metadata_json={"title": doc.title},
        )
        db.add(chunk)
        db.flush()
        chunk.embedding_id = str(chunk.id)
        points.append(
            {
                "id": chunk.id,
                "vector": vectors[idx] if idx < len(vectors) else vectors[0] if vectors else [],
                "payload": {
                    "chunk_id": chunk.id,
                    "document_id": doc.id,
                    "document_title": doc.title,
                    "content": chunk_content,
                },
            }
        )
    if points and points[0]["vector"]:
        upsert_embeddings(points)
    doc.chunk_count = len(chunks)
    doc.status = "indexed"
    doc.content = content
    db.commit()
    db.refresh(doc)
    return doc


@router.post("/upload", response_model=KBDocumentOut)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(None),
    db: Session = Depends(get_db),
):
    if not file.filename or not is_allowed_file(file.filename):
        raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, TXT, DOCX, or MD.")
    upload_dir = ensure_upload_dir(settings.upload_dir)
    filename = safe_filename(file.filename)
    path = upload_dir / filename
    content_bytes = await file.read()
    path.write_bytes(content_bytes)

    file_type = get_file_type(file.filename)
    text = extract_text_from_file(str(path), file_type)
    if not text.strip():
        raise HTTPException(status_code=400, detail="Could not extract text from document")

    doc = KnowledgeBaseDocument(
        title=title or Path(file.filename).stem.replace("_", " ").title(),
        filename=filename,
        file_type=file_type,
        content=text,
        chunk_count=0,
        status="processing",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    return _index_document(db, doc, text)


@router.get("/documents", response_model=list[KBDocumentOut])
def list_documents(db: Session = Depends(get_db)):
    return db.query(KnowledgeBaseDocument).order_by(KnowledgeBaseDocument.created_at.desc()).all()


@router.get("/documents/{document_id}", response_model=KBDocumentDetail)
def get_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeBaseDocument).filter(KnowledgeBaseDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.delete("/documents/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(KnowledgeBaseDocument).filter(KnowledgeBaseDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    delete_by_document(document_id)
    path = Path(settings.upload_dir) / doc.filename
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted"}


@router.post("/search", response_model=list[KBSearchResult])
def search(payload: KBSearchRequest, db: Session = Depends(get_db)):
    return search_knowledge_base(db, payload.query, limit=payload.limit)
