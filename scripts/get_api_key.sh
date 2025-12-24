#!/bin/bash
# Helper script to get or create an API key for testing
#
# This script will:
# 1. Check if an API key exists in environment variable
# 2. Try to find a default key from server logs
# 3. Guide you on how to create a new key

set -e

API_URL="${API_URL:-http://localhost:8000/api/v1}"

echo "🔑 MemStack API Key Helper"
echo "=========================="
echo ""

# Check environment variable
if [ -n "$API_KEY" ]; then
    echo "✓ Found API_KEY in environment:"
    echo "  $API_KEY"
    echo ""
    echo "You can use this key with:"
    echo "  export API_KEY=\"$API_KEY\""
    echo "  make test-data"
    exit 0
fi

# Check server health
echo "Checking if server is running at $API_URL..."
if ! curl -s "${API_URL}/health" > /dev/null 2>&1; then
    echo "✗ Server is not running. Please start the server first:"
    echo "  make dev"
    echo ""
    exit 1
fi

echo "✓ Server is running"
echo ""

# Try to get the default admin key from server logs
echo "Looking for default API key in server logs..."
echo ""
echo "The default API key is printed when the server starts."
echo "Look for output like:"
echo "  🔑 Default Admin API Key created: ms_sk_..."
echo ""

# Try to find from logs if server was started with make dev
if [ -f .server_log ]; then
    KEY=$(grep "Default Admin API Key created" .server_log 2>/dev/null | head -1 | sed 's/.*: //')
    if [ -n "$KEY" ]; then
        echo "✓ Found API key in logs:"
        echo "  $KEY"
        echo ""
        echo "Export it with:"
        echo "  export API_KEY=\"$KEY\""
        echo ""
        exit 0
    fi
fi

echo "Could not find default API key automatically."
echo ""
echo "Options to get an API key:"
echo ""
echo "1. Check server startup logs for the default key:"
echo "   make dev 2>&1 | grep 'API Key'"
echo ""
echo "2. Create a new API key via curl:"
echo "   # First, you'll need to authenticate (if you have login credentials)"
echo "   curl -X POST ${API_URL}/auth/keys \\"
echo "     -H 'Authorization: Bearer <existing-key>'"
echo ""
echo "3. Set the API_KEY environment variable:"
echo "   export API_KEY=\"your-api-key-here\""
echo "   make test-data"
echo ""
echo "4. Pass the key directly:"
echo "   API_KEY=\"your-key\" make test-data"
echo ""
