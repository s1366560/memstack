I will fix the `KeyError: 'label'` in `server/services/graphiti_service.py` by correcting the key used to access the edge type.

**Analysis:**
The previous search confirmed that the `r` dictionary (representing an edge) is constructed in the Cypher query with the key `"type"`, not `"label"`. My previous edit inadvertently changed `r["type"]` to `r["label"]` when refactoring the code to remove `fact_embedding`.

**Plan:**
1.  **Modify `server/services/graphiti_service.py`**:
    *   In the `get_subgraph` method, locate the line ` "label": r["label"],`.
    *   Change it back to `"label": r["type"],`.

**Verification:**
The Cypher query explicitly constructs the map with `type: type(r)`. Therefore, accessing it via `r["type"]` is correct. The error log `Failed to get subgraph: 'label'` confirms that `r["label"]` is invalid.