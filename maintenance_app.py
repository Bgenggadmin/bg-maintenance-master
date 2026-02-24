import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. LOCAL STORAGE SETUP ---
DB_FILE = "maint_logs.csv"

# Function to safely read the data
def get_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    return pd.DataFrame(columns=["Timestamp", "Machine", "Log_Type", "Technician", "Status", "Issue", "Action"])

st.title("🔧 B&G Maintenance Log")

# --- 2. MAINTENANCE ENTRY FORM ---
with st.form("maint_form", clear_on_submit=True):
    col1, col2 = st.columns(2)
    with col1:
        machine = st.selectbox("Machine", ["CNC Machine", "Welding Unit 1", "Air Compressor", "Crane"])
        log_type = st.radio("Type", ["🚨 Breakdown", "📅 Preventive", "🛠️ Spare Part"])
        tech = st.text_input("Technician Name")
    with col2:
        status = st.selectbox("Status", ["Operational", "Under Repair", "Out of Service"])
        issue = st.text_area("Issue Description")
        action = st.text_area("Action Taken")

    if st.form_submit_button("Submit Maintenance Log"):
        new_row = pd.DataFrame([{
            "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "Machine": machine,
            "Log_Type": log_type,
            "Technician": tech,
            "Status": status,
            "Issue": issue,
            "Action": action
        }])
        
        # Load current data, add new row, and save
        current_df = get_data()
        updated_df = pd.concat([current_df, new_row], ignore_index=True)
        updated_df.to_csv(DB_FILE, index=False)
        
        st.success(f"Log saved successfully!")
        st.balloons()
        st.rerun() # THIS FORCES THE APP TO SHOW THE NEW RECORD IMMEDIATELY

# --- 3. DATA VIEW & DOWNLOAD ---
st.divider()
st.subheader("📋 Recent Activity")

df = get_data() # Always get fresh data here

if not df.empty:
    # Show the table
    st.dataframe(df.sort_values(by="Timestamp", ascending=False), use_container_width=True)
    
    # Download Button
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD TO EXCEL", csv, "bg_maint_data.csv", "text/csv")
else:
    st.info("No records found in app memory yet.")
