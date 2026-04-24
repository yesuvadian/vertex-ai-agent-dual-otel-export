# GCP Log Sink Filters - Complete Guide

## 📋 **Overview**

This guide explains how to configure log sink filters in the Terraform infrastructure for the GCP-to-AWS observability pipeline. Log sink filters determine which logs get exported from GCP Cloud Logging to AWS Lambda via Pub/Sub.

---

## 🎯 **Why Filter Matters**

**Without Filtering:**
- Export ALL logs (expensive, noisy, overwhelming)
- High Pub/Sub costs
- High Lambda invocation costs
- Processing irrelevant data

**With Filtering:**
- Export only relevant logs
- Reduce costs by 80-95%
- Focus on important events
- Better signal-to-noise ratio

---

## 🏗️ **How Filters Work in Our Terraform Setup**

### Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    GCP Cloud Logging                         │
│              (All logs from all services)                    │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ↓
            ┌───────────────────────────┐
            │      LOG SINK FILTER      │
            │                           │
            │  ✓ Reasoning Engine IDs?  │
            │  ✓ Agent IDs?             │
            │  ✓ Severity >= ERROR?     │
            │  ✓ Resource Type match?   │
            │  ✓ Custom conditions?     │
            └───────────┬───────────────┘
                        │
                        ↓ (Only matching logs)
            ┌───────────────────────────┐
            │      Pub/Sub Topic        │
            └───────────┬───────────────┘
                        │
                        ↓
            ┌───────────────────────────┐
            │      AWS Lambda           │
            │  (Multi-Customer Router)  │
            └───────────────────────────┘
```

### Filter Construction Logic

The Terraform configuration builds filters dynamically based on your variables:

```hcl
# All filter variables (ALL OPTIONAL)
reasoning_engine_ids = ["engine-1", "engine-2"]  # Filter by Reasoning Engine
agent_ids           = ["agent-001", "agent-002"] # Filter by Agent ID
log_severity_filter = ["ERROR", "CRITICAL"]      # Filter by severity
log_resource_types  = ["cloud_run_revision"]     # Filter by resource type
custom_log_filter   = "labels.env=\"prod\""      # Custom filter expression

# These are combined with AND logic:
# (reasoning_engine_ids) AND (agent_ids) AND (severity) AND (resource_types) AND (custom)
```

---

## 📚 **Filter Options Reference**

### **1. Reasoning Engine IDs** (Optional)

**Variable:** `reasoning_engine_ids`

**Purpose:** Filter logs from specific Vertex AI Reasoning Engines

**Type:** `list(string)`

**Example:**
```hcl
reasoning_engine_ids = [
  "8213677864684355584",
  "6010661182900273152",
  "8019460130754002944"
]
```

**Resulting Filter:**
```
resource.labels.reasoning_engine_id="8213677864684355584" OR 
resource.labels.reasoning_engine_id="6010661182900273152" OR 
resource.labels.reasoning_engine_id="8019460130754002944"
```

**When to Use:**
- You want logs only from specific Reasoning Engines
- You have multiple engines but only care about some
- You want to isolate engine-specific logs

**Leave Empty If:**
- You want all Reasoning Engine logs
- You're not using Reasoning Engines

---

### **2. Agent IDs** (Optional)

**Variable:** `agent_ids`

**Purpose:** Filter logs from specific agents

**Type:** `list(string)`

**Example:**
```hcl
agent_ids = [
  "agent-001",
  "agent-monitoring",
  "customer-service-agent"
]
```

**Resulting Filter:**
```
resource.labels.agent_id="agent-001" OR 
resource.labels.agent_id="agent-monitoring" OR 
resource.labels.agent_id="customer-service-agent"
```

**When to Use:**
- You have multiple agents and want logs from specific ones
- You want to track particular agent instances
- You need agent-level observability

**Leave Empty If:**
- You want all agent logs
- You don't use agent_id labels

---

### **3. Log Severity Filter** (Optional)

**Variable:** `log_severity_filter`

**Purpose:** Filter by log severity level

**Type:** `list(string)`

**Available Severities:**
- `DEFAULT` (0)
- `DEBUG` (100)
- `INFO` (200)
- `NOTICE` (300)
- `WARNING` (400)
- `ERROR` (500)
- `CRITICAL` (600)
- `ALERT` (700)
- `EMERGENCY` (800)

**Example:**
```hcl
# Only errors and critical issues
log_severity_filter = ["ERROR", "CRITICAL", "ALERT"]
```

**Resulting Filter:**
```
severity="ERROR" OR severity="CRITICAL" OR severity="ALERT"
```

**Common Patterns:**

**Errors Only:**
```hcl
log_severity_filter = ["ERROR"]
```

**Warnings and Above:**
```hcl
log_severity_filter = ["WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY"]
```

**Critical Issues Only:**
```hcl
log_severity_filter = ["CRITICAL", "ALERT", "EMERGENCY"]
```

**When to Use:**
- Reduce log volume by filtering out DEBUG/INFO
- Focus on errors and critical issues
- Cost optimization

**Leave Empty If:**
- You want all severity levels
- You'll filter severity downstream (in Lambda)

---

### **4. Log Resource Types** (Optional)

**Variable:** `log_resource_types`

**Purpose:** Filter by GCP resource type

**Type:** `list(string)`

**Common Resource Types:**
```
aiplatform.googleapis.com/ReasoningEngine
cloud_run_revision
cloud_function
gce_instance
k8s_container
k8s_pod
gae_app
cloudsql_database
```

**Example:**
```hcl
log_resource_types = ["cloud_run_revision", "cloud_function"]
```

**Resulting Filter:**
```
resource.type="cloud_run_revision" OR resource.type="cloud_function"
```

**When to Use:**
- You want logs from specific GCP services
- You're monitoring multiple service types
- You want to isolate service-specific logs

**Leave Empty If:**
- You want all resource types
- You're using reasoning_engine_ids (already filters resource type)

---

### **5. Custom Log Filter** (Optional)

**Variable:** `custom_log_filter`

**Purpose:** Advanced filtering using full GCP Logging Query Language

**Type:** `string`

**Examples:**

**JSON Payload Filtering:**
```hcl
custom_log_filter = "jsonPayload.message=~\"error.*\""
```

**Label-Based Filtering:**
```hcl
custom_log_filter = "labels.environment=\"production\" AND labels.region=\"us-central1\""
```

**HTTP Request Filtering:**
```hcl
custom_log_filter = "httpRequest.status>=500 AND httpRequest.latency>\"1s\""
```

**Time-Based Filtering:**
```hcl
custom_log_filter = "timestamp>=\"2024-04-01T00:00:00Z\""
```

**Complex Combinations:**
```hcl
custom_log_filter = "(jsonPayload.error_code=\"500\" OR jsonPayload.error_code=\"503\") AND labels.customer_tier=\"premium\""
```

**When to Use:**
- You need advanced filtering logic
- Standard filters don't meet your needs
- You want to filter on JSON fields, labels, HTTP data, etc.

**Leave Empty If:**
- Standard filters are sufficient

---

### **6. Use Custom Filter Only** (Optional)

**Variable:** `use_custom_filter_only`

**Purpose:** Ignore all other filter variables and use only `custom_log_filter`

**Type:** `bool`

**Default:** `false`

**Example:**
```hcl
custom_log_filter = "resource.type=\"gce_instance\" AND severity>=\"ERROR\" AND labels.team=\"backend\""
use_custom_filter_only = true

# All other filter variables will be ignored
reasoning_engine_ids = []  # Ignored
agent_ids = []             # Ignored
log_severity_filter = []   # Ignored
log_resource_types = []    # Ignored
```

**When to Use:**
- You have very specific filtering requirements
- You want full control over the filter expression
- Standard filters create conflicts with your custom filter

**Leave `false` If:**
- You want to combine standard filters with custom filter

---

## 🎨 **Filter Combination Examples**

### **Example 1: Basic - Specific Reasoning Engines Only**

```hcl
reasoning_engine_ids = ["8213677864684355584"]
agent_ids = []
log_severity_filter = []
log_resource_types = []
custom_log_filter = ""
```

**Result:** Only logs from reasoning engine `8213677864684355584`

---

### **Example 2: Errors from Specific Agents**

```hcl
reasoning_engine_ids = []
agent_ids = ["agent-001", "agent-002"]
log_severity_filter = ["ERROR", "CRITICAL"]
log_resource_types = []
custom_log_filter = ""
```

**Result:** Only ERROR and CRITICAL logs from agent-001 and agent-002

---

### **Example 3: Production Environment Errors**

```hcl
reasoning_engine_ids = []
agent_ids = []
log_severity_filter = ["ERROR", "CRITICAL", "ALERT"]
log_resource_types = []
custom_log_filter = "labels.environment=\"production\""
```

**Result:** ERROR+ logs from production environment only

---

### **Example 4: Multi-Service Monitoring**

```hcl
reasoning_engine_ids = []
agent_ids = []
log_severity_filter = ["WARNING", "ERROR", "CRITICAL"]
log_resource_types = ["cloud_run_revision", "cloud_function"]
custom_log_filter = ""
```

**Result:** WARNING+ logs from Cloud Run and Cloud Functions

---

### **Example 5: High-Priority Customer Errors**

```hcl
reasoning_engine_ids = []
agent_ids = []
log_severity_filter = ["ERROR", "CRITICAL"]
log_resource_types = []
custom_log_filter = "labels.customer_tier=\"premium\" OR labels.customer_tier=\"enterprise\""
```

**Result:** Errors from premium/enterprise customers only

---

### **Example 6: Full Custom Control**

```hcl
reasoning_engine_ids = []
agent_ids = []
log_severity_filter = []
log_resource_types = []
custom_log_filter = "resource.type=\"aiplatform.googleapis.com/ReasoningEngine\" AND (resource.labels.reasoning_engine_id=\"8213677864684355584\" OR resource.labels.agent_id=\"agent-001\") AND severity>=\"WARNING\" AND timestamp>=\"2024-04-01T00:00:00Z\""
use_custom_filter_only = true
```

**Result:** Complete custom filter with full control

---

## 🚀 **Quick Start - Common Scenarios**

### **Scenario 1: I want ALL logs from my reasoning engines**

```hcl
reasoning_engine_ids = ["YOUR_ENGINE_ID_1", "YOUR_ENGINE_ID_2"]
agent_ids = []
log_severity_filter = []
log_resource_types = []
custom_log_filter = ""
```

---

### **Scenario 2: I want only ERRORS (cost optimization)**

```hcl
reasoning_engine_ids = ["YOUR_ENGINE_ID"]
agent_ids = []
log_severity_filter = ["ERROR", "CRITICAL", "ALERT"]
log_resource_types = []
custom_log_filter = ""
```

**Cost Savings:** ~80-90% reduction in log volume

---

### **Scenario 3: I want logs from specific agents with errors**

```hcl
reasoning_engine_ids = []
agent_ids = ["agent-001", "agent-002", "agent-monitoring"]
log_severity_filter = ["ERROR", "CRITICAL"]
log_resource_types = []
custom_log_filter = ""
```

---

### **Scenario 4: I want production logs only**

```hcl
reasoning_engine_ids = ["YOUR_ENGINE_ID"]
agent_ids = []
log_severity_filter = []
log_resource_types = []
custom_log_filter = "labels.environment=\"production\""
```

---

### **Scenario 5: I want NO filtering (everything)**

```hcl
reasoning_engine_ids = []
agent_ids = []
log_severity_filter = []
log_resource_types = []
custom_log_filter = ""
```

**Note:** This will create a filter that matches all logs: `resource.type="*"`

**Warning:** Very expensive! Only use for testing.

---

## 🧪 **Testing Your Filters**

### **Method 1: GCP Console (Logs Explorer)**

1. Go to: https://console.cloud.google.com/logs/query?project=YOUR_PROJECT_ID
2. Build your filter using the query builder
3. Test with your actual logs
4. Copy the working filter to `custom_log_filter`

### **Method 2: gcloud CLI**

```bash
# Test your filter
gcloud logging read 'YOUR_FILTER_EXPRESSION' \
  --limit=10 \
  --project=YOUR_PROJECT_ID

# Example: Test reasoning engine filter
gcloud logging read 'resource.labels.reasoning_engine_id="8213677864684355584"' \
  --limit=5 \
  --project=agentic-ai-integration-490716
```

### **Method 3: Check Current Sink Filter**

```bash
# After deployment, check what filter is actually deployed
terraform output log_sink_filter

# Or via gcloud
gcloud logging sinks describe reasoning-engine-to-pubsub \
  --project=YOUR_PROJECT_ID \
  --format="value(filter)"
```

---

## 💰 **Cost Optimization Guide**

### **Cost Impact by Filter Strategy**

| Strategy | Volume | Pub/Sub Cost | Lambda Cost | Total Cost |
|----------|--------|--------------|-------------|------------|
| No filter (everything) | 100% | $$$$ | $$$$ | **$10,000/mo** |
| Severity >= ERROR | 10% | $$$ | $$ | **$1,000/mo** |
| Specific agents + ERROR | 5% | $$ | $ | **$500/mo** |
| Production + ERROR | 2% | $ | $ | **$200/mo** |

*(Hypothetical example for 1M logs/day)*

### **Cost Optimization Strategies**

**1. Start with Severity Filtering**
```hcl
log_severity_filter = ["ERROR", "CRITICAL"]
```
**Savings:** 80-90%

**2. Add Resource Filtering**
```hcl
reasoning_engine_ids = ["specific-engine"]
log_severity_filter = ["ERROR", "CRITICAL"]
```
**Savings:** 85-95%

**3. Add Environment Filtering**
```hcl
reasoning_engine_ids = ["specific-engine"]
log_severity_filter = ["ERROR", "CRITICAL"]
custom_log_filter = "labels.environment=\"production\""
```
**Savings:** 90-95%

**4. Advanced: Sampling (if needed)**
```hcl
custom_log_filter = "sample(insertId, 0.1)"  # 10% sample
```
**Savings:** 90% (use carefully!)

---

## 🐛 **Troubleshooting**

### **Issue 1: No logs appearing in Lambda**

**Possible Causes:**
1. Filter too restrictive
2. No logs match the filter
3. Logs don't have expected labels

**Solution:**
```bash
# Test if ANY logs match your filter
gcloud logging read 'YOUR_FILTER' --limit=5 --project=YOUR_PROJECT_ID

# If no results, relax filter gradually:
# 1. Remove custom_log_filter
# 2. Remove severity filter
# 3. Remove agent_ids
# 4. Keep only reasoning_engine_ids
```

---

### **Issue 2: Too many logs (high costs)**

**Solution:**
```hcl
# Add severity filter
log_severity_filter = ["ERROR", "CRITICAL"]

# Or add custom filter
custom_log_filter = "severity>=\"ERROR\""
```

---

### **Issue 3: Filter syntax error**

**Common Mistakes:**
```hcl
# ❌ WRONG - Missing quotes
custom_log_filter = "labels.env=production"

# ✅ CORRECT
custom_log_filter = "labels.env=\"production\""

# ❌ WRONG - Invalid operator
custom_log_filter = "severity==ERROR"

# ✅ CORRECT
custom_log_filter = "severity=\"ERROR\""
```

---

### **Issue 4: Want to change filter after deployment**

**Solution:**
```bash
# 1. Update terraform.tfvars
# 2. Apply changes
terraform plan
terraform apply

# The log sink filter will be updated automatically
```

---

## 📊 **Monitoring Your Filters**

### **Check Filter Performance**

```bash
# View current sink configuration
gcloud logging sinks describe reasoning-engine-to-pubsub \
  --project=YOUR_PROJECT_ID

# Check Pub/Sub metrics (messages received)
gcloud pubsub topics describe reasoning-engine-logs-topic \
  --project=YOUR_PROJECT_ID
```

### **Monitor in Console**

**Log Sink:**
https://console.cloud.google.com/logs/router?project=YOUR_PROJECT_ID

**Pub/Sub Topic:**
https://console.cloud.google.com/cloudpubsub/topic/detail/reasoning-engine-logs-topic?project=YOUR_PROJECT_ID

**Metrics to Watch:**
- Log entries exported (per minute)
- Pub/Sub messages published
- Lambda invocations
- Costs

---

## 📝 **Best Practices**

### ✅ **DO:**

1. **Start restrictive, then expand**
   - Begin with ERROR logs only
   - Add more severities if needed

2. **Test filters before deploying**
   - Use Logs Explorer
   - Verify logs actually exist

3. **Use severity filtering**
   - Reduces volume significantly
   - Focus on important events

4. **Document your filters**
   - Comment why you chose specific filters
   - Note any special requirements

5. **Monitor costs**
   - Check Pub/Sub and Lambda metrics
   - Adjust filters if costs are high

### ❌ **DON'T:**

1. **Don't export everything**
   - Very expensive
   - Overwhelming volume

2. **Don't use overly complex regex**
   - Performance impact
   - Hard to maintain

3. **Don't filter in Lambda if you can filter in sink**
   - Pay for Lambda invocations
   - Filter at source is cheaper

4. **Don't forget to test**
   - Failed filters = no logs
   - Or too many logs = high costs

---

## 🔗 **Related Documentation**

- [Main README](./README.md) - Setup instructions
- [Terraform Architecture](./TERRAFORM_ARCHITECTURE.md) - Overall architecture
- [GCP Logging Query Language](https://cloud.google.com/logging/docs/view/logging-query-language) - Official filter syntax
- [LOG_SINK_DEEP_DIVE.md](../LOG_SINK_DEEP_DIVE.md) - Comprehensive log sink guide

---

## 📞 **Support**

**Issues or Questions?**
- Review filter syntax in GCP Logs Explorer
- Check Terraform output for deployed filter: `terraform output log_sink_filter`
- Test filter with gcloud: `gcloud logging read 'YOUR_FILTER' --limit=5`

---

**Last Updated:** 2024-04-23
