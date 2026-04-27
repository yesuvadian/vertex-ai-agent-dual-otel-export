#!/bin/bash
# Auto-detect OS and set GOOGLE_APPLICATION_CREDENTIALS

KEY_FILE="appengine-sa-key.json"

# Check if key file exists
if [ ! -f "$KEY_FILE" ]; then
    echo "ERROR: $KEY_FILE not found!"
    echo "Please generate your service account key first."
    exit 1
fi

# Set the environment variable
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/$KEY_FILE"

echo "✓ Credentials set successfully!"
echo "  GOOGLE_APPLICATION_CREDENTIALS=$GOOGLE_APPLICATION_CREDENTIALS"
echo ""
echo "Note: This variable is only set for the current terminal session."
echo "Run this script again if you open a new terminal."
