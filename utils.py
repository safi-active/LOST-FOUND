# utils.py
import os
import uuid
from datetime import datetime
from bson import ObjectId
from flask import current_app
from werkzeug.utils import secure_filename
from database import get_db

ALLOWED_EXT = {"png", "jpg", "jpeg", "gif", "webp"}
MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB


def utcnow():
    return datetime.utcnow()


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXT


def save_upload(file_storage) -> str | None:
    """Save an uploaded file to /uploads and return filename. Returns None if no file."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        raise ValueError("Unsupported file type. Allowed: png, jpg, jpeg, gif, webp.")
    # Validate size by reading (Flask may not expose size reliably); request.max_content_length is set globally
    fname = f"{uuid.uuid4().hex}_{secure_filename(file_storage.filename)}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    file_storage.save(os.path.join(upload_dir, fname))
    return fname


def log_activity(actor: str, action: str, target: str = "", meta: dict | None = None):
    db = get_db()
    db.activity_logs.insert_one({
        "actor": actor,
        "action": action,
        "target": target,
        "meta": meta or {},
        "created_at": utcnow(),
    })


def notify(recipient_type: str, recipient_id: str | None, title: str, message: str,
           link: str | None = None, report_id: str | None = None):
    """
    Create a notification.
    recipient_type: 'student' or 'admin'
    recipient_id: student OID string (or None for admin/broadcast)
    """
    db = get_db()
    doc = {
        "recipient_type": recipient_type,
        "recipient_id": recipient_id,
        "title": title,
        "message": message,
        "link": link,
        "report_id": report_id,
        "read": False,
        "created_at": utcnow(),
    }
    db.notifications.insert_one(doc)
    return doc


def notification_count(recipient_type: str, recipient_id: str | None) -> int:
    db = get_db()
    q = {"recipient_type": recipient_type, "read": False}
    if recipient_id is not None:
        q["recipient_id"] = recipient_id
    return db.notifications.count_documents(q)


def serialize(doc: dict) -> dict:
    """Convert ObjectId/date to JSON-friendly values for template use."""
    if not doc:
        return doc
    out = {}
    for k, v in doc.items():
        if isinstance(v, ObjectId):
            out[k] = str(v)
        elif isinstance(v, datetime):
            out[k] = v.strftime("%Y-%m-%d %H:%M")
        else:
            out[k] = v
    return out


def status_badge(status: str) -> str:
    return {
        "Pending": "badge-pending",
        "Found": "badge-found",
        "Returned": "badge-returned",
        "Unresolved": "badge-unresolved",
    }.get(status, "badge-pending")