# SRE Demo App — Architecture & Dependencies

## Application Overview
- **Name**: sre-demo-app-t239b
- **Type**: Python Flask Web Application
- **Runtime**: Python 3.11 on Linux
- **Hosting**: Azure App Service (Plan: sre-demo-plan, SKU: B2)
- **Region**: Sweden Central
- **URL**: https://sre-demo-app-t239b.azurewebsites.net

## Database
- **Type**: Azure Database for PostgreSQL Flexible Server
- **Name**: sre-demo-pgdb
- **SKU**: Burstable B1ms
- **Database**: sre_demo
- **Tables**: products, users

## Monitoring
- **Application Insights**: bfl-sre-9b2b519c-8f89-app-insights
- **App ID**: 9c5a3799-971b-4315-81a2-953776de9c3f

## Key Endpoints
| Endpoint | Purpose | Expected Status |
|----------|---------|-----------------|
| / | Home page with products | 200 |
| /health | Health check (app + DB) | 200 |
| /login | User login | 200 |
| /signup | User registration | 200 |
| /api/products | Products JSON API | 200 |

## Alert Rules
| Alert | Metric | Threshold | Severity |
|-------|--------|-----------|----------|
| sre-demo-http-5xx-errors | Http5xx | > 0 | Sev1 |
| sre-demo-http-4xx-errors | Http4xx | > 5 | Sev2 |
| sre-demo-high-response-time | AverageResponseTime | > 5s | Sev2 |
| sre-demo-cpu-high | CpuPercentage | > 60% | Sev2 |
| sre-demo-memory-high | MemoryPercentage | > 65% | Sev2 |
| sre-demo-pg-cpu-high | cpu_percent | > 70% | Sev2 |
| sre-demo-pg-storage-high | storage_percent | > 80% | Sev1 |
| sre-demo-pg-connections-high | active_connections | > 20 | Sev2 |

## Scaling Guidance
- **Scale up**: B2 → B3 (more CPU/memory per instance)
- **Scale out**: 1 → 2 instances (horizontal scaling)
- **PostgreSQL scale up**: B1ms → B2s (more DB compute)
- **Always scale back after issue resolves to manage costs**
