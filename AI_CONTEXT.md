# ITBase: AI Developer Context

## 1. Architecture Overview
- **Type:** Monolith with Clean Architecture principles.
- **Stack:** FastAPI (Async), SQLAlchemy 2.0, Alembic, Pydantic, Docker.
- **Frontend:** Server-Side Rendering (Jinja2 + Bootstrap).

## 2. Key Directories Logic
- `app/services/`: **BUSINESS LOGIC ONLY.** No HTTP dependencies here.
- `app/api/endpoints/`: **ROUTING ONLY.** Thin layer. Calls services.
- `app/models/`: SQLAlchemy ORM models.
- `app/schemas/`: Pydantic schemas (Validation).
- `alembic/versions/`: DB Migrations.

## 3. Critical Rules (DO NOT IGNORE)
1.  **Dictionary Logic:** We have a hybrid system.
    - `DictionaryService` (generic).
    - Specific services (e.g., `ManufacturerService`).
    - *Warning:* Check for redundancy before adding new dictionary logic.
2.  **DeviceService:** This is a large service. Be careful when refactoring.
3.  **Migrations:** If you change `app/models/`, you MUST run `make migration`.
4.  **Structure:** Do not guess file paths. Check `PROJECT_STRUCTURE.md`.

## 4. Automation Tools
- `python generate_structure.py`: Updates the file tree.
- `make test`:Executes pytest only when requested by the user.
