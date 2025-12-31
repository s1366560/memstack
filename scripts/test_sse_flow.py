#!/usr/bin/env python3
"""Monitor SSE events in real-time to see the full event flow."""

import requests
import json
import sys
import time
from datetime import datetime

def monitor_sse_events(task_id: str):
    """Monitor SSE events and print them with timestamps."""
    url = f"http://localhost:8000/api/v1/tasks/{task_id}/stream"

    print(f"📡 Monitoring SSE stream for task: {task_id}")
    print(f"   URL: {url}")
    print("=" * 80)
    print(f"{'Time':<20} {'Event Type':<15} {'Status':<12} {'Progress':<10} {'Message'}")
    print("=" * 80)

    try:
        with requests.get(url, stream=True, timeout=300) as response:
            if response.status_code != 200:
                print(f"❌ HTTP {response.status_code}")
                return

            current_event = None
            current_data = None
            event_count = 0

            for line in response.iter_lines(decode_unicode=True):
                if not line:
                    # End of event
                    if current_event and current_data:
                        event_count += 1
                        try:
                            data = json.loads(current_data)
                            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                            status = data.get('status', 'N/A')
                            progress = data.get('progress', 0)
                            message = data.get('message', '')[:30]

                            print(f"{timestamp:<20} {current_event:<15} {status:<12} {progress:<10} {message}")

                            # If completed, we're done
                            if current_event in ['completed', 'failed', 'error']:
                                print("=" * 80)
                                print(f"✅ Stream closed after {event_count} events")
                                print(f"   Final status: {status}")
                                if 'result' in data:
                                    print(f"   Result: {data['result']}")
                                break

                        except json.JSONDecodeError as e:
                            print(f"⚠️  Failed to parse JSON: {e}")

                    current_event = None
                    current_data = None
                    continue

                if line.startswith('event:'):
                    current_event = line.replace('event:', '').strip()
                elif line.startswith('data:'):
                    current_data = line.replace('data:', '').strip()

    except requests.exceptions.Timeout:
        print("⏱️  Connection timed out (5 minutes)")
    except KeyboardInterrupt:
        print("\n⚠️  Interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_sse_flow.py <task_id>")
        print("\nThis will show you the complete sequence of SSE events with timestamps.")
        sys.exit(1)

    monitor_sse_events(sys.argv[1])
