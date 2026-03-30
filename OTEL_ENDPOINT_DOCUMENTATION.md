# Portal26 OTEL Endpoint Documentation

## ❌ Swagger/OpenAPI Not Available

The Portal26 OTEL endpoint **does not expose Swagger/OpenAPI documentation** because:
- It implements the standard **OTLP (OpenTelemetry Protocol)** specification
- OTLP is a well-defined protocol, not a custom REST API
- The endpoints are **write-only** (ingestion only, no query API)

## 📚 Standard OTLP Specification

Portal26 follows the official OpenTelemetry Protocol specification:
- **Specification**: https://opentelemetry.io/docs/specs/otlp/
- **Protocol**: HTTP/protobuf or HTTP/JSON
- **Version**: OTLP 1.0

## 🔌 Available Endpoints

### 1. Traces Endpoint
```
POST https://otel-tenant1.portal26.in:4318/v1/traces
Content-Type: application/json
Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==

{
  "resourceSpans": [{
    "resource": {
      "attributes": [
        {"key": "service.name", "value": {"stringValue": "ai-agent"}},
        {"key": "portal26.user.id", "value": {"stringValue": "relusys"}},
        {"key": "portal26.tenant_id", "value": {"stringValue": "tenant1"}}
      ]
    },
    "scopeSpans": [{
      "spans": [
        {
          "traceId": "hex-encoded-16-bytes",
          "spanId": "hex-encoded-8-bytes",
          "name": "operation_name",
          "kind": 1,
          "startTimeUnixNano": 1234567890000000000,
          "endTimeUnixNano": 1234567891000000000,
          "attributes": [
            {"key": "custom.attribute", "value": {"stringValue": "value"}}
          ]
        }
      ]
    }]
  }]
}
```

**Response**: `200 OK` with `{"partialSuccess":{}}`

### 2. Metrics Endpoint
```
POST https://otel-tenant1.portal26.in:4318/v1/metrics
Content-Type: application/json
Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==

{
  "resourceMetrics": [{
    "resource": {
      "attributes": [
        {"key": "service.name", "value": {"stringValue": "ai-agent"}},
        {"key": "portal26.user.id", "value": {"stringValue": "relusys"}},
        {"key": "portal26.tenant_id", "value": {"stringValue": "tenant1"}}
      ]
    },
    "scopeMetrics": [{
      "metrics": [{
        "name": "metric_name",
        "unit": "1",
        "sum": {
          "dataPoints": [{
            "timeUnixNano": 1234567890000000000,
            "asInt": 42
          }]
        }
      }]
    }]
  }]
}
```

**Response**: `200 OK` with `{"partialSuccess":{}}`

### 3. Logs Endpoint
```
POST https://otel-tenant1.portal26.in:4318/v1/logs
Content-Type: application/json
Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==

{
  "resourceLogs": [{
    "resource": {
      "attributes": [
        {"key": "service.name", "value": {"stringValue": "ai-agent"}},
        {"key": "portal26.user.id", "value": {"stringValue": "relusys"}},
        {"key": "portal26.tenant_id", "value": {"stringValue": "tenant1"}}
      ]
    },
    "scopeLogs": [{
      "logRecords": [{
        "timeUnixNano": 1234567890000000000,
        "severityText": "INFO",
        "body": {"stringValue": "Log message here"}
      }]
    }]
  }]
}
```

**Response**: `200 OK` with `{"partialSuccess":{}}`

## 🔐 Authentication

**Method**: HTTP Basic Authentication
**Header**: `Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==`

Decoded credentials:
- Username: `titaniam`
- Password: `helloworld`

## 📊 Resource Attributes (Required for Portal26)

Every request must include these attributes:

| Attribute | Value | Description |
|-----------|-------|-------------|
| `service.name` | `ai-agent` | Service identifier |
| `portal26.user.id` | `relusys` | Portal26 user ID |
| `portal26.tenant_id` | `tenant1` | Portal26 tenant ID |
| `service.version` | `1.0` | Service version (optional) |
| `deployment.environment` | `production` | Environment (optional) |

## ✅ Verified Working

All endpoints have been tested and confirmed working:

```bash
# Traces
curl -X POST https://otel-tenant1.portal26.in:4318/v1/traces \
  -H "Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  -H "Content-Type: application/json" \
  -d '{"resourceSpans":[...]}'
# Response: 200 OK {"partialSuccess":{}}

# Metrics
curl -X POST https://otel-tenant1.portal26.in:4318/v1/metrics \
  -H "Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  -H "Content-Type: application/json" \
  -d '{"resourceMetrics":[...]}'
# Response: 200 OK {"partialSuccess":{}}

# Logs
curl -X POST https://otel-tenant1.portal26.in:4318/v1/logs \
  -H "Authorization: Basic dGl0YW5pYW06aGVsbG93b3JsZA==" \
  -H "Content-Type: application/json" \
  -d '{"resourceLogs":[...]}'
# Response: 200 OK {"partialSuccess":{}}
```

## 🚫 No Query/Read API

**Important**: These endpoints are **write-only** for telemetry ingestion.

To **read/query** the data, you must use:
- **Portal26 Dashboard UI**: https://portal26.in
- **Portal26 Query API**: (if available - check Portal26 documentation)

The OTLP endpoints do not support:
- `GET` requests (returns `405 Method Not Allowed`)
- Data retrieval or queries
- Swagger/OpenAPI documentation

## 📖 Reference Documentation

1. **OTLP Specification**: https://opentelemetry.io/docs/specs/otlp/
2. **OTLP HTTP Spec**: https://opentelemetry.io/docs/specs/otlp/#otlphttp
3. **OpenTelemetry Protocol Buffer Definitions**: https://github.com/open-telemetry/opentelemetry-proto

## 🧪 Testing Scripts

See the following scripts in this repository:
- `test_otel_send.py` - Send test data to all endpoints
- `capture_otel_export.py` - Capture real-time export with proof
- `verify_otel_export.py` - Comprehensive verification

## 💡 Summary

**Portal26 OTEL Endpoint**:
- ✅ Follows standard OTLP specification
- ✅ Accepts traces, metrics, and logs
- ✅ Returns `200 OK` with `{"partialSuccess":{}}` on success
- ❌ No Swagger/OpenAPI (not applicable for OTLP)
- ❌ No read/query API (ingestion only)

**To view data**: Use Portal26 Dashboard or Query API (separate from OTLP endpoint)
