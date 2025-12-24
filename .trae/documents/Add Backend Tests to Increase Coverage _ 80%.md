I will add comprehensive tests for the new Graphiti-integrated UI components and the Theme system to ensure code coverage exceeds 80%.

### 1. Create New Test Files

I will create the following test files to cover the new features:

#### Theme System

* **`web/src/test/stores/theme.test.ts`**: Test theme state transitions and persistence.

* **`web/src/test/components/ThemeToggle.test.tsx`**: Test theme toggle button interactions.

#### Graphiti Integration Pages

* **`web/src/test/pages/project/EntitiesList.test.tsx`**:

  * Mock `graphitiService.listEntities`.

  * Test rendering of entity cards/list.

  * Test filtering interactions.

* **`web/src/test/pages/project/CommunitiesList.test.tsx`**:

  * Mock `graphitiService.listCommunities`.

  * Test community card rendering.

  * Test "Rebuild" button interaction.

* **`web/src/test/pages/project/EnhancedSearch.test.tsx`**:

  * Test switching between search modes (Semantic, Graph, Temporal, Faceted).

  * Test search input and submission.

  * Mock `graphitiService.search*` methods.

* **`web/src/test/pages/project/Maintenance.test.tsx`**:

  * Test rendering of graph stats.

  * Test interaction with maintenance actions (Refresh, Deduplicate, etc.).

* **`web/src/test/pages/project/MemoryGraph.test.tsx`**:

  * Test graph container rendering.

  * Test node interaction (if feasible with mocks).

#### Search Pages

* **`web/src/test/pages/project/SearchPage.test.tsx`**: Test standard project search.

* **`web/src/test/pages/Search.test.tsx`**: Test global search UI.

### 2. Update Existing Tests & Fix Warnings

* **`web/src/test/pages/SpaceDashboard.test.tsx`**: Fix `act(...)` warnings.

* **`web/src/test/layouts/TenantLayout.test.tsx`**: Verify ThemeToggle integration.

### 3. Verification

* Run `make web-test` to ensure all tests pass.

* Run `make web-test-coverage` to verify > 80% coverage.

