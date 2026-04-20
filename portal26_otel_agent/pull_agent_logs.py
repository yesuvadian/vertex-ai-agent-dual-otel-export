"""
Pull logs for portal26_agent_v3 from Kinesis AND GCP Cloud Trace
Supports both AWS Kinesis and GCP Pub/Sub log sinks
"""
import boto3
import json
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# AWS Kinesis Configuration
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = "us-east-2"

STREAM_NAME = "stg_otel_source_data_stream"
SHARD_ID = "shardId-000000000006"

# GCP Configuration
GCP_PROJECT_ID = "agentic-ai-integration-490716"
GCP_ENABLED = os.environ.get("USE_GCP_TRACES", "false").lower() == "true"

# Last 60 minutes (to check for any recent relusys activity)
start_time = datetime.now(timezone.utc) - timedelta(minutes=60)

print("=" * 80)
print("PULLING PORTAL26_AGENT_V3 LOGS")
print("=" * 80)
print(f"Sources: AWS Kinesis" + (" + GCP Cloud Trace" if GCP_ENABLED else ""))
print(f"Time range: Last 60 minutes")
print(f"Looking for: tenant1, relusys, portal26_agent_v3, portal26_otel_agent")
print(f"(Will also show samples of all logs for analysis)")
print()

# Create Kinesis client - use explicit credentials if provided, otherwise use default credential chain
if AWS_ACCESS_KEY and AWS_SECRET_KEY:
    print(f"Using explicit AWS credentials")
    kinesis = boto3.client(
        'kinesis',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )
else:
    print(f"Using default AWS credential chain (environment, credentials file, or IAM role)")
    kinesis = boto3.client(
        'kinesis',
        region_name=AWS_REGION
    )

print("[1/2] Getting iterator...")
response = kinesis.get_shard_iterator(
    StreamName=STREAM_NAME,
    ShardId=SHARD_ID,
    ShardIteratorType='AT_TIMESTAMP',
    Timestamp=start_time
)
iterator = response['ShardIterator']
print("[OK]")
print()

print("[2/2] Pulling records...")
print("-" * 80)

total = 0
matched = 0
skipped = 0
output_file = f"portal26_otel_agent_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl"

with open(output_file, 'w') as f:
    max_batches = 50
    for batch_num in range(max_batches):  # Max 50 batches for longer window
        response = kinesis.get_records(ShardIterator=iterator, Limit=100)

        records = response.get('Records', [])
        iterator = response.get('NextShardIterator')

        if not records:
            break

        total += len(records)

        for idx, record in enumerate(records):
            try:
                # Data is already JSON (not base64)
                data = record['Data']
                if isinstance(data, bytes):
                    data_str = data.decode('utf-8')
                else:
                    data_str = str(data)

                data_json = json.loads(data_str)

                # Extract service name and user ID for all records
                service = "unknown"
                user_id = "unknown"
                try:
                    if 'resourceSpans' in data_json:
                        attrs = data_json['resourceSpans'][0]['resource']['attributes']
                        for attr in attrs:
                            if attr['key'] == 'service.name':
                                service = attr['value']['stringValue']
                            elif attr['key'] == 'portal26.user.id':
                                user_id = attr['value']['stringValue']
                    elif 'resourceLogs' in data_json:
                        attrs = data_json['resourceLogs'][0]['resource']['attributes']
                        for attr in attrs:
                            if attr['key'] == 'service.name':
                                service = attr['value']['stringValue']
                            elif attr['key'] == 'portal26.user.id':
                                user_id = attr['value']['stringValue']
                except:
                    pass

                arrival = record['ApproximateArrivalTimestamp']

                # Print all records (first 10 for sampling)
                if total <= 10:
                    print(f"  [SAMPLE] {arrival} | User: {user_id} | Service: {service}")

                # Check for our identifiers
                data_lower = data_str.lower()
                if any(term in data_lower for term in ['tenant1', 'relusys', 'portal26_agent', 'portal26_otel']):
                    f.write(json.dumps(data_json) + '\n')  # JSONL: one compact JSON per line
                    matched += 1
                    print(f"  [MATCH] {arrival} | User: {user_id} | Service: {service}")

            except Exception as e:
                skipped += 1
                # Uncomment for debugging: print(f"  [WARN] Skipped record: {e}")

        if not iterator:
            break

    if batch_num == max_batches - 1 and iterator:
        print()
        print("[WARN] Reached batch limit - some records may not have been retrieved")
        print(f"       Processed {max_batches} batches. Consider increasing time window or max_batches.")

print()
print("=" * 80)
print("SUMMARY")
print("=" * 80)
print(f"Total records: {total}")
print(f"Matched records: {matched}")
print(f"Skipped records: {skipped}")
print(f"Output: {output_file}")
print()

# Pull GCP Cloud Trace data if enabled
gcp_matched = 0
if GCP_ENABLED:
    print()
    print("=" * 80)
    print("PULLING FROM GCP CLOUD TRACE")
    print("=" * 80)
    try:
        from google.cloud import trace_v1

        client = trace_v1.TraceServiceClient()

        # List traces using Cloud Trace API
        request = trace_v1.ListTracesRequest(
            project_id=GCP_PROJECT_ID,
            view=trace_v1.ListTracesRequest.ViewType.COMPLETE
        )

        traces = client.list_traces(request=request)
        gcp_output_file = f"gcp_traces_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl"

        with open(gcp_output_file, 'w') as gcp_f:
            for trace in traces:
                # Check if trace is from our Reasoning Engine
                for span in trace.spans:
                    if hasattr(span, 'labels') and span.labels:
                        agent_name = span.labels.get('gen_ai.agent.name', '')
                        if 'portal26' in agent_name.lower() or 'relusys' in agent_name.lower():
                            trace_data = {
                                "trace_id": trace.trace_id,
                                "project_id": trace.project_id,
                                "timestamp": str(span.start_time) if span.start_time else None,
                                "agent_name": agent_name,
                                "spans": []
                            }

                            for s in trace.spans:
                                span_data = {
                                    "span_id": s.span_id,
                                    "name": s.name,
                                    "labels": dict(s.labels) if hasattr(s, 'labels') and s.labels else {}
                                }
                                trace_data["spans"].append(span_data)

                            gcp_f.write(json.dumps(trace_data) + '\n')
                            gcp_matched += 1
                            print(f"  [GCP MATCH] Trace: {trace.trace_id} | Agent: {agent_name}")
                            break

        print(f"\n[GCP] Found {gcp_matched} trace(s)")
        if gcp_matched > 0:
            print(f"[GCP] Output: {gcp_output_file}")

    except ImportError:
        print("[WARN] google-cloud-trace not installed. Install with: pip install google-cloud-trace")
    except Exception as e:
        print(f"[ERROR] Failed to pull GCP traces: {e}")

print()
print("=" * 80)
print("COMBINED SUMMARY")
print("=" * 80)
print(f"Kinesis matched: {matched}")
if GCP_ENABLED:
    print(f"GCP Cloud Trace matched: {gcp_matched}")
    print(f"Total matched: {matched + gcp_matched}")

if matched > 0:
    print()
    print("[SUCCESS] Found your agent's logs in Kinesis!")
    print()
    print("View logs:")
    print(f"  cat {output_file} | head -50")
    print()
    print("Search for traces:")
    print(f"  grep -i 'traceid' {output_file}")
    print()
    print("Count logs:")
    print(f"  grep -c 'service.name' {output_file}")

if gcp_matched > 0:
    print()
    print("[SUCCESS] Found traces in GCP Cloud Trace!")
    print(f"  View with: python ../gcp_traces_agent_client/view_traces.py")

if matched == 0 and gcp_matched == 0:
    print()
    print("[INFO] No logs found yet")
    print()
    print("Next steps:")
    print("  1. Send a test query in Console Playground")
    print("  2. Wait 1-2 minutes for data to reach Kinesis/GCP")
    print("  3. Run this script again")
    print()
    print("To enable GCP trace pulling:")
    print("  export USE_GCP_TRACES=true")
print()
