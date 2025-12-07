# AI Context: ITBase Project

## 1. Project Identity
**Name:** ITBase
**Purpose:** IT Asset Management System (Inventory, Lifecycle, Audit).
**Language:** Russian (Русский) - for all docs, comments, and UI.

## 2. Tech Stack (Strict)
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Database:** PostgreSQL 15+
- **ORM:** SQLAlchemy 2.0 (Async) + Alembic (Migrations)
- **Validation:** Pydantic
- **Frontend:** Server-Side Rendering (SSR) with Jinja2 + Bootstrap 5 (Vanilla CSS/JS, no React/Vue).
- **Infrastructure:** Docker Compose, Makefile.

## 3. Architecture & Patterns
**Principle:** "Thin Routers, Thick Services" (Тонкие роутеры, толстые сервисы).

### Layers
1.  **`app/api/endpoints/` (Routers):**
    *   **Responsibility:** Handle HTTP requests, parse params, call Services, return HTML/JSON.
    *   **Rule:** NO business logic here. Only control flow.
2.  **`app/services/` (Business Logic):**
    *   **Responsibility:** All calculations, DB operations, complex validations.
    *   **Rule:** "Reuse before create". Check existing services first.
3.  **`app/models/` (DB Models):**
    *   **Responsibility:** SQLAlchemy ORM definitions.
    *   **Rule:** Changes here require `make migration`.
4.  **`app/schemas/` (DTOs):**
    *   **Responsibility:** Pydantic models for API input/output validation.
5.  **`templates/` (UI):**
    *   **Responsibility:** Jinja2 HTML templates.

## 4. Key Entities & Relationships
- **`Device` (Asset):** The core entity.
    - FKs: `model_id` (DeviceModel), `employee_id` (Employee), `location_id` (Location), `status_id` (DeviceStatus).
    - **Logic:** Tracks lifecycle of hardware.
- **`Employee`:** Person who holds assets.
    - Fields: `last_name`, `first_name`, `patronymic` (Unique constraint on combination).
- **`ActionLog` (Audit):**
    - **Logic:** Automatically records changes to sensitive entities.
    - **Rule:** Never delete logs (except maybe Superuser).
- **`Component` (Polymorphic):**
    - Subtypes: `CPU`, `RAM`, `Storage`, `GPU`, `Motherboard`.
    - **Logic:** Tracks hardware parts linked to Device.
- **Dictionaries:**
    - `DeviceModel` (linked to `Manufacturer`, `AssetType`).
    - `Manufacturer`, `AssetType`, `DeviceStatus`, `Department`, `Location`.

## 5. Development Rules & Protocols

### 5.1. Anti-Duplication Protocol (STRICT)
1.  **Reuse First:** Before writing ANY new function or class, you MUST search the codebase (`grep`, file search) for similar logic.
2.  **No Ghost Files:** Do NOT create new files unless architecture explicitly requires it. Ask: "Does a file with this responsibility already exist?"
3.  **Extension over Creation:** If an existing function does 90% of what is needed, refactor/extend it. Do not create `function_v2`.
4.  **Justification:** If you create a new file, you must explicitly state WHY existing files (`app/utils`, `app/services`) are insufficient.

### 5.2. Git Protocol (Passive Mode)
- **Timing:** Do NOT propose commit messages immediately. Wait for confirmation ("Prepare commit").
- **Format:** Use Conventional Commits in Russian: `type(scope): description`.
    - Types: `feat`, `fix`, `refactor`, `style`, `docs`, `chore`.
- **Linting:** Code MUST be compliant with `flake8` and `ruff`.

### 5.3. Workflow Rules
1.  **Language:** ALWAYS answer in Russian.
2.  **Testing:** Do NOT run tests automatically. User runs `make test`.
3.  **Migrations:** If you modify `app/models/`, remind user to run `make migration`.
4.  **Analysis:** Check `app/services/` for business logic. Do NOT put logic in `endpoints`.

## 6. Key Commands (`Makefile`)
- `make dev`: Start dev server (hot reload).
- `make migrate`: Apply DB migrations.
- `make migration`: Create new migration (after model changes).
- `make lint-fix`: Fix code style (Ruff).
- `make test`: Run tests.
- `make logs-clear`: Clear Docker logs.

## 7. Project Structure Map
```text
/app
  /api/endpoints  # Routes (Web & API)
  /core           # Security, Config
  /db             # DB Setup
  /models         # SQLAlchemy Models
  /schemas        # Pydantic Schemas
  /services       # Business Logic (CRUD, complex ops)
  /utils          # Helpers
  main.py         # App Entry Point
/templates        # Jinja2 HTML
/agent_builder    # Windows Inventory Agent (Isolated Build)
/migrations       # Alembic versions
Makefile          # Task runner
docker-compose.yml
```

## 8. AI Maintenance Rules
**CRITICAL:** If you (the AI) modify the project structure, add new entities, or change the tech stack, you **MUST** update this file (`AI_CONTEXT.md`) immediately to reflect the changes. This file must always remain the Single Source of Truth.
