# Azure SRE Agent — Proof of Concept

End-to-end demo of **Azure SRE Agent** autonomously detecting, investigating, and remediating production issues on a live two-tier application.

[![Azure SRE Agent](https://img.shields.io/badge/Azure-SRE%20Agent-0078D4?logo=microsoft-azure)](https://sre.azure.com)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql)](https://postgresql.org)

---

## 🎯 What This Demonstrates

| Capability | Description |
|------------|-------------|
| **Autonomous Incident Response** | SRE Agent detects alerts, investigates root cause via App Insights, and executes remediation (restart, scale) — zero human intervention |
| **Knowledge Base** | Agent uses uploaded runbooks and architecture docs to follow your team's procedures |
| **Sub-Agents** | Specialized agents for health checks, baseline capture, and daily reporting |
| **Incident Response Plans** | Custom plans with autonomous execution mode and explicit remediation instructions |
| **Daily Reports** | Scheduled agent generates health reports with App Insights metrics and emails them |
| **Connectors** | Outlook email and Teams integration for notifications and reporting |
| **Issue Simulation** | Built-in endpoints to trigger real HTTP 500s, CPU spikes, memory pressure, and DB auth failures on demand |

---

## 🏗️ Architecture

```
                        ┌──────────────────────────────────┐
                        │       Azure SRE Agent            │
                        │       (bfl-sre)                  │
                        │                                  │
                        │  ┌────────────┐ ┌─────────────┐  │
                        │  │ Health     │ │ Baseline    │  │
                        │  │ Check     │ │ Capture     │  │
                        │  └────────────┘ └─────────────┘  │
                        │  ┌────────────┐ ┌─────────────┐  │
                        │  │ Daily     │ │ Incident    │  │
                        │  │ Report   │ │ Reporter    │  │
                        │  └────────────┘ └─────────────┘  │
                        └──────────┬───────────────────────┘
                                   │ polls alerts
                                   ▼
┌─────────────┐    ┌──────────────────────┐    ┌─────────────────┐
│  App Service │───▶│  Application Insights │───▶│  Azure Monitor  │
│  (Flask)     │    │  (Traces, Metrics)   │    │  (Alert Rules)  │
│              │    └──────────────────────┘    └────────┬────────┘
│  /login      │                                        │
│  /signup     │                                        ▼
│  /products   │                               ┌────────────────┐
│  /simulate/* │                               │  Action Group  │
└──────┬───────┘                               │  (Email)       │
       │                                       └────────────────┘
       ▼
┌──────────────┐
│  PostgreSQL  │
│  Flex Server │
└──────────────┘
```

---

## 📦 Project Structure

```
├── app.py                      # Flask app with auth & simulation endpoints
├── appinsights_config.py       # OpenCensus App Insights integration
├── wsgi.py                     # Gunicorn entry point
├── startup.sh                  # App Service startup command
├── requirements.txt            # Python dependencies
├── DEMO-SETUP-GUIDE.md         # Step-by-step portal setup guide
│
├── KnowledgeBase/              # Upload to SRE Agent → Settings → Knowledge Base
│   ├── incident-runbook.md                     # Remediation procedures per alert
│   ├── architecture.md                         # App architecture & dependencies
│   └── incident-response-plan-instructions.md  # IRP custom instructions (paste into portal)
│
└── SubAgents/                  # Create in SRE Agent → Subagent Builder
    ├── AppHealthCheck.yaml     # Investigates errors + auto-remediates
    ├── BaselineCapture.yaml    # Captures response time baselines every 15m
    ├── DailyHealthReport.yaml  # Daily health report via email
    └── IncidentReporter.yaml   # Incident summary reports
```

---

## 🚀 Deployed Resources

| Resource | Name | Type |
|----------|------|------|
| Web App | `sre-demo-app-t239b` | Python 3.11 Flask on Linux B2 |
| Database | `sre-demo-pgdb` | PostgreSQL Flexible Server (B1ms) |
| App Insights | `bfl-sre-9b2b519c-8f89-app-insights` | Telemetry & tracing |
| SRE Agent | `bfl-sre` | Autonomous mode, High access |
| Action Group | `bfl-sre-action-group` | Email notifications |

**App URL**: https://sre-demo-app-t239b.azurewebsites.net

---

## 🔔 Alert Rules (10 total)

| Alert | Metric | Threshold | Severity | Window |
|-------|--------|-----------|----------|--------|
| HTTP 5xx Errors | Http5xx | > 0 | Sev1 | 1 min |
| HTTP 4xx Errors | Http4xx | > 5 | Sev2 | 1 min |
| High Response Time | AvgResponseTime | > 5s | Sev2 | 1 min |
| CPU High | CpuPercentage | > 60% | Sev2 | 1 min |
| Memory High | MemoryPercentage | > 65% | Sev2 | 1 min |
| PostgreSQL CPU | cpu_percent | > 70% | Sev2 | 1 min |
| PostgreSQL Storage | storage_percent | > 80% | Sev1 | 1 min |
| PostgreSQL Connections | active_connections | > 20 | Sev2 | 1 min |
| App Exceptions | Log query | > 0 | Sev1 | 5 min |
| Failed Requests | Log query | > 0 | Sev1 | 5 min |

---

## 🧪 Simulation Endpoints

### App Layer Failures
| Endpoint | What It Does | Alert Triggered |
|----------|-------------|-----------------|
| `/simulate/500` | Returns HTTP 500 | sre-demo-http-5xx-errors |
| `/simulate/exception` | Throws unhandled RuntimeError | sre-demo-app-exceptions |
| `/simulate/404` | Returns HTTP 404 | sre-demo-http-4xx-errors |
| `/simulate/slow` | 30-second response delay | sre-demo-high-response-time |
| `/simulate/db-error` | Bad SQL query against PostgreSQL | sre-demo-http-5xx-errors |
| `/simulate/db-creds-break` | Breaks DB credentials for login/signup | sre-demo-http-5xx-errors |
| `/simulate/db-creds-fix` | Restores DB credentials | — |

### Infra Layer Failures
| Endpoint | What It Does | Alert Triggered |
|----------|-------------|-----------------|
| `/simulate/cpu` | CPU spike (4 threads, 60s) | sre-demo-cpu-high |
| `/simulate/memory` | Memory spike (500MB, 120s) | sre-demo-memory-high |

### Auth Pages
| Endpoint | Purpose |
|----------|---------|
| `/signup` | User registration (writes to PostgreSQL) |
| `/login` | User login (authenticates against PostgreSQL) |
| `/logout` | Clear session |

**Demo user**: `demo` / `demo123`

---

## 🎬 Demo Flow (Monday Client Meeting)

### Scenario 1: Application Error → Auto-Remediation (~3 min)
1. Show healthy app at `/` and `/health`
2. Hit `/simulate/500` × 10
3. Alert fires within ~1 min → SRE Agent picks up in ~30s
4. Agent queries App Insights → finds HTTP 500 errors
5. Agent executes `az webapp restart` → app recovers
6. Incident marked as **Mitigated by Agent** ✅

### Scenario 2: DB Authentication Failure (~3 min)
1. Show working `/login` page → login with `demo`/`demo123`
2. Hit `/simulate/db-creds-break`
3. Try login → fails with "password authentication failed" (HTTP 500)
4. Alert fires → Agent investigates → finds DB auth errors in traces
5. Agent restarts app → hit `/simulate/db-creds-fix` to fully restore

### Scenario 3: Infrastructure Pressure (~5 min)
1. Hit `/simulate/cpu` → CPU spikes to >60%
2. CPU alert fires → Agent detects resource pressure
3. Agent scales App Service Plan B2 → B3
4. CPU normalizes → Agent scales back to B2

### Scenario 4: Knowledge Base & Runbooks (~2 min)
1. Open SRE Agent → Settings → Knowledge Base
2. Show uploaded `incident-runbook.md` and `architecture.md`
3. "The agent follows YOUR team's procedures, not generic playbooks"

### Scenario 5: Daily Reports (~2 min)
1. Open Chat → show "Daily Resources Report" threads
2. Show scheduled trigger configuration
3. "Automated daily health reports — no manual effort"

### Scenario 6: Incident Dashboard (~2 min)
1. Open Incident Management tab
2. Show metrics: Incidents Reviewed, Mitigated by Agent, Assisted
3. "Full observability into agent performance and MTTD/MTTR"

---

## ⚙️ Portal Setup

See **[DEMO-SETUP-GUIDE.md](DEMO-SETUP-GUIDE.md)** for complete step-by-step instructions covering:
- Incident Response Plan (autonomous mode)
- Knowledge Base upload
- Sub-agent creation
- Trigger configuration
- Connector setup (Outlook, Teams)

---

## 🧹 Cleanup

```bash
# Delete all demo resources
az group delete --name AI --yes --no-wait

# Or delete individual resources
az webapp delete --name sre-demo-app-t239b --resource-group AI
az appservice plan delete --name sre-demo-plan --resource-group AI --yes
az postgres flexible-server delete --name sre-demo-pgdb --resource-group AI --yes
```

---

## 📋 Prerequisites

- Azure subscription with Contributor access
- Azure SRE Agent deployed ([sre.azure.com](https://sre.azure.com))
- Azure CLI installed and logged in
- Python 3.11+
