# Setup Guide - Enable Vertex AI Generative Models

## Current Status

✅ **Completed:**
- Project ID configured: `agentic-ai-integration-490716`
- Portal26 telemetry configured
- Dual-agent system ready
- Server running on port 8005

❌ **Needs Action:**
- Generative AI models not accessible
- Model access needs to be enabled

## Error You're Seeing

```
404 NOT_FOUND: Publisher Model `gemini-pro` was not found
or your project does not have access to it.
```

This means the Vertex AI API is enabled, but **Generative AI models** specifically need additional access.

---

## 🔧 Step-by-Step Fix

### Step 1: Enable Generative AI

**Option A: Via Console (Easiest)**

1. Open this link:
   https://console.cloud.google.com/vertex-ai/generative?project=agentic-ai-integration-490716

2. You should see a page about "Generative AI Studio"

3. If prompted, click **"Enable All Recommended APIs"**

4. Accept any Terms of Service if shown

**Option B: Via gcloud CLI**

```bash
# Enable the Generative Language API
gcloud services enable generativelanguage.googleapis.com \
  --project=agentic-ai-integration-490716

# Or enable all Vertex AI APIs
gcloud services enable \
  aiplatform.googleapis.com \
  generativelanguage.googleapis.com \
  --project=agentic-ai-integration-490716
```

### Step 2: Verify Model Access

Visit the Model Garden to see available models:
https://console.cloud.google.com/vertex-ai/publishers/google/model-garden?project=agentic-ai-integration-490716

You should see:
- Gemini 1.5 Pro
- Gemini 1.5 Flash
- Other Gemini models

### Step 3: Authenticate (if not done)

```bash
gcloud auth application-default login
```

This opens a browser for you to sign in with your Google account.

### Step 4: Test the Agent

Once enabled, test immediately:

```bash
curl -X POST http://127.0.0.1:8005/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in New York?"}'
```

Or use the test script:

```bash
python test_api.py
```

---

## 🔍 Verify Your Setup

### Check if APIs are enabled:

```bash
gcloud services list --enabled --project=agentic-ai-integration-490716 | grep -E "aiplatform|generativelanguage"
```

You should see:
- `aiplatform.googleapis.com` ✓
- `generativelanguage.googleapis.com` ✓

### Check IAM permissions:

https://console.cloud.google.com/iam-admin/iam?project=agentic-ai-integration-490716

Your account needs one of these roles:
- **Vertex AI User** (recommended)
- **Vertex AI Administrator**
- **Editor** or **Owner**

---

## 📊 What Happens After Enabling

Once you enable Generative AI models, the agent will:

1. ✅ Connect to Gemini model (`gemini-pro`)
2. ✅ Process your queries
3. ✅ Call tools (get_weather, get_order_status)
4. ✅ Return responses
5. ✅ Send telemetry to Portal26

---

## 🚨 Common Issues

### "API not enabled" even after enabling

**Solution:** Wait 2-3 minutes for changes to propagate, then try again.

### "Permission denied"

**Solution:** Check IAM roles. Add "Vertex AI User" role to your account:

```bash
gcloud projects add-iam-policy-binding agentic-ai-integration-490716 \
  --member="user:YOUR_EMAIL@gmail.com" \
  --role="roles/aiplatform.user"
```

### "Quota exceeded"

**Solution:** Check your quota limits:
https://console.cloud.google.com/iam-admin/quotas?project=agentic-ai-integration-490716

---

## 📞 Quick Links

| Resource | Link |
|----------|------|
| **Vertex AI Dashboard** | https://console.cloud.google.com/vertex-ai?project=agentic-ai-integration-490716 |
| **Generative AI Studio** | https://console.cloud.google.com/vertex-ai/generative?project=agentic-ai-integration-490716 |
| **API Library** | https://console.cloud.google.com/apis/library?project=agentic-ai-integration-490716 |
| **Model Garden** | https://console.cloud.google.com/vertex-ai/publishers/google/model-garden?project=agentic-ai-integration-490716 |
| **IAM & Admin** | https://console.cloud.google.com/iam-admin/iam?project=agentic-ai-integration-490716 |
| **Quotas** | https://console.cloud.google.com/iam-admin/quotas?project=agentic-ai-integration-490716 |

---

## ✅ Quick Test After Setup

Run this to verify everything works:

```bash
python -c "
from agent_manual import client, MODEL_NAME, run_agent
print('Testing agent...')
result = run_agent('What is the weather in Tokyo?')
print('Result:', result)
"
```

If you see a response (not an error), you're all set! 🎉

---

## 📝 Summary

**Current Server:** http://127.0.0.1:8005
**Model:** gemini-pro
**Status:** Waiting for model access to be enabled

Once you complete Step 1 above, the agent will work immediately!
