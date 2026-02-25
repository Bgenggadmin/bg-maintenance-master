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
REPO_NAME = st.secrets["GITHUB_REPO"]
TOKEN = st.secrets["GITHUB_TOKEN"]

st.set_page_config(page_title="B&G Maintenance Master", layout="wide")
st.title("🔧 B&G Maintenance Master")

# --- 2. GITHUB UTILITIES ---
def save_to_github(dataframe):
    try:
        g = Github(TOKEN)
        repo = g.get_repo(REPO_NAME)
        csv_content = dataframe.to_csv(index=False)
        contents = repo.get_contents(DB_FILE)
        repo.update_file(contents.path, f"Update Log {datetime.now(IST)}", csv_content, contents.sha)
        return True
    except Exception as e:
        st.error(f"GitHub Sync Error: {e}")
        return False

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Timestamp", "Equipment", "Technician", "Stage", "Reference", "Status", "Remarks", "Photo"])

# --- 3. INPUT FORM ---
with st.form("maint_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        equipment = st.text_input("Equipment Name (e.g. CNC, EOT)").upper()
    technician = st.selectbox("Technician", ["Electrician", "Prasanth", "RamaSai", "Brahmiah"])
    stage = st.selectbox("Type", ["Breakdown", "PM", "Spare Replace", "Lubrication", "Calibration"])
    with col2:
        ref_data = st.text_input("Ref (Machine ID / Part No)")
        status = st.radio("Equipment Status", ["🟢 Operational", "🔴 Down"])
        remarks = st.text_area("Work Details")

    cam_photo = st.camera_input("Take Photo")
    
    if st.form_submit_button("🚀 Submit & Sync to GitHub"):
        img_str = ""
        if cam_photo:
            img = Image.open(cam_photo)
            buffered = BytesIO()
            img.save(buffered, format="JPEG")
            img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Prepare New Data
        new_row = pd.DataFrame([{
            "Timestamp": datetime.now(IST).strftime('%Y-%m-%d %H:%M'),
            "Equipment": equipment, "Technician": technician, "Stage": stage,
            "Reference": ref_data, "Status": status, "Remarks": remarks, "Photo": img_str
        }])
        
        # Merge and Sync
        df = load_data()
        updated_df = pd.concat([df, new_row], ignore_index=True)
        
        # Save locally for speed and GitHub for permanence
        updated_df.to_csv(DB_FILE, index=False)
        if save_to_github(updated_df):
            st.success("✅ Maintenance Record Permanently Secured!")
            st.balloons()
            st.rerun()

# --- 4. VIEW LOGS & GALLERY ---
st.divider()
df_view = load_data()
if not df_view.empty:
    tab1, tab2 = st.tabs(["📜 History", "🖼️ Photo Logs"])
    with tab1:
        st.dataframe(df_view.drop(columns=["Photo"]).sort_values(by="Timestamp", ascending=False), use_container_width=True)
    with tab2:
        view_eq = st.selectbox("Filter Photos by Machine", ["-- All --"] + list(df_view['Equipment'].unique()))
        gallery = df_view if view_eq == "-- All --" else df_view[df_view['Equipment'] == view_eq]
        for _, row in gallery.iterrows():
            if isinstance(row['Photo'], str) and len(row['Photo']) > 10:
                st.write(f"**{row['Equipment']}** - {row['Stage']} ({row['Timestamp']})")
                st.image(base64.b64decode(row['Photo']), width=400)
                st.divider()
