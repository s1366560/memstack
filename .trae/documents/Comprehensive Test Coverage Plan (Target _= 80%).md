I have analyzed the current project structure and test coverage. To achieve >= 80% coverage, I propose the following plan to add unit and integration tests for both Backend and Frontend.

### **1. Backend (Python/FastAPI) -** **`server/`**

**Goal:** Cover new API endpoints, services, and LLM clients.

* **New Unit/API Tests:**

  * `tests/test_api_episodes.py`: Cover `api/episodes.py` and `api/episodes_list.py`.

  * `tests/test_api_memos.py`: Cover `api/memos.py`.

  * `tests/test_api_recall.py`: Cover `api/recall.py`.

  * `tests/test_llm_clients.py`: Unit tests for `llm_clients/` (Qwen clients) using mocks to avoid real API calls.

* **Enhance Existing Tests:**

  * Update `tests/test_service.py` to cover edge cases in `graphiti_service.py` (mocking the graph database).

  * Ensure `conftest.py` supports async database fixtures for these new tests.

### **2. Frontend (React/Vitest) -** **`web/`**

**Goal:** Cover new Layouts, Pages, and Components introduced recently.

* **New Component Tests:**

  * `web/src/test/components/WorkspaceSwitcher.test.tsx`: Test tenant/project switching logic.

  * `web/src/test/layouts/TenantLayout.test.tsx`: Test sidebar toggling and navigation.

  * `web/src/test/layouts/ProjectLayout.test.tsx`: Test project-specific navigation.

* **New Page Tests:**

  * `web/src/test/pages/tenant/TenantOverview.test.tsx`

  * `web/src/test/pages/tenant/ProjectList.test.tsx`

  * `web/src/test/pages/project/MemoryList.test.tsx`

  * `web/src/test/pages/project/NewMemory.test.tsx`

* **Configuration:**

  * Verify `web/vitest.config.ts` includes the new source directories in coverage reports.

### **Execution Strategy**

1. **Backend:** Implement missing API test files first, then Service/LLM unit tests.
2. **Frontend:** Implement Layout and Component tests first, then Page tests.
3. **Verification:** Run test suites to verify pass rate and check coverage reports.

