# Windows Local Setup - Complete Guide

## 🎯 Goal

Run Portal26 integration **on your Windows PC** to test before deploying to AWS.

## 📋 What You'll Need

- ✅ Windows 10/11
- ✅ Python 3.8+ installed
- ✅ Internet connection
- ✅ 5 minutes

## 🚀 Three Ways to Set Up

### Option 1: Super Easy (Batch Files) ⭐ RECOMMENDED

**Just double-click these files:**

1. **setup.bat** - Installs everything
2. **test.bat** - Tests Portal26 connection
3. **run.bat** - Starts the forwarder

**That's it!** See `WINDOWS_QUICKSTART.md`

### Option 2: PowerShell Commands

```powershell
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup

# Setup
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt

# Test
python test_portal26_connection.py

# Run
python monitor_pubsub_to_portal26_v2.py
```

### Option 3: Command Prompt

```cmd
cd C:\Yesu\ai_agent_projectgcp\monitoring_setup

:: Setup
python -m venv venv
venv\Scripts\activate.bat
pip install -r requirements.txt

:: Test
python test_portal26_connection.py

:: Run
python monitor_pubsub_to_portal26_v2.py
```

## 📊 Expected Output

### During Setup (setup.bat)
```
================================================================================
Portal26 Integration - Windows Setup
================================================================================

[1/5] Python detected
Python 3.11.0

[2/5] Creating virtual environment...
[OK] Virtual environment created

[3/5] Activating virtual environment...

[4/5] Installing dependencies...
[OK] Dependencies installed

[5/5] Checking configuration...
[OK] Configuration file found

================================================================================
Setup Complete!
================================================================================

Next steps:
  1. Test connection: python test_portal26_connection.py
  2. Start forwarder: python monitor_pubsub_to_portal26_v2.py

Press any key to continue . . .
```

### During Test (test.bat)
```
================================================================================
PORTAL26 OTEL CONNECTION TEST
================================================================================
Endpoint: https://otel-tenant1.portal26.in:4318
Service: gcp-vertex-monitor
================================================================================

[1/3] Testing endpoint connectivity...
[2/3] Sending test log...
[3/3] Response received
Status Code: 200

================================================================================
✅ SUCCESS - Portal26 connection working!
================================================================================
```

### During Run (run.bat)
```
================================================================================
GCP PUB/SUB → PORTAL26 FORWARDER (OTEL SDK)
================================================================================
GCP Project: agentic-ai-integration-490716
Portal26 Endpoint: https://otel-tenant1.portal26.in:4318
Service Name: gcp-vertex-monitor
Tenant ID: tenant1
================================================================================

[OTEL] ✓ Portal26 log exporter initialized

Starting Pub/Sub listener...

[11:30:45] Forwarded: engine-123 | INFO | Total: 1
[11:30:47] Forwarded: engine-123 | INFO | Total: 2
[11:30:50] Forwarded: engine-456 | ERROR | Total: 3

--- Stats: 100 received | 100 forwarded | 0 errors ---
```

## ✅ Verification Steps

### 1. Check Forwarder is Running

**Look for these messages:**
```
[OTEL] ✓ Portal26 log exporter initialized
Starting Pub/Sub listener...
[11:30:45] Forwarded: ...
```

### 2. Check Portal26 Dashboard

1. Open Portal26 in browser
2. Go to **Logs** section
3. Search: `service.name = "gcp-vertex-monitor"`
4. Filter: `tenant.id = "tenant1"`
5. **You should see logs appearing!**

### 3. Generate Test Logs

Open another terminal:
```powershell
cd C:\Yesu\ai_agent_projectgcp
python test_reasoning_engine.py
```

Within 10 seconds, you should see:
- New lines in forwarder window
- New logs in Portal26 dashboard

## 🛑 How to Stop

**If running in window:**
- Press `Ctrl+C`

**If running in background:**
```powershell
Get-Process python | Stop-Process
```

## 📁 File Structure

```
monitoring_setup/
├── setup.bat                          ← Run this first
├── test.bat                           ← Test connection
├── run.bat                            ← Start forwarder
│
├── WINDOWS_QUICKSTART.md              ← 30-second guide
├── WINDOWS_LOCAL_SETUP.md             ← Detailed guide (you are here)
├── README_WINDOWS.md                  ← This file
│
├── .env                               ← Your config (ready!)
├── requirements.txt                   ← Python packages
│
├── test_portal26_connection.py        ← Test script
├── monitor_pubsub_to_portal26_v2.py   ← Main forwarder
└── monitor_pubsub_to_portal26.py      ← Alternative
```

## 🔧 Common Issues & Fixes

### Issue: "Python not found"

**Fix:**
1. Download Python from python.org
2. Run installer
3. ✅ Check "Add Python to PATH"
4. Restart terminal

### Issue: "pip not recognized"

**Fix:**
```powershell
python -m pip install -r requirements.txt
```

### Issue: "Connection failed" (test.bat)

**Fix 1: Check internet**
```powershell
ping otel-tenant1.portal26.in
```

**Fix 2: Check firewall**
- Windows Defender Firewall
- Allow Python outbound connections

**Fix 3: Test connectivity**
```powershell
Test-NetConnection -ComputerName otel-tenant1.portal26.in -Port 4318
```

### Issue: "401 Unauthorized"

**Fix:** Check .env file:
```powershell
type .env | findstr OTEL_EXPORTER_OTLP_HEADERS
```

Should show:
```
OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA==
```

### Issue: "No messages from Pub/Sub"

**Fix 1: Check subscription**
```powershell
gcloud pubsub subscriptions describe vertex-telemetry-subscription --project=agentic-ai-integration-490716
```

**Fix 2: Trigger Reasoning Engine**
```powershell
python test_reasoning_engine.py
```

**Fix 3: Check log sink**
- See `LOG_SINK_INTEGRATION_TEST.md`

### Issue: "Module not found"

**Fix:**
```powershell
.\venv\Scripts\activate
pip install --force-reinstall -r requirements.txt
```

## 🎨 Customization

### Change Batch Size (for performance)

Edit `.env`:
```bash
# For high volume
PORTAL26_BATCH_SIZE=50
PORTAL26_BATCH_TIMEOUT=10

# For low latency
PORTAL26_BATCH_SIZE=5
PORTAL26_BATCH_TIMEOUT=2
```

### Change Service Name

Edit `.env`:
```bash
OTEL_SERVICE_NAME=my-custom-name
```

Then restart forwarder.

## 📊 Performance on Windows

**Typical resource usage:**
- CPU: 2-5%
- Memory: 100-150 MB
- Network: <1 Mbps

**Runs smoothly on:**
- Windows 10/11
- Any modern PC
- Background or foreground

## 🔄 Keep It Running

### Option 1: Leave Window Open
Just keep the PowerShell/CMD window open with run.bat

### Option 2: Run as Windows Service
See WINDOWS_LOCAL_SETUP.md for NSSM setup

### Option 3: Task Scheduler
- Import `scheduled-monitoring.xml`
- Runs automatically at boot

## 🌐 When to Move to AWS

**Keep local if:**
- ✅ Testing/development
- ✅ Your PC is always on
- ✅ Occasional monitoring

**Move to AWS if:**
- ❌ Need 24/7 reliability
- ❌ Your PC shuts down
- ❌ Production workload
- ❌ Multiple team members

See `AWS_DEPLOYMENT.md` when ready.

## 📚 Full Documentation

| Document | Purpose |
|----------|---------|
| **WINDOWS_QUICKSTART.md** | 30-second setup |
| **WINDOWS_LOCAL_SETUP.md** | Complete Windows guide |
| **SETUP_GUIDE.md** | General setup |
| **AWS_DEPLOYMENT.md** | Cloud deployment |
| **START_HERE.md** | Quick overview |

## ✨ Success Checklist

- ✅ Python installed
- ✅ Dependencies installed (setup.bat)
- ✅ Portal26 test passes (test.bat)
- ✅ Forwarder running (run.bat)
- ✅ Logs showing in forwarder window
- ✅ Logs appearing in Portal26 dashboard
- ✅ No errors in output

## 🎯 Next Steps

1. ✅ **Working locally?** Great! Keep testing
2. 🔄 **Ready for production?** Deploy to AWS
3. 🔄 **Create dashboards** in Portal26
4. 🔄 **Set up alerts** for errors
5. 🔄 **Share access** with team

---

**Questions?** See WINDOWS_LOCAL_SETUP.md for detailed troubleshooting.
