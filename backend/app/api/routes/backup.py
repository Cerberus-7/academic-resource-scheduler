from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import json

from app.core.database import get_db
from app.models.user import User, RoleName
from app.api.deps import require_roles
from app.services import backup_service
from app.services.analytics_service import log_audit

router = APIRouter(prefix="/api/backup", tags=["backup"])


@router.get("/export")
def export_backup(db: Session = Depends(get_db), user: User = Depends(require_roles(RoleName.ADMIN))):
    """Download the full current database state as a single JSON file.
    This is a local backup/demo-data feature only — SQLite remains the
    primary database at all times."""
    payload = backup_service.export_backup(db)
    log_audit(db, user.id, "EXPORT_BACKUP", "backup", None,
              f"Exported {sum(len(v) for v in payload['tables'].values())} rows across {len(payload['tables'])} tables.")
    db.commit()

    filename = f"academic-scheduler-backup-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
    return JSONResponse(
        content=payload,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import")
async def import_backup(
    file: UploadFile = File(...),
    clear_existing: bool = Query(True, description="Wipe existing data before restoring."),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(RoleName.ADMIN)),
):
    """Restore the database from a previously exported (or same-shape,
    hand-authored) JSON backup file."""
    raw = await file.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(400, f"Uploaded file is not valid JSON: {e}")

    try:
        counts = backup_service.import_backup(db, payload, clear_existing=clear_existing)
    except backup_service.BackupImportError as e:
        raise HTTPException(400, str(e))

    log_audit(db, user.id, "IMPORT_BACKUP", "backup", None,
              f"Imported {sum(counts.values())} rows across {len(counts)} tables "
              f"(clear_existing={clear_existing}) from '{file.filename}'.")
    db.commit()
    return {"message": "Backup imported successfully.", "row_counts": counts}
