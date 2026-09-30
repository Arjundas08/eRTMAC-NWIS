from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    doc_id: str
    original_filename: str
    sha256_hash: str
    file_size_bytes: int
    mime_type: str
    well_id: Optional[str] = None
    document_type: str
    source_date: Optional[str] = None
    total_pages: int
    is_scanned: bool
    status: str
    is_duplicate: bool = False
    message: str

class ExtractedEntityItem(BaseModel):
    entity_type: str
    entity_key: str
    extracted_value: str
    normalized_value: Optional[float] = None
    unit: Optional[str] = None
    confidence: float
    bbox: Optional[List[float]] = None
    text_passage: Optional[str] = None

class DocumentPageItem(BaseModel):
    page_number: int
    is_scanned: bool
    ocr_applied: bool
    ocr_confidence: float
    text_preview: str
    entity_count: int

class DocumentDetailResponse(BaseModel):
    doc_id: str
    original_filename: str
    sha256_hash: str
    file_size_bytes: int
    document_type: str
    well_id: Optional[str] = None
    source_id: Optional[str] = None
    source_date: Optional[str] = None
    source_url: Optional[str] = None
    total_pages: int
    is_scanned: bool
    status: str
    created_at: datetime
    pages: List[DocumentPageItem] = []
    entities: List[ExtractedEntityItem] = []

class DocumentListItem(BaseModel):
    doc_id: str
    original_filename: str
    document_type: str
    well_id: Optional[str] = None
    source_date: Optional[str] = None
    total_pages: int
    is_scanned: bool
    status: str
    created_at: datetime

class ExtractionJobStatus(BaseModel):
    job_id: str
    doc_id: str
    status: str
    retry_count: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
