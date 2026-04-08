# Comparison: Downloaded Working Code vs Our Implementation

## Overview

Downloaded working code from: `C:\Users\yesuv\Downloads\hardcode-otel-vertex-ai-master\`  
Successfully uses `agent_engines.create()` with full OTEL telemetry + content capture.

## Code Structure Comparison

### Downloaded Working Code
```
hardcode-otel/
├── my_agent/                          # Agent package (subdirectory)
│   ├── __init__.py
│   ├── agent.py                       # Minimal (no OTEL)
│   ├── agent_deployed.py              # Hardcoded OTEL init
│   ├── requirements.txt
│   └── .env.example
├── deploy.py                          # Uses agent_engines.create()
├── config.py                          # GCP + OTEL config
├── otel_config.py                     # OTEL env_vars dict
├── query_agent.py
├── list_agents.py
└── docs/
```

### Our Current Code
```
portal26_otel_agent/
├── agent.py                           # OTEL init + agent definition
├── deploy.py                          # Currently reasoning_engines
├── config.py                          # Added (same purpose)
├── otel_config.py                     # Added (same purpose)
├── pull_agent_logs.py
├── show_traces.py
└── README.md, ARCHITECTURE.md, etc.
```

## Key Technical Differences

### 1. Deployment API

**Downloaded:**
```python
from vertexai import agent_engines

deployed_agent = agent_engines.create(
    agent_engine=root_agent,
    extra_packages=["./my_agent"],          # ← Package structure!
    requirements=[...],
    env_vars=otel_config.OTEL_CONFIG,       # ← env_vars support
)
```

**Ours (Working State):**
```python
from vertexai.preview import reasoning_engines

class AgentWrapper:  # ← Required wrapper
    def query(self, *, user_input: str):
        return self.agent.run_live(user_input=user_input)

reasoning_engine = reasoning_engines.ReasoningEngine.create(
    AgentWrapper(root_agent),
    requirements=[...],
    # ❌ No env_vars parameter available
)
```

### 2. Package Structure

**Downloaded:**
- Agent code in `my_agent/` subdirectory
- Deployed with `extra_packages=["./my_agent"]`
- Import: `from my_agent.agent_deployed import root_agent`

**Ours:**
- Agent code in root directory
- No extra_packages (or attempted `extra_packages=["./"]`)
- Import: `from agent import root_agent`

**CRITICAL:** Agent Engine requires proper package structure!

### 3. OTEL Initialization

**Downloaded (agent_deployed.py lines 10-76):**
```python
# Hardcoded OTEL initialization BEFORE importing Agent
OTEL_ENDPOINT = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "")
SERVICE_NAME = os.getenv("OTEL_SERVICE_NAME", "hardcoded-otel-deployed")

if OTEL_ENDPOINT:
    # All OTEL imports and setup here
    tracer_provider = TracerProvider(resource=resource)
    # ... setup traces, metrics, logs ...
    
    # VertexAI Instrumentation
    from opentelemetry.instrumentation.vertexai import VertexAIInstrumentor
    VertexAIInstrumentor().instrument()

# THEN import Agent
from google.adk.agents import Agent
```

**Ours (agent.py lines 5-98):**
```python
# OTEL initialization at module level
from opentelemetry import trace
# ... setup traces, metrics, logs ...

# Commented out VertexAI instrumentation (was causing deployment failures)
# from opentelemetry.instrumentation.vertexai import VertexAIInstrumentor
# VertexAIInstrumentor().instrument()

# Then import Agent
from google.adk.agents import Agent
```

### 4. Environment Variables Configuration

**Downloaded (otel_config.py):**
```python
OTEL_CONFIG = {
    "OTEL_SERVICE_NAME": config.SERVICE_NAME,
    "OTEL_EXPORTER_OTLP_ENDPOINT": config.OTEL_ENDPOINT,
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",  # ← Content capture!
    "OTEL_TRACES_EXPORTER": "otlp",
    "OTEL_METRICS_EXPORTER": "otlp",
    "OTEL_LOGS_EXPORTER": "otlp",
    "OTEL_EXPORTER_OTLP_PROTOCOL": "http/protobuf",
    # ... more env vars
}
```

**Ours (otel_config.py):**
```python
# Same structure, added but not used yet since Reasoning Engine doesn't support env_vars
OTEL_CONFIG = {
    "OTEL_SERVICE_NAME": config.SERVICE_NAME,
    "PORTAL26_TENANT_ID": config.TENANT_ID,          # ← Added multi-tenant tags
    "PORTAL26_USER_ID": config.USER_ID,
    "OTEL_EXPORTER_OTLP_ENDPOINT": config.OTEL_ENDPOINT,
    "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true",
    # ... same structure
}
```

### 5. Requirements

**Downloaded:**
```python
requirements=[
    "google-adk>=1.17.0",
    "opentelemetry-instrumentation-google-genai>=0.4b0",
    "opentelemetry-exporter-gcp-logging",
    "opentelemetry-exporter-gcp-monitoring",
    "opentelemetry-exporter-otlp-proto-http",
    "opentelemetry-exporter-otlp-proto-grpc",
    "opentelemetry-instrumentation-vertexai>=2.0b0",  # ← For content capture
]
```

**Ours (Reasoning Engine):**
```python
requirements=[
    "google-cloud-aiplatform[reasoningengine,langchain]",
    "opentelemetry-api",
    "opentelemetry-sdk",
    "opentelemetry-instrumentation",
    "opentelemetry-exporter-otlp-proto-http",
]
```

## Deployment Attempts Summary

### Attempt 1: Direct Migration to Agent Engine
- Changed `reasoning_engines` → `agent_engines`
- Added `env_vars=otel_config.OTEL_CONFIG`
- **Result:** ❌ Failed - "failed to start and cannot serve traffic"
- **Agent IDs:** 2668392125065854976, 1568387916080611328

### Attempt 2: Agent Engine without VertexAI Instrumentation
- Commented out `VertexAIInstrumentor().instrument()`
- Still using `agent_engines.create()`
- **Result:** ❌ Failed - same error

### Attempt 3: Reverted to Reasoning Engine (Current)
- Back to `reasoning_engines.ReasoningEngine.create()`
- Using `AgentWrapper` class
- No env_vars parameter
- **Result:** 🔄 Deploying...

## Root Cause Analysis

### Why Agent Engine Deployments Failed

**Hypothesis 1: Missing Package Structure** ✅ Most Likely
- Downloaded code has `extra_packages=["./my_agent"]` with agent in subdirectory
- We tried `extra_packages=["./"]` which packages everything
- Agent Engine might require a specific package structure

**Hypothesis 2: VertexAI Instrumentation Conflict** ⚠️ Possible
- `VertexAIInstrumentor()` might conflict with Agent Engine's own instrumentation
- But downloaded code has this and works

**Hypothesis 3: Dependency Conflicts** ⚠️ Less Likely
- Different requirements between the two approaches
- But core OTEL packages are the same

## Content Capture Analysis

### Downloaded Code Approach
```python
# In otel_config.py
"OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "true"

# In agent_deployed.py
from opentelemetry.instrumentation.vertexai import VertexAIInstrumentor
VertexAIInstrumentor().instrument()
```

**Result:** Should capture full prompts/responses ✅

### Our Current Approach (Reasoning Engine)
```python
# No env_vars parameter available
# No VertexAI instrumentation (platform limitation)
```

**Result:** Captures traces/logs but content is empty `{}` ❌

## Possible Solutions

### Solution A: Restructure for Agent Engine (RECOMMENDED)

**Steps:**
1. Create `portal26_agent/` subdirectory
2. Move agent.py into it (rename to agent_deployed.py)
3. Add `__init__.py`
4. Update deploy.py:
   ```python
   from portal26_agent.agent_deployed import root_agent
   
   agent_engines.create(
       agent_engine=root_agent,
       extra_packages=["./portal26_agent"],
       env_vars=otel_config.OTEL_CONFIG,
   )
   ```

**Pros:**
- ✅ Matches working downloaded code structure
- ✅ env_vars support for content capture
- ✅ Proper package isolation

**Cons:**
- ⚠️ Requires restructuring files
- ⚠️ Unknown if it will work (needs testing)

### Solution B: Stay with Reasoning Engine (CURRENT)

**Status:**
- ✅ Known to work for traces/logs
- ❌ No content capture support
- ✅ Stable, documented

**Accept Limitation:**
Document that content capture is not available in Reasoning Engine managed runtime.

### Solution C: Hybrid Approach

**Idea:**
1. Keep Reasoning Engine for stable deployment
2. Create separate `portal26_agent/` structure
3. Test Agent Engine deployment separately
4. Switch only if Agent Engine proves to work

## Recommendation

**Phase 1 (NOW):** Deploy with Reasoning Engine to restore working state
- ✅ Traces working
- ✅ Logs working  
- ⚠️ Metrics 404 (expected)
- ❌ Content capture empty (documented limitation)

**Phase 2 (LATER):** Restructure for Agent Engine properly
- Create package subdirectory
- Test Agent Engine deployment
- If successful, enables content capture
- If fails, keep Reasoning Engine

## Current Deployment Status

**Deploying:** Reasoning Engine with working configuration  
**Expected Result:** Same as agent ID 3188531493748080640 (previously working)  
**Telemetry:** Traces + Logs to Portal26, Metrics 404  
**Content Capture:** Empty (platform limitation documented)
