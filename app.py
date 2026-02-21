import streamlit as st
import pandas as pd
from pymongo import MongoClient
import os
import requests
from agent_logic import get_agent_decision, check_incident_status
from dotenv import load_dotenv
from datetime import datetime, timedelta
import certifi

ca = certifi.where()
load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"), tlsCAFile=ca)
db = client.AgentX
engineers_col, tickets_col = db.engineers, db.tickets

st.set_page_config(page_title="AgentX Orchestrator", layout="wide", page_icon="🛡️")

def send_slack_notification(result_obj, issue_text, is_war_room=False):
    url = os.getenv("SLACK_WEBHOOK_URL")
    if not url: return
    if is_war_room:
        payload = {
            "attachments": [{
                "color": "#ff4b4b",
                "title": "WAR ROOM INITIATED",
                "text": issue_text
            }]
        }
    else:
        payload = {
            "attachments": [{
                "color": "#36a64f",
                "title": f"Assignment: {result_obj.assigned_to}",
                "fields": [
                    {"title": "Severity", "value": result_obj.severity, "short": True},
                    {"title": "Tech Stack", "value": result_obj.tech_stack, "short": True},
                    {"title": "Issue", "value": issue_text, "short": False},
                    {"title": "Reasoning", "value": result_obj.reasoning, "short": False}
                ],
                "footer": "AgentX Autonomous Orchestrator"
            }]
        }
    requests.post(url, json=payload)

# --- MAIN UI ---
st.title("Autonomous Workforce Agent")

with st.sidebar:
    st.header("Admin Controls")
    if st.button("Reset System"):
        engineers_col.update_many({}, {"$set": {"current_load": 0}})
        tickets_col.delete_many({})
        st.rerun()

col_in, col_out = st.columns([1, 1.5], gap="large")

with col_in:
    st.header("New Incident")
    u_name = st.text_input("Reporter Name")
    u_issue = st.text_area("Describe the issue...", height=100)
    
    if st.button("Submit & Orchestrate", use_container_width=True):
        if u_name and u_issue:
            # A. PRE-CHECK: Duplicate & Outage Detection
            active_tickets = list(tickets_col.find({"status": "In Progress"}))
            status = check_incident_status(u_issue, active_tickets)
            
            if status.get("is_outage"):
                send_slack_notification(None, "Multiple P1s detected! Engineers to general channel.", is_war_room=True)
                st.error("System-wide outage detected! War Room protocol initiated.")
            
            if status.get("is_duplicate"):
                st.warning(f"**Duplicate Detected!** Matches: '{status['duplicate_of']}'")
                st.info(f"Reasoning: {status['reason']}")
            else:
                # B. Normal Assignment Flow
                engineers_list = list(engineers_col.find({}, {'_id': 0}))
                with st.spinner("Agent reasoning..."):
                    result = get_agent_decision(u_issue, engineers_list)
                    st.session_state.result = result
                    
                    # Update DB
                    engineers_col.update_one({"name": result.assigned_to}, {"$inc": {"current_load": 1}})
                    tickets_col.insert_one({
                        "reporter": u_name, 
                        "issue": u_issue, 
                        "assigned_to": result.assigned_to,
                        "severity": result.severity, 
                        "status": "In Progress", 
                        "timestamp": datetime.now()
                    })
                    
                    send_slack_notification(result, u_issue)
                    st.rerun()

with col_out:
    st.header("Agentic Reasoning")
    if "result" in st.session_state:
        res = st.session_state.result
        st.metric("Target Specialist", res.assigned_to, delta=res.severity)
        with st.expander("Reasoning Trace", expanded=True):
            st.info(res.reasoning)
        st.success(f"**Immediate Fix:** {res.suggested_fix}")

st.divider()
st.header("📋 Active Task Board")

active_tickets = list(tickets_col.find({"status": "In Progress"}))

for ticket in active_tickets:
    eng = engineers_col.find_one({"name": ticket['assigned_to']})
    avg_ttr = eng.get('avg_ttr_min', 30) if eng else 30
    
    time_passed = (datetime.now() - ticket['timestamp']).total_seconds() / 60
    mins_left = avg_ttr - time_passed

    t_col1, t_col2, t_col3, t_col4 = st.columns([2, 1, 1, 1])
    t_col1.write(f"**{ticket['assigned_to']}**: {ticket['issue'][:50]}...")
    
    if mins_left < 0:
        t_col2.error(f"SLA Breach: {abs(int(mins_left))}m")
    else:
        t_col2.warning(f"{int(mins_left)}m left")
    
    with t_col3.expander("Resolve"):
        fb = st.text_input("AI Fix Helpful?", key=f"fb_{ticket['_id']}")
        if st.button("Confirm", key=f"s_{ticket['_id']}"):
            engineers_col.update_one({"name": ticket['assigned_to']}, {"$inc": {"current_load": -1}})
            tickets_col.update_one({"_id": ticket['_id']}, {"$set": {"status": "Solved", "feedback": fb}})
            st.rerun()
        
    if t_col4.button("Refuse", key=f"ref_{ticket['_id']}"):
        engineers_col.update_one({"name": ticket['assigned_to']}, {"$inc": {"current_load": -1}})
        engineers_list = list(engineers_col.find({}, {'_id': 0}))
        new_res = get_agent_decision(ticket['issue'], engineers_list, exclude_list=[ticket['assigned_to']])
        
        tickets_col.update_one({"_id": ticket['_id']}, {"$set": {"assigned_to": new_res.assigned_to, "timestamp": datetime.now()}})
        engineers_col.update_one({"name": new_res.assigned_to}, {"$inc": {"current_load": 1}})
        
        send_slack_notification(new_res, ticket['issue'])
        st.rerun()

# --- WORKFORCE STATUS ---
st.divider()
st.subheader("Workforce Status")
try:
    engineers_df = pd.DataFrame(list(engineers_col.find({}, {'_id': 0})))
    if not engineers_df.empty:
        st.dataframe(engineers_df, use_container_width=True, hide_index=True)
    else:
        st.info("No engineers found in database.")
except Exception as e:
    st.error(f"Error loading workforce: {e}")