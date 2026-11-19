# database.py
import os
from pymongo import MongoClient, ASCENDING, TEXT
from pymongo.errors import ConnectionFailure

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = "campus_lost_found"

_client = None
_db = None


def get_db():
    """Return the MongoDB database instance (singleton)."""
    global _client, _db
    if _db is None:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _db = _client[DB_NAME]
    return _db


def init_db():
    """Create collections and indexes. Safe to call multiple times."""
    db = get_db()

    # --- students ---
    db.students.create_index([("email", ASCENDING)], unique=True)
    db.students.create_index([("student_id", ASCENDING)], unique=True)

    # --- lost_reports ---
    db.lost_reports.create_index([("student_id", ASCENDING)])
    db.lost_reports.create_index([("status", ASCENDING)])
    db.lost_reports.create_index([("created_at", ASCENDING)])
    db.lost_reports.create_index(
        [("item_name", TEXT), ("category", TEXT), ("location", TEXT)]
    )

    # --- found_items ---
    db.found_items.create_index([("status", ASCENDING)])
    db.found_items.create_index([("created_at", ASCENDING)])
    db.found_items.create_index(
        [("item_name", TEXT), ("category", TEXT), ("location_found", TEXT)]
    )

    # --- notifications ---
    db.notifications.create_index([("recipient_type", ASCENDING)])
    db.notifications.create_index([("recipient_id", ASCENDING)])
    db.notifications.create_index([("read", ASCENDING)])
    db.notifications.create_index([("created_at", ASCENDING)])

    # --- activity_logs ---
    db.activity_logs.create_index([("created_at", ASCENDING)])
    db.activity_logs.create_index([("actor", ASCENDING)])

    return db


def check_connection():
    try:
        get_db().command("ping")
        return True
    except ConnectionFailure:
        return False