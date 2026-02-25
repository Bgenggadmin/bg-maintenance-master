import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
import base64
from github import Github # Add 'PyGithub' to requirements.txt
from io import BytesIO
from PIL import Image

# --- 1. CONFIGURATION ---
IST = pytz.timezone('Asia/Kolkata')
DB_FILE = "maintenance_logs.csv"
REPO_NAME = st.secrets["GITHUB_REPO"] # Your GitHub 'username/repo'
TOKEN = st.secrets["GITHUB_TOKEN"]

# --- 2. GITHUB SAVE FUNCTION ---
def save_to_github(dataframe):
    g = Github(TOKEN)
    repo = g.get_repo(REPO_NAME)
    csv_content = dataframe.to_csv(index=False)
    try:
        contents = repo.get_contents(DB_FILE)
        repo.update_file(contents.path, "Update Maintenance Logs", csv_content, contents.sha)
    except:
        repo.create_file(DB_FILE, "Initial Maintenance Log", csv_content)

st.set_page_config(page_title="B&G Maintenance Master", layout="wide")
st.title("🔧 B&G Maintenance Master")

# --- 3. DATA LOAD ---
@st.cache_data(ttl=60) # Refreshes every minute
def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Timestamp", "Equipment", "Technician", "Stage", "Reference", "Status", "Remarks", "Photo"])

df = load_data()

# --- 4. INPUT FORM ---
with st.form("maint_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        equipment = st.text_input("Equipment Name").upper()
        technician = st.selectbox("Technician", ["Subodth", "Prasanth", "RamaSai", "Naresh"])
        stage = st.selectbox("Type", ["Breakdown", "PM", "Spare Replace", "Lubrication", "Calibration"])
    with col2:
        ref_data = st.text_input("Ref (Machine ID / Part No)")
        status = st.radio("Status", ["🟢 Operational", "🔴 Down"])
        remarks = st.text_area("Observations")

    cam_photo = st.camera_input("Take Photo")
    
    if st.form_submit_button("Submit & Sync to GitHub"):
        img_str = ""
        if cam_photo:
            img = Image.open(cam_photo)
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
        
        new_row = pd.DataFrame([{
            "Timestamp": datetime.now(IST).strftime('%Y-%m-%d %H:%M'),
            "Equipment": equipment, "Technician": technician, "Stage": stage,
            "Reference": ref_data, "Status": status, "Remarks": remarks, "Photo": img_str
        }])
        
        # Save locally AND push to GitHub
        updated_df = pd.concat([df, new_row], ignore_index=True)
        updated_df.to_csv(DB_FILE, index=False)
        save_to_github(updated_df) # THE MAGIC STEP
        
        st.success("✅ Logged & Permanently Saved to GitHub!")
        st.rerun()

# --- 5. VIEW LOGS ---
st.divider()
if not df.empty:
    st.dataframe(df.drop(columns=["Photo"]).sort_values(by="Timestamp", ascending=False), use_container_width=True)
