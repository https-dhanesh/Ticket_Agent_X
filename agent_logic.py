import google.genai as genai
from pydantic import BaseModel
import os
import json
from dotenv import load_dotenv

load_dotenv()

class TicketAnalysis(BaseModel):
    tech_stack: str
    severity: str
    sentiment: str
    reasoning: str
    assigned_to: str
    suggested_fix: str

def check_incident_status(new_issue, active_tickets):
    """Detects duplicates and system-wide outages using semantic reasoning."""
    if not active_tickets:
        return {"is_duplicate": False, "is_outage": False, "reason": "No active tickets."}

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    context = "\n".join([f"- {t['issue']} (Sev: {t['severity']})" for t in active_tickets[:10]])

    prompt = f"""
    New Issue: "{new_issue}"
    Active Tickets: {context}

    TASK:
    1. Is this a semantic duplicate of an active ticket?
    2. Are there 3+ P1 tickets suggesting a 'System-wide Outage'?
    
    Return JSON: 
    {{"is_duplicate": bool, "duplicate_of": "issue_text or null", "is_outage": bool, "reason": "text"}}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    return json.loads(response.text)

def get_agent_decision(issue_text, engineers_list, exclude_list=None):
    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    with open("data/knowledge_base.json", "r") as f:
        kb = json.load(f)

    if exclude_list:
        engineers_list = [e for e in engineers_list if e['name'] not in exclude_list]

    prompt = f"""
    You are an Autonomous IT Orchestrator. 
    KNOWLEDGE BASE: {json.dumps(kb)}
    ENGINEER POOL: {json.dumps(engineers_list)}
    USER ISSUE: "{issue_text}"
    Logic: Skill Match > Current Load > Avg TTR. Prioritize Seniors for P1 issues.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config={"response_mime_type": "application/json", "response_schema": TicketAnalysis}
    )
    return response.parsed