# SRE Demo App — Incident Response Runbook

## Application: sre-demo-app-t239b
## Resource Group: AI
## Region: Sweden Central

---

## INCIDENT: HTTP 5xx Errors on Web App

### Detection
- Alert: sre-demo-http-5xx-errors (Sev1)
- Metric: Http5xx > 0 on sre-demo-app-t239b

### Investigation Steps
1. Query App Insights for failed requests in last 2 minutes
2. Check exception traces for stack traces and error details
3. Check if the errors correlate with CPU/memory spikes
4. Check recent deployments or configuration changes

### Remediation Actions (Execute Immediately)
1. **Restart the web app**:
   ```
   az webapp restart --name sre-demo-app-t239b --resource-group AI
   ```
2. **If errors persist after restart, check DB connectivity**:
   ```
   az webapp config appsettings list --name sre-demo-app-t239b --resource-group AI --query "[?name=='DB_HOST' || name=='DB_USER']"
   ```
3. **If DB authentication errors found, verify PostgreSQL credentials**:
   ```
   az postgres flexible-server show --name sre-demo-pgdb --resource-group AI --query "{state:state, fqdn:fullyQualifiedDomainName}"
   ```

### Resolution
- Mark incident as mitigated after confirming Http5xx count returns to 0
- Close the alert

---

## INCIDENT: High CPU Utilization

### Detection
- Alert: sre-demo-cpu-high (Sev2)
- Metric: CpuPercentage > 60% on sre-demo-plan

### Investigation Steps
1. Check App Service Plan CPU metrics for last 5 minutes
2. Identify which app on the plan is consuming CPU
3. Check request patterns for sudden traffic spikes

### Remediation Actions (Execute Immediately)
1. **Scale up the App Service Plan**:
   ```
   az appservice plan update --name sre-demo-plan --resource-group AI --sku B3
   ```
2. **If single app is the culprit, restart it**:
   ```
   az webapp restart --name sre-demo-app-t239b --resource-group AI
   ```
3. **After issue resolves, scale back down**:
   ```
   az appservice plan update --name sre-demo-plan --resource-group AI --sku B2
   ```

### Resolution
- Confirm CpuPercentage drops below 60%
- Mark incident as mitigated

---

## INCIDENT: High Memory Utilization

### Detection
- Alert: sre-demo-memory-high (Sev2)
- Metric: MemoryPercentage > 65% on sre-demo-plan

### Investigation Steps
1. Check MemoryWorkingSet on the web app
2. Check if memory leak pattern exists (continuously increasing)
3. Correlate with application errors

### Remediation Actions (Execute Immediately)
1. **Restart the web app to clear memory**:
   ```
   az webapp restart --name sre-demo-app-t239b --resource-group AI
   ```
2. **If memory remains high, scale up**:
   ```
   az appservice plan update --name sre-demo-plan --resource-group AI --sku B3
   ```

### Resolution
- Confirm MemoryPercentage drops below 65%
- Mark incident as mitigated

---

## INCIDENT: High Response Time

### Detection
- Alert: sre-demo-high-response-time (Sev2)
- Metric: AverageResponseTime > 5s on sre-demo-app-t239b

### Investigation Steps
1. Check which endpoints have slow response times
2. Check if CPU or memory is also elevated
3. Check database query performance

### Remediation Actions (Execute Immediately)
1. **Restart the web app**:
   ```
   az webapp restart --name sre-demo-app-t239b --resource-group AI
   ```
2. **Scale up if under resource pressure**:
   ```
   az appservice plan update --name sre-demo-plan --resource-group AI --sku B3
   ```

### Resolution
- Confirm average response time drops below 5 seconds

---

## INCIDENT: PostgreSQL High CPU

### Detection
- Alert: sre-demo-pg-cpu-high (Sev2)
- Metric: cpu_percent > 70% on sre-demo-pgdb

### Remediation Actions (Execute Immediately)
1. **Scale up PostgreSQL**:
   ```
   az postgres flexible-server update --name sre-demo-pgdb --resource-group AI --sku-name Standard_B2s
   ```

---

## INCIDENT: Database Authentication Failure (Login/Signup broken)

### Detection
- HTTP 5xx errors with exception message containing "password authentication failed"
- Login and Signup pages returning 500 errors

### Investigation Steps
1. Query App Insights exceptions for "password authentication failed" or "OperationalError"
2. Check web app configuration for DB credentials
3. Verify PostgreSQL server is accessible

### Remediation Actions (Execute Immediately)
1. **Restart the web app** (clears any cached broken state):
   ```
   az webapp restart --name sre-demo-app-t239b --resource-group AI
   ```
2. **Verify DB connectivity**:
   ```
   az postgres flexible-server show --name sre-demo-pgdb --resource-group AI --query "{state:state}"
   ```

### Resolution
- Confirm login/signup pages return HTTP 200
- Mark incident as mitigated
