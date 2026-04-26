# Log Sink Filters - High-Level Overview

## 🎯 **What It Does**

Filters control which logs get exported from Google Cloud to AWS.

**Without filters:** Export everything (expensive, noisy)  
**With filters:** Export only what matters (cheaper, focused)

---

## 💰 **Cost Impact**

| Filter Level | Logs Exported | Cost/Month |
|--------------|---------------|------------|
| Everything | 100% | $10,000 |
| Errors Only | 10% | $1,000 |
| Production Errors | 5% | $500 |

**Typical savings: 80-95%**

---

## 🎛️ **Filter Options (All Optional)**

### **1. By Reasoning Engine**
```hcl
reasoning_engine_ids = ["8213677864684355584"]
```
Filter logs from specific AI engines.

### **2. By Agent**
```hcl
agent_ids = ["agent-001", "agent-002"]
```
Filter logs from specific agents.

### **3. By Severity**
```hcl
log_severity_filter = ["ERROR", "CRITICAL"]
```
Filter by importance level.

**Options:** `DEBUG` → `INFO` → `WARNING` → `ERROR` → `CRITICAL`

### **4. By Resource Type**
```hcl
log_resource_types = ["cloud_run_revision", "cloud_function"]
```
Filter by Google Cloud service type.

### **5. Custom Filter**
```hcl
custom_log_filter = "labels.environment=\"production\""
```
Advanced filtering for special requirements.

---

## 📋 **Common Scenarios**

### **Scenario 1: Testing Phase**
```hcl
# Export everything
reasoning_engine_ids = ["YOUR_ENGINE_ID"]
```
**Cost:** High | **Use:** Short-term learning

### **Scenario 2: Production (Recommended)**
```hcl
# Export only errors
reasoning_engine_ids = ["YOUR_ENGINE_ID"]
log_severity_filter = ["ERROR", "CRITICAL"]
```
**Cost:** Low | **Savings:** 80-90%

### **Scenario 3: Production + Specific Agents**
```hcl
# Errors from specific agents only
agent_ids = ["agent-001", "agent-002"]
log_severity_filter = ["ERROR", "CRITICAL"]
```
**Cost:** Very Low | **Savings:** 90-95%

---

## 🚀 **Quick Start**

**1. Edit terraform.tfvars:**
```hcl
reasoning_engine_ids = ["YOUR_ENGINE_ID"]
log_severity_filter = ["ERROR", "CRITICAL"]
```

**2. Deploy:**
```bash
terraform apply
```

**3. Monitor costs and adjust**

---

## ✅ **Recommendations**

- **Week 1-2:** Export everything (learn patterns)
- **Week 3+:** Switch to ERROR only (save 80-90%)
- **Ongoing:** Refine based on needs

---

## 🔑 **Key Takeaway**

**More filtering = Lower costs**

Start with errors only, expand if needed.

---

**Files:**
- Technical details: `LOG_SINK_FILTERS_GUIDE.md`
- Business overview: `LOG_SINK_FILTERS_BUSINESS_OVERVIEW.md`
