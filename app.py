# app.py
import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

missing_settings = [
    name for name in ("SECRET_KEY", "ADMIN_PASSWORD")
    if not os.getenv(name)
]
if missing_settings:
    raise RuntimeError(
        "Missing required settings: "
        + ", ".join(missing_settings)
        + ". Copy .env.example to .env and set these values."
    )

from pymongo.errors import DuplicateKeyError

from datetime import datetime
from flask import (
    Flask, render_template_string, request, redirect, url_for,
    flash, session, send_from_directory, abort, jsonify
)
from bson import ObjectId
from bson.errors import InvalidId

from database import get_db, init_db, check_connection
from auth import (
    login_required_student, login_required_admin,
    hash_password, verify_password, generate_student_id,
    verify_admin, admin_session, student_session, current_student,
    ADMIN_EMAIL,
)
from utils import (
    save_upload, log_activity, notify, notification_count,
    serialize, status_badge, utcnow
)
import templates as T
import static as S

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024

# Register embedded templates
# ---------------------------------------------------------------
# Embedded template registry + real Jinja loader
# ---------------------------------------------------------------
from jinja2 import DictLoader

TEMPLATE_REGISTRY = {
    "base.html": T.STUDENT_BASE,
    "student_login.html": T.STUDENT_LOGIN,
    "student_register.html": T.STUDENT_REGISTER,
    "student_dashboard.html": T.STUDENT_DASHBOARD,
    "student_report_form.html": T.STUDENT_REPORT_FORM,
    "student_my_reports.html": T.STUDENT_MY_REPORTS,
    "student_report_detail.html": T.STUDENT_REPORT_DETAIL,
    "student_found_items.html": T.STUDENT_FOUND_ITEMS,
    "student_notifications.html": T.STUDENT_NOTIFICATIONS,
    "student_profile.html": T.STUDENT_PROFILE,
    "admin_base.html": T.ADMIN_BASE,
    "admin_login.html": T.ADMIN_LOGIN,
    "admin_dashboard.html": T.ADMIN_DASHBOARD,
    "admin_reports.html": T.ADMIN_REPORTS,
    "admin_report_detail.html": T.ADMIN_REPORT_DETAIL,
    "admin_found_items.html": T.ADMIN_FOUND_ITEMS,
    "admin_edit_found.html": T.ADMIN_EDIT_FOUND,
    "admin_students.html": T.ADMIN_STUDENTS,
    "admin_notifications.html": T.ADMIN_NOTIFICATIONS,
    "admin_activity.html": T.ADMIN_ACTIVITY,
}

# This is the critical line: tell Jinja to load templates from the dict.
app.jinja_loader = DictLoader(TEMPLATE_REGISTRY)
app.jinja_env.globals["status_badge"] = status_badge


def render(template_name: str, **kwargs):
    """Render a template from the embedded registry, injecting notif_count."""
    if session.get("role") == "student":
        kwargs.setdefault(
            "notif_count",
            notification_count("student", session.get("student_oid")),
        )
    elif session.get("role") == "admin":
        kwargs.setdefault("notif_count", notification_count("admin", None))
    else:
        kwargs.setdefault("notif_count", 0)
    return render_template_string(TEMPLATE_REGISTRY[template_name], **kwargs)


# ---------- static ----------
@app.route("/static/style.css")
def static_css():
    return app.response_class(S.CSS, mimetype="text/css")

@app.route("/static/app.js")
def static_js():
    return app.response_class(S.JS, mimetype="application/javascript")


@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    # Protect: only owner student or admin should see; but images are non-sensitive here.
    if session.get("role") not in ("student", "admin"):
        abort(403)
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


# ---------- root ----------
@app.route("/")
def index():
    if session.get("role") == "student":
        return redirect(url_for("student_dashboard"))
    if session.get("role") == "admin":
        return redirect(url_for("admin_dashboard"))
    return redirect(url_for("student_login"))


@app.route("/logout")
def logout():
    role = session.get("role")
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("admin_login") if role == "admin" else url_for("student_login"))


# ============================================================
# STUDENT AUTH
# ============================================================
@app.route("/student/login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        # 1) Check admin credentials FIRST (silently).
        if verify_admin(email, password):
            admin_session()
            log_activity(ADMIN_EMAIL, "admin_login", "admin")
            return redirect(url_for("admin_dashboard"))

        # 2) Otherwise treat as a student login.
        db = get_db()
        student = db.students.find_one({"email": email})
        if not student or not verify_password(password, student["password_hash"]):
            flash("Invalid email or password.", "error")
            return redirect(url_for("student_login"))

        student_session(student)
        log_activity(email, "student_login", student["student_id"])
        return redirect(url_for("student_dashboard"))

    return render("student_login.html")

@app.route("/student/register", methods=["GET", "POST"])
def student_register():
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm") or ""

        if len(full_name) < 2 or "@" not in email or len(password) < 6:
            flash("Please fill all fields correctly (password ≥ 6 chars).", "error")
            return redirect(url_for("student_register"))
        if password != confirm:
            flash("Passwords do not match.", "error")
            return redirect(url_for("student_register"))

        db = get_db()
        if db.students.find_one({"email": email}):
            flash("An account with that email already exists.", "error")
            return redirect(url_for("student_register"))

        sid = generate_student_id()
        doc = {
            "full_name": full_name,
            "email": email,
            "student_id": sid,
            "password_hash": hash_password(password),
            "created_at": utcnow(),
        }
       
        try:
            db.students.insert_one(doc)
        except Exception as e:
            # Surface the real reason to the terminal for debugging,
            # and show a safe message to the user.
            print(f"[REGISTER ERROR] {type(e).__name__}: {e}")
            flash("Could not create account — that email or student ID is already taken. Please try again.", "error")
            return redirect(url_for("student_register"))

        log_activity(email, "student_registered", sid)
        flash(f"Account created. Your Student ID is {sid}. Please log in.", "success")
        return redirect(url_for("student_login"))


# ============================================================
# STUDENT PAGES
# ============================================================
@app.route("/student/dashboard")
@login_required_student
def student_dashboard():
    db = get_db()
    sid = session["student_oid"]
    student = current_student()
    if not student:
        session.clear()
        return redirect(url_for("student_login"))

    all_reports = list(db.lost_reports.find({"student_oid": sid}))
    stats = {
        "total": len(all_reports),
        "pending": sum(1 for r in all_reports if r["status"] == "Pending"),
        "found": sum(1 for r in all_reports if r["status"] == "Found"),
        "returned": sum(1 for r in all_reports if r["status"] == "Returned"),
        "unresolved": sum(1 for r in all_reports if r["status"] == "Unresolved"),
    }
    recent_notifs = [serialize(n) for n in db.notifications.find(
        {"recipient_type": "student", "recipient_id": sid}
    ).sort("created_at", -1).limit(5)]
    return render("student_dashboard.html", student=serialize(student), stats=stats,
                  recent_notifications=recent_notifs)


@app.route("/student/report-lost", methods=["GET", "POST"])
@login_required_student
def student_report_lost():
    if request.method == "POST":
        item_name = (request.form.get("item_name") or "").strip()
        category = (request.form.get("category") or "").strip()
        colour = (request.form.get("colour") or "").strip()
        date_lost = (request.form.get("date_lost") or "").strip()
        location = (request.form.get("location") or "").strip()
        description = (request.form.get("description") or "").strip()

        if not (item_name and category and colour and date_lost):
            flash("Item name, category, colour, and date lost are required.", "error")
            return redirect(url_for("student_report_lost"))

        try:
            image = save_upload(request.files.get("image"))
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("student_report_lost"))

        db = get_db()
        student = current_student()
        doc = {
            "student_oid": session["student_oid"],
            "student_id": student["student_id"],
            "student_name": student["full_name"],
            "student_email": student["email"],
            "item_name": item_name,
            "category": category,
            "colour": colour,
            "date_lost": date_lost,
            "location": location,
            "description": description,
            "image": image,
            "status": "Pending",
            "history": [{
                "status": "Pending",
                "changed_by": student["email"],
                "changed_at": utcnow(),
                "note": "Report submitted by student.",
            }],
            "created_at": utcnow(),
            "updated_at": utcnow(),
        }
        result = db.lost_reports.insert_one(doc)

        # Notify admin
        notify("admin", None, "New Lost-Item Report",
               f"{student['full_name']} ({student['student_id']}) reported a lost {item_name}.",
               report_id=str(result.inserted_id))
        log_activity(student["email"], "report_created", str(result.inserted_id))
        flash("Report submitted successfully. The logistics office will investigate.", "success")
        return redirect(url_for("student_my_reports"))
    return render("student_report_form.html")


@app.route("/student/my-reports")
@login_required_student
def student_my_reports():
    db = get_db()
    sid = session["student_oid"]
    reports = []
    for r in db.lost_reports.find({"student_oid": sid}).sort("created_at", -1):
        rr = serialize(r)
        rr["badge"] = status_badge(r["status"])
        reports.append(rr)
    return render("student_my_reports.html", reports=reports)


@app.route("/student/reports/<report_id>")
@login_required_student
def student_report_detail(report_id):
    db = get_db()
    try:
        r = db.lost_reports.find_one({"_id": ObjectId(report_id), "student_oid": session["student_oid"]})
    except InvalidId:
        r = None
    if not r:
        abort(404)
    rr = serialize(r)
    rr["badge"] = status_badge(r["status"])
    history = []
    for h in r.get("history", []):
        history.append({
            "status": h.get("status"),
            "changed_at": h["changed_at"].strftime("%Y-%m-%d %H:%M") if isinstance(h.get("changed_at"), datetime) else h.get("changed_at"),
            "changed_by": h.get("changed_by"),
            "note": h.get("note"),
        })
    return render("student_report_detail.html", report=rr, history=history)


@app.route("/student/found-items")
@login_required_student
def student_found_items():
    db = get_db()
    items = []
    for it in db.found_items.find({"status": {"$ne": "Collected"}}).sort("created_at", -1):
        ii = serialize(it)
        ii["badge"] = status_badge(it.get("status", "Stored"))
        items.append(ii)
    return render("student_found_items.html", items=items)


@app.route("/student/notifications")
@login_required_student
def student_notifications():
    db = get_db()
    sid = session["student_oid"]
    notifications = [serialize(n) for n in db.notifications.find(
        {"recipient_type": "student", "recipient_id": sid}
    ).sort("created_at", -1)]
    # mark as read
    db.notifications.update_many(
        {"recipient_type": "student", "recipient_id": sid, "read": False},
        {"$set": {"read": True}}
    )
    return render("student_notifications.html", notifications=notifications)


@app.route("/student/profile")
@login_required_student
def student_profile():
    student = current_student()
    if not student:
        return redirect(url_for("student_login"))
    return render("student_profile.html", student=serialize(student))


@app.route("/student/change-password", methods=["POST"])
@login_required_student
def student_change_password():
    current = request.form.get("current") or ""
    new = request.form.get("new") or ""
    confirm = request.form.get("confirm") or ""
    if new != confirm or len(new) < 6:
        flash("New passwords do not match or are too short (min 6).", "error")
        return redirect(url_for("student_profile"))
    db = get_db()
    student = current_student()
    if not student or not verify_password(current, student["password_hash"]):
        flash("Current password is incorrect.", "error")
        return redirect(url_for("student_profile"))
    db.students.update_one({"_id": student["_id"]},
                           {"$set": {"password_hash": hash_password(new)}})
    log_activity(student["email"], "password_changed", student["student_id"])
    flash("Password updated successfully.", "success")
    return redirect(url_for("student_profile"))


# ============================================================
# ADMIN AUTH & PAGES
# ============================================================
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        if verify_admin(email, password):
            admin_session()
            log_activity(ADMIN_EMAIL, "admin_login", "admin")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid administrator credentials.", "error")
        return redirect(url_for("admin_login"))
    return render("admin_login.html")


@app.route("/admin/dashboard")
@login_required_admin
def admin_dashboard():
    db = get_db()
    total = db.lost_reports.count_documents({})
    stats = {
        "total_reports": total,
        "pending": db.lost_reports.count_documents({"status": "Pending"}),
        "found": db.lost_reports.count_documents({"status": "Found"}),
        "returned": db.lost_reports.count_documents({"status": "Returned"}),
        "unresolved": db.lost_reports.count_documents({"status": "Unresolved"}),
        "found_items_registered": db.found_items.count_documents({}),
    }
    recent = []
    for r in db.lost_reports.find().sort("created_at", -1).limit(8):
        rr = serialize(r)
        rr["badge"] = status_badge(r["status"])
        recent.append(rr)
    return render("admin_dashboard.html", stats=stats, recent=recent)


@app.route("/admin/reports")
@login_required_admin
def admin_reports():
    db = get_db()
    q = (request.args.get("q") or "").strip()
    status = (request.args.get("status") or "").strip()
    query = {}
    if q:
        query["$or"] = [
            {"item_name": {"$regex": q, "$options": "i"}},
            {"category": {"$regex": q, "$options": "i"}},
            {"student_id": {"$regex": q, "$options": "i"}},
            {"location": {"$regex": q, "$options": "i"}},
        ]
    if status:
        query["status"] = status
    reports = []
    for r in db.lost_reports.find(query).sort("created_at", -1):
        rr = serialize(r)
        rr["badge"] = status_badge(r["status"])
        rr["student_sid"] = r.get("student_id", "")
        reports.append(rr)
    return render("admin_reports.html", reports=reports, q=q, status=status)


@app.route("/admin/reports/<report_id>")
@login_required_admin
def admin_report_detail(report_id):
    db = get_db()
    try:
        r = db.lost_reports.find_one({"_id": ObjectId(report_id)})
    except InvalidId:
        r = None
    if not r:
        abort(404)
    rr = serialize(r)
    rr["badge"] = status_badge(r["status"])
    rr["student_sid"] = r.get("student_id", "")
    history = []
    for h in r.get("history", []):
        history.append({
            "status": h.get("status"),
            "changed_at": h["changed_at"].strftime("%Y-%m-%d %H:%M") if isinstance(h.get("changed_at"), datetime) else h.get("changed_at"),
            "changed_by": h.get("changed_by"),
            "note": h.get("note"),
        })
    found_items = []
    for it in db.found_items.find({"status": {"$ne": "Collected"}}).sort("created_at", -1):
        ii = serialize(it)
        found_items.append(ii)
    return render("admin_report_detail.html", report=rr, history=history, found_items=found_items)


@app.route("/admin/reports/<report_id>/status", methods=["POST"])
@login_required_admin
def admin_update_status(report_id):
    db = get_db()
    try:
        r = db.lost_reports.find_one({"_id": ObjectId(report_id)})
    except InvalidId:
        r = None
    if not r:
        abort(404)
    new_status = request.form.get("status")
    note = (request.form.get("note") or "").strip()
    if new_status not in ("Pending", "Found", "Returned", "Unresolved"):
        flash("Invalid status.", "error")
        return redirect(url_for("admin_report_detail", report_id=report_id))
    db.lost_reports.update_one({"_id": r["_id"]}, {
        "$set": {"status": new_status, "updated_at": utcnow()},
        "$push": {"history": {
            "status": new_status,
            "changed_by": session.get("admin_email", "admin"),
            "changed_at": utcnow(),
            "note": note or f"Status changed to {new_status}.",
        }},
    })
    notify("student", r["student_oid"], f"Report Update: {new_status}",
           f"Your report for '{r['item_name']}' is now {new_status}. {note}",
           report_id=str(r["_id"]))
    log_activity(session.get("admin_email", "admin"), f"status_updated_to_{new_status}", str(r["_id"]))
    flash(f"Status updated to {new_status} and student notified.", "success")
    return redirect(url_for("admin_report_detail", report_id=report_id))


@app.route("/admin/reports/<report_id>/edit", methods=["POST"])
@login_required_admin
def admin_edit_report(report_id):
    db = get_db()
    try:
        r = db.lost_reports.find_one({"_id": ObjectId(report_id)})
    except InvalidId:
        r = None
    if not r:
        abort(404)
    update = {
        "item_name": (request.form.get("item_name") or r["item_name"]).strip(),
        "category": (request.form.get("category") or r["category"]).strip(),
        "colour": (request.form.get("colour") or r["colour"]).strip(),
        "date_lost": (request.form.get("date_lost") or r["date_lost"]).strip(),
        "location": (request.form.get("location") or "").strip(),
        "description": (request.form.get("description") or "").strip(),
        "updated_at": utcnow(),
    }
    db.lost_reports.update_one({"_id": r["_id"]}, {"$set": update})
    log_activity(session.get("admin_email", "admin"), "report_edited", str(r["_id"]))
    flash("Report information updated.", "success")
    return redirect(url_for("admin_report_detail", report_id=report_id))


@app.route("/admin/reports/<report_id>/delete", methods=["POST"])
@login_required_admin
def admin_delete_report(report_id):
    db = get_db()
    try:
        r = db.lost_reports.find_one({"_id": ObjectId(report_id)})
    except InvalidId:
        r = None
    if not r:
        abort(404)
    db.lost_reports.delete_one({"_id": r["_id"]})
    notify("student", r["student_oid"], "Report Deleted",
           f"Your lost-item report for '{r['item_name']}' was removed by the logistics office.")
    log_activity(session.get("admin_email", "admin"), "report_deleted", str(r["_id"]))
    flash("Report deleted.", "success")
    return redirect(url_for("admin_reports"))


@app.route("/admin/reports/<report_id>/match", methods=["POST"])
@login_required_admin
def admin_match_found(report_id):
    db = get_db()
    try:
        r = db.lost_reports.find_one({"_id": ObjectId(report_id)})
    except InvalidId:
        r = None
    if not r:
        abort(404)
    found_id = request.form.get("found_id")
    message = (request.form.get("message") or "").strip()
    if not found_id:
        flash("Please select a found item to match.", "error")
        return redirect(url_for("admin_report_detail", report_id=report_id))
    try:
        fi = db.found_items.find_one({"_id": ObjectId(found_id)})
    except InvalidId:
        fi = None
    if not fi:
        flash("Found item not found.", "error")
        return redirect(url_for("admin_report_detail", report_id=report_id))

    db.lost_reports.update_one({"_id": r["_id"]}, {
        "$set": {"status": "Found", "matched_found_id": str(fi["_id"]), "updated_at": utcnow()},
        "$push": {"history": {
            "status": "Found",
            "changed_by": session.get("admin_email", "admin"),
            "changed_at": utcnow(),
            "note": f"Matched with found item '{fi['item_name']}'.",
        }},
    })
    db.found_items.update_one({"_id": fi["_id"]},
                              {"$set": {"status": "Matched", "updated_at": utcnow()}})

    default_msg = (f"Good news! Your '{r['item_name']}' appears to have been found. "
                   f"Please visit the Logistics Office to collect it. "
                   f"Storage location: {fi.get('storage_location','—')}.")
    notify("student", r["student_oid"], "Item Matched — Ready for Collection",
           message or default_msg, report_id=str(r["_id"]))
    log_activity(session.get("admin_email", "admin"), "report_matched", str(r["_id"]))
    flash("Match confirmed and student notified.", "success")
    return redirect(url_for("admin_report_detail", report_id=report_id))


@app.route("/admin/reports/<report_id>/collected", methods=["POST"])
@login_required_admin
def admin_mark_collected(report_id):
    db = get_db()
    try:
        r = db.lost_reports.find_one({"_id": ObjectId(report_id)})
    except InvalidId:
        r = None
    if not r:
        abort(404)
    db.lost_reports.update_one({"_id": r["_id"]}, {
        "$set": {"status": "Returned", "updated_at": utcnow()},
        "$push": {"history": {
            "status": "Returned",
            "changed_by": session.get("admin_email", "admin"),
            "changed_at": utcnow(),
            "note": "Item collected by student.",
        }},
    })
    if r.get("matched_found_id"):
        try:
            db.found_items.update_one({"_id": ObjectId(r["matched_found_id"])},
                                      {"$set": {"status": "Collected", "updated_at": utcnow()}})
        except InvalidId:
            pass
    notify("student", r["student_oid"], "Item Collected — Thank You",
           f"Your report for '{r['item_name']}' has been marked as Returned. Thank you!")
    log_activity(session.get("admin_email", "admin"), "item_returned", str(r["_id"]))
    flash("Marked as returned.", "success")
    return redirect(url_for("admin_report_detail", report_id=report_id))


# ---------- Admin Found Items ----------
@app.route("/admin/found-items")
@login_required_admin
def admin_found_items():
    db = get_db()
    items = []
    for it in db.found_items.find().sort("created_at", -1):
        ii = serialize(it)
        ii["badge"] = status_badge(it.get("status", "Stored"))
        items.append(ii)
    return render("admin_found_items.html", items=items)


@app.route("/admin/found-items/register", methods=["POST"])
@login_required_admin
def admin_register_found():
    item_name = (request.form.get("item_name") or "").strip()
    category = (request.form.get("category") or "").strip()
    colour = (request.form.get("colour") or "").strip()
    date_found = (request.form.get("date_found") or "").strip()
    location_found = (request.form.get("location_found") or "").strip()
    storage = (request.form.get("storage_location") or "").strip()
    submitted_by = (request.form.get("submitted_by") or "").strip()
    description = (request.form.get("description") or "").strip()

    if not (item_name and category and colour and date_found and location_found and storage):
        flash("All required fields must be filled.", "error")
        return redirect(url_for("admin_found_items"))
    try:
        image = save_upload(request.files.get("image"))
    except ValueError as e:
        flash(str(e), "error")
        return redirect(url_for("admin_found_items"))

    db = get_db()
    doc = {
        "item_name": item_name,
        "category": category,
        "colour": colour,
        "date_found": date_found,
        "location_found": location_found,
        "description": description,
        "image": image,
        "storage_location": storage,
        "submitted_by": submitted_by,
        "status": "Stored",
        "created_at": utcnow(),
        "updated_at": utcnow(),
    }
    result = db.found_items.insert_one(doc)
    log_activity(session.get("admin_email", "admin"), "found_item_registered", str(result.inserted_id))
    flash("Found item registered.", "success")
    return redirect(url_for("admin_found_items"))


@app.route("/admin/found-items/<found_id>/edit", methods=["GET", "POST"])
@login_required_admin
def admin_edit_found(found_id):
    db = get_db()
    try:
        it = db.found_items.find_one({"_id": ObjectId(found_id)})
    except InvalidId:
        it = None
    if not it:
        abort(404)
    if request.method == "POST":
        update = {
            "item_name": (request.form.get("item_name") or it["item_name"]).strip(),
            "category": (request.form.get("category") or it["category"]).strip(),
            "colour": (request.form.get("colour") or it["colour"]).strip(),
            "date_found": (request.form.get("date_found") or it["date_found"]).strip(),
            "location_found": (request.form.get("location_found") or it["location_found"]).strip(),
            "storage_location": (request.form.get("storage_location") or it["storage_location"]).strip(),
            "submitted_by": (request.form.get("submitted_by") or "").strip(),
            "description": (request.form.get("description") or "").strip(),
            "status": request.form.get("status") or it.get("status", "Stored"),
            "updated_at": utcnow(),
        }
        try:
            new_img = save_upload(request.files.get("image"))
            if new_img:
                update["image"] = new_img
        except ValueError as e:
            flash(str(e), "error")
            return redirect(url_for("admin_edit_found", found_id=found_id))
        db.found_items.update_one({"_id": it["_id"]}, {"$set": update})
        log_activity(session.get("admin_email", "admin"), "found_item_edited", found_id)
        flash("Found item updated.", "success")
        return redirect(url_for("admin_found_items"))
    ii = serialize(it)
    return render("admin_edit_found.html", item=ii)


@app.route("/admin/found-items/<found_id>/delete", methods=["POST"])
@login_required_admin
def admin_delete_found(found_id):
    db = get_db()
    try:
        it = db.found_items.find_one({"_id": ObjectId(found_id)})
    except InvalidId:
        it = None
    if not it:
        abort(404)
    db.found_items.delete_one({"_id": it["_id"]})
    log_activity(session.get("admin_email", "admin"), "found_item_deleted", found_id)
    flash("Found item deleted.", "success")
    return redirect(url_for("admin_found_items"))


# ---------- Admin Students ----------
@app.route("/admin/students")
@login_required_admin
def admin_students():
    db = get_db()
    q = (request.args.get("q") or "").strip()
    query = {}
    if q:
        query["$or"] = [
            {"full_name": {"$regex": q, "$options": "i"}},
            {"email": {"$regex": q, "$options": "i"}},
            {"student_id": {"$regex": q, "$options": "i"}},
        ]
    students = [serialize(s) for s in db.students.find(query).sort("created_at", -1)]
    return render("admin_students.html", students=students, q=q)


# ---------- Admin Notifications ----------
@app.route("/admin/notifications")
@login_required_admin
def admin_notifications():
    db = get_db()
    notifications = [serialize(n) for n in
                     db.notifications.find({"recipient_type": "admin"}).sort("created_at", -1)]
    db.notifications.update_many(
        {"recipient_type": "admin", "read": False}, {"$set": {"read": True}}
    )
    return render("admin_notifications.html", notifications=notifications)


@app.route("/admin/activity")
@login_required_admin
def admin_activity():
    db = get_db()
    logs = [serialize(a) for a in db.activity_logs.find().sort("created_at", -1).limit(300)]
    return render("admin_activity.html", logs=logs)


# ---------- Error handlers ----------
@app.errorhandler(404)
def not_found(e):
    return render_template_string("""
    <body style="font-family:sans-serif;padding:40px">
    <h1>404 — Not Found</h1>
    <p>The page or resource you requested does not exist.</p>
    <a href="/">Go Home</a></body>"""), 404


@app.errorhandler(413)
def too_large(e):
    flash("Uploaded file is too large (max 4MB).", "error")
    return redirect(request.referrer or url_for("index"))


# ---------- Bootstrap ----------
def bootstrap():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    if not check_connection():
        print("\n[FATAL] Cannot connect to MongoDB at", os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
        print("Start MongoDB first (see instructions).\n")
        raise SystemExit(1)
    init_db()
    print("[OK] MongoDB connected and indexes ensured.")


if __name__ == "__main__":
    import threading, webbrowser
    bootstrap()

    # Open the browser ~1 second after the server starts
    threading.Timer(
        1.0,
        lambda: webbrowser.open("http://127.0.0.1:5000/student/login"),
    ).start()

    app.run(debug=True, host="127.0.0.1", port=5000, use_reloader=False)