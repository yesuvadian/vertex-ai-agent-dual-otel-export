#!/usr/bin/env python3
"""
Deploy portal26_otel_agent to Vertex AI Agent Engine with OpenTelemetry.

Usage:
    python3 deploy.py
"""
import sys
import vertexai
from vertexai import agent_engines
from portal26_agent.agent_deployed import root_agent
import config
import otel_config

PROJECT_ID = config.GOOGLE_CLOUD_PROJECT
LOCATION = config.GOOGLE_CLOUD_LOCATION


def deploy():
    """
    Deploy agent to Vertex AI Agent Engine with Portal26 OTEL integration.
    """
    print("=" * 80)
    print("DEPLOYING PORTAL26_OTEL_AGENT TO VERTEX AI AGENT ENGINE")
    print("=" * 80)
    print(f"Project: {PROJECT_ID}")
    print(f"Location: {LOCATION}")
    print(f"Model: {config.MODEL_ID}")
    print(f"OTEL Endpoint: {config.OTEL_ENDPOINT}")
    print(f"Service Name: {config.SERVICE_NAME}")
    print(f"Tenant ID: {config.TENANT_ID}")
    print(f"User ID: {config.USER_ID}")
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
            extra_packages=["./portal26_agent"],

            # Required packages with OTEL support
            requirements=[
                "google-adk>=1.17.0",
                "opentelemetry-instrumentation-google-genai>=0.4b0",
                "opentelemetry-exporter-otlp-proto-http",
                "opentelemetry-exporter-otlp-proto-grpc",
                "opentelemetry-instrumentation-vertexai>=2.0b0",
            ],

            display_name="portal26-otel-agent",
            description="City info agent with Portal26 OTEL telemetry + content capture",

            # OpenTelemetry configuration - exports to Portal26 OTLP endpoint
            env_vars=otel_config.OTEL_CONFIG,
        )

        print()
        print("=" * 80)
        print("DEPLOYMENT SUCCESSFUL")
        print("=" * 80)
        print(f"Resource name: {deployed_agent.resource_name}")
        print(f"Display name: {deployed_agent.display_name}")
        print()
        print("Telemetry Configuration:")
        print(f"  Service name: {config.SERVICE_NAME}")
        print(f"  OTLP Endpoint: {config.OTEL_ENDPOINT}")
        print(f"  Traces: {config.OTEL_ENDPOINT}/v1/traces")
        print(f"  Logs: {config.OTEL_ENDPOINT}/v1/logs")
        print(f"  Metrics: {config.OTEL_ENDPOINT}/v1/metrics")
        print()
        print("Test in Console Playground:")
        agent_id = deployed_agent.resource_name.split('/')[-1]
        print(f"  https://console.cloud.google.com/vertex-ai/agents/agent-engines/locations/{LOCATION}/agent-engines/{agent_id}/playground?project={PROJECT_ID}")
        print()
        print(f"Agent ID: {agent_id}")
        print()

        return 0

    except Exception as e:
        print()
        print("=" * 80)
        print("DEPLOYMENT FAILED")
        print("=" * 80)
        print(f"Error: {e}")
        print()
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(deploy())
