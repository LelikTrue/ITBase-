# Структура проекта ITBase

> Этот файл сгенерирован автоматически. Не редактируйте его вручную.

```text
ITBase-/
├── .editorconfig
├── .env
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── 01_initial_database_seeding.md
├── ADMIN_USAGE_GUIDE.md
├── AI_CONTEXT.md
├── CONTRIBUTING.md
├── Dockerfile
├── Dockerfile.prod
├── Dockerfile.test
├── LICENSE
├── Makefile
├── PROBLEM_SOLUTION.md
├── PROJECT_STRUCTURE.md
├── README.dev.md
├── README.md
├── alembic.ini
├── create_admin.py
├── docker-compose.dev.yml
├── docker-compose.override.yml
├── docker-compose.prod.yml
├── docker-compose.test.yml
├── docker-compose.yml
├── init_data.py
├── openapi-assets.yaml
├── pyproject.toml
├── requirements.txt
├── run_dev.py
├── seed_assets.py
├── seed_devices.py
├── setup.cfg
├── setup.py
├── setup.sh
├── test_db_connection.py
├── test_pretty_errors.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── flash.py
│   ├── form_helpers.html
│   ├── logging_config.py
│   ├── main.py
│   ├── templating.py
│   ├── test_main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── analytics.py
│   │   │   ├── assets.py
│   │   │   ├── audit_logs.py
│   │   │   ├── auth.py
│   │   │   ├── dictionaries.py
│   │   │   ├── health.py
│   │   │   ├── tags.py
│   │   │   ├── users.py
│   │   │   ├── web_auth.py
│   ├── core/
│   │   ├── security.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── initial_data_storage.py
│   │   ├── repositories/
│   │   │   ├── analytics_repo.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── action_log.py
│   │   ├── asset_type.py
│   │   ├── attachment.py
│   │   ├── base.py
│   │   ├── department.py
│   │   ├── device.py
│   │   ├── device_model.py
│   │   ├── device_status.py
│   │   ├── employee.py
│   │   ├── location.py
│   │   ├── manufacturer.py
│   │   ├── network.py
│   │   ├── supplier.py
│   │   ├── tag.py
│   │   ├── user.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── analytics.py
│   │   ├── asset.py
│   │   ├── audit_log.py
│   │   ├── dictionary.py
│   │   ├── supplier.py
│   │   ├── tag.py
│   │   ├── user.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── asset_type_service.py
│   │   ├── audit_log_service.py
│   │   ├── base_service.py
│   │   ├── department_service.py
│   │   ├── device_model_service.py
│   │   ├── device_service.py
│   │   ├── device_status_service.py
│   │   ├── dictionary_service.py
│   │   ├── employee_service.py
│   │   ├── exceptions.py
│   │   ├── location_service.py
│   │   ├── manufacturer_service.py
│   │   ├── supplier_service.py
│   │   ├── tag_service.py
│   │   ├── mixins/
│   │   │   ├── __init__.py
│   │   │   ├── dependency_check_mixin.py
│   │   │   ├── duplicate_check_mixin.py
│   ├── templates/
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py
├── docs/
│   ├── 01_initial_database_seeding.md
├── initdb/
│   ├── 01-init.sh
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   ├── prod.txt
├── static/
│   ├── styles.css
│   ├── css/
│   │   ├── dashboard.css
│   │   ├── dictionary_modals.css
│   │   ├── styles.css
│   │   ├── vendor/
│   │   │   ├── tom-select.bootstrap5.css
│   ├── js/
│   │   ├── dashboard.js
│   │   ├── dictionary_modals.js
│   │   ├── tom-select-init.js
│   │   ├── vendor/
│   │   │   ├── chart.js
│   │   │   ├── chart.umd.min.js
│   │   │   ├── tom-select.complete.min.js
│   ├── test_data/
│   │   ├── device_fixture.json
├── templates/
│   ├── add_asset.html
│   ├── assets_list.html
│   ├── audit_logs.html
│   ├── base.html
│   ├── dashboard.html
│   ├── edit_asset.html
│   ├── error.html
│   ├── login.html
│   ├── pagination.html
│   ├── register.html
│   ├── admin/
│   │   ├── asset_types.html
│   │   ├── departments.html
│   │   ├── device_models.html
│   │   ├── device_statuses.html
│   │   ├── dictionaries_dashboard.html
│   │   ├── employees.html
│   │   ├── locations.html
│   │   ├── manufacturers.html
│   │   ├── suppliers.html
│   │   ├── tags.html
│   │   ├── users.html
│   ├── includes/
│   │   ├── flash_messages.html
│   │   ├── form_helpers.html
│   ├── modals/
│   │   ├── dictionary_modals.html
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_assets.py
│   ├── test_auth.py
│   ├── test_health.py
│   ├── test_simple.py
│   ├── test_web_auth.py
```

# 📊 Quick Stats (AI Context)

- **Total DB Models:** 14
  - List: department, device, user, attachment, network, device_status, asset_type, location, supplier, manufacturer, device_model, action_log, tag, employee
- **Total Services:** 13
- **Total API Modules:** 10