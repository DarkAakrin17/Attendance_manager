import streamlit as st
import base64
import time
from datetime import datetime
import matplotlib.pyplot as plt
from pymongo import MongoClient, errors
from passlib.context import CryptContext
import os
import math

# ---- Page Configuration ----
st.set_page_config(page_title="Attendance Tracker", layout="centered")

# ---- MONGODB SETUP ----


@st.cache_resource
def init_connection():
    """Initializes a connection to MongoDB, cached for performance."""
    try:
        # st.secrets reads from .streamlit/secrets.toml
        return MongoClient(st.secrets["mongo_uri"])
    except Exception as e:
        st.error(
            f"Failed to connect to MongoDB. Please check your connection string in secrets.toml. Error: {e}")
        return None


client = init_connection()
# Proceed only if the client is not None, otherwise stop the app
if client:
    db = client.get_database()  # The DB name is taken from your connection string
else:
    st.error("Database connection could not be established. The app cannot proceed.")
    st.stop()


# ---- PASSWORD HASHING SETUP ----
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password):
    return pwd_context.hash(password)

# ---- UI & STYLING ----


def add_bg_from_local(image_file):
    """Sets a local image as the background reliably."""
    with open(image_file, "rb") as f:
        data = f.read()
    encoded_string = base64.b64encode(data).decode()
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/png;base64,{encoded_string}");
            background-size: cover; background-position: center;
            background-repeat: no-repeat;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# --- Global CSS for a polished Liquid Glass UI ---
st.markdown("""
    <style>
    /* General Body Font */
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    /* Main Glass Container for all pages */
    .main-container {
        background: rgba(25, 25, 40, 0.75);
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border-radius: 20px; padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        position: relative;
        top:80px;
    }
    /* Login Form Glass Box */
    .auth-container {
        background: rgba(25, 25, 40, 0.75);
        backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
        border-radius: 20px; padding: 2rem;
        border: 1px solid rgba(255, 255, 255, 0.18);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        position: relative;
        top: 55px;
    }
    h1, h2, h3, h4, .stDateInput label { color: white; text-align: center; }
    p, .st-caption { text-align: center; } /* Center paragraph and caption text */
    .st-emotion-cache-16txtl3 { color: rgba(255,255,255,0.7); } /* Streamlit caption color */
    /* Polished Glass Buttons */
    .stButton>button {
        width: 100%; background: rgba(0, 150, 255, 0.4);
        backdrop-filter: blur(10px); border: 1px solid rgba(0, 150, 255, 0.2);
        color: white; font-weight: bold; border-radius: 10px; transition: background 0.3s;
    }
    .stButton>button:hover { background: rgba(0, 150, 255, 0.6); border: 1px solid #007BFF; }
    /* Dashboard List Items */
    .glass-list-item {
        background: rgba(40, 40, 60, 0.7); border-radius: 15px;
        padding: 1.5rem; margin-bottom: 1rem;
        border: 1px solid rgba(255, 255, 255, 0.1);
        position: relative;
        top: 70px;
    }
    /* Statistics Boxes */
    .glass-stat-box {
        background: rgba(0, 0, 0, 0.25); backdrop-filter: blur(5px);
        border-radius: 15px; padding: 1rem; border: 1px solid rgba(255, 255, 255, 0.1);
        color: white; text-align: center;
    }
    .stat-value { font-size: 2.2rem; font-weight: bold; }
    .stat-label { font-size: 0.9rem; text-transform: uppercase; letter-spacing: 1px; }
    /* Analysis Page Subject Cards */
    .glass-subject-row {
        background: rgba(40, 40, 60, 0.7); border-radius: 15px;
        padding: 1.5rem; margin-bottom: 1rem; border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .percentage-display { color: #00DFFC; font-weight: bold; font-size: 1.5rem; }
    /* Styled Tabs */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background-color: rgba(255, 255, 255, 0.1); backdrop-filter: blur(10px);
        border-radius: 10px; border: 1px solid rgba(255, 255, 255, 0.2); color: white;
    }
    .stTabs [data-baseweb="tab"]:hover { background-color: rgba(255, 255, 255, 0.3); }
    .stTabs [aria-selected="true"] { background-color: rgba(0, 150, 255, 0.5); }
    /* Style for the auth toggle buttons */
    .auth-container > div[data-testid="stHorizontalBlock"] > div {
        border: 1px solid rgba(255, 255, 255, 0.3); border-radius: 10px;
    }
    </style>
""", unsafe_allow_html=True)


def get_theme_css(theme):
    """Returns a CSS string based on the selected theme."""
    if theme == "dark":
        return """
            <style>
            /* Dark Theme CSS */
            .main-container, .auth-container, .glass-list-item, .glass-subject-row {
                background: rgba(25, 25, 40, 0.75);
                backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.18);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            }
            h1, h2, h3, h4, .stDateInput label, .st-emotion-cache-16txtl3, body { color: white; text-align: center; }
            .stTextInput > div > div > input { color: white; }
            .stButton>button { background: rgba(0, 150, 255, 0.4); border: 1px solid rgba(0, 150, 255, 0.2); color: white; }
            .stButton>button:hover { background: rgba(0, 150, 255, 0.6); border: 1px solid #007BFF; }
            .stTabs [data-baseweb="tab"], .auth-container > div[data-testid="stHorizontalBlock"] > div { background-color: rgba(255, 255, 255, 0.1); border: 1px solid rgba(255, 255, 255, 0.2); color: white; }
            .stTabs [data-baseweb="tab"]:hover { background-color: rgba(255, 255, 255, 0.3); }
            .stTabs [aria-selected="true"] { background-color: rgba(0, 150, 255, 0.5); }
            </style>
        """
    else:  # Light Theme
        return """
            <style>
            /* Light Theme CSS */
            .main-container, .auth-container, .glass-list-item, .glass-subject-row {
                background: rgba(255, 255, 255, 0.7);
                backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(0, 0, 0, 0.1);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.1);
            }
            h1, h2, h3, h4, .stDateInput label, .st-emotion-cache-16txtl3, body { color: #333; text-align: center; }
            .stTextInput > div > div > input { color: #333; }
            .stButton>button { background: rgba(0, 123, 255, 0.7); border: 1px solid rgba(0, 123, 255, 0.5); color: white; }
            .stButton>button:hover { background: rgba(0, 123, 255, 0.9); border: 1px solid #0056b3; }
            .stTabs [data-baseweb="tab"], .auth-container > div[data-testid="stHorizontalBlock"] > div { background-color: rgba(0, 0, 0, 0.05); border: 1px solid rgba(0, 0, 0, 0.1); color: #333; }
            .stTabs [data-baseweb="tab"]:hover { background-color: rgba(0, 0, 0, 0.1); }
            .stTabs [aria-selected="true"] { background-color: rgba(0, 123, 255, 0.2); }
            .percentage-display { color: #007BFF; }
            h1, .stMarkdown h1 { color: rgb(128,128,128); }
            </style>
        """


# ---- Main Application Logic ----
script_dir = os.path.dirname(os.path.abspath(__file__))
image_dark_path = os.path.join(script_dir, "image_dark.png")
image_light_path = os.path.join(script_dir, "image_light.png")

# --- Session State for UI Control ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"
if "auth_page" not in st.session_state:
    st.session_state["auth_page"] = "Login"
if "theme" not in st.session_state:
    st.session_state.theme = "dark"  # Default to dark theme

# Apply the selected theme and background
try:
    if st.session_state.theme == "dark":
        add_bg_from_local(image_dark_path)
    else:
        add_bg_from_local(image_light_path)
except FileNotFoundError:
    st.warning(
        "A theme background image is missing. Please ensure 'image_dark.png' and 'image_light.png' are present.")

st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)

# --- Session State for UI Control ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "page" not in st.session_state:
    st.session_state["page"] = "dashboard"
if "auth_page" not in st.session_state:
    st.session_state["auth_page"] = "Login"

# --- 1. AUTHENTICATION PAGE (Login & Sign Up) ---
if not st.session_state["authenticated"]:
    st.markdown('<div class="auth-container">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    if col1.button("Login", use_container_width=True):
        st.session_state.auth_page = "Login"
        st.rerun()
    if col2.button("Sign Up", use_container_width=True):
        st.session_state.auth_page = "Sign Up"
        st.rerun()
    st.divider()

    if st.session_state.auth_page == "Login":
        st.markdown("<h2>Login</h2>", unsafe_allow_html=True)
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login", key="login_button"):
            user_data = db.users.find_one({"_id": username})
            if user_data and verify_password(password, user_data["password"]):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    elif st.session_state.auth_page == "Sign Up":
        st.markdown("<h2>Sign Up</h2>", unsafe_allow_html=True)
        new_username = st.text_input("New Username", key="signup_user")
        new_password = st.text_input(
            "New Password", type="password", key="signup_pass")
        confirm_password = st.text_input(
            "Confirm Password", type="password", key="signup_confirm")
        if st.button("Create Account", key="create_button"):
            if not new_username or not new_password or not confirm_password:
                st.warning("Please fill out all fields.")
            elif new_password != confirm_password:
                st.error("Passwords do not match.")
            else:
                if db.users.find_one({"_id": new_username}):
                    st.error("Username already exists.")
                else:
                    hashed_pass = hash_password(new_password)
                    db.users.insert_one(
                        {"_id": new_username, "password": hashed_pass})
                    st.success("Account created! Logging you in...")
                    st.session_state["authenticated"] = True
                    st.session_state["username"] = new_username
                    time.sleep(1.5)
                    st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

# --- 2. MAIN APPLICATION (after login) ---
else:
    DAYS_OF_WEEK = ["Monday", "Tuesday", "Wednesday",
                    "Thursday", "Friday", "Saturday"]

    # --- PAGE ROUTER ---

    # 2A. TIMETABLE CREATION/EDIT PAGE
    if st.session_state.page in ["new_timetable", "edit_timetable"]:
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        is_edit_mode = st.session_state.page == "edit_timetable"
        page_title = "✏️ Edit Timetable" if is_edit_mode else "🗓️ Create New Timetable"
        list_name = st.session_state.get(
            "selected_list", "") if is_edit_mode else ""

        st.markdown(f"<h1>{page_title}</h1>", unsafe_allow_html=True)

        if is_edit_mode:
            st.markdown(f"<h2>{list_name}</h2>", unsafe_allow_html=True)
            timetable_doc = db.timetables.find_one({"_id": list_name})
            default_is_public = timetable_doc.get("is_public", True)
        else:
            list_name = st.text_input("Semester Name", key="new_list_name",
                                      label_visibility="collapsed", placeholder="Enter Semester Name")
            default_is_public = True

        is_public = st.toggle("Make this timetable public?", value=default_is_public,
                              help="Public timetables are visible to all users. Private ones are only visible to you.")
        st.divider()

        if 'form_step' not in st.session_state:
            st.session_state.form_step = 1

        if st.session_state.form_step == 1:
            st.markdown("<h3>Step 1: Define All Subjects</h3>",
                        unsafe_allow_html=True)
            if 'subject_list' not in st.session_state:
                st.session_state.subject_list = [""]
            for i in range(len(st.session_state.subject_list)):
                st.session_state.subject_list[i] = st.text_input(
                    f"Subject {i+1}", st.session_state.subject_list[i], key=f"subj_{i}")
            st.divider()
            col1, col2, col3 = st.columns([2, 2, 1])
            if col1.button("➕ Add Another Subject"):
                st.session_state.subject_list.append("")
                st.rerun()
            if col2.button("Next: Assign Hours ➡️"):
                st.session_state.subject_list = [
                    s.strip() for s in st.session_state.subject_list if s.strip()]
                if not st.session_state.subject_list:
                    st.warning("Please define at least one subject.")
                else:
                    st.session_state.form_step = 2
                    st.rerun()
            if col3.button("Back"):
                st.session_state.page = "dashboard"
                st.rerun()

        elif st.session_state.form_step == 2:
            st.markdown(
                "<h3>Step 2: Assign Hours Per Day (Mon-Sat)</h3>", unsafe_allow_html=True)
            st.caption("Set hours to 0 if there is no class.")
            day_tabs = st.tabs(DAYS_OF_WEEK)
            for i, day in enumerate(DAYS_OF_WEEK):
                with day_tabs[i]:
                    st.markdown(
                        f"<h4>Schedule for {day}</h4>", unsafe_allow_html=True)
                    for subject_name in st.session_state.subject_list:
                        st.number_input(subject_name, min_value=0,
                                        step=1, key=f"{day}_{subject_name}_hours")
            st.divider()
            col1, col2 = st.columns(2)
            if col1.button("⬅️ Back to Subjects"):
                st.session_state.form_step = 1
                st.rerun()
            if col2.button("💾 Save Timetable"):
                if not list_name:
                    st.warning("⚠️ Please provide a name.")
                else:
                    schedule = {day: [{"name": s, "hours": st.session_state.get(
                        f"{day}_{s}_hours", 0)} for s in st.session_state.subject_list if st.session_state.get(f"{day}_{s}_hours", 0) > 0] for day in DAYS_OF_WEEK}
                    db.timetables.update_one(
                        {"_id": list_name},
                        {"$set": {"schedule": schedule, "owner": st.session_state.get(
                            "username"), "is_public": is_public}},
                        upsert=True
                    )
                    st.success(f"✅ Timetable '{list_name}' saved!")
                    st.session_state.page = "dashboard"
                    for key in ["form_step", "subject_list"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    time.sleep(1)
                    st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2B. ATTENDANCE MARKING PAGE
    elif st.session_state.page == "attendance_marking":
        list_name = st.session_state.get("selected_list", "Unknown")
        username = st.session_state.get("username")
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        st.markdown(f"<h1>✒️ Mark Attendance</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2>{list_name}</h2>", unsafe_allow_html=True)
        selected_date = st.date_input(
            "Select a date to view or edit", datetime.now())
        selected_day_str = selected_date.strftime('%A')
        selected_date_str_key = selected_date.strftime("%Y-%m-%d")
        st.markdown(
            f"<h3>Schedule for: {selected_date.strftime('%A, %d %B %Y')}</h3>", unsafe_allow_html=True)
        st.divider()

        timetable_doc = db.timetables.find_one({"_id": list_name})
        query = {"list_name": list_name,
                 "date": selected_date_str_key, "username": username}
        attendance_doc = db.attendance_records.find_one(query)

        if selected_day_str == "Saturday":
            st.info(
                "This is an Open Saturday. Enter hours only for classes that were conducted.")
            schedule = timetable_doc.get("schedule", {})
            master_subject_list = sorted(
                list({s['name'] for day_sched in schedule.values() for s in day_sched}))
            if not master_subject_list:
                st.warning(
                    "No subjects found. Please edit the timetable to add subjects.")
            else:
                with st.form(key=f"attendance_form_saturday_{selected_date_str_key}"):
                    existing_records = {rec['subject']: rec for rec in attendance_doc.get(
                        "records", [])} if attendance_doc else {}
                    for subject in master_subject_list:
                        st.markdown(f"<h4>{subject}</h4>",
                                    unsafe_allow_html=True)
                        cols = st.columns([1, 2])
                        existing_hours = existing_records.get(
                            subject, {}).get('hours', 0)
                        existing_status = existing_records.get(
                            subject, {}).get('status', 'Present')
                        status_options = ["Present", "Absent"]
                        cols[0].number_input(
                            "Hours Conducted", min_value=0, step=1, key=f"hours_{subject}", value=existing_hours)
                        cols[1].radio("Status", options=status_options, key=f"status_{subject}", index=status_options.index(
                            existing_status), horizontal=True, label_visibility="collapsed")
                    if st.form_submit_button(f"Save Attendance for Saturday"):
                        new_records = [{"subject": s, "status": st.session_state[f"status_{s}"], "hours": st.session_state[f"hours_{s}"]}
                                       for s in master_subject_list if st.session_state[f"hours_{s}"] > 0]
                        db.attendance_records.update_one(
                            query, {"$set": {"records": new_records}}, upsert=True)
                        st.success(f"Saturday's attendance has been saved!")
                        time.sleep(1)
                        st.rerun()

        else:  # REGULAR LOGIC FOR MONDAY - FRIDAY
            schedule = timetable_doc.get("schedule", {}).get(
                selected_day_str, []) if timetable_doc else []
            if not schedule:
                st.info(f"No classes scheduled for {selected_day_str}. 🌴")
            else:
                with st.form(key=f"attendance_form_{selected_date_str_key}"):
                    existing_records = {rec['subject']: rec['status'] for rec in attendance_doc.get(
                        "records", [])} if attendance_doc else {}
                    for subject in schedule:
                        st.markdown(
                            f"<h4>{subject['name']} ({subject['hours']} Hours)</h4>", unsafe_allow_html=True)
                        status_options = ["Present", "Absent"]
                        current_status = existing_records.get(
                            subject['name'], "Present")
                        st.radio("Status", options=status_options, key=f"status_{subject['name']}", index=status_options.index(
                            current_status), horizontal=True, label_visibility="collapsed")
                    if st.form_submit_button(f"Save Attendance"):
                        new_records = [
                            {"subject": s['name'], "status": st.session_state[f"status_{s['name']}"], "hours": s['hours']} for s in schedule]
                        db.attendance_records.update_one(
                            query, {"$set": {"records": new_records}}, upsert=True)
                        st.success(
                            f"Attendance for {selected_date.strftime('%A, %d %B')} has been saved!")

        st.divider()
        st.markdown(f"<h2>📊 Your Cumulative Statistics</h2>",
                    unsafe_allow_html=True)
        user_records_cursor = list(db.attendance_records.find(
            {"list_name": list_name, "username": username}))

        total_conducted = sum(entry.get(
            'hours', 1) for doc in user_records_cursor for entry in doc.get("records", []))
        total_present = sum(entry.get('hours', 1) for doc in user_records_cursor for entry in doc.get(
            "records", []) if entry['status'] == 'Present')
        total_absent = total_conducted - total_present

        stat_cols = st.columns(3)
        stat_cols[0].markdown(
            f'<div class="glass-stat-box"><div class="stat-value">{total_conducted}</div><div class="stat-label">Conducted Hours</div></div>', unsafe_allow_html=True)
        stat_cols[1].markdown(
            f'<div class="glass-stat-box"><div class="stat-value">{total_present}</div><div class="stat-label">Present Hours</div></div>', unsafe_allow_html=True)
        stat_cols[2].markdown(
            f'<div class="glass-stat-box"><div class="stat-value">{total_absent}</div><div class="stat-label">Absent Hours</div></div>', unsafe_allow_html=True)

        st.divider()
        col_back, col_edit = st.columns(2)
        if col_back.button("🔙 Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        if col_edit.button("✏️ Edit This Timetable"):
            st.session_state.page = "edit_timetable"
            st.session_state.form_step = 1
            timetable_doc = db.timetables.find_one({"_id": list_name}) or {}
            schedule = timetable_doc.get("schedule", {})
            subjects = sorted(
                list({s['name'] for day_sched in schedule.values() for s in day_sched}))
            st.session_state.subject_list = subjects if subjects else [""]
            for day in DAYS_OF_WEEK:
                day_schedule = schedule.get(day, [])
                subject_hours_map = {subj['name']: subj['hours']
                                     for subj in day_schedule}
                for subject_name in st.session_state.subject_list:
                    st.session_state[f"{day}_{subject_name}_hours"] = subject_hours_map.get(
                        subject_name, 0)
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2C. ANALYSIS PAGE
    elif st.session_state.page == "analysis":
        list_name = st.session_state.get("selected_list", "Unknown")
        username = st.session_state.get("username")
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        st.markdown("<h1>📊 Your Attendance Analysis</h1>",
                    unsafe_allow_html=True)
        st.markdown(f"<h2>{list_name}</h2>", unsafe_allow_html=True)
        st.divider()

        subject_stats = {}
        user_records_cursor = db.attendance_records.find(
            {"list_name": list_name, "username": username})

        for doc in user_records_cursor:
            for record in doc.get("records", []):
                subject_name = record['subject']
                hours = record.get('hours', 1)
                if subject_name not in subject_stats:
                    subject_stats[subject_name] = {
                        'conducted': 0, 'present': 0}
                subject_stats[subject_name]['conducted'] += hours
                if record['status'] == 'Present':
                    subject_stats[subject_name]['present'] += hours

        if not subject_stats:
            st.info("You haven't marked any attendance for this list yet.")
        else:
            for subject, stats in subject_stats.items():
                stats['absent'] = stats['conducted'] - stats['present']
                st.markdown('<div class="glass-subject-row">',
                            unsafe_allow_html=True)
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"<h3>{subject}</h3>", unsafe_allow_html=True)
                    percentage = (
                        stats['present'] / stats['conducted'] * 100) if stats['conducted'] > 0 else 0
                    st.markdown(
                        f"**Attendance:** <span class='percentage-display'>{percentage:.1f}%</span>", unsafe_allow_html=True)
                    mini_stat_cols = st.columns(3)
                    mini_stat_cols[0].markdown(
                        f"<div class='glass-stat-box' style='padding: 0.5rem;'><div class='stat-value' style='font-size: 1.5rem;'>{stats['conducted']}</div><div class='stat-label'>Conducted</div></div>", unsafe_allow_html=True)
                    mini_stat_cols[1].markdown(
                        f"<div class='glass-stat-box' style='padding: 0.5rem;'><div class='stat-value' style='font-size: 1.5rem;'>{stats['present']}</div><div class='stat-label'>Present</div></div>", unsafe_allow_html=True)
                    mini_stat_cols[2].markdown(
                        f"<div class='glass-stat-box' style='padding: 0.5rem;'><div class='stat-value' style='font-size: 1.5rem;'>{stats['absent']}</div><div class='stat-label'>Absent</div></div>", unsafe_allow_html=True)
                with col2:
                    if stats['conducted'] > 0:
                        labels, sizes, colors = ['Present', 'Absent'], [
                            stats['present'], stats['absent']], ['#00DFFC', '#F44336']
                        text_color = 'white' if st.session_state.theme == 'dark' else '#333'
                        fig, ax = plt.subplots(figsize=(3, 3))
                        ax.pie(sizes, autopct='%1.1f%%', startangle=90,
                               colors=colors, wedgeprops=dict(width=0.4))
                        fig.patch.set_alpha(0.0)
                        ax.patch.set_alpha(0.0)
                        plt.setp(ax.texts, color=text_color,
                                 size=10, weight="bold")
                        ax.axis('equal')
                        st.pyplot(fig)
                st.markdown('</div>', unsafe_allow_html=True)
        if st.button("🔙 Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2D. CHANGE PASSWORD PAGE
    elif st.session_state.page == "change_password":
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        username = st.session_state.get("username")
        st.markdown("<h1>🔑 Change Password</h1>", unsafe_allow_html=True)
        st.markdown(f"<h2>User: {username}</h2>", unsafe_allow_html=True)
        st.divider()
        with st.form(key="change_password_form"):
            old_password = st.text_input("Old Password", type="password")
            new_password = st.text_input("New Password", type="password")
            confirm_new_password = st.text_input(
                "Confirm New Password", type="password")
            submitted = st.form_submit_button("Update Password")
            if submitted:
                if not old_password or not new_password or not confirm_new_password:
                    st.warning("Please fill in all fields.")
                else:
                    user_data = db.users.find_one({"_id": username})
                    if user_data and verify_password(old_password, user_data["password"]):
                        if new_password == confirm_new_password:
                            hashed_pass = hash_password(new_password)
                            db.users.update_one({"_id": username}, {
                                                "$set": {"password": hashed_pass}})
                            st.success("Password updated successfully!")
                            time.sleep(1.5)
                            st.session_state.page = "dashboard"
                            st.rerun()
                        else:
                            st.error("New passwords do not match.")
                    else:
                        st.error("Incorrect old password.")
        if st.button("🔙 Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2E. CHANGE USERNAME PAGE
    elif st.session_state.page == "change_username":
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        old_username = st.session_state.get("username")
        st.markdown("<h1>👤 Change Username</h1>", unsafe_allow_html=True)
        st.markdown(
            f"<h2>Current User: {old_username}</h2>", unsafe_allow_html=True)
        st.warning(
            "Changing your username will update all your owned timetables and attendance records.")
        st.divider()
        with st.form(key="change_username_form"):
            new_username = st.text_input("New Username")
            current_password = st.text_input(
                "Verify with Current Password", type="password")
            submitted = st.form_submit_button("Confirm and Change Username")
            if submitted:
                if not new_username or not current_password:
                    st.warning("Please fill in all fields.")
                elif new_username == old_username:
                    st.error("New username cannot be the same as the old one.")
                else:
                    user_data = db.users.find_one({"_id": old_username})
                    if user_data and verify_password(current_password, user_data["password"]):
                        if db.users.find_one({"_id": new_username}):
                            st.error(
                                "This username is already taken. Please choose another one.")
                        else:
                            try:
                                with client.start_session() as session:
                                    with session.start_transaction():
                                        db.users.insert_one(
                                            {"_id": new_username, "password": user_data["password"]}, session=session)
                                        db.timetables.update_many({"owner": old_username}, {
                                                                  "$set": {"owner": new_username}}, session=session)
                                        db.attendance_records.update_many({"username": old_username}, {
                                                                          "$set": {"username": new_username}}, session=session)
                                        db.users.delete_one(
                                            {"_id": old_username}, session=session)
                                st.success(
                                    f"Username successfully changed to '{new_username}'!")
                                st.session_state["username"] = new_username
                                time.sleep(2)
                                st.session_state.page = "dashboard"
                                st.rerun()
                            except errors.PyMongoError as e:
                                st.error(
                                    f"A database error occurred. Your username was not changed. Error: {e}")
                    else:
                        st.error("Incorrect password.")
        if st.button("🔙 Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2F. IMPORT DATA PAGE
    elif st.session_state.page == "import_data":
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        st.markdown("<h1>📥 Import Existing Data</h1>", unsafe_allow_html=True)
        st.caption(
            "Enter the totals from your Excel sheet to bring your records up to date.")
        st.divider()
        username = st.session_state.get("username")
        user_timetables = list(db.timetables.find({}, {"_id": 1}))
        timetable_options = [t["_id"] for t in user_timetables]
        if not timetable_options:
            st.warning(
                "You must create or have access to at least one timetable before importing data.")
        else:
            selected_list = st.selectbox(
                "Select the timetable to import data into:", timetable_options)
            import_date = st.date_input(
                "Import data as of date:", datetime.now())
            import_date_str = import_date.strftime("%Y-%m-%d")
            st.markdown("<h3>Enter Subject Totals</h3>",
                        unsafe_allow_html=True)
            if 'import_subjects' not in st.session_state:
                st.session_state.import_subjects = [
                    {"name": "", "present": 0, "absent": 0}]
            for i, subject in enumerate(st.session_state.import_subjects):
                cols = st.columns([2, 1, 1])
                st.session_state.import_subjects[i]['name'] = cols[0].text_input(
                    "Subject Name", value=subject['name'], key=f"import_name_{i}")
                st.session_state.import_subjects[i]['present'] = cols[1].number_input(
                    "Present", min_value=0, value=subject['present'], key=f"import_present_{i}")
                st.session_state.import_subjects[i]['absent'] = cols[2].number_input(
                    "Absent", min_value=0, value=subject['absent'], key=f"import_absent_{i}")
            if st.button("➕ Add Subject"):
                st.session_state.import_subjects.append(
                    {"name": "", "present": 0, "absent": 0})
                st.rerun()
            st.divider()
            if st.button("✅ Import Data", type="primary"):
                with st.spinner("Importing records..."):
                    all_records = []
                    for subject_data in st.session_state.import_subjects:
                        name = subject_data['name'].strip()
                        if not name:
                            continue
                        for _ in range(subject_data['present']):
                            all_records.append(
                                {"subject": name, "status": "Present"})
                        for _ in range(subject_data['absent']):
                            all_records.append(
                                {"subject": name, "status": "Absent"})
                    if not all_records:
                        st.warning(
                            "Please enter some attendance data before importing.")
                    else:
                        db.attendance_records.update_one({"list_name": selected_list, "date": import_date_str, "username": username}, {
                                                         "$set": {"records": all_records, "is_import": True}}, upsert=True)
                        st.success(
                            f"Successfully imported historical data for '{selected_list}'!")
                        del st.session_state.import_subjects
                        time.sleep(2)
                        st.session_state.page = "dashboard"
                        st.rerun()
        if st.button("🔙 Back to Dashboard"):
            st.session_state.page = "dashboard"
            if 'import_subjects' in st.session_state:
                del st.session_state.import_subjects
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # 2G. PREDICTION PAGE
    elif st.session_state.page == "prediction":
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        st.markdown("<h1>🔮 Attendance Prediction</h1>", unsafe_allow_html=True)
        st.caption(
            "Calculate how many classes you need to attend per subject to reach 80%.")
        st.divider()

        username = st.session_state.get("username")
        query = {"$or": [{"is_public": True}, {"owner": username}]}
        timetable_options = [t["_id"]
                             for t in db.timetables.find(query, {"_id": 1})]

        if not timetable_options:
            st.warning("No timetables available. Please create one first.")
        else:
            selected_list = st.selectbox(
                "Select a timetable for prediction:", timetable_options)

            if selected_list:
                timetable_doc = db.timetables.find_one({"_id": selected_list})
                schedule = timetable_doc.get("schedule", {})
                all_subjects = sorted(
                    list({s['name'] for day_sched in schedule.values() for s in day_sched}))

                user_records_cursor = list(db.attendance_records.find(
                    {"list_name": selected_list, "username": username}))

                st.markdown(
                    f"<h3>Prediction Status for '{selected_list}'</h3>", unsafe_allow_html=True)

                if not all_subjects:
                    st.warning("No subjects are defined for this timetable.")
                else:
                    for subject_name in all_subjects:
                        subject_conducted = 0
                        subject_present = 0
                        for doc in user_records_cursor:
                            for record in doc.get("records", []):
                                if record.get("subject") == subject_name:
                                    subject_conducted += 1
                                    if record.get("status") == "Present":
                                        subject_present += 1

                        st.markdown('<div class="glass-subject-row">',
                                    unsafe_allow_html=True)
                        st.markdown(f"<h4>{subject_name}</h4>",
                                    unsafe_allow_html=True)

                        if subject_conducted == 0:
                            st.info("No attendance marked for this subject yet.")
                        else:
                            current_percentage = (
                                subject_present / subject_conducted) * 100
                            st.markdown(
                                f"**Current Attendance:** <span class='percentage-display'>{current_percentage:.2f}%</span>", unsafe_allow_html=True)

                            if current_percentage >= 80:
                                st.success("🎉 Target met! Keep it up.")
                            else:
                                classes_needed = math.ceil(
                                    4 * subject_conducted - 5 * subject_present)
                                st.warning(
                                    f"You need to attend **{classes_needed} more classes** of this subject to reach 80%.")
                        st.markdown('</div>', unsafe_allow_html=True)

        if st.button("🔙 Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

        # 2H. NEW: RESET ATTENDANCE PAGE
    elif st.session_state.page == "reset_attendance":
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        st.markdown("<h1>🗑️ Reset Attendance</h1>", unsafe_allow_html=True)
        st.caption(
            "Permanently delete your attendance record for a specific date.")
        st.divider()

        username = st.session_state.get("username")
        query = {"$or": [{"is_public": True}, {"owner": username}]}
        timetable_options = [t["_id"]
                             for t in db.timetables.find(query, {"_id": 1})]

        if not timetable_options:
            st.warning("No timetables available to reset.")
        else:
            selected_list = st.selectbox(
                "Select a timetable:", timetable_options)
            selected_date = st.date_input(
                "Select the date to reset:", datetime.now())

            st.divider()

            if st.button("Find and Reset Record", type="primary"):
                date_str = selected_date.strftime("%Y-%m-%d")
                query_to_delete = {"list_name": selected_list,
                                   "date": date_str, "username": username}

                # Check if a record exists before attempting deletion
                record_to_delete = db.attendance_records.find_one(
                    query_to_delete)

                if record_to_delete:
                    db.attendance_records.delete_one(query_to_delete)
                    st.success(
                        f"Your attendance record for {selected_list} on {date_str} has been successfully deleted.")
                else:
                    st.error(
                        f"No attendance record found for you in '{selected_list}' on {date_str}.")

        if st.button("🔙 Back to Dashboard"):
            st.session_state.page = "dashboard"
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # 2I. DASHBOARD PAGE (Default)
    else:
        st.markdown('<div class="main-container">', unsafe_allow_html=True)
        username = st.session_state.get('username', 'User')
        st.markdown(f"<h1>Welcome, {username}!</h1>", unsafe_allow_html=True)
        st.markdown(
            f"<p style='text-align: center; color: #90EE90;'>Today is <strong>{datetime.now().strftime('%A, %d %B %Y')}</strong>.</p>", unsafe_allow_html=True)

        header_cols = st.columns([4, 1])
        with header_cols[0]:
            date_color = "#90EE90" if st.session_state.theme == "dark" else "#2E8B57"
           # st.markdown(
            #    f"<p style='text-align: center; color: {date_color};'>Today is <strong>{datetime.now().strftime('%A, %d %B %Y')}</strong>.</p>", unsafe_allow_html=True)

        with header_cols[1]:
            theme_icon = "🌞" if st.session_state.theme == "dark" else "🌙"
            if st.button(f"{theme_icon} Switch Theme", key="theme_toggle"):
                st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
                st.rerun()

        st.divider()

        # Dashboard buttons organized in a 3x2 grid for clarity
        st.markdown("<h4>Actions</h4>", unsafe_allow_html=True)
        d_cols1 = st.columns(3)
        if d_cols1[0].button("➕ Create List"):
            st.session_state.page = "new_timetable"
            st.session_state.form_step = 1
            st.session_state.subject_list = [""]
            st.rerun()
        if d_cols1[1].button("📥 Import Data"):
            st.session_state.page = "import_data"
            st.rerun()
        if d_cols1[2].button("🔮 Predict"):
            st.session_state.page = "prediction"
            st.rerun()

        st.markdown("<h4>Account Settings</h4>", unsafe_allow_html=True)
        d_cols2 = st.columns(3)
        if d_cols2[0].button("🔑 Change Password"):
            st.session_state.page = "change_password"
            st.rerun()
        if d_cols2[1].button("👤 Change Username"):
            st.session_state.page = "change_username"
            st.rerun()
        if d_cols2[2].button("🗑️ Reset Date"):
            st.session_state.page = "reset_attendance"
            st.rerun()

        st.divider()
        st.markdown("<h2>Available Attendance Lists</h2>",
                    unsafe_allow_html=True)
        st.caption(
            "You can see all public lists and any private lists you have created.")

        query = {"$or": [{"is_public": True}, {"owner": username}]}
        all_timetables = list(db.timetables.find(
            query, {"_id": 1, "owner": 1, "is_public": 1}))
        if not all_timetables:
            st.info("No attendance lists available. Be the first to create one!")
        else:
            for timetable in all_timetables:
                list_name = timetable["_id"]
                owner = timetable.get("owner")
                is_public = timetable.get("is_public", False)

                if st.session_state.get("confirming_delete") == list_name:
                    st.markdown(
                        '<div class="glass-list-item" style="border-color: #F44336;">', unsafe_allow_html=True)
                    st.warning(
                        f"⚠️ Are you sure you want to delete '{list_name}' for EVERYONE?")
                    st.caption(
                        "This will permanently delete the timetable and all associated attendance records for ALL users. This action cannot be undone.")
                    c1, c2 = st.columns(2)
                    if c1.button("Yes, Delete for All", key=f"confirm_delete_{list_name}", type="primary"):
                        db.timetables.delete_one({"_id": list_name})
                        db.attendance_records.delete_many(
                            {"list_name": list_name})
                        st.session_state.confirming_delete = None
                        st.success(
                            f"'{list_name}' has been permanently deleted.")
                        time.sleep(2)
                        st.rerun()
                    if c2.button("Cancel", key=f"cancel_delete_{list_name}"):
                        st.session_state.confirming_delete = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    continue

                if st.session_state.get("confirming_clear") == list_name:
                    st.markdown(
                        '<div class="glass-list-item" style="border-color: #FFC107;">', unsafe_allow_html=True)
                    st.warning(
                        f"⚠️ Are you sure you want to clear YOUR records for '{list_name}'?")
                    st.caption(
                        "This will only delete your personal attendance data. The public timetable will remain.")
                    c1, c2 = st.columns(2)
                    if c1.button("Yes, Clear My Records", key=f"confirm_clear_{list_name}"):
                        db.attendance_records.delete_many(
                            {"list_name": list_name, "username": username})
                        st.session_state.confirming_clear = None
                        st.success(
                            f"Your records for '{list_name}' have been cleared.")
                        time.sleep(2)
                        st.rerun()
                    if c2.button("Cancel", key=f"cancel_clear_{list_name}"):
                        st.session_state.confirming_clear = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                    continue

                st.markdown('<div class="glass-list-item">',
                            unsafe_allow_html=True)
                st.markdown(f"<h3>{list_name}</h3>", unsafe_allow_html=True)
                visibility = "Public" if is_public else "Private (Yours)"
                st.caption(f"Created by: {owner} | Status: {visibility}")
                cols = st.columns([2, 2, 4])
                if cols[0].button("✒️ Mark Attendance", key=f"attend_{list_name}"):
                    st.session_state.selected_list = list_name
                    st.session_state.page = "attendance_marking"
                    st.rerun()
                if cols[1].button("📊 My Analysis", key=f"analyze_{list_name}"):
                    st.session_state.selected_list = list_name
                    st.session_state.page = "analysis"
                    st.rerun()
                with cols[2]:
                    if owner == username:
                        c1, c2 = st.columns(2)
                        if c1.button("✏️", key=f"edit_{list_name}", help="Edit Timetable"):
                            st.session_state.selected_list = list_name
                            st.session_state.page = "edit_timetable"
                            st.session_state.form_step = 1
                            timetable_doc = db.timetables.find_one(
                                {"_id": list_name}) or {}
                            schedule = timetable_doc.get("schedule", {})
                            subjects = sorted(
                                list({s['name'] for day_sched in schedule.values() for s in day_sched}))
                            st.session_state.subject_list = subjects if subjects else [
                                ""]
                            for day in DAYS_OF_WEEK:
                                day_schedule = schedule.get(day, [])
                                subject_hours_map = {
                                    subj['name']: subj['hours'] for subj in day_schedule}
                                for subject_name in st.session_state.subject_list:
                                    st.session_state[f"{day}_{subject_name}_hours"] = subject_hours_map.get(
                                        subject_name, 0)
                            st.rerun()
                        if c2.button("🗑️", key=f"delete_all_{list_name}", help="Delete for All Users"):
                            st.session_state.confirming_delete = list_name
                            st.rerun()
                    else:
                        if st.button("🧹 Clear My Records", key=f"clear_{list_name}"):
                            st.session_state.confirming_clear = list_name
                            st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

        st.divider()
        if st.button("Logout"):
            for key in list(st.session_state.keys()):
                if key != 'authenticated':
                    del st.session_state[key]
            st.session_state['authenticated'] = False
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
