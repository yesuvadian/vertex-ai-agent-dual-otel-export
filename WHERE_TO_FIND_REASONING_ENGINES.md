# Where to Find Vertex AI Reasoning Engines in Google Cloud Console

**Date**: 2026-04-10

---

## Navigation Path

### Method 1: Via Vertex AI
```
1. Go to: https://console.cloud.google.com/
2. Select Project: agentic-ai-integration-490716
3. Click hamburger menu (☰) → Vertex AI
4. In left sidebar → Agent Builder
5. Click → Reasoning Engines
```

### Method 2: Direct URL
```
https://console.cloud.google.com/vertex-ai/reasoning-engines?project=agentic-ai-integration-490716
```

### Method 3: Search
```
1. Press "/" in Google Cloud Console (search)
2. Type: "reasoning engines"
3. Click the result
```

---

## Why They Don't Show in Cloud Run

| Service Type | Location | Purpose |
|--------------|----------|---------|
| **Reasoning Engines** | Vertex AI → Agent Builder | Managed AI agents with reasoning capabilities |
| **Cloud Run** | Cloud Run section | Containerized HTTP services |
| **Endpoints** | Vertex AI → Endpoints | Model serving endpoints (for ML models) |
| **Cloud Functions** | Cloud Functions section | Event-driven serverless functions |

They are **completely different services** even though they all run code in the cloud.

---

## Visual Hierarchy

```
Google Cloud Console
│
├─ Compute
│  ├─ Compute Engine (VMs)
│  ├─ Cloud Run (Containers)
│  └─ Cloud Functions (Serverless)
│
└─ Vertex AI
   ├─ Model Registry (Stored models)
   ├─ Endpoints (Deployed models)
   ├─ Training (Model training jobs)
   └─ Agent Builder
      ├─ Reasoning Engines ← HERE!
      └─ Search & Conversation
```

---

## Why This Was Confusing

### 1. Service Name Mismatch
```
OTEL telemetry showed:
  service.name: "portal26_otel_agent"

This is NOT the Reasoning Engine name!
It's just an environment variable:
  OTEL_SERVICE_NAME="portal26_otel_agent"
```

### 2. Actual Reasoning Engine Names Were Different
```
✓ Reasoning Engine 1: "Post-ADK Manual OTEL Test"
✓ Reasoning Engine 2: "Post-ADK Debug Agent"

Both had OTEL_SERVICE_NAME="portal26_otel_agent" in their .env
```

### 3. Console UI Lag
The Vertex AI Reasoning Engines section is relatively new (2024-2025) and not as prominent as older services like Cloud Run.

---

## How to Check via Console (Step-by-Step)

### Before (When Engines Existed)

1. Navigate to: Console → Vertex AI → Agent Builder → Reasoning Engines
2. You would see:

| Display Name | ID | Created | Status |
|--------------|----|---------:|--------|
| Post-ADK Manual OTEL Test | 4833919858389286912 | 2026-04-09 14:02 | Active |
| Post-ADK Debug Agent | 7765763215807479808 | 2026-04-09 13:15 | Active |

3. Click on name to see:
   - Environment variables (OTEL_SERVICE_NAME, etc.)
   - Query history
   - Sessions
   - Performance metrics

### After (Now - Deleted)

1. Navigate to same location
2. You'll see:
   ```
   No reasoning engines found
   ```

---

## API vs Console

| Method | Pros | Cons |
|--------|------|------|
| **Console UI** | Visual, easy to browse | Can be hard to find, slower |
| **gcloud CLI** | Fast, scriptable | Not all features available |
| **REST API (curl)** | Most complete, direct | Verbose, requires auth tokens |

We used the REST API because:
- `gcloud vertex-ai reasoning-engines` command doesn't exist yet
- Console UI wasn't obvious where to look
- API is always up-to-date with latest features

---

## Other Hidden Vertex AI Services

These also don't show in Cloud Run:

1. **Reasoning Engines** - Vertex AI → Agent Builder
2. **Agent Builder Apps** - Vertex AI → Agent Builder
3. **Model Garden** - Vertex AI → Model Garden
4. **Batch Predictions** - Vertex AI → Batch predictions
5. **Feature Store** - Vertex AI → Feature Store
6. **Pipelines** - Vertex AI → Pipelines

All are under **Vertex AI**, not Compute services!

---

## Quick Reference Card

**To check what's running in your GCP project:**

```bash
# Cloud Run services
gcloud run services list

# Vertex AI Endpoints (deployed models)
gcloud ai endpoints list --region=us-central1

# Vertex AI Models (in registry)
gcloud ai models list --region=us-central1

# Vertex AI Reasoning Engines (via API)
curl -s -X GET \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/agentic-ai-integration-490716/locations/us-central1/reasoningEngines" \
  -H "Authorization: Bearer $(gcloud auth application-default print-access-token)"

# Compute Engine VMs
gcloud compute instances list

# Cloud Functions
gcloud functions list
```

---

## Lesson Learned

**When debugging telemetry sources:**

1. ✓ Check `service.name` in telemetry (this is configurable!)
2. ✓ Check `os.type` to distinguish cloud (N/A) vs local (darwin/win32)
3. ✓ Check ALL Vertex AI sections, not just Cloud Run
4. ✓ Use API when CLI/Console doesn't show results
5. ✓ Service name in telemetry ≠ actual service/agent name

---

**TL;DR**: Reasoning Engines are in **Vertex AI → Agent Builder**, not Cloud Run. The telemetry's `service.name` is just an environment variable, not the actual resource name.
