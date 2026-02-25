import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import os
from github import Github
from PIL import Image

# --- 1. SETUP & TIMEZONE (IST) ---
IST = pytz.timezone('Asia/Kolkata')
MAINT_LOG = "maintenance_records.csv"
PHOTO_DIR = "maintenance_photos"

# Headers exactly as shown in your Recent Logs
HEADERS = ["Timestamp", "Technician", "Machine_ID", "Type", "Issue_Status", "Action_Taken", "Photo_Path"]

# --- 2. GITHUB SYNC ---
def sync_to_github(file_path, is_image=False):
    try:
        if "GITHUB_TOKEN" in st.secrets:
            g = Github(st.secrets["GITHUB_TOKEN"])
            repo = g.get_repo(st.secrets["GITHUB_REPO"])
            
            mode = "rb" if is_image else "r"
            with open(file_path, mode) as f:
                content = f.read()
            
            try:
                contents = repo.get_contents(file_path)
                repo.update_file(contents.path, f"Maint Sync {datetime.now(IST)}", content, contents.sha)
            except:
                repo.create_file(file_path, "Initial Maintenance Create", content)
    except Exception as e:
        st.error(f"Sync Error: {e}")

st.set_page_config(page_title="B&G Maintenance Master", layout="wide")
st.title("⚙️ B&G Machine Maintenance & PM")

# --- 3. ENTRY FORM ---
col1, col2 = st.columns(2)
with col1:
    tech_name = st.selectbox("Technician/Supervisor", ["Brahmiah", "Ravindra", "Prasanth"])
    machine_id = st.selectbox("Machine ID", ["Plasma-01", "Welding-Machine-05", "Bending-Rolls", "Overhead-Crane"])
    m_type = st.radio("Log Type", ["Breakdown (Unplanned)", "Preventive (PM)", "General Service"], horizontal=True)
    status = st.selectbox("Current Status", ["🟢 Running", "🟡 Under Observation", "🔴 Breakdown/Offline"])

with col2:
    img_file = st.camera_input("📸 Take Photo of Issue/Part")
    action_taken = st.text_area("Observations / Action Taken")

if st.button("⚙️ Submit Maintenance Record"):
    ts = datetime.now(IST).strftime('%Y-%m-%d %H:%M')
    photo_path = "None"
    
    if img_file:
        if not os.path.exists(PHOTO_DIR): os.makedirs(PHOTO_DIR)
        photo_path = f"{PHOTO_DIR}/MAINT_{datetime.now(IST).strftime('%d%m%Y_%H%M%S')}.png"
        Image.open(img_file).save(photo_path)
        sync_to_github(photo_path, is_image=True)
    
    new_row = [ts, tech_name, machine_id, m_type, status, action_taken, photo_path]
    
    if os.path.exists(MAINT_LOG):
        df = pd.read_csv(MAINT_LOG)
        df = df.loc[:, ~df.columns.duplicated()]
        df = pd.concat([df[HEADERS], pd.DataFrame([new_row], columns=HEADERS)], ignore_index=True)
    else:
        df = pd.DataFrame([new_row], columns=HEADERS)
        
    df.to_csv(MAINT_LOG, index=False)
    sync_to_github(MAINT_LOG)
    st.success(f"✅ Maintenance Record Synced at {ts}")
    st.rerun()

# --- 4. DISPLAY & GALLERY ---
st.divider()
if os.path.exists(MAINT_LOG):
    df_view = pd.read_csv(MAINT_LOG).reindex(columns=HEADERS)
    st.subheader("📊 Recent Maintenance Logs")
    st.dataframe(df_view.sort_values(by="Timestamp", ascending=False), use_container_width=True)

    st.divider()
    st.subheader("🖼️ Maintenance Photo Gallery")
    # Safety filter to prevent the gallery from showing "No photos captured yet" incorrectly
    photo_df = df_view[df_view['Photo_Path'].notna() & (df_view['Photo_Path'] != "None")]
    
    if not photo_df.empty:
        gallery_options = (photo_df['Timestamp'] + " - " + photo_df['Machine_ID']).tolist()
        selected_record = st.selectbox("Select Record to View Photo", gallery_options, key="m_gal")
        
        path_to_show = photo_df[(photo_df['Timestamp'] + " - " + photo_df['Machine_ID']) == selected_record]['Photo_Path'].values[0]
        
        if isinstance(path_to_show, str) and os.path.exists(path_to_show):
            st.image(path_to_show, caption=f"Part Detail: {selected_record}", use_container_width=True)
    else:
        st.info("No photos captured yet.")
else:
    st.info("No maintenance records found.")
