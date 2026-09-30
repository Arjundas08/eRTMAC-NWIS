from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import uuid
from .database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class Well(Base):
    __tablename__ = "wells"

    well_id = Column(String(64), primary_key=True, index=True)
    uwi = Column(String(64), unique=True, nullable=False, index=True)
    well_name = Column(String(128), nullable=False)
    field_name = Column(String(64), nullable=False, index=True)
    operator = Column(String(64), default="Equinor")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    kb_elevation_m = Column(Float, nullable=False)
    total_depth_md_m = Column(Float, nullable=True)
    total_depth_tvd_m = Column(Float, nullable=True)
    spud_date = Column(String(32), nullable=True)
    completion_date = Column(String(32), nullable=True)
    well_type = Column(String(32), default="DEVELOPMENT")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    surveys = relationship("WellboreSurvey", back_populates="well", cascade="all, delete-orphan")
    formation_tops = relationship("FormationTop", back_populates="well", cascade="all, delete-orphan")
    drilling_events = relationship("DrillingEvent", back_populates="well", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="well")

class WellboreSurvey(Base):
    __tablename__ = "wellbore_surveys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    well_id = Column(String(64), ForeignKey("wells.well_id"), nullable=False, index=True)
    md_m = Column(Float, nullable=False)
    inclination_deg = Column(Float, nullable=False)
    azimuth_deg = Column(Float, nullable=False)
    tvd_m = Column(Float, nullable=False)
    tvdss_m = Column(Float, nullable=False, index=True)
    dogleg_severity_deg_30m = Column(Float, default=0.0)

    well = relationship("Well", back_populates="surveys")

class FormationTop(Base):
    __tablename__ = "formation_tops"

    id = Column(Integer, primary_key=True, autoincrement=True)
    well_id = Column(String(64), ForeignKey("wells.well_id"), nullable=False, index=True)
    formation_name = Column(String(64), nullable=False, index=True)
    top_md_m = Column(Float, nullable=False)
    top_tvdss_m = Column(Float, nullable=False, index=True)
    base_tvdss_m = Column(Float, nullable=True)
    lithology_primary = Column(String(64), default="Sandstone")
    confidence_level = Column(String(16), default="CONFIRMED")

    well = relationship("Well", back_populates="formation_tops")

# =============================================================================
# DATA SOURCE & LICENCE REGISTRY
# =============================================================================

class DataSource(Base):
    __tablename__ = "data_sources"

    source_id = Column(String(64), primary_key=True, index=True)
    name = Column(String(128), nullable=False)
    source_type = Column(String(64), default="PUBLIC_OPERATOR") # REGULATORY, PUBLIC_OPERATOR, INTERNAL_OPERATOR
    base_url = Column(String(255), nullable=True)
    country = Column(String(64), default="Norway")
    basin = Column(String(64), default="South Viking Graben")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    licences = relationship("SourceLicence", back_populates="source", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="data_source")

class SourceLicence(Base):
    __tablename__ = "source_licences"

    licence_id = Column(String(64), primary_key=True, index=True)
    source_id = Column(String(64), ForeignKey("data_sources.source_id"), nullable=False)
    licence_name = Column(String(128), nullable=False)
    licence_url = Column(String(255), nullable=True)
    commercial_allowed = Column(Boolean, default=False)
    attribution_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    source = relationship("DataSource", back_populates="licences")

# =============================================================================
# DOCUMENT MANAGEMENT & OCR STORE
# =============================================================================

class Document(Base):
    __tablename__ = "documents"

    doc_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=False)
    sha256_hash = Column(String(64), unique=True, nullable=False, index=True)
    file_size_bytes = Column(Integer, nullable=False)
    mime_type = Column(String(64), default="application/pdf")
    document_type = Column(String(64), default="DAILY_DRILLING_REPORT") # DAILY_DRILLING_REPORT, WELL_COMPLETION_REPORT, MUD_LOG
    well_id = Column(String(64), ForeignKey("wells.well_id"), nullable=True, index=True)
    source_id = Column(String(64), ForeignKey("data_sources.source_id"), nullable=True)
    source_date = Column(String(32), nullable=True, index=True)
    source_url = Column(String(512), nullable=True)
    total_pages = Column(Integer, default=1)
    is_scanned = Column(Boolean, default=False)
    status = Column(String(32), default="INGESTED", index=True) # INGESTED, PROCESSING, EXTRACTED, VERIFIED, FAILED
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    well = relationship("Well", back_populates="documents")
    data_source = relationship("DataSource", back_populates="documents")
    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    versions = relationship("DocumentVersion", back_populates="document", cascade="all, delete-orphan")
    extraction_jobs = relationship("ExtractionJob", back_populates="document", cascade="all, delete-orphan")
    entities = relationship("ExtractedEntity", back_populates="document", cascade="all, delete-orphan")
    evidence_records = relationship("EventEvidence", back_populates="document", cascade="all, delete-orphan")

class DocumentVersion(Base):
    __tablename__ = "document_versions"

    version_id = Column(String(64), primary_key=True, default=generate_uuid)
    doc_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=False, index=True)
    version_number = Column(Integer, default=1)
    sha256_hash = Column(String(64), nullable=False)
    change_summary = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="versions")

class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=False)
    is_scanned = Column(Boolean, default=False)
    ocr_applied = Column(Boolean, default=False)
    ocr_confidence = Column(Float, default=1.0)
    image_path = Column(String(512), nullable=True)
    layout_json = Column(Text, nullable=True) # Structured layout blocks, bboxes, tables
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="pages")

class ExtractionJob(Base):
    __tablename__ = "extraction_jobs"

    job_id = Column(String(64), primary_key=True, default=generate_uuid)
    doc_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=False, index=True)
    status = Column(String(32), default="PENDING", index=True) # PENDING, RUNNING, COMPLETED, FAILED, RETRYING
    retry_count = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    document = relationship("Document", back_populates="extraction_jobs")

class ExtractedEntity(Base):
    __tablename__ = "extracted_entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    entity_type = Column(String(64), nullable=False, index=True) # DEPTH_MD, DEPTH_TVD, MUD_WEIGHT, FORMATION_NAME, INCIDENT_KEYWORD, OPERATING_PARAM
    entity_key = Column(String(64), nullable=False)
    extracted_value = Column(String(255), nullable=False)
    normalized_value = Column(Float, nullable=True)
    unit = Column(String(32), nullable=True)
    confidence = Column(Float, default=1.0)
    bbox_json = Column(String(128), nullable=True) # [x0, y0, x1, y1]
    text_passage = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    document = relationship("Document", back_populates="entities")

# =============================================================================
# HISTORICAL DRILLING EVENTS & EVIDENCE PASSPORT
# =============================================================================

class DrillingEvent(Base):
    __tablename__ = "drilling_events"

    event_id = Column(String(64), primary_key=True, index=True)
    well_id = Column(String(64), ForeignKey("wells.well_id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True) # LOST_CIRCULATION, STUCK_PIPE, PACKOFF, TIGHT_HOLE, KICK, etc.
    severity = Column(String(16), nullable=False)               # MINOR, MODERATE, SEVERE, CRITICAL
    depth_md_m = Column(Float, nullable=False)
    depth_tvdss_m = Column(Float, nullable=False, index=True)
    formation_name = Column(String(64), nullable=False, index=True)
    relative_formation_depth_m = Column(Float, nullable=True)
    npt_hours = Column(Float, default=0.0)
    operational_narrative = Column(Text, nullable=False)
    mitigation_applied = Column(Text, nullable=True)
    source_citation = Column(String(255), nullable=False)
    event_timestamp = Column(String(32), nullable=True)
    
    # Phase 2 Provenance & Verification Extensions
    verification_status = Column(String(32), default="VERIFIED", index=True) # VERIFIED, PENDING_REVIEW, CONFLICTING_EVIDENCE, INSUFFICIENT_SOURCE, REJECTED
    doc_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=True)
    page_number = Column(Integer, nullable=True)
    source_availability_timestamp = Column(String(32), nullable=True)
    extraction_method = Column(String(32), default="STRUCTURED_INGESTION") # NATIVE_PDF, OCR_EXTRACT, TABLE_PARSER, MANUAL_VERIFIED
    confidence_score = Column(Float, default=1.0)
    reviewed_by = Column(String(64), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    well = relationship("Well", back_populates="drilling_events")
    evidence_records = relationship("EventEvidence", back_populates="event", cascade="all, delete-orphan")

class EventEvidence(Base):
    __tablename__ = "event_evidence"

    evidence_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    event_id = Column(String(64), ForeignKey("drilling_events.event_id"), nullable=False, index=True)
    doc_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    quoted_passage = Column(Text, nullable=False)
    bbox_json = Column(String(128), nullable=True) # [x0, y0, x1, y1] normalized coords
    extraction_method = Column(String(32), default="NATIVE_PDF")
    confidence_score = Column(Float, default=1.0)
    evidence_status = Column(String(32), default="VERIFIED", index=True) # VERIFIED, PENDING_REVIEW, CONFLICTING_EVIDENCE, INSUFFICIENT_SOURCE, REJECTED
    missing_fields_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    event = relationship("DrillingEvent", back_populates="evidence_records")
    document = relationship("Document", back_populates="evidence_records")

# =============================================================================
# HUMAN-IN-THE-LOOP REVIEW WORKFLOW
# =============================================================================

class ReviewTask(Base):
    __tablename__ = "review_tasks"

    task_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    doc_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=False, index=True)
    event_id = Column(String(64), ForeignKey("drilling_events.event_id"), nullable=True, index=True)
    evidence_id = Column(String(64), ForeignKey("event_evidence.evidence_id"), nullable=True)
    status = Column(String(32), default="PENDING", index=True) # PENDING, IN_REVIEW, RESOLVED, REJECTED
    flag_reason = Column(String(64), nullable=False) # LOW_CONFIDENCE, CONFLICTING_VALUES, AMBIGUOUS_DEPTH, UNPRECEDENTED_HAZARD
    original_payload_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    decisions = relationship("ReviewDecision", back_populates="task", cascade="all, delete-orphan")

class ReviewDecision(Base):
    __tablename__ = "review_decisions"

    decision_id = Column(String(64), primary_key=True, default=generate_uuid)
    task_id = Column(String(64), ForeignKey("review_tasks.task_id"), nullable=False, index=True)
    reviewer_id = Column(String(64), nullable=False)
    reviewer_role = Column(String(64), default="DRILLING_SUPERINTENDENT")
    decision = Column(String(32), nullable=False) # APPROVED, REJECTED, MODIFIED
    corrections_json = Column(Text, nullable=True)
    comments = Column(Text, nullable=True)
    decision_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    task = relationship("ReviewTask", back_populates="decisions")

# =============================================================================
# GEOLOGICAL INTERPRETATIONS & DATUMS
# =============================================================================

class GeologicalInterpretation(Base):
    __tablename__ = "geological_interpretations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    well_id = Column(String(64), ForeignKey("wells.well_id"), nullable=False, index=True)
    formation_name = Column(String(64), nullable=False)
    top_tvdss_m = Column(Float, nullable=False)
    base_tvdss_m = Column(Float, nullable=True)
    source_citation = Column(String(255), nullable=False)
    interpreter_name = Column(String(128), default="Regional Geological Study")
    interpretation_date = Column(String(32), nullable=True)
    confidence = Column(String(32), default="VERIFIED")

class DepthDatum(Base):
    __tablename__ = "depth_datums"

    id = Column(Integer, primary_key=True, autoincrement=True)
    well_id = Column(String(64), ForeignKey("wells.well_id"), nullable=False, unique=True)
    datum_type = Column(String(32), default="RKB") # RKB, MSL, GL
    kb_elevation_m = Column(Float, nullable=False)
    water_depth_m = Column(Float, default=0.0)
    ground_elevation_m = Column(Float, default=0.0)
    source_citation = Column(String(255), nullable=False)

# =============================================================================
# LEGACY & AUDIT STORES (Preserved for compatibility)
# =============================================================================

class DocumentExtraction(Base):
    __tablename__ = "document_extractions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    doc_name = Column(String(255), nullable=False)
    page_number = Column(Integer, nullable=False)
    section_type = Column(String(64), nullable=False)
    extracted_text = Column(Text, nullable=False)
    extracted_json = Column(Text, nullable=True)
    ocr_confidence_score = Column(Float, nullable=False)
    review_status = Column(String(20), default="APPROVED")
    reviewed_by = Column(String(64), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class LookaheadAlert(Base):
    __tablename__ = "lookahead_alerts"

    alert_id = Column(String(64), primary_key=True, default=generate_uuid)
    active_well_id = Column(String(64), nullable=False, index=True)
    current_bit_tvdss_m = Column(Float, nullable=False)
    target_formation = Column(String(64), nullable=False)
    horizon_window_m = Column(Float, nullable=False)
    hazard_predicted = Column(String(64), nullable=False)
    risk_score = Column(Float, nullable=False)
    matched_event_id = Column(String(64), nullable=True)
    recommended_mitigation = Column(Text, nullable=False)
    evidence_citation = Column(String(255), nullable=False)
    
    # Closed-loop driller feedback
    driller_response = Column(String(32), default="UNACKNOWLEDGED")
    driller_comments = Column(Text, nullable=True)
    response_timestamp = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    user_id = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False)
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=False)
    details_json = Column(Text, nullable=True)

class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    user_id = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False) # DOCUMENT_UPLOAD, EXTRACTION_TRIGGERED, REVIEW_DECISION, QUARANTINE
    resource_type = Column(String(64), nullable=False)
    resource_id = Column(String(64), nullable=False)
    details_json = Column(Text, nullable=True)
    integrity_hmac = Column(String(64), nullable=True)

# =============================================================================
# NWIS GEOCORE — CANONICAL SUBSURFACE DATA MODEL (PHASE 03)
# =============================================================================

class Field(Base):
    __tablename__ = "fields"

    field_id = Column(String(64), primary_key=True, index=True)
    field_name = Column(String(128), unique=True, nullable=False, index=True)
    country = Column(String(64), default="Norway")
    basin = Column(String(128), default="South Viking Graben")
    operator = Column(String(64), default="Equinor")
    discovery_year = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Reservoir(Base):
    __tablename__ = "reservoirs"

    reservoir_id = Column(String(64), primary_key=True, index=True)
    field_id = Column(String(64), ForeignKey("fields.field_id"), nullable=False, index=True)
    reservoir_name = Column(String(128), nullable=False)
    primary_formation = Column(String(64), nullable=False)
    lithology = Column(String(64), default="Sandstone")
    avg_porosity_pct = Column(Float, nullable=True)
    avg_permeability_md = Column(Float, nullable=True)
    drive_mechanism = Column(String(64), default="Water Drive / Gas Expansion")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class Wellbore(Base):
    __tablename__ = "wellbores"

    wellbore_id = Column(String(64), primary_key=True, index=True) # e.g. NO-15/9-F-12
    well_id = Column(String(64), ForeignKey("wells.well_id"), nullable=False, index=True)
    wellbore_name = Column(String(128), nullable=False)
    wellbore_type = Column(String(32), default="ORIGINAL") # ORIGINAL, SIDETRACK, BYPASS, RE-ENTRY
    parent_wellbore_id = Column(String(64), nullable=True)
    kickoff_depth_md_m = Column(Float, nullable=True)
    total_depth_md_m = Column(Float, nullable=False)
    total_depth_tvdss_m = Column(Float, nullable=False)
    status = Column(String(32), default="COMPLETED")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class WellboreRelationship(Base):
    __tablename__ = "wellbore_relationships"

    id = Column(Integer, primary_key=True, autoincrement=True)
    parent_wellbore_id = Column(String(64), ForeignKey("wellbores.wellbore_id"), nullable=False, index=True)
    child_wellbore_id = Column(String(64), ForeignKey("wellbores.wellbore_id"), nullable=False, index=True)
    relationship_type = Column(String(32), default="SIDETRACK") # SIDETRACK, MULTILATERAL, TWIN
    kickoff_depth_md_m = Column(Float, nullable=False)
    kickoff_formation = Column(String(64), nullable=True)
    notes = Column(Text, nullable=True)

class SurveyVersion(Base):
    __tablename__ = "survey_versions"

    version_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    wellbore_id = Column(String(64), ForeignKey("wellbores.wellbore_id"), nullable=False, index=True)
    version_number = Column(Integer, default=1)
    survey_tool = Column(String(64), default="MWD / Gyro")
    survey_company = Column(String(64), default="Schlumberger")
    calculation_method = Column(String(64), default="MINIMUM_CURVATURE")
    is_definitive = Column(Boolean, default=True)
    source_citation = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class SurveyStation(Base):
    __tablename__ = "survey_stations"

    id = Column(Integer, primary_key=True, autoincrement=True)
    survey_version_id = Column(String(64), ForeignKey("survey_versions.version_id"), nullable=False, index=True)
    station_index = Column(Integer, nullable=False)
    md_m = Column(Float, nullable=False)
    inclination_deg = Column(Float, nullable=False)
    azimuth_deg = Column(Float, nullable=False)
    tvd_m = Column(Float, nullable=False)
    tvdss_m = Column(Float, nullable=False, index=True)
    northing_m = Column(Float, default=0.0)
    easting_m = Column(Float, default=0.0)
    dogleg_severity_deg_30m = Column(Float, default=0.0)
    is_interpolated = Column(Boolean, default=False)

class Formation(Base):
    __tablename__ = "formations"

    formation_id = Column(String(64), primary_key=True, index=True)
    formation_name = Column(String(128), unique=True, nullable=False, index=True)
    stratigraphic_group = Column(String(128), nullable=False)
    geological_age = Column(String(64), default="Jurassic")
    primary_lithology = Column(String(64), default="Sandstone")
    typical_thickness_m = Column(Float, nullable=True)
    reservoir_potential = Column(String(32), default="MODERATE") # PRIMARY_TARGET, SECONDARY, CAP_ROCK, NON_RESERVOIR
    color_code = Column(String(16), default="#CD853F")
    description = Column(Text, nullable=True)

class FormationInterpretation(Base):
    __tablename__ = "formation_interpretations"

    interpretation_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    wellbore_id = Column(String(64), ForeignKey("wellbores.wellbore_id"), nullable=False, index=True)
    formation_id = Column(String(64), ForeignKey("formations.formation_id"), nullable=False, index=True)
    version_number = Column(Integer, default=1)
    interpreter_name = Column(String(128), default="Regional Geological Study")
    source_document_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=True)
    top_md_m = Column(Float, nullable=False)
    top_tvdss_m = Column(Float, nullable=False, index=True)
    base_md_m = Column(Float, nullable=True)
    base_tvdss_m = Column(Float, nullable=True)
    confidence_level = Column(String(32), default="CONFIRMED") # CONFIRMED, PROBABLE, INFERRED, UNCERTAIN
    uncertainty_m = Column(Float, default=2.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class FormationBottom(Base):
    __tablename__ = "formation_bottoms"

    id = Column(Integer, primary_key=True, autoincrement=True)
    interpretation_id = Column(String(64), ForeignKey("formation_interpretations.interpretation_id"), nullable=False, index=True)
    formation_id = Column(String(64), nullable=False)
    bottom_md_m = Column(Float, nullable=False)
    bottom_tvdss_m = Column(Float, nullable=False)
    is_proven = Column(Boolean, default=True) # False if extrapolated

class LithologyInterval(Base):
    __tablename__ = "lithology_intervals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wellbore_id = Column(String(64), ForeignKey("wellbores.wellbore_id"), nullable=False, index=True)
    top_md_m = Column(Float, nullable=False)
    base_md_m = Column(Float, nullable=False)
    lithology_name = Column(String(64), nullable=False) # Sandstone, Claystone, Shale, Limestone
    porosity_pct = Column(Float, nullable=True)
    source_log = Column(String(64), default="COMPOSITE_LOG")

class FaultBlock(Base):
    __tablename__ = "fault_blocks"

    fault_block_id = Column(String(64), primary_key=True, index=True)
    field_id = Column(String(64), ForeignKey("fields.field_id"), nullable=False, index=True)
    block_name = Column(String(128), nullable=False)
    structural_compartment = Column(String(64), default="Central Graben High")
    displacement_throw_m = Column(Float, default=0.0)
    sealing_nature = Column(String(32), default="SEALING")

class OperationalInterval(Base):
    __tablename__ = "operational_intervals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    wellbore_id = Column(String(64), ForeignKey("wellbores.wellbore_id"), nullable=False, index=True)
    section_name = Column(String(64), nullable=False) # 17.5 in, 12.25 in, 8.5 in
    top_md_m = Column(Float, nullable=False)
    base_md_m = Column(Float, nullable=False)
    hole_size_in = Column(Float, nullable=False)
    casing_size_in = Column(Float, nullable=True)
    mud_type = Column(String(64), default="Versatec OBM")
    mud_density_min_sg = Column(Float, default=1.20)
    mud_density_max_sg = Column(Float, default=1.35)

class GeologicalCorrelation(Base):
    __tablename__ = "geological_correlations"

    correlation_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    primary_wellbore_id = Column(String(64), ForeignKey("wellbores.wellbore_id"), nullable=False, index=True)
    offset_wellbore_id = Column(String(64), ForeignKey("wellbores.wellbore_id"), nullable=False, index=True)
    formation_id = Column(String(64), ForeignKey("formations.formation_id"), nullable=False, index=True)
    correlation_type = Column(String(32), default="TVDSS_ALIGNED") # TVDSS_ALIGNED, PROPORTIONAL, TOPS_ONLY
    primary_relative_depth_m = Column(Float, nullable=False)
    offset_relative_depth_m = Column(Float, nullable=False)
    depth_shift_m = Column(Float, nullable=False) # Primary TVDSS - Offset TVDSS
    confidence_score = Column(Float, default=1.0)
    uncertainty_m = Column(Float, default=2.5)
    abstention_flag = Column(Boolean, default=False)
    abstention_reason = Column(String(128), nullable=True) # INSUFFICIENT_EVIDENCE, FAULT_DISCONTINUITY, UNCORRELATED_FORMATION
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class CorrelationReview(Base):
    __tablename__ = "correlation_reviews"

    review_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    correlation_id = Column(String(64), ForeignKey("geological_correlations.correlation_id"), nullable=False, index=True)
    reviewer_name = Column(String(128), nullable=False)
    reviewer_role = Column(String(64), default="PRINCIPAL_GEOLOGIST")
    decision = Column(String(32), nullable=False) # APPROVED, REJECTED, MODIFIED, UNCERTAIN
    review_notes = Column(Text, nullable=True)
    review_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AnalogueCandidate(Base):
    __tablename__ = "analogue_candidates"

    candidate_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    primary_wellbore_id = Column(String(64), nullable=False, index=True)
    offset_wellbore_id = Column(String(64), nullable=False, index=True)
    distance_km = Column(Float, nullable=False)
    field_match = Column(Boolean, default=True)
    formation_overlap = Column(Boolean, default=True)
    trajectory_match = Column(String(32), default="MODERATE") # HIGH, MODERATE, LOW
    eligibility_status = Column(String(32), default="ELIGIBLE") # ELIGIBLE, EXCLUDED, UNCERTAIN
    exclusion_reason = Column(String(255), nullable=True)

class AnalogueEvaluation(Base):
    __tablename__ = "analogue_evaluations"

    evaluation_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    primary_wellbore_id = Column(String(64), nullable=False, index=True)
    offset_wellbore_id = Column(String(64), nullable=False, index=True)
    geological_similarity_score = Column(Float, nullable=False)
    operational_similarity_score = Column(Float, nullable=False)
    spatial_proximity_score = Column(Float, nullable=False)
    composite_score = Column(Float, nullable=False)
    explanation_json = Column(Text, nullable=False)
    rank_order = Column(Integer, default=1)
    evaluation_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# =============================================================================
# NWIS CHRONOS — HISTORICAL REPLAY LABORATORY DATA MODEL (PHASE 04)
# =============================================================================

class ReplaySession(Base):
    __tablename__ = "replay_sessions"

    session_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    well_id = Column(String(64), ForeignKey("wells.well_id"), nullable=False, index=True)
    start_depth_md_m = Column(Float, nullable=False, default=0.0)
    current_depth_md_m = Column(Float, nullable=False, default=0.0)
    end_depth_md_m = Column(Float, nullable=False)
    start_time = Column(String(32), nullable=True)
    current_time = Column(String(32), nullable=True)
    speed_factor = Column(Float, default=1.0)
    status = Column(String(32), default="INITIALIZED", index=True) # INITIALIZED, PLAYING, PAUSED, COMPLETED
    snapshot_id = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ReplayEligibility(Base):
    __tablename__ = "replay_eligibility"

    id = Column(Integer, primary_key=True, autoincrement=True)
    well_id = Column(String(64), ForeignKey("wells.well_id"), nullable=False, unique=True, index=True)
    eligibility_tier = Column(String(64), default="DEPTH_INDEXED") # FULL_TIME_INDEXED, DEPTH_INDEXED, DAILY_REPORT_RECONSTRUCTION, RETROSPECTIVE_ONLY, INSUFFICIENT_DATA
    has_drilling_dates = Column(Boolean, default=True)
    has_verified_events = Column(Boolean, default=True)
    has_definitive_survey = Column(Boolean, default=True)
    has_formation_tops = Column(Boolean, default=True)
    has_prior_offsets = Column(Boolean, default=True)
    exclusion_reason = Column(String(255), nullable=True)
    evaluation_notes = Column(Text, nullable=True)

class HistoricalMemorySnapshot(Base):
    __tablename__ = "historical_memory_snapshots"

    snapshot_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    target_well_id = Column(String(64), nullable=False, index=True)
    cutoff_timestamp = Column(String(32), nullable=False)
    cutoff_depth_md_m = Column(Float, nullable=True)
    eligible_offset_ids_json = Column(Text, nullable=False) # JSON list of prior well IDs
    verified_events_count = Column(Integer, default=0)
    documents_available_count = Column(Integer, default=0)
    checksum_sha256 = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ReplayPacket(Base):
    __tablename__ = "replay_packets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    well_id = Column(String(64), nullable=False, index=True)
    packet_index = Column(Integer, nullable=False)
    timestamp = Column(String(32), nullable=True)
    depth_md_m = Column(Float, nullable=False, index=True)
    depth_tvd_m = Column(Float, nullable=False)
    depth_tvdss_m = Column(Float, nullable=False)
    formation_name = Column(String(64), nullable=False)
    rop_m_hr = Column(Float, default=15.0)
    wob_klbs = Column(Float, default=22.0)
    torque_kft_lb = Column(Float, default=14.5)
    spp_psi = Column(Float, default=2850.0)
    mud_weight_sg = Column(Float, default=1.28)
    is_drilling = Column(Boolean, default=True)
    is_connection = Column(Boolean, default=False)

class GroundTruthEvent(Base):
    __tablename__ = "ground_truth_events"

    event_id = Column(String(64), primary_key=True, index=True)
    well_id = Column(String(64), ForeignKey("wells.well_id"), nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    severity = Column(String(32), nullable=False)
    depth_md_m = Column(Float, nullable=False)
    depth_tvdss_m = Column(Float, nullable=False)
    formation_name = Column(String(64), nullable=False)
    timestamp = Column(String(32), nullable=True)
    npt_hours = Column(Float, default=0.0)
    narrative = Column(Text, nullable=False)
    adjudication_status = Column(String(64), default="ORIGINAL_VERIFIED") # ORIGINAL_VERIFIED, DERIVED_FROM_VERIFIED_SOURCE, RECONSTRUCTED_FIXTURE, SYNTHETIC_FIXTURE, UNVERIFIED, REJECTED
    source_citation = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AdvisoryEvent(Base):
    __tablename__ = "advisory_events"

    advisory_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(64), nullable=True, index=True)
    target_well_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(String(32), nullable=True)
    bit_depth_md_m = Column(Float, nullable=False)
    bit_depth_tvdss_m = Column(Float, nullable=False)
    formation_name = Column(String(64), nullable=False)
    advisory_state = Column(String(64), default="ELEVATED_HISTORICAL_EXPOSURE") # INFORMATIONAL, REVIEW_RECOMMENDED, ELEVATED_HISTORICAL_EXPOSURE, INSUFFICIENT_EVIDENCE, STALE_DATA
    risk_category = Column(String(64), nullable=False) # LOST_CIRCULATION, STUCK_PIPE, PACKOFF, TIGHT_HOLE
    risk_score = Column(Float, nullable=False)
    lead_distance_m = Column(Float, nullable=True)
    source_wells_json = Column(Text, nullable=False)
    explanation = Column(Text, nullable=False)
    evidence_passport_json = Column(Text, nullable=True)
    human_review_status = Column(String(32), default="UNREVIEWED")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class AdvisoryEvidence(Base):
    __tablename__ = "advisory_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    advisory_id = Column(String(64), ForeignKey("advisory_events.advisory_id"), nullable=False, index=True)
    source_well_id = Column(String(64), nullable=False)
    event_id = Column(String(64), nullable=False)
    doc_id = Column(String(64), nullable=True)
    quoted_passage = Column(Text, nullable=False)
    correlation_type = Column(String(32), default="FORMATION_RELATIVE")
    source_availability_timestamp = Column(String(32), nullable=True)

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    run_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    target_well_id = Column(String(64), nullable=False, index=True)
    evaluation_type = Column(String(64), default="CHRONOS_LEAVE_ONE_WELL_OUT") # CHRONOS_LEAVE_ONE_WELL_OUT, BASELINE_DISTANCE_ONLY, BASELINE_FORMATION_ONLY
    lookahead_window_m = Column(Float, default=100.0)
    cooldown_window_m = Column(Float, default=50.0)
    total_events = Column(Integer, default=0)
    true_positives = Column(Integer, default=0)
    false_positives = Column(Integer, default=0)
    false_negatives = Column(Integer, default=0)
    abstentions = Column(Integer, default=0)
    precision = Column(Float, default=0.0)
    recall = Column(Float, default=0.0)
    f1_score = Column(Float, default=0.0)
    false_alarms_per_100m = Column(Float, default=0.0)
    avg_lead_distance_m = Column(Float, default=0.0)
    execution_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class EvaluationMatch(Base):
    __tablename__ = "evaluation_matches"

    match_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    run_id = Column(String(64), ForeignKey("evaluation_runs.run_id"), nullable=False, index=True)
    ground_truth_event_id = Column(String(64), nullable=False)
    matched_advisory_id = Column(String(64), nullable=True)
    lead_distance_m = Column(Float, nullable=True)
    is_true_positive = Column(Boolean, default=False)
    match_status = Column(String(32), default="TRUE_POSITIVE") # TRUE_POSITIVE, FALSE_NEGATIVE, SUPPRESSED

# =============================================================================
# PHASE 5: NWIS SENTINEL INTELLIGENCE & HYBRID RETRIEVAL DATA MODELS
# =============================================================================

class KnowledgeChunk(Base):
    """
    Petroleum-aware document chunk preserving bounding box, depth intervals,
    numerical technical measurements with units, provenance tier, and verification status.
    """
    __tablename__ = "knowledge_chunks"

    chunk_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    doc_id = Column(String(64), ForeignKey("documents.doc_id"), nullable=False, index=True)
    well_id = Column(String(64), ForeignKey("wells.well_id"), nullable=False, index=True)
    page_number = Column(Integer, nullable=False)
    passage_text = Column(Text, nullable=False)
    bounding_box_json = Column(String(128), nullable=True) # {"x0": 0.1, "y0": 0.2, "x1": 0.9, "y1": 0.4}
    formation_name = Column(String(64), nullable=True, index=True)
    event_category = Column(String(64), nullable=True, index=True)
    depth_start_md_m = Column(Float, nullable=True)
    depth_end_md_m = Column(Float, nullable=True)
    depth_datum = Column(String(16), default="MD") # MD, TVD, TVDSS
    technical_measurements_json = Column(Text, nullable=True) # {"mud_weight": "1.28 SG", "loss_rate": "42 bbl/hr"}
    provenance_tier = Column(String(32), default="ORIGINAL_VERIFIED", index=True) # ORIGINAL_VERIFIED, DERIVED_FROM_VERIFIED_SOURCE, RECONSTRUCTED_FIXTURE
    verification_status = Column(String(32), default="VERIFIED", index=True)
    sha256_hash = Column(String(64), nullable=False)
    source_date = Column(String(32), nullable=True)
    availability_timestamp = Column(String(32), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class QueryPlanRecord(Base):
    """
    Deterministic engineering query plan capturing target formation, event category,
    depth limits, datum requirements, and historical date range.
    """
    __tablename__ = "query_plans"

    plan_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    raw_query = Column(Text, nullable=False)
    target_well_id = Column(String(64), nullable=True)
    target_formation = Column(String(64), nullable=True)
    event_category = Column(String(64), nullable=True)
    depth_min_m = Column(Float, nullable=True)
    depth_max_m = Column(Float, nullable=True)
    depth_datum = Column(String(16), default="MD")
    temporal_cutoff = Column(String(32), nullable=True)
    intent_type = Column(String(64), default="HAZARD_LOOKUP")
    answer_mode = Column(String(32), default="TEXT") # TEXT, TABLE, GEOLOGICAL, EVIDENCE, CHRONOS
    is_ambiguous = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AnswerClaimRecord(Base):
    """
    Individual engineering claim produced in a Sentinel answer, bound to supporting evidence.
    """
    __tablename__ = "answer_claims"

    claim_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    session_id = Column(String(64), nullable=False, index=True)
    claim_text = Column(Text, nullable=False)
    claim_type = Column(String(32), default="HAZARD") # HAZARD, PARAMETER, FORMATION, OFFSET, MITIGATION
    verification_status = Column(String(32), default="VERIFIED") # VERIFIED, UNVERIFIED, CONTRADICTED, ABSTAINED
    confidence_score = Column(Float, default=1.0)
    supporting_chunk_id = Column(String(64), ForeignKey("knowledge_chunks.chunk_id"), nullable=True)
    source_citation = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class GenerationAudit(Base):
    """
    Full audit trail of AI question-answering sessions for compliance and cyber-governance.
    """
    __tablename__ = "generation_audits"

    audit_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(64), default="ENGINEER_OIL_01")
    query_text = Column(Text, nullable=False)
    plan_id = Column(String(64), nullable=True)
    retrieval_status = Column(String(64), default="SUCCESS")
    evidence_chunks_count = Column(Integer, default=0)
    claims_count = Column(Integer, default=0)
    verified_claims_count = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    model_provider = Column(String(64), default="DETERMINISTIC_ENGINE")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class SentinelEvaluationResult(Base):
    """
    Independent QA evaluation metrics comparing Baseline A (Keyword), Baseline B (Vector),
    Baseline C (Hybrid), and Proposed Sentinel (Formation-Aware Hybrid).
    """
    __tablename__ = "sentinel_evaluation_results"

    eval_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    benchmark_name = Column(String(64), default="PETROLEUM_QA_BENCHMARK_VOLVE")
    baseline_name = Column(String(64), nullable=False) # BASELINE_KEYWORD, BASELINE_VECTOR, BASELINE_HYBRID, SENTINEL_FORMATION_AWARE
    total_questions = Column(Integer, default=10)
    recall_at_5 = Column(Float, default=0.0)
    precision_at_5 = Column(Float, default=0.0)
    mrr = Column(Float, default=0.0)
    ndcg = Column(Float, default=0.0)
    citation_correctness = Column(Float, default=0.0)
    groundedness_score = Column(Float, default=0.0)
    abstention_correctness = Column(Float, default=0.0)
    avg_latency_ms = Column(Float, default=0.0)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))


# =============================================================================
# PHASE 06: NWIS PULSE — INDUSTRIAL DRILLING TELEMETRY & ADVISORY MODELS
# =============================================================================

class TelemetrySource(Base):
    """
    Industrial telemetry connection source (WITSML, ETP, Recorded Replay, Synthetic Demo).
    Maintains strict source mode separation and connection health state.
    """
    __tablename__ = "telemetry_sources"

    source_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    source_name = Column(String(128), nullable=False)
    source_type = Column(String(32), nullable=False) # WITSML_1411, WITSML_21, ETP_12, CSV_JSON_EXPORT, CHRONOS_REPLAY, SYNTHETIC_STREAM
    source_mode = Column(String(32), nullable=False, default="GENUINE_RECORDED_REPLAY") # AUTHORIZED_LIVE, GENUINE_RECORDED_REPLAY, SYNTHETIC_DEMO
    connection_status = Column(String(32), default="OFFLINE", index=True) # ONLINE, DEGRADED, STALE, INSUFFICIENT, OFFLINE
    endpoint_url = Column(String(255), nullable=True)
    is_read_only = Column(Boolean, default=True) # Strict read-only invariant (no rig control)
    last_heartbeat = Column(DateTime, nullable=True)
    config_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TelemetryChannelMapping(Base):
    """
    Mapping from source/vendor channel mnemonics (e.g., ROPA, BPOS, SPPA) to canonical channels.
    """
    __tablename__ = "telemetry_channel_mappings"

    mapping_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    source_id = Column(String(64), ForeignKey("telemetry_sources.source_id"), nullable=False, index=True)
    source_mnemonic = Column(String(64), nullable=False)
    canonical_name = Column(String(64), nullable=False, index=True) # ROP, BIT_DEPTH, MD, TVD, WOB, RPM, TORQUE, SPP, FLOW_IN, FLOW_OUT, PIT_VOLUME, MUD_WEIGHT, ECD, GAS_TOTAL
    source_unit = Column(String(32), nullable=False)
    canonical_unit = Column(String(32), nullable=False)
    scale_multiplier = Column(Float, default=1.0)
    offset_value = Column(Float, default=0.0)
    is_measured = Column(Boolean, default=True) # True if directly measured by sensor, False if calculated/derived


class RawTelemetryPacket(Base):
    """
    Preserves original incoming raw telemetry packet for auditability and non-repudiation.
    """
    __tablename__ = "raw_telemetry_packets"

    packet_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    source_id = Column(String(64), ForeignKey("telemetry_sources.source_id"), nullable=False, index=True)
    wellbore_id = Column(String(64), nullable=False, index=True)
    raw_payload = Column(Text, nullable=False)
    protocol_version = Column(String(32), default="WITSML_1.4.1.1")
    source_timestamp = Column(String(32), nullable=True)
    reception_timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    checksum_sha256 = Column(String(64), nullable=False)
    is_duplicate = Column(Boolean, default=False)


class NormalizedTelemetry(Base):
    """
    Canonical time-series drilling telemetry record with quality state and geological enrichment.
    """
    __tablename__ = "normalized_telemetry"

    telemetry_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    source_id = Column(String(64), ForeignKey("telemetry_sources.source_id"), nullable=False, index=True)
    wellbore_id = Column(String(64), nullable=False, index=True)
    timestamp = Column(String(32), nullable=False, index=True) # ISO8601 UTC
    
    # Depths
    md_m = Column(Float, nullable=False, index=True)
    bit_depth_m = Column(Float, nullable=False)
    tvd_m = Column(Float, nullable=True)
    tvdss_m = Column(Float, nullable=True, index=True)
    
    # Mechanical & Hydraulic Channels
    rop_m_hr = Column(Float, nullable=True)
    wob_kn = Column(Float, nullable=True)
    rpm = Column(Float, nullable=True)
    torque_kn_m = Column(Float, nullable=True)
    spp_kpa = Column(Float, nullable=True)
    hookload_kn = Column(Float, nullable=True)
    flow_in_lpm = Column(Float, nullable=True)
    flow_out_pct = Column(Float, nullable=True)
    pit_volume_m3 = Column(Float, nullable=True)
    mud_weight_sg = Column(Float, nullable=True)
    ecd_sg = Column(Float, nullable=True)
    gas_total_pct = Column(Float, nullable=True)
    
    # GeoCore Live Enrichment
    current_formation = Column(String(64), nullable=True, index=True)
    formation_top_tvdss_m = Column(Float, nullable=True)
    formation_base_tvdss_m = Column(Float, nullable=True)
    formation_penetration_pct = Column(Float, nullable=True)
    subsurface_corridor_id = Column(String(64), nullable=True)
    
    # Data Quality Assessment
    quality_state = Column(String(32), default="HEALTHY", index=True) # HEALTHY, DEGRADED, STALE, INSUFFICIENT, OFFLINE
    is_connection = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class TelemetryQualityEvent(Base):
    """
    Records data quality anomalies, staleness events, packet loss, or sensor drifts.
    """
    __tablename__ = "telemetry_quality_events"

    event_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    source_id = Column(String(64), ForeignKey("telemetry_sources.source_id"), nullable=False, index=True)
    wellbore_id = Column(String(64), nullable=False, index=True)
    issue_type = Column(String(64), nullable=False, index=True) # MISSING_TIMESTAMP, DUPLICATE_PACKET, OUT_OF_ORDER, STALE_TELEMETRY, SENSOR_DRIFT, OUTLIER, DISCONNECTION
    severity = Column(String(16), default="WARNING") # INFO, WARNING, CRITICAL
    channel_name = Column(String(64), nullable=True)
    details_json = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)


class EngineeringRuleVersion(Base):
    """
    Versioned operational anomaly detection rule (approved by drilling superintendent).
    No arbitrary black-box thresholds.
    """
    __tablename__ = "engineering_rule_versions"

    rule_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    rule_name = Column(String(128), nullable=False)
    rule_version = Column(String(32), default="v1.0.0")
    hazard_type = Column(String(64), nullable=False, index=True) # KICK_GAS, LOST_CIRCULATION, STUCK_PIPE, PACKOFF, DRILLSTRING_VIBRATION
    conditions_json = Column(Text, nullable=False) # Structured parameter thresholds
    required_channels_json = Column(Text, nullable=False) # e.g. ["FLOW_IN", "FLOW_OUT", "PIT_VOLUME"]
    hysteresis_window_s = Column(Integer, default=30)
    cooldown_s = Column(Integer, default=120)
    approved_by = Column(String(64), default="CHIEF_DRILLING_ENGINEER")
    approved_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class OperationalAdvisory(Base):
    """
    Decision support advisory generated from live telemetry + GeoCore + Historical memory.
    Equipped with Two-Layer Evidence Passport. Human driller holds final decision authority.
    """
    __tablename__ = "operational_advisories"

    advisory_id = Column(String(64), primary_key=True, default=generate_uuid, index=True)
    wellbore_id = Column(String(64), nullable=False, index=True)
    source_mode = Column(String(32), default="GENUINE_RECORDED_REPLAY")
    timestamp = Column(String(32), nullable=False)
    hazard_type = Column(String(64), nullable=False, index=True) # KICK_GAS, LOST_CIRCULATION, STUCK_PIPE, PACKOFF
    severity = Column(String(16), default="WARNING") # INFO, CAUTION, WARNING, CRITICAL
    advisory_state = Column(String(32), default="NEW", index=True) # NEW, ACKNOWLEDGED, UNDER_REVIEW, RESOLVED, SUPPRESSED, EXPIRED
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=False)
    rule_id = Column(String(64), ForeignKey("engineering_rule_versions.rule_id"), nullable=True)
    
    # Physical/Geological Context
    bit_depth_md_m = Column(Float, nullable=False)
    bit_depth_tvdss_m = Column(Float, nullable=False)
    formation_name = Column(String(64), nullable=False)
    
    # Signature Innovation: Two-Layer Evidence Passport
    # Layer A: Current Telemetry Evidence (live channels, values, delta, threshold, quality)
    telemetry_evidence_json = Column(Text, nullable=False)
    # Layer B: Verified Historical Evidence (offset well, event narrative, citation, report passage)
    historical_evidence_json = Column(Text, nullable=False)
    
    # Human-in-the-Loop Decision & Review
    acknowledged_by = Column(String(64), nullable=True)
    acknowledged_at = Column(DateTime, nullable=True)
    ack_comments = Column(Text, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class AdvisoryReviewEvent(Base):
    """
    Immutable audit trail of driller/superintendent interactions with an advisory.
    """
    __tablename__ = "advisory_review_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    advisory_id = Column(String(64), ForeignKey("operational_advisories.advisory_id"), nullable=False, index=True)
    old_state = Column(String(32), nullable=False)
    new_state = Column(String(32), nullable=False)
    actor_id = Column(String(64), nullable=False)
    actor_role = Column(String(64), default="DRILLING_SUPERINTENDENT")
    notes = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)




