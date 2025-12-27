I will modify the `EntityNode` and `CommunityNode` models in `vendor/graphiti/graphiti_core/nodes.py` to exclude the `name_embedding` field from serialization. This ensures that the field is removed from API responses while preserving the internal logic that relies on it for database operations and semantic search.

**Plan:**

1. **Verification Setup**: Create a temporary script `verify_serialization.py` to inspect the JSON output of `EntityNode` and `CommunityNode`.
2. **Verify Current State**: Run the script to confirm that `name_embedding` is currently present in the output.
3. **Apply Changes**: Modify `vendor/graphiti/graphiti_core/nodes.py`:

   * Update `EntityNode.name_embedding` field definition to include `exclude=True`.

   * Update `CommunityNode.name_embedding` field definition to include `exclude=True`.
4. **Verify Changes**: Run the verification script again to confirm that `name_embedding` is now absent from the output.
5. **Cleanup**: Delete the temporary verification script.

