I will replace `print` statements with the `logging` framework in the backend files. The project already has a logging configuration in `server/logging_config.py`.

Here is the plan:

1.  **Modify `server/auth.py`**:
    *   Import `get_logger` from `server.logging_config`.
    *   Initialize `logger`.
    *   Replace `print` statements in `verify_password`, `create_user`, and `initialize_default_credentials` with appropriate `logger.debug`, `logger.info`, or `logger.error` calls.

2.  **Modify `server/api/auth.py`**:
    *   Use the existing `logger` instance.
    *   Replace debug `print` statements with `logger.debug`.
    *   **Security Note**: I will ensure passwords are NOT logged, even in debug mode, or are masked.

3.  **Modify `server/api/memories.py`**:
    *   Import `get_logger` from `server.logging_config`.
    *   Initialize `logger`.
    *   Replace the `print` statement in the exception handler (Graphiti integration) with `logger.error`.

4.  **Modify `server/debug_utils.py`**:
    *   Update `pretty_print_json` to use `logger.debug` instead of `print` to ensure all output goes through the configured logging system.

This will standardize output handling, support different log levels, and ensure logs are properly formatted and potentially captured by file handlers or other sinks configured in the future.