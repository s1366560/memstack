#!/usr/bin/env python3
"""Test SSE connection like a browser EventSource would."""

import requests
import json
import sys
import time

def test_sse_like_browser(task_id: str):
    """Simulate browser EventSource connection."""
    url = f"http://localhost:8000/api/v1/tasks/{task_id}/stream"
    print(f"📡 Connecting to SSE: {url}")
    print("=" * 70)

    try:
        with requests.get(url, stream=True, timeout=30) as response:
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}: {response.text}")
                return

            print(f"✅ Connected (HTTP {response.status_code})")
            print(f"   Content-Type: {response.headers.get('content-type')}")
            print("=" * 70)

            # Read SSE events line by line
            current_event = None
            current_data = None

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    # Empty line marks end of an event
                    if current_event and current_data:
                        print(f"\n📨 Event: {current_event}")
                        print(f"📦 Data: {current_data}")

                        # Parse and validate JSON
                        try:
                            data = json.loads(current_data)
                            if 'status' in data:
                                print(f"   ✓ Status: {data['status']}")
                            if 'progress' in data:
                                print(f"   ✓ Progress: {data['progress']}%")
                            if 'message' in data:
                                print(f"   ✓ Message: {data['message']}")
                        except json.JSONDecodeError as e:
                            print(f"   ⚠️  Invalid JSON: {e}")

                    current_event = None
                    current_data = None
                    continue

                # Parse SSE format
                if line.startswith('event:'):
                    current_event = line.replace('event:', '').strip()
                elif line.startswith('data:'):
                    current_data = line.replace('data:', '').strip()

    except requests.exceptions.Timeout:
        print("⏱️  Connection timed out (30s)")
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_eventsource.py <task_id>")
        print("\nThis simulates how a browser EventSource would connect to the SSE endpoint.")
        sys.exit(1)

    test_sse_like_browser(sys.argv[1])
