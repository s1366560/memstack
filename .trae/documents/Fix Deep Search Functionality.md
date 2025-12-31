I will fix the Deep Search functionality in `src/infrastructure/adapters/primary/web/routers/enhanced_search.py` by restoring missing logic found in the original implementation.

### Changes:
1.  **Restore Node Distance Reranking**: Pass the `focal_node_uuid` parameter (as `center_node_uuid`) to the `graphiti_client.search_` call. This enables the "Deep Search" capability to rerank results based on graph proximity to a focal node.
2.  **Fix Date Filtering**: Implement `SearchFilters` construction to correctly handle the `since` parameter, which is currently parsed but ignored.
3.  **Import Dependencies**: Add necessary imports from `graphiti_core.search.search_filters`.

### Implementation Details:
-   Import `SearchFilters`, `DateFilter`, `ComparisonOperator` from `graphiti_core.search.search_filters`.
-   In `search_advanced`:
    -   Construct `search_filter` if `since` is provided.
    -   Update `graphiti_client.search_` call to include `center_node_uuid=focal_node_uuid` and `search_filter=search_filter`.

This aligns the current implementation with the original "Deep Search" logic from the `main` branch.