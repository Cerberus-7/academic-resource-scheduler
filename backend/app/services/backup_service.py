"""
JSON export/import backup service.

Per the project's cost/dependency rules, SQLite remains the primary
database at all times — this module only supports:
  (a) exporting the full current database state to a single JSON document
      the admin can download and keep as a local backup, and
  (b) restoring the database from a previously exported JSON document
      (or hand-authored demo-data JSON matching the same shape).

It is intentionally generic: it walks every table registered on
Base.metadata (topologically sorted so foreign-key dependencies are
respected on both export and import) rather than hand-listing tables,
so it stays in sync automatically as models evolve.
"""
import base64
import datetime
from typing import Any
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.core.database import Base

DATETIME_PREFIX = "__dt__:"
BYTES_PREFIX = "__b64__:"

BACKUP_FORMAT_VERSION = 1


def _serialize_value(value: Any) -> Any:
    if isinstance(value, (datetime.datetime, datetime.date)):
        return DATETIME_PREFIX + value.isoformat()
    if isinstance(value, bytes):
        return BYTES_PREFIX + base64.b64encode(value).decode("ascii")
    return value


def _deserialize_value(value: Any) -> Any:
    if isinstance(value, str) and value.startswith(DATETIME_PREFIX):
        raw = value[len(DATETIME_PREFIX):]
        try:
            return datetime.datetime.fromisoformat(raw)
        except ValueError:
            return datetime.date.fromisoformat(raw)
    if isinstance(value, str) and value.startswith(BYTES_PREFIX):
        return base64.b64decode(value[len(BYTES_PREFIX):])
    return value


def export_backup(db: Session) -> dict:
    """Serialize every table's rows to plain JSON-safe values."""
    tables = Base.metadata.sorted_tables
    data: dict[str, list[dict]] = {}
    for table in tables:
        rows = db.execute(select(table)).mappings().all()
        data[table.name] = [
            {col: _serialize_value(val) for col, val in dict(row).items()}
            for row in rows
        ]
    return {
        "format_version": BACKUP_FORMAT_VERSION,
        "exported_at": datetime.datetime.utcnow().isoformat(),
        "tables": data,
    }


class BackupImportError(ValueError):
    pass


def import_backup(db: Session, payload: dict, clear_existing: bool = True) -> dict:
    """Restore the database from a previously exported (or hand-authored,
    same-shape) JSON document. Runs inside a single transaction — if any
    table fails to import, nothing is committed."""
    if "tables" not in payload:
        raise BackupImportError("Invalid backup file: missing 'tables' key.")

    tables_by_name = {t.name: t for t in Base.metadata.sorted_tables}
    unknown = set(payload["tables"].keys()) - set(tables_by_name.keys())
    if unknown:
        raise BackupImportError(f"Backup references unknown tables: {sorted(unknown)}")

    sorted_tables = Base.metadata.sorted_tables
    counts = {}

    try:
        if clear_existing:
            for table in reversed(sorted_tables):
                if table.name in payload["tables"]:
                    db.execute(delete(table))

        for table in sorted_tables:
            rows = payload["tables"].get(table.name, [])
            if not rows:
                counts[table.name] = 0
                continue
            valid_columns = {c.name for c in table.columns}
            clean_rows = []
            for row in rows:
                clean_row = {k: _deserialize_value(v) for k, v in row.items() if k in valid_columns}
                clean_rows.append(clean_row)
            if clean_rows:
                db.execute(table.insert(), clean_rows)
            counts[table.name] = len(clean_rows)

        db.commit()
    except Exception as exc:
        db.rollback()
        raise BackupImportError(f"Import failed and was rolled back: {exc}") from exc

    return counts
