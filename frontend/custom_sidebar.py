"""EcoVision navigation drawer.

The native Streamlit multipage navigation is hidden. Logged-out pages have no
sidebar at all. After authentication, this drawer becomes the application's
real sidebar, similar to the LearnMate architecture.
"""
from __future__ import annotations
import streamlit as st
from streamlit_option_menu import option_menu

_DRAWER_WIDTH = "280px"
_DRAWER_MOBILE = "82vw"

USER_NAV = [
    ("🏠 Dashboard", "pages/3_🏠_Citizen_Dashboard.py"),
    ("📢 Report Waste", "pages/4_📢_Report_Waste.py"),
    ("📜 Complaint History", "pages/5_📜_Complaint_History.py"),
    ("🏆 Rewards", "pages/6_🏆_Rewards.py"),
    ("🧑‍💼 Officer Dashboard", "pages/7_🧑‍💼_Officer_Dashboard.py"),
    ("♻️ Recycling Guide", "pages/10_♻️_Recycling_Guide.py"),
    ("🌍 Carbon Calculator", "pages/11_🌍_Carbon_Calculator.py"),
    ("📈 Dashboard Generator", "pages/12_📈_Dashboard_Generator.py"),
    ("📍 Recycling Centres", "pages/13_📍_Recycling_Centres.py"),
    ("🌱 Awareness Hub", "pages/14_🌱_Awareness_Hub.py"),
    ("🎓 Certifications & Jobs", "pages/15_🎓_Certifications_and_Jobs.py"),
    ("📄 Reports", "pages/16_📄_Reports.py"),
    ("ℹ️ About & Contact", "pages/17_ℹ️_About_Contact.py"),
    ("🌿 Prakriti AI", "pages/9_🤖_Prakriti_AI_Connect.py"),
]


def _role_nav():
    user = st.session_state.get("user") or {}
    role = user.get("role", "citizen")
    if role == "officer":
        return [
            ("🧑‍💼 Officer Dashboard", "pages/7_🧑‍💼_Officer_Dashboard.py"),
            ("📢 Report Waste", "pages/4_📢_Report_Waste.py"),
            ("♻️ Recycling Guide", "pages/10_♻️_Recycling_Guide.py"),
            ("🌍 Carbon Calculator", "pages/11_🌍_Carbon_Calculator.py"),
            ("📈 Dashboard Generator", "pages/12_📈_Dashboard_Generator.py"),
            ("📍 Recycling Centres", "pages/13_📍_Recycling_Centres.py"),
            ("🌱 Awareness Hub", "pages/14_🌱_Awareness_Hub.py"),
            ("🎓 Certifications & Jobs", "pages/15_🎓_Certifications_and_Jobs.py"),
            ("📄 Reports", "pages/16_📄_Reports.py"),
            ("ℹ️ About & Contact", "pages/17_ℹ️_About_Contact.py"),
            ("🌿 Prakriti AI", "pages/9_🤖_Prakriti_AI_Connect.py"),
        ]
    return [
        ("🏠 Dashboard", "pages/3_🏠_Citizen_Dashboard.py"),
        ("📢 Report Waste", "pages/4_📢_Report_Waste.py"),
        ("📜 Complaint History", "pages/5_📜_Complaint_History.py"),
        ("🏆 Rewards", "pages/6_🏆_Rewards.py"),
        ("♻️ Recycling Guide", "pages/10_♻️_Recycling_Guide.py"),
        ("🌍 Carbon Calculator", "pages/11_🌍_Carbon_Calculator.py"),
        ("📈 Dashboard Generator", "pages/12_📈_Dashboard_Generator.py"),
        ("📍 Recycling Centres", "pages/13_📍_Recycling_Centres.py"),
        ("🌱 Awareness Hub", "pages/14_🌱_Awareness_Hub.py"),
        ("🎓 Certifications & Jobs", "pages/15_🎓_Certifications_and_Jobs.py"),
        ("📄 Reports", "pages/16_📄_Reports.py"),
        ("ℹ️ About & Contact", "pages/17_ℹ️_About_Contact.py"),
        ("🌿 Prakriti AI", "pages/9_🤖_Prakriti_AI_Connect.py"),
    ]


def _sidebar_css(open_state: bool):
    transform = "translateX(0)" if open_state else "translateX(-100%)"
    margin = _DRAWER_WIDTH if open_state else "0px"
    st.markdown(f"""
    <style>
      section[data-testid="stSidebar"] {{
        position: fixed !important; left: 0 !important; top: 0 !important;
        height: 100vh !important; width: {_DRAWER_WIDTH} !important;
        min-width: {_DRAWER_WIDTH} !important; max-width: {_DRAWER_WIDTH} !important;
        z-index: 999998 !important; transform: {transform};
        transition: transform .25s ease !important; overflow-y: auto !important;
        background: #0b2524 !important;
      }}
      section[data-testid="stSidebarNav"] {{ display:none !important; }}
      div[data-testid="stSidebarHeader"] {{ display:block !important; }}
      div[class*="st-key-eco_nav_toggle"] {{
        position: fixed !important; left: 14px; top: 14px; z-index: 1000000;
      }}
      div[class*="st-key-eco_nav_toggle"] button {{
        width:44px !important; height:44px !important; border-radius:14px !important;
        padding:0 !important; box-shadow:0 8px 24px rgba(0,0,0,.35) !important;
      }}
      @media (min-width: 641px) {{
        section[data-testid="stMain"], .main {{
          margin-left: {margin} !important;
          width: calc(100% - {margin}) !important;
          max-width: calc(100% - {margin}) !important;
          box-sizing:border-box !important;
          transition: margin-left .25s ease, width .25s ease;
        }}
      }}
      @media (max-width:640px) {{
        section[data-testid="stSidebar"] {{
          width:{_DRAWER_MOBILE} !important; min-width:{_DRAWER_MOBILE} !important;
          max-width:{_DRAWER_MOBILE} !important;
        }}
      }}
      html, body, .stApp, div[data-testid="stAppViewContainer"] {{ overflow-x:hidden; }}
      div[data-testid="stToolbarActions"], .stAppDeployButton {{
        display:none !important;
      }}
      div[data-testid="stSidebarCollapseButton"], div[data-testid="collapsedControl"] {{
        display:none !important;
      }}
      .block-container {{ padding-top: 4.5rem !important; }}
    </style>
    """, unsafe_allow_html=True)


def render_custom_sidebar_controls():
    st.session_state.setdefault("sidebar_open", True)
    with st.container(key="eco_nav_toggle"):
        if st.button("🌎", key="eco_nav_toggle_button", help="Open / close EcoVision navigation"):
            st.session_state["sidebar_open"] = not st.session_state["sidebar_open"]
            st.rerun()
    _sidebar_css(st.session_state["sidebar_open"])

    nav = _role_nav()
    labels = [x[0] for x in nav]
    pages = {x[0]: x[1] for x in nav}
    current = st.session_state.get("nav_page", labels[0])
    if current not in labels:
        current = labels[0]

    with st.sidebar:
        user = st.session_state.get("user") or {}
        st.markdown(
            f"<div style='font-size:1.3rem;font-weight:800;'>🌿 EcoVision AI</div>"
            f"<div style='opacity:.72;margin-top:4px;'>Hi, {user.get('full_name','').split()[0]} 👋</div>",
            unsafe_allow_html=True,
        )
        st.divider()
        selected = option_menu(
            menu_title=None,
            options=labels,
            default_index=labels.index(current),
            key="eco_main_nav",
            styles={
                "container": {"padding":"0", "background-color":"transparent"},
                "icon": {"color":"#5eead4", "font-size":"16px"},
                "nav-link": {"font-size":"13px","text-align":"left","margin":"3px 0","border-radius":"10px"},
                "nav-link-selected": {"background":"linear-gradient(120deg,#10b981,#0ea5a4)","color":"white"},
            },
        )
        if selected != current:
            st.session_state["nav_page"] = selected
            st.switch_page(pages[selected])

        st.divider()
        if st.button("🤖 Open Prakriti AI", use_container_width=True):
            st.session_state["prakriti_open"] = True
            st.rerun()
        if st.button("🛡️ Admin Panel", use_container_width=True):
            st.switch_page("pages/8_🛠️_Admin_Dashboard.py")
        if st.button("🚪 Logout", use_container_width=True):
            from utils.helpers import logout
            logout()
            st.rerun()


def hide_public_sidebar():
    st.markdown("""
    <style>
      section[data-testid="stSidebar"] { display:none !important; }
      div[data-testid="collapsedControl"] { display:none !important; }
      div[data-testid="stToolbarActions"], .stAppDeployButton { display:none !important; }
      .block-container { max-width: 1200px; }
    </style>
    """, unsafe_allow_html=True)


def render_admin_sidebar():
    st.session_state.setdefault("admin_sidebar_open", True)
    transform = "translateX(0)" if st.session_state["admin_sidebar_open"] else "translateX(-100%)"
    st.markdown(f"""
    <style>
      section[data-testid="stSidebar"] {{
        position:fixed !important; left:0 !important; top:0 !important; height:100vh !important;
        width:280px !important; min-width:280px !important; max-width:280px !important;
        z-index:999998 !important; transform:{transform}; transition:transform .25s ease !important;
        background:#0b2524 !important;
      }}
      section[data-testid="stSidebarNav"] {{display:none !important;}}
      div[class*="st-key-admin_nav_toggle"] {{position:fixed !important; left:14px; top:14px; z-index:1000000;}}
      div[class*="st-key-admin_nav_toggle"] button {{width:44px !important;height:44px !important;border-radius:14px !important;padding:0 !important;}}
      @media(min-width:641px){{
        section[data-testid="stMain"],.main{{margin-left:{"280px" if st.session_state["admin_sidebar_open"] else "0px"} !important;
        width:calc(100% - {"280px" if st.session_state["admin_sidebar_open"] else "0px"}) !important;max-width:calc(100% - {"280px" if st.session_state["admin_sidebar_open"] else "0px"}) !important;}}
      }}
      div[data-testid="stToolbarActions"],.stAppDeployButton,div[data-testid="stSidebarCollapseButton"],div[data-testid="collapsedControl"]{{display:none !important;}}
      .block-container{{padding-top:4.5rem !important;}}
    </style>
    """, unsafe_allow_html=True)
    with st.container(key="admin_nav_toggle"):
        if st.button("🛡️", key="admin_nav_toggle_btn", help="Open / close Admin Panel navigation"):
            st.session_state["admin_sidebar_open"] = not st.session_state["admin_sidebar_open"]
            st.rerun()
    options=["Dashboard","Users","Officers","Complaints","Categories","Analytics","Settings"]
    icons=["speedometer2","people","person-badge","clipboard-data","collection","bar-chart","gear"]
    current=st.session_state.get("admin_section","Dashboard")
    with st.sidebar:
        admin=st.session_state.get("admin_user") or {}
        st.markdown(f"<div style='font-size:1.25rem;font-weight:800;'>🛡️ Admin Panel</div><div style='opacity:.7;'>Hi, {admin.get('first_name','')} 👋</div>", unsafe_allow_html=True)
        st.divider()
        selected=option_menu(None,options=options,icons=icons,default_index=options.index(current),key="admin_main_nav",
            styles={"container":{"padding":"0","background-color":"transparent"},"icon":{"color":"#5eead4","font-size":"16px"},
                    "nav-link":{"font-size":"13px","text-align":"left","margin":"3px 0","border-radius":"10px"},
                    "nav-link-selected":{"background":"linear-gradient(120deg,#10b981,#0ea5a4)","color":"white"}})
        if selected != current:
            st.session_state["admin_section"]=selected
            st.rerun()
        st.divider()
        if st.button("🚪 Exit Admin Panel",use_container_width=True):
            st.session_state["admin_user"]=None
            st.session_state["admin_section"]="Dashboard"
            st.rerun()
        if st.button("🏠 Return to User App",use_container_width=True):
            st.switch_page("app.py")
