# Структура проекта ITBase

```text
ITBase-/
├── .coverage
├── .editorconfig
├── .env
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── ADMIN_USAGE_GUIDE.md
├── CONTRIBUTING.md
├── Dockerfile
├── Dockerfile.prod
├── Dockerfile.test
├── GEMINI.md
├── LICENSE
├── Makefile
├── Makefile.dev
├── PROBLEM_SOLUTION.md
├── PROJECT_STRUCTURE.md
├── README.dev.md
├── README.md
├── alembic.ini
├── coverage.xml
├── docker-compose.ci.yml
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
├── setup.cfg
├── setup.py
├── setup.sh
├── test_db_connection.py
├── test_pretty_errors.py
├── .github/
│   ├── workflows/
│   │   ├── ci.yml
├── .windsurf/
│   ├── rules/
│   │   ├── rules-agent.md
├── alembic/
│   ├── README
│   ├── env.py
│   ├── script.py.mako
│   ├── versions/
│   │   ├── 20250918_01a80f183d11_update_employee_model_with_detailed_.py
│   │   ├── 20250918_09e830d715e0_add_relationship_between_devicemodel_.py
│   │   ├── 20250918_34859191a603_add_description_and_relationship_to_.py
│   │   ├── 20250918_4631d721d198_refactor_models_to_sqlalchemy_2_0_style.py
│   │   ├── 20250918_6eaecc82f376_update_employee_model_with_detailed_.py
│   │   ├── 20250918_ae316e4eff6d_add_employees_relationship_to_department.py
│   │   ├── 20250918_bc78fd1429a7_add_description_to_assettype.py
│   │   ├── 20250918_c64ca42f0f7a_add_description_to_assettype.py
│   │   ├── 20250918_e4500be6f749_add_foreign_key_from_devicemodel_to_.py
│   │   ├── 20250918_f029a47844f1_systemic_refactoring_of_all_models.py
│   │   ├── 20250921_228b8e1b2221_add_tag_model_and_many_to_many_.py
│   │   ├── 20250921_96fd1a49c9fb_add_prefix_column_to_asset_types.py
│   │   ├── 20250922_f621c06f6b7b_add_suppliers_table.py
│   │   ├── 20250923_09b093ccb03c_add_unique_constraint_to_device_statuses.py
│   │   ├── 20250923_35b42474934b_create_departmentservice_and_add_unique_.py
│   │   ├── 20250923_9abbc70e6178_add_unique_constraint_to_locations.py
│   │   ├── 20250923_ef2aae8cb837_create_manufacturerservice_and_add_.py
│   │   ├── 20250923_f405d01a666c_add_unique_constraint_to_device_models.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── flash.py
│   ├── form_helpers.html
│   ├── main.py
│   ├── templating.py
│   ├── test_main.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── endpoints/
│   │   │   ├── __init__.py
│   │   │   ├── admin.py
│   │   │   ├── assets.py
│   │   │   ├── audit_logs.py
│   │   │   ├── dictionaries.py
│   │   │   ├── health.py
│   │   │   ├── tags.py
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py
│   │   ├── initial_data_storage.py
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
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── asset.py
│   │   ├── audit_log.py
│   │   ├── dictionary.py
│   │   ├── tag.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── asset_type_service.py
│   │   ├── audit_log_service.py
│   │   ├── base_dictionary_service.py
│   │   ├── department_service.py
│   │   ├── device_model_service.py
│   │   ├── device_service.py
│   │   ├── device_status_service.py
│   │   ├── dictionary_service.py
│   │   ├── employee_service.py
│   │   ├── exceptions.py
│   │   ├── location_service.py
│   │   ├── manufacturer_service.py
│   │   ├── tag_service.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── helpers.py
├── initdb/
│   ├── 01-init.sh
├── itbase.egg-info/
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   ├── requires.txt
│   ├── top_level.txt
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   ├── prod.txt
├── static/
│   ├── styles.css
│   ├── css/
│   │   ├── dictionary_modals.css
│   │   ├── styles.css
│   │   ├── vendor/
│   │   │   ├── tom-select.bootstrap5.css
│   ├── js/
│   │   ├── dictionary_modals.js
│   │   ├── tom-select-init.js
│   │   ├── vendor/
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
│   ├── pagination.html
│   ├── admin/
│   │   ├── asset_types.html
│   │   ├── departments.html
│   │   ├── device_models.html
│   │   ├── device_statuses.html
│   │   ├── dictionaries_dashboard.html
│   │   ├── locations.html
│   │   ├── manufacturers.html
│   ├── includes/
│   │   ├── form_helpers.html
│   ├── modals/
│   │   ├── dictionary_modals.html
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_assets.py
│   ├── test_health.py
│   ├── test_simple.py
```
