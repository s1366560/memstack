Migrate essential backend functionality (Auth, Tenants, Projects) from `server/` to `src/` to support frontend E2E tests, and enable code coverage tracking.

## 1. Backend Migration (Refactoring to Hexagonal Architecture)
We will port the missing logic from `server/` to `src/` without direct imports, adhering to the "no reference to old code" rule.

- **Schemas (DTOs)**:
    - Create `src/application/schemas/` directory.
    - Port Pydantic models from `server/models/{auth,tenant,project,enums}.py` to `src/application/schemas/`.
    - Create `src/domain/model/enums.py` for shared enumerations.
- **Persistence Layer**:
    - Update `src/infrastructure/adapters/secondary/persistence/models.py` to include full SQLAlchemy models (`User`, `Tenant`, `Project`, `APIKey`, etc.) from `server/db_models.py`.
- **Application Services**:
    - Create `src/application/services/auth_service.py` to house authentication logic (password hashing, JWT generation) ported from `server/auth.py`.
- **Web Adapters (Routers)**:
    - Create `src/infrastructure/adapters/primary/web/routers/` directory.
    - Port API logic from `server/api/{auth,tenants,projects}.py` to new routers in `src/infrastructure/adapters/primary/web/routers/`.
    - Update `src/infrastructure/adapters/primary/web/main.py` to register these new routers.

## 2. Frontend Coverage Setup
- **Action**: Install `vite-plugin-istanbul` in `web/`.
- **Action**: Configure `web/vite.config.ts` to use the plugin for code instrumentation.
- **Action**: Update `web/playwright.config.ts` to collect coverage data.

## 3. Execution & Verification
- **Action**: Start the new `src` backend (which will now have Auth/Tenant/Project support).
- **Action**: Run the existing E2E tests (`web/e2e/`) against the new backend.
- **Goal**: Verify tests pass and generate a coverage report > 80%.
