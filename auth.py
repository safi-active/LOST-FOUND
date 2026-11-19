# auth.py
import os
import functools
from flask import session, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash, check_password_hash
from bson import ObjectId
from datetime import datetime
from pymongo import ReturnDocument
from database import get_db

# --- Admin credentials from environment ---
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@university.edu")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
ADMIN_NAME = os.getenv("ADMIN_NAME", "Logistics Administrator")


def verify_admin(email: str, password: str) -> bool:
    return email.strip().lower() == ADMIN_EMAIL.strip().lower() and password == ADMIN_PASSWORD


def admin_session():
    session.clear()
    session["role"] = "admin"
    session["admin_email"] = ADMIN_EMAIL
    session["admin_name"] = ADMIN_NAME


def student_session(student_doc):
    session.clear()
    session["role"] = "student"
    session["student_email"] = student_doc["email"]
    session["student_id"] = student_doc["student_id"]
    session["student_oid"] = str(student_doc["_id"])
    session["student_name"] = student_doc["full_name"]


def hash_password(pw: str) -> str:
    return generate_password_hash(pw)


def verify_password(pw: str, hashed: str) -> bool:
    return check_password_hash(hashed, pw)

def generate_student_id() -> str:
    """
    Generate a unique, monotonically increasing student ID like UNI-2025-0001.

    Uses a per-year counter document in the `counters` collection so IDs
    never collide — even if students are deleted and re-added.
    """
    from pymongo import ReturnDocument

    db = get_db()
    year = datetime.utcnow().year

    result = db.counters.find_one_and_update(
        {"_id": f"student_id_{year}"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=ReturnDocument.AFTER,
    )
    seq = result["seq"]
    sid = f"UNI-{year}-{seq:04d}"

    # Safety net: if for any reason this ID already exists (e.g. counters reset),
    # keep incrementing until we find a free slot.
    while db.students.find_one({"student_id": sid}):
        seq += 1
        sid = f"UNI-{year}-{seq:04d}"
        db.counters.update_one(
            {"_id": f"student_id_{year}"},
            {"$set": {"seq": seq}},
        )
    return sid



# ---------- Route protection decorators ----------

def login_required_student(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "student":
            flash("Please log in as a student.", "error")
            return redirect(url_for("student_login"))
        return view(*args, **kwargs)
    return wrapped


def login_required_admin(view):
    @functools.wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Administrator access required.", "error")
            return redirect(url_for("admin_login"))
        return view(*args, **kwargs)
    return wrapped


def current_student():
    """Fetch the logged-in student document or None."""
    if session.get("role") != "student":
        return None
    try:
        return get_db().students.find_one({"_id": ObjectId(session["student_oid"])})
    except Exception:
        return None

    