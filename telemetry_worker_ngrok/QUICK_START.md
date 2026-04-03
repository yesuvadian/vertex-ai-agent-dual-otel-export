# Quick Start - 3 Terminals

## Terminal 1: Flask App

```bash
cd telemetry_worker_ngrok
python main.py
```

**Keep this running** - you'll see all processing logs here

---

## Terminal 2: ngrok

```bash
ngrok http 8080
```

**Copy the ngrok URL** (e.g., `https://abc123.ngrok.io`)

---

## Terminal 3: Setup & Test

```bash
cd telemetry_worker_ngrok

# Set your ngrok URL
export NGROK_URL="https://abc123.ngrok.io"

# Update Pub/Sub
gcloud pubsub subscriptions update telemetry-processor \
  --push-endpoint="${NGROK_URL}/process" \
  --project=agentic-ai-integration-490716

# Test
python test_local.py \
  agentic-ai-integration-490716 \
  677b68ce5e429ca85cdc16ef54631ee6 \
  test_local \
  ${NGROK_URL}/process
```

**Watch Terminal 1** for processing logs!

---

## Test with Real Agent

1. Go to: https://console.cloud.google.com/vertex-ai/agents/agent-engines/8081657304514035712
2. Click "Playground"
3. Send: "What is the weather in Tokyo?"
4. **Watch Terminal 1** - traces will flow automatically!

---

## Cleanup

```bash
# Terminal 3
./cleanup.sh

# Terminal 1 & 2
Ctrl+C
```

---

## That's It!

✅ No Cloud Run permissions needed  
✅ See real-time logs  
✅ Test Portal26 export  
✅ Full end-to-end flow
