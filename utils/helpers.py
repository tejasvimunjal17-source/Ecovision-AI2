"""Shared session, navigation, styling and access helpers."""
import streamlit as st
from pathlib import Path
from datetime import datetime
ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


def load_css(public: bool = False, show_chat: bool = True):
    css_path = ASSETS_DIR / "style.css"
    if css_path.exists():
        st.markdown(f"<style>{css_path.read_text()}</style>", unsafe_allow_html=True)

    from frontend.custom_sidebar import hide_public_sidebar, render_custom_sidebar_controls
    if public or not st.session_state.get("user"):
        hide_public_sidebar()
    elif st.session_state.get("user"):
        render_custom_sidebar_controls()
        if show_chat:
            from chatbot.prakriti import render_floating_widget
            render_floating_widget()


def init_session_state():
    defaults = {
        "user": None,
        "theme": "dark",
        "chat_history": [],
        "chat_session_id": datetime.utcnow().strftime("%Y%m%d%H%M%S%f"),
        "prakriti_open": False,
        "prakriti_widget_history": [],
        "nav_page": "🏠 Dashboard",
        "_db_initialized": False,
    }
    for k, v in defaults.items():
        st.session_state.setdefault(k, v)

    if not st.session_state.get("_db_initialized"):
        from database.db import init_db
        try:
            init_db()
            st.session_state["_db_initialized"] = True
        except Exception as exc:
            st.session_state["_db_error"] = str(exc)


def require_login(allowed_roles=None):
    init_session_state()
    if not st.session_state.get("user"):
        load_css(public=True, show_chat=False)
        st.warning("🔒 Please log in to access this page.")
        st.page_link("pages/1_🔐_Login.py", label="Go to Login", icon="🔐")
        st.stop()
    if allowed_roles and st.session_state["user"]["role"] not in allowed_roles:
        st.error("⛔ You don't have permission to view this page.")
        st.stop()


def logout():
    st.session_state["user"] = None
    st.session_state["chat_history"] = []
    st.session_state["prakriti_widget_history"] = []
    st.session_state["prakriti_open"] = False
    st.session_state["nav_page"] = "🏠 Dashboard"
    try:
        if hasattr(st, "user") and getattr(st.user, "is_logged_in", False) and hasattr(st, "logout"):
            st.logout()
    except Exception:
        pass


def status_badge(status: str) -> str:
    colors = {
        "Submitted": "#64748b", "Under Review": "#f59e0b", "Assigned": "#3b82f6",
        "In Progress": "#8b5cf6", "Resolved": "#10b981", "Rejected": "#ef4444",
    }
    color = colors.get(status, "#64748b")
    return f'<span style="background:{color}22;color:{color};padding:4px 12px;border-radius:20px;font-weight:600;font-size:.85em;border:1px solid {color}55;">{status}</span>'


def priority_badge(priority: str) -> str:
    colors = {"Low": "#10b981", "Medium": "#f59e0b", "High": "#ef4444"}
    color = colors.get(priority, "#64748b")
    return f'<span style="background:{color}22;color:{color};padding:4px 12px;border-radius:20px;font-weight:600;font-size:.85em;border:1px solid {color}55;">{priority}</span>'


def toast(message: str, icon: str = "✅"):
    st.toast(message, icon=icon)


def format_datetime(dt_str):
    if not dt_str:
        return "-"
    try:
        dt = datetime.fromisoformat(str(dt_str).replace("Z","+00:00"))
        return dt.astimezone().strftime("%d %b %Y, %I:%M %p")
    except Exception:
        return str(dt_str)
