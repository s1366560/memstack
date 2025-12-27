I will modify `server/services/graphiti_service.py` to explicitly remove the `name_embedding` field from the graph data response. This is necessary because the current implementation directly unpacks Neo4j node properties into the response dictionary, bypassing the Pydantic model filtering I implemented earlier.

**Plan:**

1.  **Modify `get_graph_data`**:
    *   In `server/services/graphiti_service.py`, locate the `get_graph_data` method.
    *   Before constructing the node data dictionary, create a copy of `source_props` and `target_props` and remove the `name_embedding` key if it exists.
2.  **Modify `get_subgraph`**:
    *   In `server/services/graphiti_service.py`, locate the `get_subgraph` method.
    *   Similarly, remove `name_embedding` from `n["props"]` before using it to construct the node data.

**Verification:**
Since I cannot query the running server directly to verify the API output (as it requires a specific database state), I will rely on code analysis and the fact that explicitly popping the key from the dictionary guarantees its removal. The user's issue is clearly caused by `**r["source_props"]` including all raw properties from the database.

**Refinement:**
I will create a helper function or simply use `.pop("name_embedding", None)` inline to handle this cleanly. I will also check if there are other large fields to exclude, but `name_embedding` is the primary concern raised.