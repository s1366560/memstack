I will refactor the project's concurrency and threading model to improve performance, scalability, and stability.

The current implementation creates a dedicated worker task for *each* active group (user/project). While simple, this approach has significant drawbacks for high-performance scenarios:
1.  **Unbounded Concurrency**: If 1,000 groups are active, 1,000 concurrent processing tasks are spawned, potentially hitting LLM rate limits (429 errors) or exhausting database connections.
2.  **Resource Contention**: Lack of a global limit means the server can be easily overwhelmed by a burst of traffic.
3.  **Inefficient Scheduling**: Groups with many tasks can starve others if not managed correctly (though the current sequential model is fair per-group, it doesn't balance global load).

### Proposed Solution: Worker Pool with Round-Robin Scheduling

I will refactor `QueueService` to use a **Producer-Consumer Worker Pool** pattern.

#### 1. Architecture Changes
*   **Global Worker Pool**: Instead of one worker per group, we will maintain a fixed pool of generic worker tasks (e.g., configurable `MAX_ASYNC_WORKERS`, default 50).
*   **Fair Scheduling**: Implement a **Round-Robin Scheduler**.
    *   Maintain a queue of "Active Groups" (groups that have pending items).
    *   Workers pick a group from the Active Queue, process **one batch** of items (or a single item), and then return the group to the back of the queue if it still has work.
    *   This ensures that a single group with 1,000 items doesn't block other groups from getting processed.
*   **Concurrency Control**: The fixed number of workers acts as a global semaphore, protecting your LLM providers and Database from overload.

#### 2. Implementation Details

**A. `server/config.py`**
*   Add `MAX_ASYNC_WORKERS` configuration (default: 20-50).
*   Add `QUEUE_BATCH_SIZE` configuration (default: 1) to allow batch processing optimization in the future.

**B. `server/services/queue_service.py`**
*   **Remove**: The `_queue_workers` dictionary and per-group `_process_episode_queue` loops.
*   **Add**:
    *   `self._active_groups`: An `asyncio.Queue` storing `group_id`s that have pending work.
    *   `self._workers`: A list of global worker tasks started at initialization.
*   **Logic**:
    *   `add_episode_task`: Pushes task to the group's specific queue. If the group was not already in `_active_groups`, add it there.
    *   `_worker_loop`:
        1.  Pull `group_id` from `_active_groups`.
        2.  Process an item from `_episode_queues[group_id]`.
        3.  If the group queue is not empty, put `group_id` back into `_active_groups`.
        4.  Else, mark group as idle.

#### 3. Benefits
*   **High Performance**: Maximizes throughput up to the safe limit of your infrastructure.
*   **Stability**: Prevents crashes and rate-limit errors during traffic spikes.
*   **Scalability**: Logic is decoupled from the number of users/groups.

I will implement these changes in `server/services/queue_service.py` and `server/config.py`.