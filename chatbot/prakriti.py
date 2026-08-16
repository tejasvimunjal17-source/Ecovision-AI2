"""Prakriti AI Connect: bilingual full page + floating widget."""
from __future__ import annotations
import html
from database.db import insert, select, delete
from utils.ai_client import stream_chat_completion
from config import settings
import streamlit as st

SYSTEM_PROMPT_EN = """You are Prakriti AI Connect, a friendly AI Sustainability Assistant for
Indian citizens, built for the {municipality} Smart Waste Management platform.

You ONLY help with:
- Waste segregation (wet/dry/hazardous)
- Plastic recycling and reduction
- Composting at home
- E-waste and battery disposal
- Government / MCG waste policies and guidelines
- How to file or track a waste complaint on this platform
- Sustainable lifestyle tips and climate education

Rules:
- Keep answers concise, practical, and India-specific (mention MCG / Swachh Bharat norms where relevant).
- Use simple language and markdown formatting where helpful.
- Reply in English when the user selects English and in Hindi when the user selects Hindi.
- If asked something unrelated to sustainability/waste/civic topics, politely redirect the conversation.
- Never provide harmful, illegal, or dangerous instructions.
"""

SYSTEM_PROMPT_HI = """आप Prakriti AI Connect हैं, भारतीय नागरिकों के लिए एक मित्रवत AI स्थिरता सहायक,
जो {municipality} स्मार्ट कचरा प्रबंधन प्लेटफ़ॉर्म के लिए बनाया गया है।

आप केवल इनमें मदद करते हैं:
- कचरे का पृथक्करण (गीला/सूखा/खतरनाक)
- प्लास्टिक रीसाइक्लिंग और कमी
- घर पर खाद बनाना
- ई-वेस्ट और बैटरी निपटान
- सरकारी/MCG कचरा नीतियाँ
- इस प्लेटफ़ॉर्म पर शिकायत दर्ज या ट्रैक करना
- टिकाऊ जीवनशैली और जलवायु शिक्षा

नियम:
- संक्षिप्त, व्यावहारिक और भारत-केंद्रित उत्तर दें।
- जब उपयोगकर्ता Hindi चुनता है तो Hindi में और English चुनता है तो English में उत्तर दें।
- असंबंधित प्रश्नों को विनम्रता से sustainability/waste विषय पर वापस लाएं।
- हानिकारक या अवैध निर्देश न दें।
"""


def get_system_prompt(language="English"):
    template = SYSTEM_PROMPT_HI if language.lower().startswith("hi") else SYSTEM_PROMPT_EN
    return template.format(municipality=settings.MUNICIPALITY_NAME)


def build_messages(history, user_message, language="English"):
    return [{"role": "system", "content": get_system_prompt(language)}] + history[-10:] + [
        {"role": "user", "content": user_message}
    ]


def stream_reply(history, user_message, language="English"):
    yield from stream_chat_completion(build_messages(history, user_message, language),
                                      temperature=0.5, max_tokens=600)


def save_message(user_id, session_id, role, message, language="en"):
    if not user_id:
        return
    insert("chat_history", {
        "user_id": user_id, "session_id": session_id,
        "role": role, "message": message, "language": language
    })


def load_history(user_id, session_id, limit=50):
    if not user_id:
        return []
    rows = select("chat_history", "role,message,language",
                  filters={"user_id": user_id, "session_id": session_id},
                  order_by="created_at", descending=False, limit=limit)
    return [{"role": r["role"], "content": r["message"]} for r in rows]


def clear_history(user_id, session_id):
    if user_id:
        delete("chat_history", {"user_id": user_id, "session_id": session_id})


def _render_messages(history):
    chunks=[]
    for msg in history[-8:]:
        css = "chat-bubble-user" if msg["role"]=="user" else "chat-bubble-ai"
        icon = "🧑" if msg["role"]=="user" else "🌿"
        chunks.append(f'<div class="{css}">{icon} {html.escape(msg["content"]).replace(chr(10),"<br>")}</div>')
    return "".join(chunks)


def render_floating_widget():
    """Small IBM SkillsBuild-style floating assistant. No sidebar dependency."""
    if not st.session_state.get("user"):
        return

    st.session_state.setdefault("prakriti_open", False)
    st.session_state.setdefault("prakriti_language", "English")
    st.session_state.setdefault("prakriti_widget_history", [])

    st.markdown("""
    <style>
      div[class*="st-key-prakriti_float_button"] {
        position: fixed !important; right: 22px; bottom: 22px; z-index: 1000001;
      }
      div[class*="st-key-prakriti_float_button"] button {
        border-radius: 999px !important; min-height: 54px !important;
        padding: 0 18px !important; font-weight: 800 !important;
        box-shadow: 0 10px 28px rgba(0,0,0,.35) !important;
      }
      div[class*="st-key-prakriti_float_panel"] {
        position: fixed !important; right: 22px; bottom: 88px; z-index: 1000000;
        width: min(390px, calc(100vw - 32px)); max-height: 68vh;
        overflow: auto; padding: 16px; border-radius: 20px;
        background: rgba(9, 35, 37, .98); border: 1px solid rgba(79, 209, 167, .25);
        box-shadow: 0 20px 55px rgba(0,0,0,.42);
      }
      @media (max-width: 640px) {
        div[class*="st-key-prakriti_float_button"] { right: 12px; bottom: 14px; }
        div[class*="st-key-prakriti_float_panel"] { right: 10px; bottom: 78px; width: calc(100vw - 20px); }
      }
    </style>
    """, unsafe_allow_html=True)

    with st.container(key="prakriti_float_button"):
        label = "🌿 Prakriti AI" if not st.session_state["prakriti_open"] else "✕ Close"
        if st.button(label, key="prakriti_float_toggle", use_container_width=False):
            st.session_state["prakriti_open"] = not st.session_state["prakriti_open"]
            st.rerun()

    if not st.session_state["prakriti_open"]:
        return

    user = st.session_state["user"]
    with st.container(key="prakriti_float_panel"):
        st.markdown("### 🌿 Prakriti AI Connect")
        st.caption("24×7 bilingual sustainability assistant")
        lang = st.radio("Language / भाषा", ["English", "हिंदी (Hindi)"],
                         horizontal=True, key="prakriti_language")
        if st.button("🗑 Clear", key="prakriti_clear"):
            clear_history(user["id"], st.session_state["chat_session_id"])
            st.session_state["prakriti_widget_history"] = []
            st.rerun()

        if not st.session_state["prakriti_widget_history"]:
            st.session_state["prakriti_widget_history"] = load_history(
                user["id"], st.session_state["chat_session_id"], limit=30
            )
        if not st.session_state["prakriti_widget_history"]:
            st.session_state["prakriti_widget_history"] = [{
                "role": "assistant",
                "content": "🌿 Namaste! Ask me about waste segregation, recycling, composting, e-waste or MCG guidelines."
            }]

        st.markdown(_render_messages(st.session_state["prakriti_widget_history"]), unsafe_allow_html=True)

        with st.form("prakriti_float_form", clear_on_submit=True):
            prompt = st.text_input("Ask Prakriti AI Connect…", label_visibility="collapsed")
            send = st.form_submit_button("Send", use_container_width=True)
        if send and prompt.strip():
            st.session_state["prakriti_widget_history"].append({"role":"user","content":prompt.strip()})
            save_message(user["id"], st.session_state["chat_session_id"], "user", prompt.strip(),
                         "hi" if lang.startswith("हिं") else "en")
            response = ""
            for chunk in stream_reply(st.session_state["prakriti_widget_history"][:-1], prompt.strip(), lang):
                response += chunk
            st.session_state["prakriti_widget_history"].append({"role":"assistant","content":response})
            save_message(user["id"], st.session_state["chat_session_id"], "assistant", response,
                         "hi" if lang.startswith("हिं") else "en")
            st.rerun()
