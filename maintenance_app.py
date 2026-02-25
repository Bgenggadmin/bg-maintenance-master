import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import base64
from github import Github
from io import BytesIO
from PIL import Image

# --- 1. CONFIGURATION ---
IST = pytz.timezone('Asia/Kolkata')
DB_FILE = "maintenance_logs.csv"

# Safety check for Secrets
try:
    REPO_NAME = st.secrets["GITHUB_REPO"]
    TOKEN = st.secrets["GITHUB_TOKEN"]
except Exception:
    st.error("❌ Streamlit Secrets (GITHUB_REPO or GITHUB_TOKEN) are missing!")
    st.stop()

st.set_page_config(page_title="B&G Maintenance Master", layout="wide", page_icon="🔧")

# --- 2. GITHUB UTILITIES ---
def save_to_github(dataframe):
    try:
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        csv_content = dataframe.to_csv(index=False)
        contents = repo.get_contents(DB_FILE)
        repo.update_file(contents.path, f"Maint Update {datetime.now(IST)}", csv_content, contents.sha)
        return True
    except Exception as e:
        # Show a friendly error but don't stop the app
        st.warning(f"⚠️ Cloud Sync Delayed: {e}. Data saved locally.")
        return False

def load_data():
    if os.path.exists(DB_FILE):
        try:
            if os.stat(DB_FILE).st_size > 0:
                return pd.read_csv(DB_FILE)
        except Exception: pass
    return pd.DataFrame(columns=["Timestamp", "Equipment", "Technician", "Stage", "Reference", "Status", "Remarks", "Photo"])

# --- 3. UI DESIGN ---
st.title("🔧 B&G Maintenance Master")
st.divider()

# --- 4. DATA ENTRY ---
with st.form("maint_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        equipment = st.text_input("Machine Name").upper()
        technician = st.selectbox("Technician", ["Electrician", "Prasanth", "RamaSai", "Brahmiah"])
    with col2:
        stage = st.selectbox("Type", ["Breakdown Repair", "Preventive Maintenance (PM)", "Spare Replacement"])
        status = st.radio("Status", ["🟢 Operational", "🔴 Down"], horizontal=True)
    
    ref_data = st.text_input("Ref (Job Code / Machine ID)")
    remarks = st.text_area("Work Details")
    cam_photo = st.camera_input("Capture Proof")

    if st.form_submit_button("🚀 Finalize Record"):
        timestamp = datetime.now(IST).strftime('%Y-%m-%d %H:%M')
        
        img_str = ""
        if cam_photo:
            img = Image.open(cam_photo)
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()

        new_row = pd.DataFrame([{
            "Timestamp": timestamp, "Equipment": equipment, "Technician": technician, 
            "Stage": stage, "Reference": ref_data, "Status": status, 
            "Remarks": remarks, "Photo": img_str
        }])

        df = load_data()
        updated_df = pd.concat([df, new_row], ignore_index=True)
        updated_df.to_csv(DB_FILE, index=False)
        
        # Try to sync, but success isn't mandatory to continue
        save_to_github(updated_df)
        st.success(f"✅ Record Logged at {timestamp}")
        st.rerun()

# --- 5. VIEW LOGS ---
st.divider()
df_view = load_data()
if not df_view.empty:
    st.subheader("📜 Maintenance History")
    st.dataframe(df_view.drop(columns=["Photo"]).sort_values(by="Timestamp", ascending=False), use_container_width=True)
