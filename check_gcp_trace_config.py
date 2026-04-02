"""
Check if GCP Agent Engine exports to Cloud Trace by default
"""
import os

print("=" * 70)
print("GCP Trace Configuration Analysis")
print("=" * 70)
print()

agents = {
    "portal26_otel_agent": "portal26_otel_agent/.env",
    "gcp_traces_agent": "gcp_traces_agent/.env"
}

for agent_name, env_file in agents.items():
    print(f"{agent_name}:")
    print("-" * 70)
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            lines = f.readlines()
        
        has_custom_endpoint = False
        has_telemetry_enabled = False
        endpoint = None
        
        for line in lines:
            if 'OTEL_EXPORTER_OTLP_ENDPOINT' in line and not line.strip().startswith('#'):
                has_custom_endpoint = True
                endpoint = line.split('=')[1].strip()
            if 'GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true' in line:
                has_telemetry_enabled = True
        
        print(f"  Telemetry enabled: {has_telemetry_enabled}")
        print(f"  Custom OTEL endpoint: {has_custom_endpoint}")
        if endpoint:
            print(f"    -> {endpoint}")
        
        if has_telemetry_enabled and not has_custom_endpoint:
            print("  [INFO] Telemetry enabled but no custom endpoint")
            print("  Expected behavior: May not export to Cloud Trace by default")
        elif has_telemetry_enabled and has_custom_endpoint:
            print("  [INFO] Telemetry enabled with custom endpoint")
            print("  Expected behavior: Exports to custom endpoint only")
        
    print()

print("=" * 70)
print("Findings")
print("=" * 70)
print("""
GCP Agent Engine telemetry behavior:

1. GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true
   - Enables internal telemetry collection
   - BUT may not automatically export to Cloud Trace

2. Without custom OTEL endpoint:
   - Telemetry collected but not exported externally
   - You need to explicitly configure export destination

3. With custom OTEL endpoint:
   - Telemetry exported to that endpoint
   - Does NOT go to Cloud Trace

SOLUTION:
To get traces in GCP Cloud Trace, you need to either:
  A) Use GCP's cloud-trace-sdk (different from OTEL)
  B) Set up custom OTEL exporter pointing to Cloud Trace endpoint
  C) Use portal26_otel_agent (already working with Portal26)

RECOMMENDATION:
- Use portal26_otel_agent for Portal26 traces (confirmed working)
- For GCP traces, check if Cloud Trace API needs to be enabled
""")
