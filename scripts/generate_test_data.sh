#!/bin/bash
# Convenience script to generate test data for MemStack
#
# Usage:
#   ./scripts/generate_test_data.sh [options]
#
# Examples:
#   # Generate 50 random episodes
#   ./scripts/generate_test_data.sh
#
#   # Generate 100 random episodes
#   ./scripts/generate_test_data.sh --count 100
#
#   # Generate user activity series
#   ./scripts/generate_test_data.sh --mode user-series --user-name "Alice Johnson" --days 14
#
#   # Generate project collaboration data
#   ./scripts/generate_test_data.sh --mode collaboration --project-name "Alpha Research" --days 30

set -e

# Default values
API_URL="${API_URL:-http://localhost:8000/api/v1}"
API_KEY="${API_KEY:-}"
COUNT="${COUNT:-50}"
MODE="${MODE:-random}"

# Change to script directory
cd "$(dirname "$0")/.."

# Run the Python script
python scripts/generate_test_data.py \
    --api-url "$API_URL" \
    ${API_KEY:+--api-key "$API_KEY"} \
    --count "$COUNT" \
    --mode "$MODE" \
    "$@"
