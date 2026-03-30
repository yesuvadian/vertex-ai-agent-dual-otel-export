#!/usr/bin/env python3
"""
Start ngrok and get the public URL
"""
import subprocess
import time
import requests
import sys

print("=" * 70)
print("Starting ngrok tunnel for port 4318...")
print("=" * 70)
print()

# Start ngrok in background
try:
    # Start ngrok process
    process = subprocess.Popen(
        ["ngrok", "http", "4318"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == 'win32' else 0
    )

    print("Waiting for ngrok to initialize...")
    time.sleep(5)

    # Get tunnel information from ngrok API
    for attempt in range(10):
        try:
            response = requests.get("http://localhost:4040/api/tunnels", timeout=2)
            if response.status_code == 200:
                data = response.json()
                tunnels = data.get('tunnels', [])

                if tunnels:
                    public_url = tunnels[0]['public_url']
                    print()
                    print("=" * 70)
                    print("SUCCESS! ngrok tunnel is running")
                    print("=" * 70)
                    print()
                    print(f"Public URL: {public_url}")
                    print()
                    print("=" * 70)
                    print("Next Steps:")
                    print("=" * 70)
                    print()
                    print("1. Copy the URL above")
                    print()
                    print("2. Update Cloud Run:")
                    print(f"   gcloud run services update ai-agent \\")
                    print(f"     --region=us-central1 \\")
                    print(f"     --update-env-vars=\"OTEL_EXPORTER_OTLP_ENDPOINT={public_url}\"")
                    print()
                    print("3. Test the connection")
                    print()
                    print("4. View ngrok requests at: http://localhost:4040")
                    print()
                    print("=" * 70)
                    print()
                    print("Keep this window open while using ngrok!")
                    print()

                    # Save URL to file
                    with open("ngrok_url.txt", "w") as f:
                        f.write(public_url)

                    sys.exit(0)
        except requests.exceptions.RequestException:
            pass

        time.sleep(1)
        print(f"Waiting for ngrok... (attempt {attempt + 1}/10)")

    print()
    print("[ERROR] Could not connect to ngrok API after 10 attempts")
    print()
    print("Please manually start ngrok:")
    print("  ngrok http 4318")
    print()
    print("Then visit: http://localhost:4040")
    sys.exit(1)

except FileNotFoundError:
    print("[ERROR] ngrok command not found!")
    print()
    print("Please install ngrok:")
    print("  - Download: https://ngrok.com/download")
    print("  - Or: choco install ngrok")
    print("  - Or: scoop install ngrok")
    sys.exit(1)
except Exception as e:
    print(f"[ERROR] {e}")
    sys.exit(1)
