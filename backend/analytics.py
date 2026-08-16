"""Analytics calculated from Supabase PostgreSQL data."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timedelta, timezone
from database.db import select


def _complaints(limit=5000):
    return select("complaints", "*", order_by="created_at", descending=True, limit=limit)


def kpi_summary():
    complaints = _complaints()
    resolved = sum(1 for c in complaints if c.get("status") == "Resolved")
    pending = sum(1 for c in complaints if c.get("status") not in ("Resolved", "Rejected"))
    citizens = len(select("users", "id", filters={"role": "citizen"}, limit=5000))
    high_open = sum(1 for c in complaints if c.get("priority") == "High" and c.get("status") not in ("Resolved", "Rejected"))
    durations = []
    for c in complaints:
        if c.get("created_at") and c.get("resolved_at"):
            try:
                a = datetime.fromisoformat(c["created_at"].replace("Z","+00:00"))
                b = datetime.fromisoformat(c["resolved_at"].replace("Z","+00:00"))
                durations.append((b-a).total_seconds()/3600)
            except Exception:
                pass
    avg = sum(durations)/len(durations) if durations else 0
    total = len(complaints)
    return {
        "total_complaints": total, "resolved": resolved, "pending": pending,
        "resolution_rate": round(resolved/total*100,1) if total else 0,
        "citizens": citizens, "high_priority_open": high_open,
        "avg_resolution_hours": round(avg,1),
    }


def _count(field):
    rows = _complaints()
    counts = Counter(r.get(field) or "Unknown" for r in rows)
    return [{"%s" % field: k, "count": v} for k,v in counts.most_common()]


def complaints_by_category():
    return [{"category": k, "count": v} for k,v in Counter(r.get("category") or "Unknown" for r in _complaints()).most_common()]


def complaints_by_status():
    return [{"status": k, "count": v} for k,v in Counter(r.get("status") or "Unknown" for r in _complaints()).most_common()]


def complaints_by_priority():
    return [{"priority": k, "count": v} for k,v in Counter(r.get("priority") or "Unknown" for r in _complaints()).most_common()]


def complaints_by_ward():
    return [{"ward": k, "count": v} for k,v in Counter(r.get("ward") for r in _complaints() if r.get("ward")).most_common()]


def complaints_daily_trend(days=30):
    cutoff = datetime.now(timezone.utc) - timedelta(days=int(days))
    counts = Counter()
    for r in _complaints():
        try:
            dt = datetime.fromisoformat(r["created_at"].replace("Z","+00:00"))
            if dt >= cutoff:
                counts[dt.date().isoformat()] += 1
        except Exception:
            pass
    return [{"day": k, "count": v} for k,v in sorted(counts.items())]


def complaints_monthly_trend():
    counts = Counter()
    for r in _complaints():
        try:
            dt = datetime.fromisoformat(r["created_at"].replace("Z","+00:00"))
            counts[dt.strftime("%Y-%m")] += 1
        except Exception:
            pass
    return [{"month": k, "count": v} for k,v in sorted(counts.items())]


def officer_performance():
    officers = select("users", "id,full_name", filters={"role": "officer"}, limit=500)
    complaints = _complaints()
    result=[]
    for officer in officers:
        assigned=[c for c in complaints if c.get("assigned_officer_id")==officer["id"]]
        result.append({"officer": officer["full_name"], "assigned": len(assigned),
                        "resolved": sum(1 for c in assigned if c.get("status")=="Resolved")})
    return result
