#!/usr/bin/env python3
"""
Test script to verify SSE endpoint is working.
Run this while a community rebuild task is running.
"""

import requests
import sys
import time

def test_sse_stream(task_id: str):
    """Test the SSE streaming endpoint."""
    url = f"http://localhost:8000/api/v1/tasks/{task_id}/stream"

    print(f"📡 Connecting to SSE stream: {url}")
    print("-" * 60)

    try:
        with requests.get(url, stream=True, timeout=300) as response:
            if response.status_code != 200:
                print(f"❌ Failed to connect: HTTP {response.status_code}")
                print(response.text)
                return

            print("✅ Connected to SSE stream")
            print("-" * 60)

            # Read SSE events
            for line in response.iter_lines():
                if line:
                    line_str = line.decode('utf-8')

                    # Parse SSE format
                    if line_str.startswith('event:'):
                        event_type = line_str.replace('event:', '').strip()
                        print(f"\n📨 Event: {event_type}")
                    elif line_str.startswith('data:'):
                        data_str = line_str.replace('data:', '').strip()
                        print(f"📦 Data: {data_str}")

                        # Parse JSON for pretty printing
                        try:
                            import json
                            data = json.loads(data_str)
                            if 'progress' in data:
                                print(f"   Progress: {data['progress']}%")
                            if 'message' in data:
                                print(f"   Message: {data['message']}")
                            if 'status' in data:
                                print(f"   Status: {data['status']}")
                        except:
                            pass

                    # Check for terminal states
                    if 'completed' in line_str.lower():
                        print("\n✅ Task completed!")
                        break
                    elif 'failed' in line_str.lower():
                        print("\n❌ Task failed!")
                        break

    except requests.exceptions.Timeout:
        print("⏱️ Request timed out (5 minutes)")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_sse.py <task_id>")
        print("\nTo get a task_id, first trigger a community rebuild:")
        print("  curl 'http://localhost:8000/api/v1/communities/rebuild?background=true'")
        sys.exit(1)

    task_id = sys.argv[1]
    test_sse_stream(task_id)
