import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. LOCAL STORAGE SETUP ---
DB_FILE = "maint_data.csv"

if os.path.exists(DB_FILE):
    df = pd.read_csv(DB_FILE)
else:
    df = pd.DataFrame(columns=["Timestamp", "Machine", "Type", "Technician", "Issue", "Action", "Status"])

st.title("🔧 B&G Maintenance Log")

# --- 2. BACKEND CONTROL ---
with st.expander("📥 DOWNLOAD DATA / RESET"):
    if not df.empty:
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="DOWNLOAD ALL MAINT RECORDS TO EXCEL",
            data=csv,
            file_name=f"BG_Maint_Backup_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        if st.button("Delete All Records (Warning!)"):
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
                st.rerun()
    else:
        st.write("No maintenance records yet.")

# --- 3. MAINTENANCE ENTRY FORM ---
st.divider()
with st.form("maint_form", clear_on_submit=True):
    c1, c2 = st.columns(2)
    with c1:
        machine = st.selectbox("Machine / Equipment", ["CNC Machine", "Welding Unit 1", "Welding Unit 2", "Air Compressor", "Overhead Crane"])
        m_type = st.radio("Log Type", ["🚨 Breakdown", "📅 Preventive", "🛠️ Spare Part Change"])
        technician = st.text_input("Technician Name")
    with c2:
        status = st.selectbox("Current Status", ["🛠️ In Progress", "✅ Operational", "❌ Out of Service"])
        issue_desc = st.text_area("Issue Description")
        action_taken = st.text_area("Action Taken / Spares Used")

    if st.form_submit_button("Submit Maintenance Log"):
        new_row = pd.DataFrame([{
            "Timestamp": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "Machine": machine,
            "Type": m_type,
            "Technician": technician,
            "Issue": issue_desc,
            "Action": action_taken,
            "Status": status
        }])
        
        df = pd.concat([df, new_row], ignore_index=True)
        df.to_csv(DB_FILE, index=False)
        st.success(f"Log for {machine} saved successfully!")
        st.balloons()

# --- 4. DATA VIEW ---
st.divider()
st.subheader("📋 Recent Maintenance History")
st.dataframe(df.sort_values(by="Timestamp", ascending=False), use_container_width=True)
