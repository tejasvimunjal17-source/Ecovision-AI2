import streamlit as st
import pandas as pd
import plotly.express as px

from backend.admin_auth import verify_admin_login, AdminAuthError, ensure_bootstrap_admin
from backend.auth import register_user
from database.db import select, get_one, update, insert
from backend import analytics
from config import settings
from utils.helpers import load_css, init_session_state

st.set_page_config(page_title="Admin Panel | EcoVision AI", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")
init_session_state()
st.session_state.setdefault("admin_user", None)
st.session_state.setdefault("admin_section", "Dashboard")

# Completely separate admin authentication and UI.
if not st.session_state.get("admin_user"):
    load_css(public=True, show_chat=False)
    ensure_bootstrap_admin()
    st.markdown(
        '<div class="eco-hero"><h1>🛡️ EcoVision AI Admin Panel</h1>'
        '<p>Separate administrative control center for users, complaints, categories and analytics.</p></div>',
        unsafe_allow_html=True,
    )
    st.info("Admin access is separate from citizen/officer login. Configure ADMIN_EMAIL and ADMIN_PASSWORD once to bootstrap the first admin.")
    with st.form("admin_login"):
        email=st.text_input("Admin Email")
        password=st.text_input("Admin Password",type="password")
        submit=st.form_submit_button("🔐 Sign in to Admin Panel",type="primary",use_container_width=True)
    if submit:
        try:
            st.session_state["admin_user"]=verify_admin_login(email,password).to_dict()
            st.rerun()
        except AdminAuthError as exc:
            st.error(str(exc))
    st.page_link("app.py",label="← Back to EcoVision AI",icon="🌿")
    st.stop()

from frontend.custom_sidebar import render_admin_sidebar
render_admin_sidebar()
st.markdown('<div class="eco-hero"><h1>🛡️ Admin Control Center</h1><p>System-wide management and analytics powered by Supabase PostgreSQL.</p></div>', unsafe_allow_html=True)

section=st.session_state["admin_section"]

if section=="Dashboard":
    k=analytics.kpi_summary()
    cols=st.columns(5)
    for col,(v,label) in zip(cols,[(k["citizens"],"Citizens"),(k["total_complaints"],"Complaints"),(k["resolved"],"Resolved"),(f'{k["resolution_rate"]}%',"Resolution Rate"),(k["high_priority_open"],"High Priority Open")]):
        with col:
            st.markdown(f'<div class="eco-stat"><div class="num">{v}</div><div class="label">{label}</div></div>',unsafe_allow_html=True)
    st.markdown("### 📊 System Overview")
    c1,c2=st.columns(2)
    with c1:
        data=analytics.complaints_by_category()
        if data: st.plotly_chart(px.bar(pd.DataFrame(data),x="category",y="count",title="Complaints by Category"),use_container_width=True)
    with c2:
        data=analytics.complaints_by_status()
        if data: st.plotly_chart(px.pie(pd.DataFrame(data),names="status",values="count",title="Complaint Status",hole=.4),use_container_width=True)

elif section=="Users":
    st.subheader("👥 Citizen Accounts")
    users=select("users","id,full_name,email,phone,ward,reward_points,is_active,auth_provider,created_at",
                 filters={"role":"citizen"},order_by="created_at",descending=True,limit=1000)
    if users:
        st.dataframe(pd.DataFrame(users),use_container_width=True,hide_index=True)
        uid=st.number_input("Citizen ID",min_value=1,step=1)
        if st.button("Toggle Active / Inactive",use_container_width=False):
            u=get_one("users",{"id":uid},"id,is_active")
            if not u: st.error("User not found.")
            else:
                update("users",{"id":uid},{"is_active":not bool(u["is_active"])})
                st.success("User status updated."); st.rerun()
    else: st.info("No citizens registered yet.")

elif section=="Officers":
    st.subheader("🧑‍💼 Officers")
    officers=select("users","id,full_name,email,phone,ward,is_active,created_at",filters={"role":"officer"},order_by="created_at",descending=True,limit=500)
    if officers: st.dataframe(pd.DataFrame(officers),use_container_width=True,hide_index=True)
    with st.form("add_officer"):
        c1,c2=st.columns(2)
        with c1: name=st.text_input("Full Name"); email=st.text_input("Email")
        with c2: phone=st.text_input("Phone"); ward=st.text_input("Assigned Ward")
        password=st.text_input("Temporary Password",type="password",value="Officer@123")
        submit=st.form_submit_button("Add Officer",type="primary")
    if submit:
        ok,result=register_user(name,email,phone,password,ward=ward,role="officer",
                                security_question="What is your favorite city?",security_answer="reset")
        if ok: st.success("Officer created."); st.rerun()
        else: st.error(result)

elif section=="Complaints":
    st.subheader("📋 System-wide Complaints")
    complaints=select("complaints","*",order_by="created_at",descending=True,limit=1000)
    user_ids={c.get("user_id") for c in complaints}
    names={}
    for uid in user_ids:
        u=get_one("users",{"id":uid},"id,full_name,email")
        if u: names[uid]=u["full_name"]
    for c in complaints: c["citizen"]=names.get(c.get("user_id"),"Unknown")
    if complaints: st.dataframe(pd.DataFrame(complaints),use_container_width=True,hide_index=True)
    else: st.info("No complaints submitted yet.")

elif section=="Categories":
    st.subheader("🗂️ Waste Categories")
    cats=select("categories","*",order_by="name",descending=False,limit=100)
    if cats: st.dataframe(pd.DataFrame(cats),use_container_width=True,hide_index=True)
    with st.form("add_category"):
        c1,c2=st.columns(2)
        with c1: name=st.text_input("Category Name"); icon=st.text_input("Icon")
        with c2: desc=st.text_area("Description"); guide=st.text_area("Disposal Guide")
        submit=st.form_submit_button("Add Category")
    if submit and name.strip():
        try:
            insert("categories",{"name":name.strip(),"icon":icon,"description":desc,"disposal_guide":guide,"is_active":True})
            st.success("Category added."); st.rerun()
        except Exception as exc: st.error(f"Could not add category: {exc}")

elif section=="Analytics":
    st.subheader("📈 Smart Analytics")
    for title,data,x,y,kind in [
        ("Category Distribution",analytics.complaints_by_category(),"category","count","bar"),
        ("Ward Distribution",analytics.complaints_by_ward(),"ward","count","bar"),
        ("Monthly Trend",analytics.complaints_monthly_trend(),"month","count","line"),
    ]:
        if data:
            if kind=="line": fig=px.line(pd.DataFrame(data),x=x,y=y,title=title,markers=True)
            else: fig=px.bar(pd.DataFrame(data),x=x,y=y,title=title)
            st.plotly_chart(fig,use_container_width=True)
    st.subheader("Officer Performance")
    perf=analytics.officer_performance()
    if perf: st.dataframe(pd.DataFrame(perf),use_container_width=True,hide_index=True)

elif section=="Settings":
    st.subheader("⚙️ Platform Settings")
    st.write(f"**Municipality:** {settings.MUNICIPALITY_NAME}")
    st.write(f"**Support:** {settings.SUPPORT_EMAIL} · {settings.SUPPORT_PHONE}")
    st.write(f"**AI configured:** {'Yes' if settings.is_ai_configured() else 'No'}")
    st.write(f"**Supabase configured:** {'Yes' if settings.is_supabase_configured() else 'No'}")
    st.caption("Secrets are read from Streamlit Secrets first and .env only for local development. No SQLite database is used.")
