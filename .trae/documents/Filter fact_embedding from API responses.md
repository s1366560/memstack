I will modify `server/services/graphiti_service.py` to remove `fact_embedding` from the API response. I will strictly adhere to the user's instruction **not to modify any code in the `vendor/` directory**.

**Plan:**

1.  **Modify `get_graph_data` in `server/services/graphiti_service.py`**:
    *   Locate the loop where edges are processed (around line 1713).
    *   Before appending the edge data to `edges_list`, check if `r["edge_props"]` contains `fact_embedding`.
    *   If present, delete `fact_embedding` from `r["edge_props"]`.

2.  **Modify `get_subgraph` in `server/services/graphiti_service.py`**:
    *   Locate the loop where edges are processed (around line 1573).
    *   Inside the loop constructing `edges_list`, access `r["props"]` (which contains edge properties).
    *   Check if `fact_embedding` exists in the properties and delete it if present.

**Verification:**
This approach ensures that the large vector data is filtered out at the service layer before being returned to the API caller, satisfying the requirement without touching the vendored library code.