#!/bin/bash
# Quick test script to verify Alembic integration

cd /Users/tiejunsun/github/mem/memstack || exit 1

echo "Testing Alembic Integration..."
echo "================================"

# Run the test
PYTHONPATH=. uv run python scripts/test_alembic.py

echo ""
echo "If you see '✅ Alembic integration is working!' above, everything is set up correctly."
echo ""
echo "Next: Start the application with 'make dev' and check for migration logs."
