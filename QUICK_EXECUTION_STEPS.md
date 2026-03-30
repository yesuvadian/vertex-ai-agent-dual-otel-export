# ⚡ Quick Execution Steps

---

## 🖥️ FROM LOCAL MACHINE

### 1. Weather Test
```bash
TOKEN=$(gcloud auth print-identity-token)
curl -X POST https://ai-agent-czvzx73drq-uc.a.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the weather in Tokyo?"}'
```

### 2. Order Test
```bash
TOKEN=$(gcloud auth print-identity-token)
curl -X POST https://ai-agent-czvzx73drq-uc.a.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Check order ORDER-123"}'
```

### 3. OTEL Test
```bash
python test_otel_send.py
```

### 4. Check Logs
```bash
gcloud logging read "resource.labels.service_name=ai-agent" --limit=10 --freshness=5m
```

---

## ☁️ FROM CLOUD CONSOLE

### 1. Open Cloud Shell
- Go to: https://console.cloud.google.com
- Click terminal icon (top-right)

### 2. Run Test
```bash
TOKEN=$(gcloud auth print-identity-token)
curl -X POST https://ai-agent-czvzx73drq-uc.a.run.app/chat \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Weather in Paris"}'
```

### 3. View Logs
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=ai-agent" \
  --limit=10 --freshness=5m
```

---

## 📊 VIEW IN PORTAL26

1. Go to: https://portal26.in
2. Login: `titaniam` / `helloworld`
3. Filter: Service=`ai-agent`, Tenant=`tenant1`

---

## ✅ Expected Results

- **HTTP Status:** 200
- **Response:** `{"final_answer": "..."}`
- **OTEL Status:** HTTP 200 (data accepted)
- **Logs:** Show OTEL exporters configured

---

**✅ Tested:** 2026-03-27
**✅ Status:** ALL WORKING
