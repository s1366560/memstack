Restoring the development environment and fixing E2E tests to achieve the >80% coverage goal.

## 1. Restore Environment (Fix Connection Refused)
The "Connection Refused" error occurs because the development servers were stopped.
- **Action**: Start the `src` backend server on port 8000.
- **Action**: Start the frontend dev server on port 3000.

## 2. Fix E2E Test Failures
Several tests (`memory.spec.ts`, `entities.spec.ts`, `search.spec.ts`) failed with timeouts waiting for the "Add Memory" button.
- **Diagnosis**: The tests assume the "Add Memory" button is immediately visible after creating a project, but it might require navigation to the "Memories" tab or the selector might be incorrect.
- **Action**: Verify the "Add Memory" button location in `MemoryList.tsx` and ensure the test navigates to the correct view (e.g., clicking the "Memories" tab) before attempting to click it.
- **Action**: Update `web/e2e/memory.spec.ts` and other affected tests to correctly navigate the UI.

## 3. Improve Code Coverage (>80%)
Current coverage is ~20% because most tests failed.
- **Action**: Once tests are fixed and passing, re-run coverage analysis.
- **Action**: If coverage is still below 80%, add targeted tests for:
    - **Edge Cases**: Invalid inputs, network errors.
    - **Missing Flows**: Tenant management, detailed graph interactions, user profile updates.

## 4. Verification
- **Action**: Run the full E2E suite (`npx playwright test`).
- **Action**: Generate and verify the coverage report.
