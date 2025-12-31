#!/usr/bin/env python3
"""Detailed SSE test to see all events."""

import requests
import json
import sys

def test_sse(task_id: str):
    url = f"http://localhost:8000/api/v1/tasks/{task_id}/stream"

    print(f"Testing SSE for task: {task_id}")
    print("=" * 60)

    with requests.get(url, stream=True, timeout=10) as response:
        print(f"HTTP Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type')}")
        print("=" * 60)

        for line in response.iter_lines():
            if line:
                decoded = line.decode('utf-8')
                print(decoded)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_sse_detailed.py <task_id>")
        sys.exit(1)

    test_sse(sys.argv[1])
