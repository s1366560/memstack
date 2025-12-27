I have confirmed the user's suspicion. The issue lies in `server/llm_clients/qwen_client.py`.

**Root Cause:**
The `QwenClient` implements heuristic logic to handle cases where the LLM returns a JSON Schema definition instead of the actual data.
- In `_clean_parsed_json` (lines 145-152) and `_generate_response` (lines 325-337), the code attempts to extract data from the `description` field of the returned JSON object if it looks like a schema.
- Unfortunately, the `description` field for the `summary` property in the `graphiti_core` prompt is "Summary containing the important information about the entity. Under 500 characters."
- The heuristic blindly accepts this description as the extracted value because it is longer than 10 characters, bypassing the retry logic that would otherwise correct the LLM's output.

**Solution:**
1.  **Modify `server/llm_clients/qwen_client.py`**:
    - Add a check to ignore the `description` field if it matches the specific placeholder text.
    - This will cause the extraction to fail (return empty/None), which correctly triggers the existing retry logic (lines 358+) that sends a correction prompt to the LLM ("You returned the JSON Schema definition...").

2.  **Cleanup Existing Data**:
    - Create `scripts/fix_entity_summaries.py` to update existing entities in the database that have this incorrect summary.

### Plan Details

**Step 1: Update `server/llm_clients/qwen_client.py`**
- Define `PLACEHOLDER_SUMMARY = "Summary containing the important information about the entity. Under 500 characters."`
- Update `_clean_parsed_json`:
  ```python
  if (
      "description" in value
      and isinstance(value.get("description"), str)
      and value["description"] != PLACEHOLDER_SUMMARY  # Add this check
      and ("type" in value or "title" in value or len(value) == 1)
  ):
      cleaned_data[key] = value["description"]
  ```
- Update `_generate_response` heuristic block similarly to exclude the placeholder.

**Step 2: Cleanup Script**
- Create `scripts/fix_entity_summaries.py` to run:
  ```cypher
  MATCH (n:Entity)
  WHERE n.summary = 'Summary containing the important information about the entity. Under 500 characters.'
  SET n.summary = n.name
  ```
  
This ensures the LLM client correctly identifies the schema output as invalid and retries, rather than silently saving the prompt instruction as data.