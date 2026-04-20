# Windows Quick Start (30 Seconds)

## Super Simple Setup

### Step 1: Run Setup (Double-click)
```
setup.bat
```

### Step 2: Test Connection (Double-click)
```
test.bat
```

**Look for:** `✅ SUCCESS - Portal26 connection working!`

### Step 3: Start Forwarder (Double-click)
```
run.bat
```

**Leave it running!** Logs will flow to Portal26.

---

## That's It!

Your logs are now forwarding:
- GCP Vertex AI → Pub/Sub → Portal26

**Verify:** Open Portal26 dashboard and search:
```
service.name = "gcp-vertex-monitor"
```

---

## Manual Commands (Optional)

If you prefer PowerShell:

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
```

---

## Troubleshooting

**"Python not found"**
- Install Python from python.org
- Make sure "Add to PATH" is checked

**"Connection failed"**
- Check internet connection
- Verify firewall allows outbound HTTPS

**"No messages"**
- Trigger your Reasoning Engine
- Wait 10-20 seconds for logs

---

## Full Documentation

- **WINDOWS_LOCAL_SETUP.md** - Complete Windows guide
- **SETUP_GUIDE.md** - Detailed instructions
- **AWS_DEPLOYMENT.md** - Deploy to cloud

---

**Need help?** See WINDOWS_LOCAL_SETUP.md for detailed troubleshooting.
