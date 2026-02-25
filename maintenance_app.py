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
        st.error(f"Sync Error: {e}")
        return False

def load_data():
    if os.path.exists(DB_FILE):
        try:
            if os.stat(DB_FILE).st_size > 0:
                return pd.read_csv(DB_FILE)
        except Exception: pass
    return pd.DataFrame(columns=["Timestamp", "Equipment", "Technician", "Stage", "Reference", "Status", "Remarks", "Photo"])

# --- 3. UI HEADER ---
st.title("🔧 B&G Maintenance Master")
st.markdown("### Shopfloor Equipment Reliability & Repair Tracking")
st.divider()

# --- 4. DATA ENTRY SECTION ---
with st.container():
    with st.form("maint_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📋 Equipment Info")
            equipment = st.text_input("Machine Name (e.g., CNC-01, EOT Crane)").upper()
            ref_data = st.text_input("Reference No (Machine ID / Spare Part No)")
            technician = st.selectbox("Assign Technician", ["Electrician", "Prasanth", "RamaSai", "Brahmiah"])
            
        with col2:
            st.subheader("⚙️ Maintenance Status")
            status = st.select_slider("Current Machine Status", 
                                     options=["🔴 Down", "🟡 Under Monitoring", "🟢 Operational"],
                                     value="🟢 Operational")
            stage = st.selectbox("Activity Type", ["Breakdown Repair", "Preventive Maintenance (PM)", "Spare Replacement", "Lubrication", "Calibration"])
            remarks = st.text_area("Work Details / Technical Observations")

        st.subheader("📸 Visual Proof")
        cam_photo = st.camera_input("Capture Part/Condition Photo")
        
        if st.form_submit_button("🚀 Finalize & Sync Record"):
            if not equipment or not ref_data:
                st.error("Please provide Equipment Name and Reference Number.")
            else:
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
                
                df = load_data()
                updated_df = pd.concat([df, new_row], ignore_index=True)
                updated_df.to_csv(DB_FILE, index=False)
                
                if save_to_github(updated_df):
                    st.success(f"Successfully logged maintenance for {equipment}!")
                    st.balloons()
                    st.rerun()

# --- 5. LOGS & ANALYTICS ---
st.divider()
df_view = load_data()

if not df_view.empty:
    tab1, tab2 = st.tabs(["📜 Detailed Audit Log", "🖼️ Machine Photo Gallery"])
    
    with tab1:
        st.subheader("Maintenance History")
        # Style the dataframe for better visibility
        st.dataframe(df_view.drop(columns=["Photo"]).sort_values(by="Timestamp", ascending=False), use_container_width=True)
        
    with tab2:
        st.subheader("Visual Traceability")
        search_eq = st.selectbox("Search Records by Machine", ["All Machines"] + list(df_view['Equipment'].unique()))
        
        gallery = df_view if search_eq == "All Machines" else df_view[df_view['Equipment'] == search_eq]
        
        for _, row in gallery.iterrows():
            if isinstance(row['Photo'], str) and len(row['Photo']) > 10:
                with st.expander(f"View {row['Equipment']} - {row['Timestamp']}"):
                    c1, c2 = st.columns([1, 2])
                    with c1:
                        st.write(f"**Status:** {row['Status']}")
                        st.write(f"**Type:** {row['Stage']}")
                        st.write(f"**Tech:** {row['Technician']}")
                        st.write(f"**Remarks:** {row['Remarks']}")
                    with c2:
                        st.image(base64.b64decode(row['Photo']), use_container_width=True)
else:
    st.info("No maintenance logs detected. Please submit your first record above.")
