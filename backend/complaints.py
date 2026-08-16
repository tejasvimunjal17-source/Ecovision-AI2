"""Supabase-backed complaint lifecycle and rewards."""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from database.db import insert, select, get_one, update
from config import settings

logger = logging.getLogger("ecovision.complaints")


def _now():
    return datetime.now(timezone.utc).isoformat()


def create_complaint(user_id, category, description, ai_description="", ai_predicted_category="",
                     ai_confidence=None, priority="Medium", image_path="", latitude=None,
                     longitude=None, ward="", address_text=""):
    row = insert("complaints", {
        "user_id": user_id, "category": category,
        "ai_predicted_category": ai_predicted_category,
        "ai_confidence": ai_confidence, "description": description,
        "ai_description": ai_description, "priority": priority,
        "status": "Submitted", "image_path": image_path,
        "latitude": latitude, "longitude": longitude,
        "ward": ward, "address_text": address_text,
        "created_at": _now(), "updated_at": _now(),
    })
    if not row:
        raise RuntimeError("Supabase did not return the complaint.")
    complaint_id = row["id"]
    _add_timeline(complaint_id, "Submitted", "Complaint submitted by citizen", user_id)
    award_points(user_id, settings.REWARD_POINTS["complaint_submitted"], "Complaint submitted")
    return complaint_id


def _add_timeline(complaint_id, status, note, changed_by):
    insert("complaint_timeline", {
        "complaint_id": complaint_id, "status": status,
        "note": note, "changed_by": changed_by, "created_at": _now()
    })


def get_complaint(complaint_id):
    return get_one("complaints", {"id": complaint_id})


def get_user_complaints(user_id, limit=100):
    return select("complaints", filters={"user_id": user_id},
                  order_by="created_at", descending=True, limit=limit)


def get_all_complaints(status=None, ward=None, category=None, limit=500):
    filters = {}
    if status and status != "All": filters["status"] = status
    if ward and ward != "All": filters["ward"] = ward
    if category and category != "All": filters["category"] = category
    rows = select("complaints", filters=filters, order_by="created_at", descending=True, limit=limit)
    user_ids = {r.get("user_id") for r in rows if r.get("user_id") is not None}
    users = {}
    for uid in user_ids:
        u = get_one("users", {"id": uid}, "id,full_name")
        if u: users[uid] = u.get("full_name", "")
    for r in rows:
        r["citizen_name"] = users.get(r.get("user_id"), "Unknown")
    return rows


def get_timeline(complaint_id):
    return select("complaint_timeline", filters={"complaint_id": complaint_id},
                  order_by="created_at", descending=False, limit=500)


def update_status(complaint_id, new_status, changed_by, note=""):
    data = {"status": new_status, "updated_at": _now()}
    if new_status == "Resolved":
        data["resolved_at"] = _now()
    update("complaints", {"id": complaint_id}, data)
    if new_status == "Resolved":
        complaint = get_complaint(complaint_id)
        if complaint:
            award_points(complaint["user_id"], settings.REWARD_POINTS["complaint_resolved_bonus"],
                         "Complaint resolved bonus")
    _add_timeline(complaint_id, new_status, note, changed_by)


def assign_officer(complaint_id, officer_id, worker_name="", changed_by=None):
    update("complaints", {"id": complaint_id}, {
        "assigned_officer_id": officer_id, "assigned_worker": worker_name,
        "status": "Assigned", "updated_at": _now()
    })
    _add_timeline(
        complaint_id, "Assigned",
        f"Assigned to officer #{officer_id}" + (f" / worker {worker_name}" if worker_name else ""),
        changed_by,
    )


def award_points(user_id, points, reason):
    insert("rewards", {"user_id": user_id, "points": points, "reason": reason, "created_at": _now()})
    user = get_one("users", {"id": user_id}, "id,reward_points")
    if user:
        update("users", {"id": user_id}, {"reward_points": int(user.get("reward_points") or 0) + points})


def get_user_rewards(user_id):
    return select("rewards", filters={"user_id": user_id}, order_by="created_at", descending=True, limit=500)


def get_leaderboard(limit=20):
    rows = select("users", "full_name,ward,reward_points",
                  filters={"role": "citizen"}, order_by="reward_points", descending=True, limit=limit)
    return rows


def get_officers():
    return select("users", "id,full_name,ward",
                  filters={"role": "officer", "is_active": True}, order_by="full_name", descending=False, limit=500)


def get_wards():
    rows = select("complaints", "ward", order_by="ward", descending=False, limit=1000)
    return sorted({r["ward"] for r in rows if r.get("ward")})
