#!/usr/bin/env python3
"""
Automated validation script for AI Agent OTEL integration
Runs all tests and produces a validation report
"""

import requests
import subprocess
import time
import json
from datetime import datetime

# ANSI color codes (disabled for Windows compatibility)
GREEN = ""
RED = ""
YELLOW = ""
BLUE = ""
RESET = ""

class ValidationReport:
    def __init__(self):
        self.tests = []
        self.passed = 0
        self.failed = 0
        self.warnings = 0

    def add_test(self, name, status, details=""):
        self.tests.append({
            "name": name,
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })

        if status == "PASS":
            self.passed += 1
        elif status == "FAIL":
            self.failed += 1
        elif status == "WARN":
            self.warnings += 1

    def print_summary(self):
        print("\n" + "=" * 80)
        print("VALIDATION REPORT SUMMARY")
        print("=" * 80)
        print(f"\nTotal Tests: {len(self.tests)}")
        print(f"Passed: {self.passed}")
        print(f"Failed: {self.failed}")
        print(f"Warnings: {self.warnings}")
        print("\nDetailed Results:")
        print("-" * 80)

        for test in self.tests:
            status_icon = {
                "PASS": "[OK]",
                "FAIL": "[FAIL]",
                "WARN": "[WARN]",
                "SKIP": "[SKIP]"
            }.get(test["status"], "[?]")

            print(f"{status_icon} {test['name']}")
            if test['details']:
                print(f"    {test['details']}")

        print("\n" + "=" * 80)

        if self.failed == 0:
            print("RESULT: ALL TESTS PASSED")
            print("Your OTEL integration is working correctly!")
        else:
            print(f"RESULT: {self.failed} TEST(S) FAILED")
            print("Review failures above and check troubleshooting guide.")
        print("=" * 80 + "\n")

def run_command(cmd, timeout=30):
    """Run shell command and return output"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timeout"
    except Exception as e:
        return False, "", str(e)

def main():
    print("=" * 80)
    print("AI AGENT OTEL INTEGRATION - AUTOMATED VALIDATION")
    print("=" * 80)
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n")

    report = ValidationReport()

    # Configuration
    AI_AGENT_URL = "https://ai-agent-961756870884.us-central1.run.app"
    OTEL_ENDPOINT = "https://otel-tenant1.portal26.in:4318"
    PROJECT_ID = "agentic-ai-integration-490716"
    SERVICE_NAME = "ai-agent"
    REGION = "us-central1"

    # Test 1: Check gcloud authentication
    print("Test 1: Checking gcloud authentication...")
    print("-" * 80)
    success, stdout, stderr = run_command("gcloud auth list --filter=status:ACTIVE --format='value(account)'")
    if success and stdout.strip():
        print(f"[OK] Authenticated as: {stdout.strip()}")
        report.add_test("gcloud Authentication", "PASS", f"Account: {stdout.strip()}")
    else:
        print("[FAIL] Not authenticated. Run: gcloud auth login")
        report.add_test("gcloud Authentication", "FAIL", "Not authenticated")
        print("\nPlease authenticate and run this script again.")
        return

    # Test 2: Get auth token
    print("\nTest 2: Getting identity token...")
    print("-" * 80)
    success, token, stderr = run_command("gcloud auth print-identity-token")
    token = token.strip()
    if success and token:
        print("[OK] Token obtained")
        report.add_test("Identity Token", "PASS")
    else:
        print("[FAIL] Could not get token")
        report.add_test("Identity Token", "FAIL", stderr)
        token = None

    # Test 3: Check Cloud Run service
    print("\nTest 3: Checking Cloud Run service status...")
    print("-" * 80)
    success, stdout, stderr = run_command(
        f"gcloud run services describe {SERVICE_NAME} --region={REGION} --format='value(status.url)'"
    )
    if success and AI_AGENT_URL in stdout:
        print(f"[OK] Service deployed: {AI_AGENT_URL}")
        report.add_test("Cloud Run Service", "PASS", AI_AGENT_URL)
    else:
        print(f"[FAIL] Service not found or not deployed")
        report.add_test("Cloud Run Service", "FAIL", stderr)

    # Test 4: Check OTEL environment variables
    print("\nTest 4: Checking OTEL configuration...")
    print("-" * 80)
    success, stdout, stderr = run_command(
        f"gcloud run services describe {SERVICE_NAME} --region={REGION} --format='yaml(spec.template.spec.containers[0].env)'"
    )

    required_vars = [
        "OTEL_TRACES_EXPORTER",
        "OTEL_METRICS_EXPORTER",
        "OTEL_LOGS_EXPORTER",
        "OTEL_EXPORTER_OTLP_ENDPOINT"
    ]

    missing_vars = []
    for var in required_vars:
        if var not in stdout:
            missing_vars.append(var)

    if not missing_vars:
        print("[OK] All OTEL environment variables configured")
        report.add_test("OTEL Environment Variables", "PASS")
    else:
        print(f"[FAIL] Missing variables: {', '.join(missing_vars)}")
        report.add_test("OTEL Environment Variables", "FAIL", f"Missing: {missing_vars}")

    # Test 5: Test status endpoint
    print("\nTest 5: Testing AI Agent status endpoint...")
    print("-" * 80)
    try:
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        response = requests.get(f"{AI_AGENT_URL}/status", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Status endpoint working")
            print(f"    Agent Mode: {data.get('agent_mode')}")
            report.add_test("Status Endpoint", "PASS", f"Agent mode: {data.get('agent_mode')}")
        else:
            print(f"[FAIL] Status: {response.status_code}")
            report.add_test("Status Endpoint", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        report.add_test("Status Endpoint", "FAIL", str(e))

    # Test 6: Send test request to AI agent
    print("\nTest 6: Sending test request to AI Agent...")
    print("-" * 80)
    test_id = f"VALIDATION-{int(time.time())}"
    try:
        headers = {"Content-Type": "application/json"}
        if token:
            headers["Authorization"] = f"Bearer {token}"

        payload = {"message": f"{test_id}: What is the weather in Tokyo?"}
        response = requests.post(f"{AI_AGENT_URL}/chat", headers=headers, json=payload, timeout=30)

        if response.status_code == 200:
            print(f"[OK] Request successful")
            print(f"    Test ID: {test_id}")
            print(f"    Response: {response.text[:100]}...")
            report.add_test("AI Agent Chat Request", "PASS", f"Test ID: {test_id}")
        else:
            print(f"[FAIL] Status: {response.status_code}")
            report.add_test("AI Agent Chat Request", "FAIL", f"HTTP {response.status_code}")
    except Exception as e:
        print(f"[FAIL] Error: {e}")
        report.add_test("AI Agent Chat Request", "FAIL", str(e))

    # Test 7: Check Cloud Run logs for OTEL initialization
    print("\nTest 7: Checking Cloud Run logs for OTEL initialization...")
    print("-" * 80)
    success, stdout, stderr = run_command(
        f'gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name={SERVICE_NAME}" '
        f'--limit=50 --format="value(textPayload)" --project={PROJECT_ID}'
    )

    if success:
        exporters_found = {
            "traces": "OTLP trace exporter configured" in stdout,
            "metrics": "OTLP metric exporter configured" in stdout,
            "logs": "OTLP log exporter configured" in stdout
        }

        all_found = all(exporters_found.values())

        if all_found:
            print("[OK] All OTEL exporters initialized")
            report.add_test("OTEL Exporters Initialization", "PASS")
        else:
            missing = [k for k, v in exporters_found.items() if not v]
            print(f"[FAIL] Missing exporters: {', '.join(missing)}")
            report.add_test("OTEL Exporters Initialization", "FAIL", f"Missing: {missing}")

        # Check for errors
        if "Failed to export" in stdout or "export failed" in stdout.lower():
            print("[WARN] Found export errors in logs")
            report.add_test("OTEL Export Errors", "WARN", "Errors found in logs")
        else:
            print("[OK] No export errors found")
            report.add_test("OTEL Export Errors", "PASS")
    else:
        print("[FAIL] Could not retrieve logs")
        report.add_test("OTEL Exporters Initialization", "FAIL", "Cannot retrieve logs")

    # Test 8: Test OTLP endpoints directly
    print("\nTest 8: Testing Portal26 OTLP endpoints...")
    print("-" * 80)

    auth_header = "Authorization=Basic dGl0YW5pYW06aGVsbG93b3JsZA=="
    headers = {"Content-Type": "application/json"}
    for header in auth_header.split(","):
        if "=" in header:
            key, value = header.split("=", 1)
            headers[key.strip()] = value.strip()

    endpoints = {
        "Traces": f"{OTEL_ENDPOINT}/v1/traces",
        "Metrics": f"{OTEL_ENDPOINT}/v1/metrics",
        "Logs": f"{OTEL_ENDPOINT}/v1/logs"
    }

    for name, endpoint in endpoints.items():
        try:
            # Minimal valid OTLP payload
            payload = {
                "resourceSpans" if "traces" in endpoint else "resourceMetrics" if "metrics" in endpoint else "resourceLogs": []
            }

            response = requests.post(endpoint, headers=headers, json=payload, timeout=10)

            if response.status_code in [200, 201, 202, 204]:
                print(f"[OK] {name} endpoint: {response.status_code}")
                report.add_test(f"OTLP {name} Endpoint", "PASS", f"HTTP {response.status_code}")
            else:
                print(f"[FAIL] {name} endpoint: {response.status_code}")
                report.add_test(f"OTLP {name} Endpoint", "FAIL", f"HTTP {response.status_code}")
        except Exception as e:
            print(f"[FAIL] {name} endpoint error: {e}")
            report.add_test(f"OTLP {name} Endpoint", "FAIL", str(e))

    # Wait for data propagation
    print("\nWaiting 3 seconds for telemetry to propagate...")
    time.sleep(3)

    # Print report
    report.print_summary()

    # Print next steps
    print("\nNEXT STEPS:")
    print("-" * 80)
    print("\n1. View data in Portal26:")
    print("   URL: https://portal26.in")
    print("   Login: titaniam / helloworld")
    print("   Filter by:")
    print("     - Service: ai-agent")
    print("     - Tenant: tenant1")
    print(f"     - Search for: {test_id}")
    print()
    print("2. Run individual test scripts:")
    print("   python test_otel_send.py")
    print("   python verify_otel_export.py")
    print("   python capture_otel_export.py")
    print()
    print("3. Check documentation:")
    print("   USER_TESTING_MANUAL.md - Complete testing guide")
    print("   TESTING_QUICK_REFERENCE.md - Quick reference")
    print()

    # Save report to file
    report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(report.tests),
                "passed": report.passed,
                "failed": report.failed,
                "warnings": report.warnings
            },
            "tests": report.tests
        }, f, indent=2)

    print(f"Report saved to: {report_file}")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
    except Exception as e:
        print(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
