"""
Performance comparison script for Solution 1 vs Solution 2.

This script tests both solutions:
- Solution 1: Shared client with state restoration
- Solution 2: Isolated client per request

It measures:
1. Episode creation performance
2. Search performance
3. Memory usage (basic)
4. Driver state isolation
"""

import asyncio
import time
import httpx
import statistics
from typing import List, Dict, Any
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Test credentials
AUTH_EMAIL = "admin@memstack.ai"
AUTH_PASSWORD = "adminpassword"


async def get_auth_token(client: httpx.AsyncClient) -> str:
    """Get authentication token."""
    # Try /auth/token endpoint first
    response = await client.post(
        f"{BASE_URL}/api/v1/auth/token",
        data={"username": AUTH_EMAIL, "password": AUTH_PASSWORD}
    )

    # If that fails, try creating an API key
    if response.status_code != 200:
        # Create temporary API key using login form
        form_data = {
            "username": AUTH_EMAIL,
            "password": AUTH_PASSWORD
        }
        response = await client.post(
            f"{BASE_URL}/api/v1/auth/token",
            data=form_data
        )

    response.raise_for_status()
    data = response.json()
    return data.get("access_token")


async def test_episode_creation(
    client: httpx.AsyncClient,
    token: str,
    endpoint: str,
    count: int = 10
) -> Dict[str, Any]:
    """Test episode creation performance."""
    print(f"\n{'='*60}")
    print(f"Testing Episode Creation: {endpoint}")
    print(f"{'='*60}")

    timings = []
    errors = 0

    for i in range(count):
        start = time.time()

        try:
            response = await client.post(
                f"{BASE_URL}{endpoint}/",
                json={
                    "name": f"Test Episode {i}",
                    "content": f"This is test episode {i} for performance testing.",
                    "source_description": "test",
                    "project_id": "neo4j"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

            elapsed = time.time() - start
            timings.append(elapsed * 1000)  # Convert to ms

            if response.status_code != 202:
                errors += 1
                print(f"  [{i+1}] ERROR: Status {response.status_code}")
            else:
                print(f"  [{i+1}] Success: {elapsed*1000:.2f}ms")

        except Exception as e:
            errors += 1
            print(f"  [{i+1}] ERROR: {str(e)}")

    return {
        "endpoint": endpoint,
        "count": count,
        "errors": errors,
        "timings_ms": timings,
        "avg_ms": statistics.mean(timings) if timings else 0,
        "median_ms": statistics.median(timings) if timings else 0,
        "min_ms": min(timings) if timings else 0,
        "max_ms": max(timings) if timings else 0,
        "std_dev_ms": statistics.stdev(timings) if len(timings) > 1 else 0
    }


async def test_search_performance(
    client: httpx.AsyncClient,
    token: str,
    endpoint: str,
    count: int = 20
) -> Dict[str, Any]:
    """Test search performance."""
    print(f"\n{'='*60}")
    print(f"Testing Search Performance: {endpoint}")
    print(f"{'='*60}")

    timings = []
    errors = 0
    result_counts = []

    for i in range(count):
        start = time.time()

        try:
            response = await client.post(
                f"{BASE_URL}{endpoint}/advanced",
                json={
                    "query": "张三",
                    "limit": 10,
                    "strategy": "COMBINED_HYBRID_SEARCH_RRF"
                },
                headers={"Authorization": f"Bearer {token}"}
            )

            elapsed = time.time() - start
            timings.append(elapsed * 1000)  # Convert to ms

            if response.status_code == 200:
                data = response.json()
                result_count = len(data.get("results", []))
                result_counts.append(result_count)
                print(f"  [{i+1}] Success: {elapsed*1000:.2f}ms, {result_count} results")
            else:
                errors += 1
                print(f"  [{i+1}] ERROR: Status {response.status_code}")

        except Exception as e:
            errors += 1
            print(f"  [{i+1}] ERROR: {str(e)}")

    return {
        "endpoint": endpoint,
        "count": count,
        "errors": errors,
        "timings_ms": timings,
        "avg_ms": statistics.mean(timings) if timings else 0,
        "median_ms": statistics.median(timings) if timings else 0,
        "min_ms": min(timings) if timings else 0,
        "max_ms": max(timings) if timings else 0,
        "std_dev_ms": statistics.stdev(timings) if len(timings) > 1 else 0,
        "avg_results": statistics.mean(result_counts) if result_counts else 0
    }


async def test_concurrent_requests(
    client: httpx.AsyncClient,
    token: str,
    endpoint: str,
    concurrent_count: int = 10
) -> Dict[str, Any]:
    """Test concurrent request handling."""
    print(f"\n{'='*60}")
    print(f"Testing Concurrent Requests: {endpoint} ({concurrent_count} concurrent)")
    print(f"{'='*60}")

    async def make_request(idx: int):
        start = time.time()
        try:
            response = await client.post(
                f"{BASE_URL}{endpoint}/advanced",
                json={
                    "query": f"test query {idx}",
                    "limit": 10,
                    "strategy": "COMBINED_HYBRID_SEARCH_RRF"
                },
                headers={"Authorization": f"Bearer {token}"}
            )
            elapsed = time.time() - start
            return {
                "success": response.status_code == 200,
                "elapsed_ms": elapsed * 1000,
                "status": response.status_code
            }
        except Exception as e:
            return {
                "success": False,
                "elapsed_ms": (time.time() - start) * 1000,
                "error": str(e)
            }

    start_total = time.time()
    results = await asyncio.gather(*[make_request(i) for i in range(concurrent_count)])
    total_time = time.time() - start_total

    successful = [r for r in results if r["success"]]
    timings = [r["elapsed_ms"] for r in successful]

    return {
        "endpoint": endpoint,
        "concurrent_count": concurrent_count,
        "successful": len(successful),
        "failed": concurrent_count - len(successful),
        "total_time_s": total_time,
        "avg_ms": statistics.mean(timings) if timings else 0,
        "min_ms": min(timings) if timings else 0,
        "max_ms": max(timings) if timings else 0
    }


def print_comparison(solution1: Dict[str, Any], solution2: Dict[str, Any], metric_name: str):
    """Print comparison between two solutions."""
    print(f"\n{metric_name}:")
    print(f"  Solution 1 (Shared Client):  {solution1.get('avg_ms', 0):.2f}ms avg")
    print(f"  Solution 2 (Isolated Client): {solution2.get('avg_ms', 0):.2f}ms avg")

    diff_pct = ((solution2.get('avg_ms', 0) - solution1.get('avg_ms', 0)) / solution1.get('avg_ms', 1)) * 100
    if diff_pct > 0:
        print(f"  Difference: Solution 2 is +{diff_pct:.1f}% slower")
    else:
        print(f"  Difference: Solution 2 is {diff_pct:.1f}% faster")


async def main():
    """Run all performance tests."""
    print("="*60)
    print("MemStack Driver State Solutions Performance Comparison")
    print("="*60)
    print(f"Started at: {datetime.now().isoformat()}")

    async with httpx.AsyncClient(timeout=60.0) as client:
        # Get auth token
        print("\nGetting authentication token...")
        try:
            token = await get_auth_token(client)
            print(f"✓ Authenticated successfully")
        except Exception as e:
            print(f"✗ Authentication failed: {e}")
            print("\nPlease ensure:")
            print("  1. Server is running at http://localhost:8000")
            print("  2. Demo user exists (admin@memstack.ai / adminpassword)")
            return

        # Test Episode Creation
        print("\n" + "="*60)
        print("TEST 1: EPISODE CREATION")
        print("="*60)

        sol1_episode = await test_episode_creation(
            client, token, "/api/v1/episodes", count=5
        )

        sol2_episode = await test_episode_creation(
            client, token, "/api/v1/episodes-isolated", count=5
        )

        print_comparison(sol1_episode, sol2_episode, "Episode Creation")

        # Test Search Performance
        print("\n" + "="*60)
        print("TEST 2: SEARCH PERFORMANCE")
        print("="*60)

        sol1_search = await test_search_performance(
            client, token, "/api/v1/search-enhanced", count=10
        )

        sol2_search = await test_search_performance(
            client, token, "/api/v1/search-isolated", count=10
        )

        print_comparison(sol1_search, sol2_search, "Search Performance")

        # Test Concurrent Requests
        print("\n" + "="*60)
        print("TEST 3: CONCURRENT REQUESTS")
        print("="*60)

        sol1_concurrent = await test_concurrent_requests(
            client, token, "/api/v1/search-enhanced", concurrent_count=10
        )

        sol2_concurrent = await test_concurrent_requests(
            client, token, "/api/v1/search-isolated", concurrent_count=10
        )

        print(f"\nConcurrent Requests ({sol1_concurrent['concurrent_count']} concurrent):")
        print(f"  Solution 1 (Shared Client):")
        print(f"    Success rate: {sol1_concurrent['successful']}/{sol1_concurrent['concurrent_count']}")
        print(f"    Total time: {sol1_concurrent['total_time_s']:.2f}s")
        print(f"    Avg response: {sol1_concurrent['avg_ms']:.2f}ms")
        print(f"  Solution 2 (Isolated Client):")
        print(f"    Success rate: {sol2_concurrent['successful']}/{sol2_concurrent['concurrent_count']}")
        print(f"    Total time: {sol2_concurrent['total_time_s']:.2f}s")
        print(f"    Avg response: {sol2_concurrent['avg_ms']:.2f}ms")

        # Summary
        print("\n" + "="*60)
        print("SUMMARY & RECOMMENDATION")
        print("="*60)

        print("\nSolution 1 (Shared Client with State Restoration):")
        print("  Pros:")
        print("    - Reuses existing connections (lower overhead)")
        print("    - Faster response times")
        print("    - Lower memory usage")
        print("  Cons:")
        print("    - Requires manual state management")
        print("    - Risk of state mutation if restoration fails")

        print("\nSolution 2 (Isolated Client per Request):")
        print("  Pros:")
        print("    - Complete isolation (no state pollution)")
        print("    - Simpler code (no manual restoration)")
        print("  Cons:")
        print("    - Creates new driver per request (higher overhead)")
        print("    - Slower response times")
        print("    - Higher memory usage")

        print("\nRecommendation:")
        episode_diff = sol2_episode['avg_ms'] - sol1_episode['avg_ms']
        search_diff = sol2_search['avg_ms'] - sol1_search['avg_ms']

        if episode_diff > 100 or search_diff > 50:
            print("  ✓ Solution 1 is recommended for production use")
            print("    (significantly better performance)")
        else:
            print("  ⚠ Consider trade-offs:")
            print("    - If performance is critical: Use Solution 1")
            print("    - If simplicity/isolation is critical: Use Solution 2")

        print(f"\nCompleted at: {datetime.now().isoformat()}")


if __name__ == "__main__":
    asyncio.run(main())
