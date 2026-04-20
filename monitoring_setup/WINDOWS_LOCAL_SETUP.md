# Windows Local Setup Guide

Test the Portal26 integration on your Windows machine before deploying to AWS.

## Prerequisites

✅ Python 3.8+ installed
✅ GCP credentials file exists
✅ Internet connection to access Portal26

## Step-by-Step Setup

### Step 1: Open PowerShell/Command Prompt

```powershell
# Navigate to monitoring folder
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup
```

### Step 2: Create Virtual Environment (Recommended)

```powershell
# Create virtual environment
python -m venv venv

# Activate it
.\venv\Scripts\activate

# You should see (venv) in your prompt
```

### Step 3: Install Dependencies

```powershell
pip install -r requirements.txt
```

**Expected output:**
```
Successfully installed google-cloud-pubsub-2.18.4 python-dotenv-1.0.0 ...
```

### Step 4: Verify GCP Credentials

```powershell
# Check if credentials file exists
dir C:\Yesu\ai_agent_projectgcp\gcp-credentials.json
```

If missing, download it:
```powershell
# From GCP Console: IAM > Service Accounts > Keys > Add Key > JSON
# Save to: C:\Yesu\ai_agent_projectgcp\gcp-credentials.json
```

### Step 5: Check .env Configuration

```powershell
# View your .env file
type .env
```

**Should show:**
```
OTEL_EXPORTER_OTLP_ENDPOINT=https://otel-tenant1.portal26.in:4318
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
...
```

### Step 6: Test Portal26 Connection

```powershell
python test_portal26_connection.py
```

**Expected output:**
```
================================================================================
PORTAL26 OTEL CONNECTION TEST
================================================================================
Endpoint: https://otel-tenant1.portal26.in:4318
Service: gcp-vertex-monitor
================================================================================

[1/3] Testing endpoint connectivity...
URL: https://otel-tenant1.portal26.in:4318/v1/logs

[2/3] Sending test log...
Payload size: 456 bytes

[3/3] Response received
Status Code: 200
Response: 

================================================================================
✅ SUCCESS - Portal26 connection working!
================================================================================

Next steps:
1. Check Portal26 dashboard for test log
2. Run: python monitor_pubsub_to_portal26.py
3. Verify Reasoning Engine logs appear in Portal26
```

**If you see ✅ SUCCESS** - Portal26 connection is working!

**If you see errors** - See troubleshooting section below.

### Step 7: Test Pub/Sub (Optional)

```powershell
# Pull messages for 30 seconds to test
python ..\portal26_otel_agent\monitor_pubsub.py
```

**Expected output:**
```
Starting scheduled pull
Project: agentic-ai-integration-490716, Timeout: 30s
Listening for messages (30 second timeout)...
```

If you see messages, Pub/Sub is working!

### Step 8: Start Portal26 Forwarder

```powershell
# Use OTEL SDK version (recommended)
python monitor_pubsub_to_portal26_v2.py
```

**Expected output:**
```
================================================================================
GCP PUB/SUB → PORTAL26 FORWARDER (OTEL SDK)
================================================================================
GCP Project: agentic-ai-integration-490716
Pub/Sub Topic: vertex-telemetry-topic
Subscription: vertex-telemetry-subscription
Portal26 Endpoint: https://otel-tenant1.portal26.in:4318
Service Name: gcp-vertex-monitor
Tenant ID: tenant1
User ID: relusys_terraform
================================================================================

[OTEL] ✓ Portal26 log exporter initialized

Starting Pub/Sub listener...
Will forward Reasoning Engine logs to Portal26

[10:30:15] Forwarded: engine-123 | INFO | Total: 1
[10:30:16] Forwarded: engine-123 | INFO | Total: 2
...
```

**Leave this running!** It will continuously forward logs.

### Step 9: Verify in Portal26 Dashboard

1. Open Portal26 in your browser
2. Navigate to **Logs** section
3. Enter query:
   ```
   service.name = "gcp-vertex-monitor"
   ```
4. You should see logs appearing!

Filter by your tenant:
```
tenant.id = "tenant1"
```

### Step 10: Generate Test Logs (Optional)

In another PowerShell window, trigger your Reasoning Engine:

```powershell
# Navigate to project root
cd C:\Yesu\ai_agent_projectgcp

# Run your test script
python test_reasoning_engine.py
```

Within 5-10 seconds, you should see:
- Logs in the forwarder window: `[10:30:20] Forwarded: ...`
- Logs in Portal26 dashboard

## Running in Background (Windows)

### Option 1: Keep PowerShell Window Open

Just leave the PowerShell window running with the forwarder.

### Option 2: Run as Background Process

```powershell
# Start in background
Start-Process python -ArgumentList "monitor_pubsub_to_portal26_v2.py" -WindowStyle Hidden -RedirectStandardOutput "forwarder.log" -RedirectStandardError "forwarder_error.log"

# Check if running
Get-Process python

# View logs
Get-Content forwarder.log -Wait

# Stop
Get-Process python | Where-Object {$_.CommandLine -like "*monitor_pubsub*"} | Stop-Process
```

### Option 3: Windows Service (Advanced)

Use NSSM (Non-Sucking Service Manager):

```powershell
# Download NSSM from nssm.cc
# Install as service
nssm install Portal26Forwarder "C:\Yesu\ai_agent_projectgcp\monitoring_setup\venv\Scripts\python.exe" "C:\Yesu\ai_agent_projectgcp\monitoring_setup\monitor_pubsub_to_portal26_v2.py"

# Start service
nssm start Portal26Forwarder

# Check status
nssm status Portal26Forwarder
```

## Monitoring

### Check if Running

```powershell
# Find Python processes
Get-Process python

# Check for forwarder specifically
Get-Process | Where-Object {$_.ProcessName -eq "python"} | Select-Object Id,ProcessName,StartTime
```

### View Logs

```powershell
# If running in foreground - logs in console

# If running in background
Get-Content forwarder.log -Wait
```

### Stop Forwarder

```powershell
# If running in foreground - Press Ctrl+C

# If running in background
Stop-Process -Name python
```

## Troubleshooting

### Issue 1: "pip not recognized"

```powershell
# Install Python from python.org
# Or use py instead
py -m pip install -r requirements.txt
```

### Issue 2: Portal26 Connection Test Fails

**Error: Connection timeout**
```powershell
# Test internet connectivity
ping otel-tenant1.portal26.in

# Check if port is blocked
Test-NetConnection -ComputerName otel-tenant1.portal26.in -Port 4318
```

**Error: 401 Unauthorized**
```powershell
# Verify credentials in .env
type .env | findstr OTEL_EXPORTER_OTLP_HEADERS

# Should show: Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
```

### Issue 3: No Messages from Pub/Sub

```powershell
# Check subscription exists
gcloud pubsub subscriptions describe vertex-telemetry-subscription --project=agentic-ai-integration-490716

# Check for messages
gcloud pubsub subscriptions pull vertex-telemetry-subscription --limit=5 --project=agentic-ai-integration-490716
```

### Issue 4: GCP Credentials Error

```powershell
# Set explicitly
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\Yesu\ai_agent_projectgcp\gcp-credentials.json"

# Verify
echo $env:GOOGLE_APPLICATION_CREDENTIALS
```

### Issue 5: Module Import Errors

```powershell
# Reinstall dependencies
pip uninstall -y -r requirements.txt
pip install -r requirements.txt

# Or reinstall specific module
pip install --force-reinstall google-cloud-pubsub
```

### Issue 6: Firewall Blocking

```powershell
# Check Windows Firewall
# Control Panel > Windows Defender Firewall > Advanced Settings
# Ensure Python is allowed for outbound connections
```

Add firewall rule:
```powershell
# Run as Administrator
New-NetFirewallRule -DisplayName "Python HTTPS" -Direction Outbound -Program "C:\Python39\python.exe" -Action Allow -Protocol TCP -RemotePort 443,4318
```

## Performance Check

### CPU Usage

```powershell
# Check Python process CPU
Get-Process python | Select-Object ProcessName,CPU,WorkingSet
```

Should be < 5% CPU, ~150MB memory.

### Network Usage

```powershell
# View network stats
netstat -e | findstr "Bytes"
```

Should be minimal (<1 Mbps).

## Verification Checklist

✅ Python and pip working
✅ Dependencies installed
✅ GCP credentials file exists
✅ .env configured correctly
✅ Portal26 connection test passes (✅ SUCCESS)
✅ Pub/Sub subscription accessible
✅ Forwarder running without errors
✅ Logs appearing in Portal26 dashboard

## Next Steps After Local Testing

Once everything works locally:

1. ✅ **Confirmed working** - Great!
2. 🔄 **Deploy to AWS** - Follow `AWS_DEPLOYMENT.md` for 24/7 operation
3. 🔄 **Set up monitoring** - CloudWatch alarms for failures
4. 🔄 **Create dashboards** - Portal26 visualizations

## Quick Commands Reference

```powershell
# Setup
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Test
python test_portal26_connection.py

# Run
python monitor_pubsub_to_portal26_v2.py

# Stop
Ctrl+C
```

## Need Help?

- **Connection issues:** Check firewall and internet
- **Auth errors:** Verify .env credentials
- **No Pub/Sub messages:** Check subscription and log sink
- **Script errors:** Check Python version (3.8+)

---

**Ready!** Start with Step 1 and work through each step.
