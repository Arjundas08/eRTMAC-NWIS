from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from pathlib import Path

from backend.app.db.database import get_db
from backend.app.db.models import Document
from backend.app.services.document_service import document_service, DocumentSecurityError
from backend.app.services.evidence_service import evidence_service
from backend.app.schemas.document_schemas import (
    DocumentUploadResponse, DocumentListItem, DocumentDetailResponse
)

router = APIRouter(prefix="/documents", tags=["Document Intelligence & Ingestion"])

@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    well_id: Optional[str] = Form(None),
    source_id: Optional[str] = Form("SRC-VOLVE-001"),
    db: Session = Depends(get_db)
):
    """
    Ingests an authentic petroleum PDF report.
    Validates file signature, detects malicious exploits, computes SHA-256 hash,
    runs OCR and layout extraction, links evidence, and routes low-confidence items to review.
    """
    contents = await file.read()
    try:
        res = document_service.ingest_document_file(
            file_bytes=contents,
            original_filename=file.filename or "uploaded_document.pdf",
            db=db,
            well_id=well_id,
            source_id=source_id
        )
        return res
    except DocumentSecurityError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {str(e)}")

@router.get("", response_model=List[DocumentListItem])
@router.get("/", response_model=List[DocumentListItem], include_in_schema=False)
def list_documents(db: Session = Depends(get_db)):
    """Lists all ingested documents in the trusted repository."""
    docs = db.query(Document).order_by(Document.created_at.desc()).all()
    return [
        DocumentListItem(
            doc_id=d.doc_id,
            original_filename=d.original_filename,
            document_type=d.document_type,
            well_id=d.well_id,
            source_date=d.source_date,
            total_pages=d.total_pages,
            is_scanned=d.is_scanned,
            status=d.status,
            created_at=d.created_at
        )
        for d in docs
    ]

@router.get("/{doc_id}", response_model=DocumentDetailResponse)
def get_document(doc_id: str, db: Session = Depends(get_db)):
    """Retrieves document metadata, page layouts, and extracted engineering entities."""
    details = document_service.get_document_details(doc_id, db)
    if not details:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found.")
    return details

@router.get("/{doc_id}/pages/{page_number}/preview")
def preview_document_page(
    doc_id: str,
    page_number: int,
    highlight: bool = True,
    db: Session = Depends(get_db)
):
    """
    Renders and serves the document page image, highlighting the supporting
    evidence bounding box if available.
    """
    if highlight:
        img_path = evidence_service.render_highlighted_passage_image(doc_id, page_number, db)
    else:
        img_path = None

    if not img_path or not Path(img_path).exists():
        # Fallback to direct page render
        doc = db.query(Document).filter(Document.doc_id == doc_id).first()
        if not doc or not Path(doc.file_path).exists():
            raise HTTPException(status_code=404, detail="Document or page not found.")
        from backend.app.services.ocr_service import ocr_service
        img_path = ocr_service.render_page_with_highlight(doc.file_path, page_number, None, f"temp_{doc_id}_p{page_number}.png")

    if Path(img_path).exists():
        return FileResponse(img_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Page render unavailable.")
