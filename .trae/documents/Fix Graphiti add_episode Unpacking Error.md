I have identified the bug in the `graphiti` vendor library included in the project. The `add_episode` method in `vendor/graphiti/graphiti_core/graphiti.py` incorrectly handles the result of `semaphore_gather` when `update_communities=True`. It attempts to unpack a list of results into two variables, which fails unless there are exactly two results (and even then, the logic is semantically incorrect).

My plan is:
1.  **Create a reproduction script** (`reproduce_bug.py`) to confirm the `ValueError: not enough values to unpack` when calling `add_episode` with `update_communities=True`.
2.  **Fix the bug** in `vendor/graphiti/graphiti_core/graphiti.py` by correctly iterating over the results of `semaphore_gather` and aggregating communities and edges, similar to how it's done in `build_communities`.
3.  **Run the reproduction script again** to verify the fix.
4.  **Perform a comprehensive check** of other `semaphore_gather` usages in the codebase to ensure no similar bugs exist.
5.  **Run existing tests** to ensure no regressions.

This will resolve the `ValueError` and ensure the Graphiti integration works correctly for adding episodes.