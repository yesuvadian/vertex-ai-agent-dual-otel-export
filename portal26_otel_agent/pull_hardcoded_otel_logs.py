"""
Pull logs for hardcoded-otel-deployed agent from Kinesis
Separate from portal26_otel_agent logs for comparison
"""
import boto3
import json
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = "us-east-2"

STREAM_NAME = "stg_otel_source_data_stream"
SHARD_ID = "shardId-000000000006"

# Last 5 minutes
start_time = datetime.now(timezone.utc) - timedelta(minutes=5)

print("=" * 80)
print("PULLING HARDCODED-OTEL-DEPLOYED LOGS FROM KINESIS")
print("=" * 80)
print(f"Time range: Last 5 minutes")
print(f"Looking for: hardcoded-otel-deployed service")
print()

# Create Kinesis client
if AWS_ACCESS_KEY and AWS_SECRET_KEY:
    print(f"Using explicit AWS credentials")
    kinesis = boto3.client(
        'kinesis',
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY
    )
else:
    print(f"Using default AWS credential chain")
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
output_file = f"hardcoded_otel_logs_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.jsonl"

with open(output_file, 'w') as f:
    max_batches = 20
    for batch_num in range(max_batches):  # Max 20 batches
        response = kinesis.get_records(ShardIterator=iterator, Limit=100)

        records = response.get('Records', [])
        iterator = response.get('NextShardIterator')

        if not records:
            break

        total += len(records)

        for record in records:
            try:
                # Data is already JSON (not base64)
                data = record['Data']
                if isinstance(data, bytes):
                    data_str = data.decode('utf-8')
                else:
                    data_str = str(data)

                data_json = json.loads(data_str)

                # Check for hardcoded-otel-deployed service
                data_lower = data_str.lower()
                if 'hardcoded-otel-deployed' in data_lower or 'hardcoded-otel' in data_lower:
                    f.write(json.dumps(data_json) + '\n')  # JSONL: one compact JSON per line
                    matched += 1

                    # Extract service name
                    service = "unknown"
                    try:
                        if 'resourceSpans' in data_json:
                            attrs = data_json['resourceSpans'][0]['resource']['attributes']
                            for attr in attrs:
                                if attr['key'] == 'service.name':
                                    service = attr['value']['stringValue']
                                    break
                        elif 'resourceLogs' in data_json:
                            attrs = data_json['resourceLogs'][0]['resource']['attributes']
                            for attr in attrs:
                                if attr['key'] == 'service.name':
                                    service = attr['value']['stringValue']
                                    break
                    except:
                        pass

                    arrival = record['ApproximateArrivalTimestamp']
                    print(f"  [MATCH] {arrival} | Service: {service}")

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

if matched > 0:
    print("[SUCCESS] Found hardcoded-otel logs!")
    print()
    print("View logs:")
    print(f"  cat {output_file} | head -50")
    print()
    print("Compare with portal26_otel_agent:")
    print(f"  python compare_agents.py")
else:
    print("[INFO] No logs found yet")
    print()
    print("Next steps:")
    print("  1. Send a test query to hardcoded-otel agent in Console Playground")
    print("  2. Wait 1-2 minutes for data to reach Kinesis")
    print("  3. Run this script again")
print()
