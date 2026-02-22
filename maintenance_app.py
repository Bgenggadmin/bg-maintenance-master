import streamlit as st
import pandas as pd
from datetime import datetime
import os

# --- 1. DATA FILES ---
MAINT_LOG = "bg_maintenance_records.csv"

# --- 2. SECURITY ---
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.title("🛠️ B&G Maintenance Access")
    pwd = st.text_input("Enter Maintenance Password", type="password")
    if st.button("Log In"):
        if pwd == "BGMAINT": 
            st.session_state["authenticated"] = True
            st.rerun()
        else: st.error("Access Denied")
    st.stop()

# --- 3. MAIN INTERFACE ---
st.title("🔧 B&G Engineering: Machinery Maintenance")
tabs = st.tabs(["🛠️ Service Log", "📅 Machine Health View"])

with tabs[0]:
    st.subheader("Record Machine Service/Issue")
    
    machines = [
        "TIG Welding Machine", "EOT Crane", "CNC Cutting Machine", 
        "Buffing Machine", "Grinding Machine", "Lathe Machine", 
        "Drilling Machine", "Air Compressor", "Plasma Cutter", "Hydraulic Press"
    ]
    
    c1, c2 = st.columns(2)
    with c1:
        machine = st.selectbox("Select Machinery", machines)
        unit = st.selectbox("Location Unit", ["A", "B", "C"])
        service_type = st.selectbox("Action Type", ["Breakdown Repair", "Preventive Maintenance", "Oil/Filter Change", "General Inspection"])
    with c2:
        status = st.radio("Machine Condition", ["🟢 Operational", "🟡 Under Service", "🔴 Breakdown"])
        next_service = st.date_input("Next Service Due Date")

    details = st.text_area("Work Done / Parts Replaced")

    if st.button("Submit Maintenance Record"):
        now = datetime.now()
        row = f"{now.strftime('%Y-%m-%d')},{machine},{unit},{service_type},{status},{next_service},{details.replace(',', ';')}\n"
        with open(MAINT_LOG, "a") as f: f.write(row)
        st.success(f"Maintenance log for {machine} saved!")

with tabs[1]:
    st.subheader("Current Machinery Status")
    if os.path.exists(MAINT_LOG):
        df = pd.read_csv(MAINT_LOG, names=["Date","Machine","Unit","Type","Status","NextDue","Details"])
        
        # Show breakdown alerts
        breakdowns = df[df["Status"] == "🔴 Breakdown"]
        if not breakdowns.empty:
            st.error(f"Alert: {len(breakdowns)} machines are currently down!")
            st.dataframe(breakdowns)
        
        st.write("### 🏗️ Full Machine History")
        st.dataframe(df.sort_values(by="Date", ascending=False))
    else:
        st.info("No maintenance logs yet.")
