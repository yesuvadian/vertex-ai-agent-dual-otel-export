import logging
import time
from fastapi import FastAPI
from pydantic import BaseModel
from agent_router import run_agent, get_agent_status

# Initialize OpenTelemetry before app creation
from telemetry import tracer, meter

app = FastAPI()

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# OpenTelemetry instrumentation (optional - may fail with newer FastAPI versions)
try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    FastAPIInstrumentor.instrument_app(app)
    logger.info("[app] OpenTelemetry instrumentation enabled")
except Exception as e:
    logger.warning(f"[app] OpenTelemetry instrumentation skipped: {e}")

# Create metrics
request_counter = meter.create_counter(
    name="agent_requests_total",
    description="Total number of agent requests",
    unit="1"
)

response_time_histogram = meter.create_histogram(
    name="agent_response_time_seconds",
    description="Agent response time in seconds",
    unit="s"
)

class ChatRequest(BaseModel):
    message: str

@app.get("/")
def root():
    logger.info("Root endpoint accessed")
    return {
        "service": "AI Agent API",
        "agent_config": get_agent_status(),
        "endpoints": {
            "chat": "POST /chat",
            "status": "GET /status"
        }
    }

@app.get("/status")
def status():
    logger.info("Status endpoint accessed")
    return get_agent_status()

@app.post("/chat")
def chat(req: ChatRequest):
    start_time = time.time()
    logger.info(f"Chat request received: {req.message[:50]}...")

    with tracer.start_as_current_span("agent_chat") as span:
        span.set_attribute("user.message", req.message)

        try:
            result = run_agent(req.message)
            span.set_attribute("agent.success", True)

            # Record metrics
            request_counter.add(1, {"status": "success", "agent_mode": result.get("agent_mode", "unknown")})

            elapsed = time.time() - start_time
            response_time_histogram.record(elapsed, {"status": "success"})

            logger.info(f"Chat request completed successfully in {elapsed:.2f}s")
            return result

        except Exception as e:
            span.set_attribute("agent.success", False)
            span.set_attribute("error", str(e))

            # Record error metrics
            request_counter.add(1, {"status": "error"})

            elapsed = time.time() - start_time
            response_time_histogram.record(elapsed, {"status": "error"})

            logger.error(f"Chat request failed after {elapsed:.2f}s: {str(e)}")
            raise
