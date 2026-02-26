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
        repo.update_file(contents.path, f"Maint Photo Update {datetime.now(IST)}", csv_content, contents.sha)
        return True
    except Exception as e:
        st.error(f"Sync Error: {e}")
        return False

# Added cache decorator for instant data refresh
@st.cache_data(ttl=1)
def load_data():
    if os.path.exists(DB_FILE):
        try:
            if os.stat(DB_FILE).st_size > 0:
                return pd.read_csv(DB_FILE)
        except Exception: pass
    return pd.DataFrame(columns=["Timestamp", "Equipment", "Technician", "Stage", "Reference", "Status", "Remarks", "Photo"])

# --- 3. INPUT FORM ---
with st.form("maint_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        equipment = st.text_input("Machine Name").upper()
        technician = st.selectbox("Technician", ["Electrician", "Prasanth", "RamaSai", "Brahmiah"])
    with col2:
        stage = st.selectbox("Type", ["Breakdown Repair", "PM", "Spare Replacement"])
        status = st.radio("Status", ["🟢 Operational", "🔴 Down"], horizontal=True)
    
    ref_data = st.text_input("Ref (Job/Machine ID)")
    remarks = st.text_area("Work Details")
    cam_photo = st.camera_input("Capture Proof")

    if st.form_submit_button("🚀 Submit & Sync"):
        img_str = ""
        if cam_photo:
            img = Image.open(cam_photo)
            
            # OPTIMIZATION: Resize to Passport size (400px width)
            img.thumbnail((400, 400))
            
            buffered = BytesIO()
            # OPTIMIZATION: Compress to ~60KB target
            img.save(buffered, format="JPEG", quality=40, optimize=True)
            img_str = base64.b64encode(buffered.getvalue()).decode()

        new_row = pd.DataFrame([{
            "Timestamp": datetime.now(IST).strftime('%Y-%m-%d %H:%M'),
            "Equipment": equipment, "Technician": technician, "Stage": stage,
            "Reference": ref_data, "Status": status, "Remarks": remarks, "Photo": img_str
        }])

        # Load fresh, concatenate and save
        df_current = load_data()
        updated_df = pd.concat([df_current, new_row], ignore_index=True)
        updated_df.to_csv(DB_FILE, index=False)
        
        if save_to_github(updated_df):
            # Clear cache so the tabs update immediately
            st.cache_data.clear()
            st.success("✅ Record Secured!")
            st.rerun()

# --- 4. VIEW LOGS & PHOTOS ---
st.divider()
df_view = load_data()

if not df_view.empty:
    tab1, tab2 = st.tabs(["📜 Audit Log", "🖼️ Photo Gallery"])
    
    with tab1:
        # Hide the raw photo code so the table stays clean
        st.dataframe(df_view.drop(columns=["Photo"]).sort_values(by="Timestamp", ascending=False), use_container_width=True)
        
    with tab2:
        st.subheader("Visual Traceability")
        # Filter photos by Machine Name
        view_eq = st.selectbox("Select Machine to View Photos", ["All"] + list(df_view['Equipment'].unique()))
        gallery = df_view if view_eq == "All" else df_view[df_view['Equipment'] == view_eq]
        
        # Displaying newest photos first in gallery
        for _, row in gallery.sort_values(by="Timestamp", ascending=False).iterrows():
            if isinstance(row['Photo'], str) and len(row['Photo']) > 50:
                with st.container():
                    st.write(f"**{row['Equipment']}** | {row['Stage']} | {row['Timestamp']}")
                    # Decodes and displays at optimized passport width
                    st.image(base64.b64decode(row['Photo']), width=400)
                    st.divider()
else:
    st.info("No records found.")
