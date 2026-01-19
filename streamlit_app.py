import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Daily Flow Pro", layout="wide", initial_sidebar_state="expanded")

# --- FILE PERSISTENCE LOGIC ---
# This saves your data to a local file so it doesn't disappear when you close the app.
DATA_FILE = "daily_flow_data.json"

def save_data():
    data = {
        "all_templates": st.session_state.all_templates,
        "contacts": st.session_state.contacts_df.to_dict()
    }
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            st.session_state.all_templates = data.get("all_templates", {})
            st.session_state.contacts_df = pd.DataFrame(data.get("contacts", {}))

# --- INITIALIZE SESSION STATES ---
if 'schedule' not in st.session_state:
    st.session_state.schedule = []
if 'all_templates' not in st.session_state:
    st.session_state.all_templates = {}
if 'contacts_df' not in st.session_state:
    st.session_state.contacts_df = pd.DataFrame(columns=["Name", "Phone", "Email"])
if 'last_notified' not in st.session_state:
    st.session_state.last_notified = None

# Load persistent data on first run
if not st.session_state.all_templates and os.path.exists(DATA_FILE):
    load_data()

# --- BROWSER NOTIFICATION JAVASCRIPT ---
st_notification_js = """
<script>
function playNotify(taskName) {
    var audio = new Audio('https://actions.google.com/sounds/v1/alarms/beep_short.ogg');
    audio.play();
    alert("⏰ TIME FOR: " + taskName);
}
</script>
"""
st.components.v1.html(st_notification_js, height=0)

# --- SIDEBAR: CONTROLS ---
with st.sidebar:
    st.title("⚙️ Controls")
    
    # 1. Templates
    st.subheader("📋 Templates")
    temp_name = st.text_input("New Template Name")
    if st.button("💾 Save Current as Template"):
        if st.session_state.schedule:
            st.session_state.all_templates[temp_name] = st.session_state.schedule
            save_data()
            st.success(f"Saved {temp_name}")

    if st.session_state.all_templates:
        load_choice = st.selectbox("Load Saved Template", options=list(st.session_state.all_templates.keys()))
        if st.button("📂 Load Template"):
            st.session_state.schedule = st.session_state.all_templates[load_choice]
            st.rerun()

    st.divider()

    # 2. Add Tasks
    st.subheader("➕ Add Activity")
    new_name = st.text_input("Task Name")
    new_type = st.selectbox("Type", ["Standard", "Workout", "Reach Out"])
    new_time = st.time_input("Start Time")
    
    if st.button("✅ Add to Schedule"):
        task = {
            "name": new_name, 
            "type": new_type, 
            "time": new_time.strftime("%H:%M"), 
            "log": "", 
            "done": False
        }
        st.session_state.schedule.append(task)
        st.session_state.schedule = sorted(st.session_state.schedule, key=lambda x: x['time'])
        st.rerun()

# --- MAIN DASHBOARD ---
st.title("🚀 My Daily Flow")
curr_time = datetime.now().strftime("%H:%M")
st.write(f"### {datetime.now().strftime('%A, %B %d')} | {datetime.now().strftime('%I:%M %p')}")

# Image of an interactive daily schedule planner with task categories and progress icons


# Check for notifications
for task in st.session_state.schedule:
    if task['time'] == curr_time and st.session_state.last_notified != curr_time:
        st.session_state.last_notified = curr_time
        st.components.v1.html(f"<script>playNotify('{task['name']}');</script>", height=0)

# Display Schedule
if not st.session_state.schedule:
    st.info("Your schedule is empty. Use the sidebar to add tasks or load a template.")

for i, task in enumerate(st.session_state.schedule):
    is_now = task['time'] == curr_time
    with st.expander(f"{'🔔 ' if is_now else ''}{task['time']} - {task['name']}", expanded=is_now):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            if task['type'] == "Reach Out":
                if not st.session_state.contacts_df.empty:
                    selected_contact = st.selectbox("Select Contact", st.session_state.contacts_df['Name'], key=f"contact_{i}")
                    c_info = st.session_state.contacts_df[st.session_state.contacts_df['Name'] == selected_contact].iloc[0]
                    st.info(f"📞 {c_info['Phone']} | ✉️ {c_info.get('Email', 'N/A')}")
                task['log'] = st.text_input("Interaction Notes:", value=task['log'], key=f"log_{i}")
            
            elif task['type'] == "Workout":
                task['log'] = st.text_area("Workout Tracking (Sets/Reps):", value=task['log'], key=f"log_{i}")
            
            else:
                task['log'] = st.text_input("Progress Update:", value=task['log'], key=f"log_{i}")

        with col2:
            if st.button("🗑️ Delete", key=f"del_{i}"):
                st.session_state.schedule.pop(i)
                st.rerun()
            task['done'] = st.checkbox("Task Completed", value=task['done'], key=f"done_{i}")

# --- CONTACT MANAGEMENT ---
st.divider()
with st.expander("👤 Contact Manager & Spreadsheet Import"):
    csv_file = st.file_uploader("Import Contacts (CSV)", type="csv")
    if csv_file:
        st.session_state.contacts_df = pd.read_csv(csv_file)
        save_data()
        st.success("Contact list updated!")
    st.dataframe(st.session_state.contacts_df, use_container_width=True)
