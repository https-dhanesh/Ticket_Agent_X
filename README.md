# AgentX: Autonomous Workforce Orchestrator

**AgentX** is an intelligent, agentic system designed to manage IT incident lifecycles autonomously. Moving beyond simple keyword matching, AgentX uses LLM-based reasoning to analyze technical issues, evaluate live workforce capacity, and orchestrate resolutions via a closed-loop feedback system.

---

## Key Features

* **Autonomous Resource Orchestration**: Matches incidents to specialists using a weighted score of skills, current load, and historical TTR (Time-To-Resolve).
* **Semantic Duplicate Detection**: Uses Gemini 1.5 Flash to detect redundant issues reported with different phrasing, preventing alert fatigue.
* **War Room Automation**: Detects clusters of high-severity (P1) incidents and autonomously triggers a Crisis Mode alert via Slack.
* **SLA Breach Predictor**: Real-time monitoring of ticket ages against engineer performance metrics stored in MongoDB Atlas.
* **Dynamic Re-assignment**: Handles human unpredictability by re-orchestrating tasks instantly if an engineer refuses a task.
* **RAG-Powered Grounding**: Uses Retrieval-Augmented Generation to ensure all suggested fixes align with company-specific SOPs found in `knowledge_base.json`.

---

## Tech Stack

- **Brain:** Gemini 2.5 Flash (Google GenAI)
- **Framework:** Python, Streamlit
- **Database:** MongoDB Atlas (State Management)
- **Communication:** Slack API (Webhooks)
- **Data Handling:** Pydantic (Structured Output), Pandas

---

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/https-dhanesh/Ticket_Agent_X.git](https://github.com/https-dhanesh/Ticket_Agent_X.git)
   cd AgentX
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables (.env):**
   ```
    MONGO_URI=your_mongodb_connection_string
    GEMINI_API_KEY=your_google_api_key
    SLACK_WEBHOOK_URL=your_slack_webhook_url
    ```

4. **Run the Application:**
    ```
    streamlit run app.py
    ```

## System Architecture
- The system operates on a "Reasoning-First" loop:

- Ingest: User submits a ticket.

- Audit: Semantic check for duplicates and outages.

- Reason: Gemini selects the best engineer based on live MongoDB telemetry.

- Notify: Real-time push to Slack with the internal reasoning trace.

- Monitor: SLA countdown begins; system awaits a "Solved" or "Refused" trigger.

