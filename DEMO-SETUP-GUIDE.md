# SRE Agent Demo — Complete Portal Setup Guide

## ⚠️ CRITICAL: Why Incidents Show "Pending User Action"

The default incident response plan runs in **review** mode. Even though the agent's
top-level mode is `autonomous`, each incident response plan has its OWN autonomy setting.
The default plan = review = agent asks for approval = "Pending User Action".

---

## STEP 1: Fix Incident Response Plan (Fixes Pending User Action)

1. Go to **sre.azure.com** → Select **bfl-sre**
2. Click **Incident platform** tab
3. You'll see the default plan. Click **Edit** (or create a new plan)
4. Configure:
   - **Incident type**: Default (covers all)
   - **Impacted service**: All impacted services
   - **Priority**: All priorities (Sev0-Sev4)
   - **Title contains**: (leave empty to match all)
   - **Execution mode**: ⚡ **Autonomous** ← THIS IS THE KEY FIX
5. Check **Add custom instructions**
6. Paste the contents from `KnowledgeBase/incident-response-plan-instructions.md`
7. Click **Generate** to let the agent build the tool list
8. Review and **Save**

After this, new incidents will be handled autonomously → "Mitigated by Agent" count goes up.

---

## STEP 2: Upload Knowledge Base (Runbooks)

1. Go to **sre.azure.com** → **bfl-sre** → **Settings** → **Knowledge Base** → **Files**
2. Upload these files from the `KnowledgeBase/` folder:
   - `incident-runbook.md` — Detailed remediation procedures for each alert type
   - `architecture.md` — Application architecture and dependencies
3. The agent will index these and use them during incident investigations

**Demo talking point**: "The SRE agent uses your team's runbooks and documentation to make
informed decisions. It doesn't just look at metrics — it follows YOUR procedures."

---

## STEP 3: Configure Connectors

### Outlook Email Connector (for Daily Reports)
1. Go to **sre.azure.com** → **bfl-sre** → **Settings** → **Connectors**
2. Click **Add connector** → **Outlook**
3. Sign in with your Microsoft account
4. Authorize the agent to send emails on your behalf
5. Test by sending a test email

### Teams Connector (optional, for incident notifications)
1. In **Connectors** → **Add connector** → **Teams**
2. Provide your Teams channel webhook URL
3. The agent will post incident updates to Teams

**Demo talking point**: "The agent integrates with your existing communication tools —
Teams for real-time alerts, Outlook for reports, and can connect to any external system via MCP."

---

## STEP 4: Create Sub-Agents in Portal

### Sub-Agent: AppHealthCheck
1. **Subagent builder** → **Create** → **Subagent**
2. Name: `AppHealthCheck`
3. Instructions: Copy from `SubAgents/AppHealthCheck.yaml` (the system_prompt section)
4. Tools: QueryAppInsightsByAppId, GetAzCliHelp, RunAzCliReadCommands, RunAzCliWriteCommands, SearchMemory
5. Handoff: "Health check for SRE Demo App - investigates errors, performance issues"
6. **Create subagent**

### Sub-Agent: BaselineCapture
1. Name: `BaselineCapture`
2. Instructions: Copy from `SubAgents/BaselineCapture.yaml`
3. Tools: QueryAppInsightsByAppId, UploadKnowledgeDocument
4. Handoff: "Capture baseline response time and error rate metrics"

### Sub-Agent: DailyHealthReport
1. Name: `DailyHealthReport`
2. Instructions: Copy from `SubAgents/DailyHealthReport.yaml`
3. Tools: QueryAppInsightsByAppId, RunAzCliReadCommands, SendOutlookEmail
4. Handoff: "Generate and send daily health report"

### Sub-Agent: IncidentReporter
1. Name: `IncidentReporter`
2. Instructions: Copy from `SubAgents/IncidentReporter.yaml`
3. Tools: QueryAppInsightsByAppId, SendOutlookEmail

---

## STEP 5: Create Triggers

### Incident Trigger: All Alerts
1. **Subagent builder** → **Create** → **Incident trigger**
2. Name: `AllAlertsTrigger`
3. Severity: All severity levels
4. Title contains: (leave empty)
5. Agent Autonomy: **Autonomous**
6. Connected subagent: `AppHealthCheck`

### Scheduled Trigger: BaselineTask
1. **Create** → **Scheduled trigger**
2. Name: `BaselineTask`
3. Schedule: Every 15 minutes
4. Connected subagent: `BaselineCapture`

### Scheduled Trigger: DailyReport
1. **Create** → **Scheduled trigger**
2. Name: `DailyReport`
3. Schedule: Daily at 7:00 AM UTC
4. Connected subagent: `DailyHealthReport`

---

## STEP 6: Validate Everything

After portal setup, trigger simulations and verify:

1. Hit https://sre-demo-app-t239b.azurewebsites.net/simulate/500 (10 times)
2. Wait ~2 minutes for alert to fire
3. Check sre.azure.com → bfl-sre → Chat to see the investigation
4. Verify the agent EXECUTES remediation (restart/scale) without asking
5. Check Incident Management dashboard:
   - "Mitigated by Agent" should increase
   - "Pending User Action" should NOT increase

---

## Demo Script: Feature Walkthrough

### 1. Knowledge Base Demo (2 min)
- Show uploaded runbooks in Settings → Knowledge Base
- "The agent uses these runbooks to follow YOUR procedures"

### 2. Incident Response Plan Demo (3 min)
- Show the autonomous plan in Incident Platform tab
- "Every alert is automatically investigated and remediated"
- Trigger /simulate/500 → watch agent handle it end-to-end

### 3. Sub-Agents Demo (2 min)
- Show Subagent Builder with all agents listed
- "Specialized agents for different tasks — health checks, baselines, reporting"

### 4. Connectors Demo (1 min)
- Show configured connectors (Outlook, Teams)
- "Agent communicates through your existing channels"

### 5. Daily Reports Demo (2 min)
- Show the Daily Resources Report thread in Chat
- Show the scheduled trigger configuration
- "Automated daily health reports delivered to your inbox"

### 6. Autonomous Mitigation Demo (5 min)
- Show Incident Management dashboard
- Trigger /simulate/cpu → watch CPU alert fire
- Agent detects → scales up plan → verifies fix → closes incident
- Show "Mitigated by Agent" counter increase
- "Zero human intervention. MTTD under 2 minutes, MTTR under 5 minutes."

### 7. DB Auth Failure Demo (3 min)
- Show working login page
- Hit /simulate/db-creds-break
- Try login → fails with DB auth error (HTTP 500)
- Alert fires → Agent investigates → finds "password authentication failed"
- Agent restarts web app → login works again
- Hit /simulate/db-creds-fix to fully restore
