# Portal26 Authentication Issue - DIAGNOSIS

**Status:** ❌ **Portal26 is rejecting traces due to missing authentication**

**Date:** 2026-03-31  
**Root Cause:** 401 Unauthorized - "no basic auth provided"

---

## Issue Summary

**Problem:** Portal26 dashboard shows no logs despite data being sent

**Cause:** Portal26 endpoint requires Basic Authentication, which we're not sending

**Evidence:**
```
Response Status: 401
Response Body: "no basic auth provided"
```

---

## Test Results

### Direct Portal26 Test

```bash
$ python check_portal26_response.py

POST https://otel-tenant1.portal26.in:4318/v1/traces

Response Status: 401
Response Body: no basic auth provided

[ERROR] Authentication required - check credentials
```

**Diagnosis:** Portal26 is receiving requests but rejecting them ❌

---

## What's Happening

### Current Flow (Failing)

```
Agent → Local Receiver → Portal26
                         ↓
                    POST /v1/traces
                    Headers:
                    - Content-Type: application/x-protobuf
                    - X-Tenant-ID: tenant1
                    ✗ NO AUTHENTICATION
                         ↓
                    401 Unauthorized
                    "no basic auth provided"
                         ↓
                    Portal26 REJECTS data
                         ↓
                    NO LOGS in dashboard ❌
```

---

## What Portal26 Requires

**Authentication Type:** Basic Authentication

**Required Header:**
```http
Authorization: Basic <base64(username:password)>
```

**Example:**
```python
import base64

username = "your_portal26_username"
password = "your_portal26_password"

# Create base64 encoded credentials
credentials = f"{username}:{password}"
encoded = base64.b64encode(credentials.encode()).decode()

headers = {
    'Content-Type': 'application/x-protobuf',
    'X-Tenant-ID': 'tenant1',
    'Authorization': f'Basic {encoded}'  # REQUIRED!
}
```

---

## What Needs to Be Updated

### 1. Local OTEL Receiver

**File:** `local_otel_receiver.py`

**Current (lines 115-126):**
```python
# Forward to Portal26
try:
    headers = {
        'Content-Type': self.headers.get('Content-Type', 'application/x-protobuf'),
        'X-Tenant-ID': 'tenant1'
        # ❌ MISSING: Authorization header
    }
    response = requests.post(
        PORTAL26_ENDPOINT,
        data=body,
        headers=headers,
        timeout=10
    )
```

**Need to Add:**
```python
import base64
import os

# Get credentials from environment
PORTAL26_USERNAME = os.environ.get("PORTAL26_USERNAME", "")
PORTAL26_PASSWORD = os.environ.get("PORTAL26_PASSWORD", "")

# Create auth header
if PORTAL26_USERNAME and PORTAL26_PASSWORD:
    credentials = f"{PORTAL26_USERNAME}:{PORTAL26_PASSWORD}"
    encoded = base64.b64encode(credentials.encode()).decode()
    auth_header = f'Basic {encoded}'
else:
    auth_header = None

# Forward to Portal26
headers = {
    'Content-Type': self.headers.get('Content-Type', 'application/x-protobuf'),
    'X-Tenant-ID': 'tenant1'
}

if auth_header:
    headers['Authorization'] = auth_header  # ✓ ADD THIS

response = requests.post(PORTAL26_ENDPOINT, data=body, headers=headers, timeout=10)
```

### 2. Agent Direct Export (portal26_otel_agent)

**File:** `portal26_otel_agent/agent.py`

**Current (lines 32):**
```python
otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
# ❌ MISSING: Authentication
```

**Need to Add:**
```python
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Get credentials
portal26_username = os.environ.get("PORTAL26_USERNAME", "")
portal26_password = os.environ.get("PORTAL26_PASSWORD", "")

# Create exporter with auth
if portal26_username and portal26_password:
    credentials = f"{portal26_username}:{portal26_password}"
    encoded = base64.b64encode(credentials.encode()).decode()

    otlp_exporter = OTLPSpanExporter(
        endpoint=endpoint,
        headers={
            'Authorization': f'Basic {encoded}',  # ✓ ADD THIS
            'X-Tenant-ID': 'tenant1'
        }
    )
else:
    otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
```

### 3. Environment Variables

**Add to `.env` files:**

```env
# Portal26 Authentication
PORTAL26_USERNAME=your_username_or_api_key
PORTAL26_PASSWORD=your_password_or_secret
```

---

## How to Get Portal26 Credentials

### Option 1: Portal26 Dashboard

1. Log in to Portal26: https://portal26.in (or your Portal26 URL)
2. Navigate to: **Settings** → **API Keys** or **Authentication**
3. Create new API key or view existing credentials
4. Copy Username/API Key and Password/Secret

### Option 2: Portal26 Documentation

Check Portal26 documentation for:
- OTLP endpoint authentication requirements
- API key generation
- Service account credentials

### Option 3: Portal26 Support

Contact Portal26 support:
- Ask for OTLP endpoint authentication credentials
- Mention you're sending telemetry to: `https://otel-tenant1.portal26.in:4318`
- Request tenant_id: `tenant1` credentials

---

## Testing After Fix

Once credentials are added:

### Test 1: Direct Test
```bash
# Add credentials to environment
export PORTAL26_USERNAME="your_username"
export PORTAL26_PASSWORD="your_password"

# Run test
python check_portal26_response.py

# Expected: 200 OK
```

### Test 2: Via Local Receiver
```bash
# Start receiver with credentials
PORTAL26_USERNAME="user" PORTAL26_PASSWORD="pass" python local_otel_receiver.py

# Send test trace
python send_test_trace.py

# Check receiver output for:
# [OK] Forwarded to Portal26: 200
```

### Test 3: Check Portal26 Dashboard

1. Log in to Portal26
2. Navigate to Traces/Telemetry
3. Filter by:
   - Tenant: `tenant1`
   - User: `relusys`
4. Should see traces! ✓

---

## Summary

**Issue:** Portal26 requires authentication (Basic Auth)

**Current State:**
- ✅ Network connectivity: Working
- ✅ Endpoint: Correct
- ✅ Payload format: Valid
- ✅ Data being sent: Yes
- ❌ Authentication: **MISSING**
- ❌ Portal26 response: 401 Unauthorized
- ❌ Logs in dashboard: None

**Solution:** Add Basic Authentication headers

**Need from you:**
1. Portal26 username or API key
2. Portal26 password or secret

**Once provided:**
- I'll update local_otel_receiver.py
- I'll update agent configurations
- Test and verify Portal26 accepts data
- Confirm logs appear in Portal26 dashboard

---

## Quick Fix Commands

**After you provide credentials:**

```bash
# 1. Add to local receiver environment
export PORTAL26_USERNAME="your_username"
export PORTAL26_PASSWORD="your_password"

# 2. Restart receiver
python local_otel_receiver.py

# 3. Send test
python send_test_trace.py

# 4. Should see: [OK] Forwarded to Portal26: 200
```

---

**Waiting for Portal26 credentials to proceed with fix.** 🔐
