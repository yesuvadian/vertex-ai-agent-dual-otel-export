# GCP Pub/Sub - Deep Dive Study Guide

## 📚 **What is Pub/Sub?**

**Google Cloud Pub/Sub** is a fully-managed, asynchronous messaging service that enables event-driven systems and streaming analytics.

**Official Name:** `Cloud Pub/Sub` (Publish/Subscribe)

**Purpose:** Decouple services that produce events (publishers) from services that process events (subscribers).

**Key Characteristics:**
- Asynchronous messaging
- At-least-once delivery guarantee
- Global scale (millions of messages per second)
- Fully managed (no servers to manage)
- Works across cloud providers

---

## 🏗️ **Core Architecture**

### The Pub/Sub Model

```
┌─────────────┐                  ┌─────────────┐                  ┌─────────────┐
│ PUBLISHER   │                  │  PUB/SUB    │                  │ SUBSCRIBER  │
│             │                  │   TOPIC     │                  │             │
│  (Sender)   │─────publish────▶ │             │◀────subscribe────│  (Receiver) │
│             │                  │  (Queue)    │                  │             │
└─────────────┘                  └─────────────┘                  └─────────────┘
                                        │
                                        │
                                   Messages stored
                                   in topic queue
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │  SUBSCRIPTION       │
                              │                     │
                              │  Push or Pull       │
                              └─────────────────────┘
                                        │
                                        │
                                        ▼
                              ┌─────────────────────┐
                              │  ENDPOINT           │
                              │  (Lambda, Cloud     │
                              │   Function, etc)    │
                              └─────────────────────┘
```

### Three Main Components

#### 1. **Topic**
- Named resource to which publishers send messages
- Acts as a message queue/channel
- Can have multiple subscriptions

#### 2. **Message**
- Data payload sent to a topic
- Contains data + attributes (metadata)
- Unique message ID

#### 3. **Subscription**
- Named resource representing stream of messages from a topic
- Delivers messages to subscribers
- Can be Push or Pull type

---

## 📬 **Topics Explained**

### What is a Topic?

A **Topic** is a named entity that represents a feed of messages.

**Think of it as:**
- A post office box
- A radio station frequency
- A WhatsApp group (publishers post, subscribers read)

### Topic Properties

| Property | Description |
|----------|-------------|
| **Name** | Unique identifier: `projects/PROJECT_ID/topics/TOPIC_NAME` |
| **Labels** | Key-value pairs for organization |
| **Message Retention** | How long undelivered messages are stored (default: 7 days, max: 31 days) |
| **Schema** | Optional: enforce message structure |

### Creating a Topic

#### gcloud CLI
```bash
gcloud pubsub topics create TOPIC_NAME \
  --project=PROJECT_ID
```

**Example:**
```bash
gcloud pubsub topics create reasoning-engine-logs-topic \
  --project=agentic-ai-integration-490716
```

#### Python API
```python
from google.cloud import pubsub_v1

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('PROJECT_ID', 'TOPIC_NAME')

topic = publisher.create_topic(request={"name": topic_path})
print(f"Created topic: {topic.name}")
```

#### Console
1. Go to Pub/Sub → Topics
2. Click "Create Topic"
3. Enter topic name
4. Click "Create"

**URL:** https://console.cloud.google.com/cloudpubsub/topic/list?project=PROJECT_ID

### Topic Operations

```bash
# List topics
gcloud pubsub topics list --project=PROJECT_ID

# Describe topic
gcloud pubsub topics describe TOPIC_NAME --project=PROJECT_ID

# Delete topic
gcloud pubsub topics delete TOPIC_NAME --project=PROJECT_ID

# Publish test message
gcloud pubsub topics publish TOPIC_NAME \
  --message="Hello World" \
  --project=PROJECT_ID
```

---

## 📨 **Messages Explained**

### Message Structure

A Pub/Sub message contains:

```json
{
  "data": "Base64-encoded message payload",
  "attributes": {
    "key1": "value1",
    "key2": "value2"
  },
  "messageId": "1234567890",
  "publishTime": "2024-04-22T10:30:45.123Z",
  "orderingKey": "optional-ordering-key"
}
```

### Message Components

#### 1. **Data (Payload)**
- Actual message content
- Base64-encoded string
- Max size: 10 MB

**Example:**
```python
data = "Agent log: Query received"
encoded_data = base64.b64encode(data.encode('utf-8'))
```

#### 2. **Attributes (Metadata)**
- Key-value pairs (strings only)
- Used for filtering, routing, metadata
- Max 100 attributes per message
- Max attribute size: 1024 bytes per key/value

**Example:**
```python
attributes = {
    "source": "vertex-ai",
    "agent_id": "8213677864684355584",
    "severity": "INFO"
}
```

#### 3. **Message ID**
- Unique identifier assigned by Pub/Sub
- Automatically generated
- Used for deduplication

#### 4. **Publish Time**
- Timestamp when message was published
- Set by Pub/Sub server

#### 5. **Ordering Key** (Optional)
- Used to maintain message order
- Messages with same key delivered in order
- Requires ordered delivery enabled

### Publishing Messages

#### Python Example
```python
from google.cloud import pubsub_v1
import json

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('PROJECT_ID', 'TOPIC_NAME')

# Message data
message_data = {
    "agent": "reasoning-engine",
    "query": "What's the temperature?",
    "response": "15°C"
}

# Convert to JSON and encode
data = json.dumps(message_data).encode('utf-8')

# Attributes
attributes = {
    "source": "vertex-ai",
    "timestamp": "2024-04-22T10:30:00Z"
}

# Publish
future = publisher.publish(topic_path, data, **attributes)
message_id = future.result()
print(f"Published message ID: {message_id}")
```

#### gcloud CLI
```bash
# Simple message
gcloud pubsub topics publish TOPIC_NAME \
  --message="Hello World"

# Message with attributes
gcloud pubsub topics publish TOPIC_NAME \
  --message="Agent log" \
  --attribute="source=vertex-ai,severity=INFO"
```

### Message Lifecycle

```
1. Publisher sends message → Topic
2. Topic stores message in queue
3. Topic forwards message to ALL subscriptions
4. Subscription delivers message to subscriber
5. Subscriber processes message
6. Subscriber acknowledges (ACK) message
7. Subscription removes message from queue

If no ACK received:
8. Subscription re-delivers message (retry)
9. After max retries → Dead Letter Queue (optional)
```

---

## 📥 **Subscriptions Explained**

### What is a Subscription?

A **Subscription** represents the stream of messages from a specific topic to a subscriber.

**Key Concept:** One topic can have multiple subscriptions, and each subscription receives ALL messages from the topic.

```
                         ┌─────────────────┐
                         │     TOPIC       │
                         │   (1 message)   │
                         └────────┬────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
                ▼                 ▼                 ▼
        ┌───────────┐     ┌───────────┐     ┌───────────┐
        │ Subscription│     │ Subscription│     │ Subscription│
        │      A      │     │      B      │     │      C      │
        └───────────┘     └───────────┘     └───────────┘
                │                 │                 │
                ▼                 ▼                 ▼
           Subscriber A      Subscriber B      Subscriber C

Each subscription gets a COPY of the message!
```

### Subscription Types

#### 1. **Pull Subscription**

**How it works:**
- Subscriber **actively pulls** messages from Pub/Sub
- Subscriber controls when to request messages
- Good for batch processing

**Flow:**
```
1. Subscriber: "Give me messages" (pull request)
2. Pub/Sub: "Here are 10 messages"
3. Subscriber: Processes messages
4. Subscriber: "I'm done with message IDs: 1,2,3" (ACK)
5. Repeat
```

**Use Cases:**
- Batch processing jobs
- Worker pools
- When subscriber controls processing rate

**Example (Python):**
```python
from google.cloud import pubsub_v1

subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path('PROJECT_ID', 'SUBSCRIPTION_NAME')

def callback(message):
    print(f"Received: {message.data.decode('utf-8')}")
    message.ack()  # Acknowledge

# Start pulling
streaming_pull_future = subscriber.subscribe(subscription_path, callback=callback)

try:
    streaming_pull_future.result()
except KeyboardInterrupt:
    streaming_pull_future.cancel()
```

#### 2. **Push Subscription** (What We Use!)

**How it works:**
- Pub/Sub **actively pushes** messages to a configured endpoint
- Pub/Sub makes HTTPS POST requests
- No subscriber code needed to pull

**Flow:**
```
1. Message arrives in topic
2. Pub/Sub immediately sends HTTPS POST to endpoint
3. Endpoint processes and returns HTTP 200 OK
4. If 200 OK → message acknowledged
5. If error → Pub/Sub retries
```

**Use Cases:**
- Real-time processing
- Webhooks
- Serverless functions (Lambda, Cloud Functions)
- **Cross-cloud integration** (GCP → AWS)

**Our Setup:**
```
Log Sink → Pub/Sub Topic → Push Subscription → AWS Lambda URL
```

**Creating Push Subscription:**
```bash
gcloud pubsub subscriptions create SUBSCRIPTION_NAME \
  --topic=TOPIC_NAME \
  --push-endpoint="https://your-endpoint.com" \
  --project=PROJECT_ID
```

**Our Example:**
```bash
gcloud pubsub subscriptions create reasoning-engine-to-oidc \
  --topic=reasoning-engine-logs-topic \
  --push-endpoint="https://gd2ohh3wa7dgenayxkkwq2ht6a0jacor.lambda-url.us-east-1.on.aws/" \
  --push-auth-service-account=pubsub-oidc-invoker@agentic-ai-integration-490716.iam.gserviceaccount.com \
  --push-auth-token-audience="https://gd2ohh3wa7dgenayxkkwq2ht6a0jacor.lambda-url.us-east-1.on.aws/" \
  --project=agentic-ai-integration-490716
```

### Subscription Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| **Ack Deadline** | Time to acknowledge message before redelivery | 10 seconds |
| **Message Retention** | How long to retain unacknowledged messages | 7 days |
| **Retry Policy** | Exponential backoff settings | Enabled |
| **Dead Letter Topic** | Topic for messages that fail repeatedly | None |
| **Filter** | Only deliver messages matching filter | None |
| **Expiration** | Delete subscription after period of inactivity | Never |

### Subscription Operations

```bash
# Create subscription
gcloud pubsub subscriptions create SUB_NAME --topic=TOPIC_NAME

# List subscriptions
gcloud pubsub subscriptions list --project=PROJECT_ID

# Describe subscription
gcloud pubsub subscriptions describe SUB_NAME --project=PROJECT_ID

# Update subscription
gcloud pubsub subscriptions update SUB_NAME \
  --ack-deadline=20

# Pull messages (for pull subscriptions)
gcloud pubsub subscriptions pull SUB_NAME \
  --limit=10 \
  --auto-ack

# Delete subscription
gcloud pubsub subscriptions delete SUB_NAME --project=PROJECT_ID
```

---

## 🔐 **Push Subscription with OIDC Authentication**

### What is OIDC in Push Subscriptions?

When using Push subscriptions to send messages to external endpoints (like AWS Lambda), you need authentication to prove the request is from legitimate GCP Pub/Sub.

**OIDC (OpenID Connect)** provides this authentication using JWT tokens.

### How It Works

```
┌──────────────────────────────────────────────────────────────┐
│ 1. Message arrives in Pub/Sub Topic                          │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 2. Push Subscription needs to send message                   │
│    "I need authentication token to send this"                │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 3. Pub/Sub requests JWT token from GCP IAM                   │
│    Service Account: pubsub-oidc-invoker@...                  │
│    Audience: https://lambda-url...                           │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 4. GCP IAM generates JWT token                               │
│    - Signs with Google's private key                         │
│    - Includes audience, issuer, expiration                   │
│    - Valid for 1 hour                                        │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 5. Pub/Sub sends HTTPS POST to endpoint                      │
│    Header: Authorization: Bearer <JWT_TOKEN>                 │
│    Body: Message data (Base64 encoded)                       │
└───────────────────────────┬──────────────────────────────────┘
                            │
                            ▼
┌──────────────────────────────────────────────────────────────┐
│ 6. Endpoint (AWS Lambda) receives request                    │
│    - Extracts JWT from Authorization header                  │
│    - Verifies JWT with Google OAuth API                      │
│    - Checks audience and issuer                              │
│    - If valid: processes message                             │
│    - Returns HTTP 200 OK                                     │
└──────────────────────────────────────────────────────────────┘
```

### Setting Up OIDC Push Subscription

#### Step 1: Create Service Account
```bash
gcloud iam service-accounts create pubsub-oidc-invoker \
  --display-name="Pub/Sub OIDC Token Generator" \
  --project=PROJECT_ID
```

#### Step 2: Grant Token Creator Role
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountTokenCreator"
```

#### Step 3: Create Push Subscription with OIDC
```bash
gcloud pubsub subscriptions create SUBSCRIPTION_NAME \
  --topic=TOPIC_NAME \
  --push-endpoint="https://your-endpoint-url/" \
  --push-auth-service-account=pubsub-oidc-invoker@PROJECT_ID.iam.gserviceaccount.com \
  --push-auth-token-audience="https://your-endpoint-url/" \
  --ack-deadline=10 \
  --project=PROJECT_ID
```

### Push Request Format

When Pub/Sub pushes a message to your endpoint:

**HTTP Request:**
```http
POST /your-endpoint HTTP/1.1
Host: your-endpoint.com
Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
Content-Type: application/json

{
  "message": {
    "data": "SGVsbG8gV29ybGQ=",
    "attributes": {
      "key1": "value1"
    },
    "messageId": "1234567890",
    "publishTime": "2024-04-22T10:30:45.123Z"
  },
  "subscription": "projects/PROJECT_ID/subscriptions/SUB_NAME"
}
```

**Your Endpoint Must:**
1. Extract `Authorization` header
2. Verify JWT token
3. Process message data (Base64 decode)
4. Return HTTP 200 OK (acknowledges message)
5. Return HTTP 4xx/5xx (triggers retry)

---

## ⚙️ **Key Concepts**

### At-Least-Once Delivery

**Guarantee:** Every message will be delivered at least one time.

**Reality:** Messages may be delivered more than once (duplicate delivery possible).

**Why:** Network issues, acknowledgment timeouts, retries

**Solution:** Make your subscriber **idempotent** (processing same message twice has same result).

**Example:**
```python
# Bad - not idempotent
def process_message(message):
    counter += 1  # Will increment multiple times if duplicated

# Good - idempotent
def process_message(message):
    message_id = message.message_id
    if already_processed(message_id):
        return  # Skip duplicate
    
    # Process message
    save_to_database(message.data)
    mark_as_processed(message_id)
```

### Acknowledgment (ACK)

**What:** Signal from subscriber to Pub/Sub that message was successfully processed.

**When to ACK:**
- ✅ After successful processing
- ✅ When you don't want to receive the message again

**When NOT to ACK:**
- ❌ If processing failed (let it retry)
- ❌ If you want message redelivered

**Ack Deadline:**
- Time window to acknowledge message
- Default: 10 seconds
- Range: 10 seconds to 10 minutes
- If deadline passes without ACK → message redelivered

**Example (Python):**
```python
def callback(message):
    try:
        # Process message
        process(message.data)
        
        # Success - acknowledge
        message.ack()
    except Exception as e:
        # Failed - don't acknowledge (will retry)
        print(f"Error: {e}")
        message.nack()  # Explicitly reject (immediate redelivery)
```

**Push Subscription ACK:**
```python
# AWS Lambda handler
def lambda_handler(event, context):
    try:
        # Process message
        process_message(event)
        
        # Return 200 = ACK
        return {
            'statusCode': 200,
            'body': json.dumps({'status': 'success'})
        }
    except Exception as e:
        # Return error = NACK (will retry)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
```

### Message Retention

**What:** How long Pub/Sub keeps unacknowledged messages.

**Default:** 7 days
**Maximum:** 31 days
**Minimum:** 10 minutes

**After retention period:** Message is deleted (lost forever).

**Set retention:**
```bash
gcloud pubsub topics update TOPIC_NAME \
  --message-retention-duration=7d
```

### Dead Letter Queue (DLQ)

**What:** A separate topic for messages that fail repeatedly.

**Use Case:** Messages that can't be processed after many retries.

**How it works:**
```
1. Message fails processing
2. Subscription retries (exponential backoff)
3. After max retries (e.g., 5 attempts)
4. Message moved to Dead Letter Topic
5. Separate process handles failed messages
```

**Setup:**
```bash
# Create dead letter topic
gcloud pubsub topics create dead-letter-topic

# Update subscription with DLQ
gcloud pubsub subscriptions update SUBSCRIPTION_NAME \
  --dead-letter-topic=dead-letter-topic \
  --max-delivery-attempts=5
```

### Message Filtering

**What:** Only deliver messages that match a filter expression.

**Use Case:** Multiple subscribers need different subsets of messages from same topic.

**Example:**
```bash
# Only receive ERROR severity logs
gcloud pubsub subscriptions create errors-only \
  --topic=logs-topic \
  --message-filter='attributes.severity="ERROR"'

# Only receive logs from specific agent
gcloud pubsub subscriptions create agent-logs \
  --topic=logs-topic \
  --message-filter='attributes.agent_id="8213677864684355584"'
```

**Filter Syntax:**
```
# Simple equality
attributes.key="value"

# Multiple conditions
attributes.severity="ERROR" AND attributes.source="agent"

# NOT
NOT attributes.severity="INFO"
```

### Ordering Keys

**What:** Ensures messages with same ordering key are delivered in order.

**Use Case:** When order matters (e.g., database updates for same user).

**How to use:**
```python
# Publisher
publisher.publish(
    topic_path,
    data,
    ordering_key="user-123"  # All messages for user-123 will be ordered
)
```

**Enable ordered delivery:**
```bash
gcloud pubsub subscriptions create SUBSCRIPTION_NAME \
  --topic=TOPIC_NAME \
  --enable-message-ordering
```

---

## 📊 **Monitoring & Metrics**

### Key Metrics (Available in Cloud Console)

#### Topic Metrics
- **Send message operations** - Number of messages published
- **Send message operation latencies** - Time to publish
- **Unacked messages** - Messages not yet acknowledged
- **Oldest unacked message age** - How long oldest message has been waiting

#### Subscription Metrics
- **Pull/Push request count** - Number of delivery attempts
- **Unacked messages by region** - Geographic distribution
- **Oldest unacked message age** - Critical metric for backlog
- **Num outstanding messages** - Current backlog size

### Monitoring Dashboard

**Access:** Cloud Console → Pub/Sub → Topics/Subscriptions → Metrics tab

**Important Alerts to Set:**
1. **High unacked message count** - Backlog building up
2. **Old unacked messages** - Messages not being processed
3. **High error rate** - Delivery failures

**Example Alert:**
```bash
# Alert when unacked messages > 1000
gcloud alpha monitoring policies create \
  --notification-channels=CHANNEL_ID \
  --display-name="Pub/Sub Backlog Alert" \
  --condition-display-name="High unacked messages" \
  --condition-threshold-value=1000 \
  --condition-threshold-duration=300s
```

---

## 💰 **Pricing**

### Cost Components

#### 1. Message Operations
**Cost:** $0.40 per million operations (first 10 GB free per month)

**Operations include:**
- Publish
- Push/Pull delivery
- Acknowledge
- Seek

**Example:**
- 1 million messages published = 1M operations
- 1 million messages delivered = 1M operations
- 1 million ACKs = 1M operations
- **Total:** 3M operations = $1.20

#### 2. Data Volume
**Cost:** $0.06 per GB

**Calculation:** Based on message size including data + attributes

**Example:**
- 1 million messages × 1 KB each = 1 GB
- Cost: $0.06

#### 3. Retained Acknowledged Messages
**Cost:** $0.27 per GB per month

**Only if:** You enable message retention after acknowledgment

### Cost Optimization Tips

1. **Use appropriate message sizes** - Don't send huge payloads
2. **Acknowledge promptly** - Don't let messages pile up
3. **Use filters** - Reduce unnecessary deliveries
4. **Batch publishing** - Combine multiple messages when possible
5. **Monitor backlog** - Prevent message retention costs

---

## 🔧 **Common Patterns**

### Pattern 1: Fan-Out

**Use Case:** One message needs to trigger multiple independent processes.

```
              Publisher
                 │
                 ▼
              Topic
                 │
        ┌────────┼────────┐
        │        │        │
        ▼        ▼        ▼
      Sub A    Sub B    Sub C
        │        │        │
        ▼        ▼        ▼
    Process  Analytics Email
     Order    Pipeline  Notification
```

**Example:** Order placed → Process payment + Update analytics + Send email

### Pattern 2: Work Queue

**Use Case:** Distribute work among multiple workers.

```
    Publishers
    (Multiple)
        │
        ▼
      Topic
        │
        ▼
   Subscription
        │
    ┌───┼───┐
    │   │   │
    ▼   ▼   ▼
  Worker Worker Worker
  (Pool of workers pull messages)
```

**Example:** Image processing jobs distributed to worker pool

### Pattern 3: Cross-Cloud Integration (Our Setup!)

**Use Case:** Send data from GCP to AWS.

```
GCP Side:
  Log Sink → Topic → Push Subscription (with OIDC)
                            │
                            │ HTTPS POST with JWT
                            ▼
AWS Side:
                      Lambda Function
                            │
                            ▼
                      Portal26 OTEL
```

### Pattern 4: Event Sourcing

**Use Case:** Store all events in order, replay when needed.

```
App Events → Topic → Subscription (with ordering keys)
                            │
                            ▼
                    Event Store (BigQuery)
```

---

## 🐛 **Troubleshooting**

### Issue 1: Messages Not Being Delivered

**Check:**
```bash
# 1. Verify topic exists
gcloud pubsub topics describe TOPIC_NAME

# 2. Verify subscription exists
gcloud pubsub subscriptions describe SUBSCRIPTION_NAME

# 3. Check if messages in topic
gcloud pubsub topics describe TOPIC_NAME

# 4. Try pulling manually (for pull subscriptions)
gcloud pubsub subscriptions pull SUBSCRIPTION_NAME --limit=1
```

### Issue 2: High Unacked Message Count

**Causes:**
- Subscriber not processing fast enough
- Subscriber down/crashed
- Ack deadline too short

**Solutions:**
```bash
# Increase ack deadline
gcloud pubsub subscriptions update SUBSCRIPTION_NAME \
  --ack-deadline=60

# Scale up subscribers
# Add more workers/instances

# Temporarily stop publishing
# Clear backlog, then resume
```

### Issue 3: Push Subscription Not Working

**Check:**
```bash
# 1. Verify endpoint URL is accessible
curl -X POST https://your-endpoint.com

# 2. Check subscription configuration
gcloud pubsub subscriptions describe SUBSCRIPTION_NAME

# 3. View push delivery logs
gcloud logging read "resource.type=pubsub_subscription AND resource.labels.subscription_id=SUBSCRIPTION_NAME"

# 4. Test with simple endpoint
# Create temporary Cloud Function to test
```

### Issue 4: Authentication Failures (OIDC)

**Check:**
```bash
# 1. Verify service account exists
gcloud iam service-accounts describe SERVICE_ACCOUNT_EMAIL

# 2. Verify token creator role
gcloud projects get-iam-policy PROJECT_ID \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/iam.serviceAccountTokenCreator"

# 3. Test JWT generation manually
gcloud auth print-identity-token \
  --audiences="https://your-endpoint.com" \
  --impersonate-service-account=SERVICE_ACCOUNT_EMAIL
```

---

## 📖 **Best Practices**

### 1. Design for Idempotency
Every subscriber should handle duplicate messages gracefully.

### 2. Set Appropriate Ack Deadlines
- Too short: Unnecessary redeliveries
- Too long: Delayed retries
- Sweet spot: 2-3x average processing time

### 3. Use Dead Letter Queues
Prevent poison messages from blocking queue.

### 4. Monitor Unacked Message Age
Alert when messages are stuck.

### 5. Use Message Attributes for Metadata
Don't put routing/filtering info in message body.

### 6. Implement Exponential Backoff
For failed message processing, wait longer between retries.

### 7. Use Filters to Reduce Costs
Only deliver messages subscribers actually need.

### 8. Test with Small Messages First
Verify setup before sending large payloads.

### 9. Use Ordering Keys Sparingly
Only when order truly matters (adds overhead).

### 10. Plan for Scale
Pub/Sub scales automatically, but ensure subscribers can too.

---

## 🔗 **Official Documentation**

**Google Cloud Docs:**
- Pub/Sub Overview: https://cloud.google.com/pubsub/docs/overview
- Publisher Guide: https://cloud.google.com/pubsub/docs/publisher
- Subscriber Guide: https://cloud.google.com/pubsub/docs/subscriber
- Push Subscriptions: https://cloud.google.com/pubsub/docs/push
- OIDC Authentication: https://cloud.google.com/pubsub/docs/authenticate-push-subscriptions

**API Reference:**
- Python Client: https://cloud.google.com/python/docs/reference/pubsub/latest
- REST API: https://cloud.google.com/pubsub/docs/reference/rest

---

## 📝 **Quick Reference Card**

### Common Commands

```bash
# Topics
gcloud pubsub topics create TOPIC_NAME
gcloud pubsub topics list
gcloud pubsub topics describe TOPIC_NAME
gcloud pubsub topics delete TOPIC_NAME
gcloud pubsub topics publish TOPIC_NAME --message="Hello"

# Subscriptions
gcloud pubsub subscriptions create SUB_NAME --topic=TOPIC_NAME
gcloud pubsub subscriptions list
gcloud pubsub subscriptions describe SUB_NAME
gcloud pubsub subscriptions delete SUB_NAME
gcloud pubsub subscriptions pull SUB_NAME --auto-ack

# Push subscription with OIDC
gcloud pubsub subscriptions create SUB_NAME \
  --topic=TOPIC_NAME \
  --push-endpoint="https://endpoint.com" \
  --push-auth-service-account=SA@PROJECT.iam.gserviceaccount.com \
  --push-auth-token-audience="https://endpoint.com"
```

### Python Quick Start

```python
from google.cloud import pubsub_v1

# Publish
publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path('PROJECT_ID', 'TOPIC_NAME')
future = publisher.publish(topic_path, b'Hello World')
print(f"Published: {future.result()}")

# Subscribe (Pull)
subscriber = pubsub_v1.SubscriberClient()
subscription_path = subscriber.subscription_path('PROJECT_ID', 'SUB_NAME')

def callback(message):
    print(f"Received: {message.data}")
    message.ack()

subscriber.subscribe(subscription_path, callback=callback)
```

---

This comprehensive guide covers everything about GCP Pub/Sub. Use it as your reference for all Pub/Sub operations!
