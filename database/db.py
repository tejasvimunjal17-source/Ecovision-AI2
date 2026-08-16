"""
Supabase-only persistence layer for EcoVision AI.

All application data is persisted in Supabase PostgreSQL. SQLite is no longer
used at runtime. Uploaded complaint media is stored in Supabase Storage and
its storage path is recorded in PostgreSQL.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from config import settings

logger = logging.getLogger("ecovision.db")
_client_cache: dict[str, Any] = {}


class SupabaseUnavailableError(RuntimeError):
    pass


def get_client():
    if "client" in _client_cache:
        return _client_cache["client"]
    if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_ROLE_KEY:
        raise SupabaseUnavailableError(
            "Supabase is not configured. Add SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
            "to Streamlit Secrets (or .env locally)."
        )
    try:
        from supabase import create_client
        _client_cache["client"] = create_client(
            settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY
        )
        return _client_cache["client"]
    except Exception as exc:
        raise SupabaseUnavailableError(f"Could not connect to Supabase: {exc}") from exc


def is_supabase_configured() -> bool:
    return bool(settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY)


def init_db():
    """Validate the connection and seed only reference data."""
    client = get_client()
    try:
        rows = client.table("categories").select("id").limit(1).execute().data or []
        if not rows:
            seed_categories()
        centres = client.table("recycling_centres").select("id").limit(1).execute().data or []
        if not centres:
            seed_recycling_centres()
    except Exception as exc:
        raise SupabaseUnavailableError(f"Supabase schema check failed: {exc}") from exc


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def select(table: str, columns: str = "*", filters: dict[str, Any] | None = None,
           order_by: str | None = None, descending: bool = True, limit: int | None = None):
    q = get_client().table(table).select(columns)
    for key, value in (filters or {}).items():
        if value is None:
            q = q.is_(key, "null")
        else:
            q = q.eq(key, value)
    if order_by:
        q = q.order(order_by, desc=descending)
    if limit:
        q = q.limit(limit)
    return q.execute().data or []


def get_one(table: str, filters: dict[str, Any], columns: str = "*"):
    rows = select(table, columns=columns, filters=filters, limit=1)
    return rows[0] if rows else None


def insert(table: str, data: dict[str, Any], returning: str = "*"):
    resp = get_client().table(table).insert(data).execute()
    rows = resp.data or []
    return rows[0] if rows else None


def update(table: str, filters: dict[str, Any], data: dict[str, Any]):
    q = get_client().table(table).update(data)
    for key, value in filters.items():
        q = q.eq(key, value)
    resp = q.execute()
    rows = resp.data or []
    return rows[0] if rows else None


def delete(table: str, filters: dict[str, Any]):
    q = get_client().table(table).delete()
    for key, value in filters.items():
        q = q.eq(key, value)
    return q.execute().data or []


def count(table: str, filters: dict[str, Any] | None = None) -> int:
    q = get_client().table(table).select("id", count="exact")
    for key, value in (filters or {}).items():
        if value is None:
            q = q.is_(key, "null")
        else:
            q = q.eq(key, value)
    resp = q.limit(1).execute()
    return int(resp.count or 0)


def upload_media(file_bytes: bytes, storage_path: str, content_type: str = "application/octet-stream") -> str:
    bucket = settings.SUPABASE_STORAGE_BUCKET
    try:
        storage = get_client().storage.from_(bucket)
        storage.upload(
            storage_path,
            file_bytes,
            {"content-type": content_type, "upsert": False},
        )
        return storage_path
    except Exception as exc:
        raise SupabaseUnavailableError(f"Supabase Storage upload failed: {exc}") from exc


def signed_media_url(storage_path: str, expires_in: int = 3600) -> str | None:
    if not storage_path:
        return None
    try:
        result = get_client().storage.from_(settings.SUPABASE_STORAGE_BUCKET).create_signed_url(
            storage_path, expires_in
        )
        if isinstance(result, dict):
            return result.get("signedURL") or result.get("signedUrl")
        return None
    except Exception:
        logger.exception("Could not create signed media URL")
        return None


def seed_categories():
    defaults = [
        ("Plastic", "Plastic bottles, bags, wrappers, containers", "🧴",
         "Rinse and place in the dry-waste bin; drop bulk plastic at an authorized recycler."),
        ("Organic", "Food scraps, garden waste, biodegradable matter", "🍂",
         "Compost at home or place in the wet-waste (green) bin for municipal composting."),
        ("Paper", "Newspaper, cardboard, cartons, office paper", "📄",
         "Flatten and keep dry; place in the dry-waste bin or sell to a kabadiwala/recycler."),
        ("Glass", "Bottles, jars and glass containers", "🍾",
         "Wrap broken glass safely and keep it separate; send it to an authorized recycler."),
        ("Metal", "Cans, tins, aluminium and scrap metal", "🥫",
         "Keep dry and send to an authorized scrap dealer or recycling centre."),
        ("Mixed", "Mixed or non-segregated household waste", "🗑️",
         "Avoid mixing waste. Separate wet, dry, hazardous and e-waste before disposal."),
        ("E-Waste", "Electronics, chargers, batteries and cables", "🔋",
         "Do not place in household bins. Use an authorized e-waste collection centre."),
        ("Biomedical", "Sanitary and biomedical waste", "🧪",
         "Keep isolated and follow municipal/healthcare disposal guidance."),
        ("Construction", "Concrete, rubble, tiles and construction debris", "🧱",
         "Arrange collection through an authorized construction-waste channel."),
    ]
    for name, desc, icon, guide in defaults:
        try:
            get_client().table("categories").upsert(
                {"name": name, "description": desc, "icon": icon, "disposal_guide": guide, "is_active": True},
                on_conflict="name",
            ).execute()
        except Exception:
            logger.exception("Could not seed category %s", name)


def seed_recycling_centres():
    # Reference rows only; municipalities can replace/extend these in Admin.
    centres = [
        {
            "name": "MCG Waste Management Centre",
            "type": "Municipal",
            "address": "Gurugram, Haryana",
            "ward": "City",
            "latitude": 28.4595,
            "longitude": 77.0266,
            "contact": "",
            "materials_accepted": "Dry waste, plastic, paper",
            "is_active": True,
        },
        {
            "name": "Authorized E-Waste Collection Centre",
            "type": "E-Waste",
            "address": "Gurugram, Haryana",
            "ward": "City",
            "latitude": 28.4595,
            "longitude": 77.0266,
            "contact": "",
            "materials_accepted": "Electronics, batteries, cables",
            "is_active": True,
        },
    ]
    for row in centres:
        try:
            existing = get_one("recycling_centres", {"name": row["name"]})
            if not existing:
                insert("recycling_centres", row)
        except Exception:
            logger.exception("Could not seed recycling centre")
