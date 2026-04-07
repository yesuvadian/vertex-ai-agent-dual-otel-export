"""
Deploy portal26_otel_agent to Vertex AI Agent Engine with full telemetry
Uses Agent Engine API (not Reasoning Engine) to enable content capture
"""
import sys
import vertexai
from vertexai import agent_engines
from agent import root_agent
import config
import otel_config

PROJECT_ID = config.GOOGLE_CLOUD_PROJECT
LOCATION = config.GOOGLE_CLOUD_LOCATION


def deploy():
    """
    Deploy agent to Vertex AI Agent Engine with Portal26 OTEL integration
    """
    print("=" * 80)
    print("DEPLOYING PORTAL26_OTEL_AGENT TO VERTEX AI AGENT ENGINE")
    print("=" * 80)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Model: {config.MODEL_ID}")
    print()
    print("🔭 Telemetry Configuration:")
    print(f"  Service Name: {config.SERVICE_NAME}")
    print(f"  Portal26 Endpoint: {config.OTEL_ENDPOINT}")
    print(f"  Tenant ID: {config.TENANT_ID}")
    print(f"  User ID: {config.USER_ID}")
    print(f"  Content Capture: {otel_config.OTEL_CONFIG['OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT']}")
    print()

    vertexai.init(
        project=PROJECT_ID,
        location=LOCATION,
        staging_bucket=f"gs://{PROJECT_ID}-adk-staging"
    )

    try:
        deployed_agent = agent_engines.create(
            agent_engine=root_agent,

            # Include the agent package
            extra_packages=["./"],

            # Required packages with OTEL and VertexAI instrumentation support
            requirements=[
                "google-adk>=1.17.0",
                "opentelemetry-api",
                "opentelemetry-sdk",
                "opentelemetry-instrumentation",
                "opentelemetry-exporter-otlp-proto-http",
                "opentelemetry-instrumentation-vertexai>=2.0b0",  # Critical for content capture
                "opentelemetry-instrumentation-google-genai>=0.4b0",
            ],

            display_name="portal26-otel-agent",
            description="City info agent with full Portal26 OTEL telemetry + content capture",

            # CRITICAL: env_vars enables content capture via Agent Engine
            env_vars=otel_config.OTEL_CONFIG,
        )

        print()
        print("=" * 80)
        print("✅ DEPLOYMENT SUCCESSFUL")
        print("=" * 80)
        print(f"Agent Name: {root_agent.name}")
        print(f"Resource Name: {deployed_agent.resource_name}")
        print(f"Display Name: {deployed_agent.display_name}")
        print()
        print("🔍 Telemetry Endpoints:")
        print(f"  Traces: {config.OTEL_ENDPOINT}/v1/traces")
        print(f"  Logs: {config.OTEL_ENDPOINT}/v1/logs")
        print(f"  Metrics: {config.OTEL_ENDPOINT}/v1/metrics")
        print()
        print("📝 Test in Console Playground:")
        agent_id = deployed_agent.resource_name.split('/')[-1]
        print(f"  https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/{LOCATION}/agent-engines/{agent_id}/playground?project={PROJECT_ID}")
        print()
        print(f"🆔 Agent ID: {agent_id}")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 80)
        print("❌ DEPLOYMENT FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(deploy())
