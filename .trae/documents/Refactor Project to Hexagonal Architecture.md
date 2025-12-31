I have analyzed the project structure and the architectural rules in `AGENTS.md` and `domain_driven_design_hexagonal_arhictecture_python_rules.md`. The current codebase is a monolithic FastAPI application (`server/`) that needs to be refactored into a **Hexagonal Architecture**.

Refactoring the entire project at once is risky and complex. I propose a **phased approach**, starting with the core **Memory Domain** (Episodes, Entities, Graphiti integration) as a pilot to establish the patterns.

### Refactoring Plan

#### Phase 1: Foundation & Structure
1.  **Create Directory Structure**: Set up the `src/` hierarchy:
    *   `src/domain/` (Entities, Value Objects, Ports)
    *   `src/application/` (Use Cases, Primary Ports)
    *   `src/infrastructure/` (Adapters, DB, External APIs)
    *   `src/configuration/` (DI Container, Settings)
2.  **Define Shared Kernel**: Implement base classes for `Entity`, `ValueObject`, `DomainEvent` in `src/domain/shared_kernel.py`.

#### Phase 2: Domain Modeling (Memory Module)
1.  **Extract Entities**: Move logic from `server/models` and `GraphitiService` to rich Domain Entities:
    *   `src/domain/model/memory/episode.py`
    *   `src/domain/model/memory/entity.py`
    *   `src/domain/model/memory/community.py`
2.  **Define Ports**: Create interface definitions (ABCs) in `src/domain/ports/`:
    *   `MemoryRepository` (for CRUD operations)
    *   `GraphServicePort` (for graph traversals and search)

#### Phase 3: Application Layer (Use Cases)
1.  **Implement Use Cases**: Move business logic from `server/api/` and `GraphitiService` to Use Cases:
    *   `CreateMemoryUseCase` (Orchestrates storage + graph ingestion)
    *   `SearchMemoryUseCase` (Handles hybrid search logic)
    *   `GetGraphDataUseCase` (Handles graph visualization data)

#### Phase 4: Infrastructure Layer (Adapters)
1.  **Implement Secondary Adapters**:
    *   `GraphitiAdapter`: Refactor `GraphitiService` into a proper adapter implementing `GraphServicePort`.
    *   `SqlAlchemyMemoryRepository`: Implement SQL persistence.
2.  **Implement Primary Adapters**:
    *   Create new FastAPI routers in `src/infrastructure/adapters/primary/web/` that depend on Use Cases, not Services.

#### Phase 5: Configuration & Wiring
1.  **Dependency Injection**: Create `src/configuration/container.py` to wire Adapters to Use Cases.
2.  **Entry Point**: Update `main.py` to use the new application structure.

### Immediate Next Step
I will start with **Phase 1 and Phase 2**, creating the directory structure and defining the `Memory` domain models and ports. This will provide a solid foundation for the rest of the refactoring.
