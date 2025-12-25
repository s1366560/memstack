I will add end-to-end (E2E) tests to the project using Playwright, covering critical user flows for both the tenant console and project workbench.

### Plan

1.  **Setup Playwright Environment**:
    *   Initialize a new `e2e` directory in the project root.
    *   Install Playwright and its dependencies (if not already present, I will guide the user or add a setup script).
    *   Create a `playwright.config.ts` to configure the test runner (base URL, browser settings, timeouts).

2.  **Define Critical Test Scenarios**:
    *   **Authentication**: Login flow (success/failure).
    *   **Tenant Management**: Creating a new tenant (if applicable via UI) or selecting a tenant.
    *   **Project Management**: Creating a new project, navigating to a project.
    *   **Memory Operations**:
        *   Adding a new memory (text input).
        *   Viewing the memory list.
        *   Verifying the memory graph renders (basic check for canvas presence).
    *   **Search**: Performing a search and verifying results.

3.  **Implement Test Files**:
    *   `e2e/auth.spec.ts`: Login tests.
    *   `e2e/project.spec.ts`: Project creation and navigation.
    *   `e2e/memory.spec.ts`: Memory creation and graph visualization checks.

4.  **Integration**:
    *   Add a `test:e2e` script to the root `package.json` (or `web/package.json` if preferred) to easily run these tests.
    *   Ensure the tests can run against the local development environment (`localhost:3000`).

### Verification
*   I will run the implemented Playwright tests to ensure they pass against the current local environment.

### Note on Directory Structure
I will create the `e2e` folder at the project root level to keep it distinct from unit tests in `server/tests` or `web/src/test`.
