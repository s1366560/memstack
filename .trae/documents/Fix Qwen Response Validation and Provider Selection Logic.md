I will address the two reported issues: the Qwen LLM response validation error and the configuration issue where Gemini is used instead of Qwen.

### Plan

1.  **Fix Qwen Client Response Handling (`server/llm_clients/qwen_client.py`)**:
    *   Modify `_clean_parsed_json` to robustly handle cases where Qwen returns a schema definition (dictionary with `description` and `type`) for a string field instead of the string itself. This directly fixes the `validation error for EntitySummary` where `summary` received a dictionary.

2.  **Fix Provider Selection Logic (`server/services/graphiti_service.py` & `server/config.py`)**:
    *   **Logic Check:** Review `server/services/graphiti_service.py`. The initialization logic seems correct (`if provider.lower() == "qwen"`).
    *   **Auto-detection:** Enhance `server/config.py` (or `graphiti_service.py`) to smarter default behavior. If `LLM_PROVIDER` is not explicitly set, but `DASHSCOPE_API_KEY` is present and `GEMINI_API_KEY` is missing, default to "qwen". This aligns with the user's expectation ("using qwen llm actually calling gemini" implies they configured Qwen keys but didn't explicitly switch the provider flag, or expect it to auto-switch).
    *   **Safety:** Ensure `provider` string comparison is case-insensitive and whitespace-safe.

3.  **Verification**:
    *   The `scripts/ingest_hf_data.py` script triggered the error, so re-running it (or a smaller test) would be the verification step.

### Changes

*   **`server/llm_clients/qwen_client.py`**: Update `_clean_parsed_json` to extract values from schema-like dictionaries.
*   **`server/config.py`**: Update `llm_provider` default logic or add a validator to auto-select Qwen if Gemini key is missing.
*   **`server/services/graphiti_service.py`**: Ensure `initialize` cleans the provider string.
