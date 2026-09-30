"""
Ingestion script for authentic petroleum documents into eRTMAC-NWIS database.
Ingests:
- VOLVE_DDR_20080914_F14.pdf (Lost circulation in Hugin FM)
- VOLVE_DDR_20080922_F14.pdf (Stuck pipe in Hugin FM)
- VOLVE_DDR_20090218_F15S.pdf (Packoff in Skagerrak FM)
- VOLVE_DDR_ROUTINE_DRILLING_CLEAN.pdf (Routine drilling, zero incidents)
- VOLVE_DDR_SCANNED_MUD_REPORT.pdf (Scanned report with tight hole)
"""

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.db.database import SessionLocal
from backend.app.services.document_service import document_service

DOCS_DIR = ROOT_DIR / "data" / "documents" / "raw"

def main():
    db = SessionLocal()
    try:
        pdf_files = list(DOCS_DIR.glob("*.pdf"))
        print(f"Found {len(pdf_files)} authentic PDF documents in {DOCS_DIR}")

        for pdf_path in pdf_files:
            print(f"\nProcessing: {pdf_path.name}...")
            with open(pdf_path, "rb") as f:
                content = f.read()

            well_id = None
            if "F14" in pdf_path.name:
                well_id = "NO-15/9-F-14"
            elif "F15S" in pdf_path.name:
                well_id = "NO-15/9-F-15S"
            elif "F12" in pdf_path.name:
                well_id = "NO-15/9-F-12"
            elif "SCANNED" in pdf_path.name:
                well_id = "NO-15/9-F-4"

            res = document_service.ingest_document_file(
                file_bytes=content,
                original_filename=pdf_path.name,
                db=db,
                well_id=well_id,
                source_id="SRC-VOLVE-001"
            )
            print(f"  -> Ingestion status: {res['status']}")
            print(f"  -> Doc ID: {res['doc_id']}")
            print(f"  -> Total Pages: {res['total_pages']} | Is Scanned: {res['is_scanned']}")
            print(f"  -> Message: {res['message']}")

        # Verify duplicate detection (idempotency test)
        print("\nTesting duplicate ingestion idempotency on VOLVE_DDR_20080914_F14.pdf...")
        first_pdf = DOCS_DIR / "VOLVE_DDR_20080914_F14.pdf"
        with open(first_pdf, "rb") as f:
            content = f.read()
        dup_res = document_service.ingest_document_file(
            file_bytes=content,
            original_filename="VOLVE_DDR_20080914_F14.pdf",
            db=db,
            well_id="NO-15/9-F-14"
        )
        assert dup_res["is_duplicate"] == True, "Duplicate must be detected"
        print(f"  [OK] Idempotency verified: is_duplicate={dup_res['is_duplicate']}")

    finally:
        db.close()

if __name__ == "__main__":
    main()
