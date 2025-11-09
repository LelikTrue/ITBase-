# Структура проекта ITBase

```text
ITBase-/
├── .editorconfig
├── .env
├── .env.example
├── .gitignore
├── .pre-commit-config.yaml
├── 01_initial_database_seeding.md
├── ADMIN_USAGE_GUIDE.md
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
│   │   ├── 20250925_f54c7505ea53_add_indexes_to_action_log_table.py
│   │   ├── 20250926_88b1196ca226_add_supplier_relationship_to_device_.py
│   │   ├── 20251011_413e5e7e7c66_feat_consolidate_all_pending_model_.py
│   │   ├── 20251012_7a9c8d6b5e4f_add_category_field_to_tags.py
│   │   ├── 20251019_8fc178ad1a1b_добавим_description_to_tags.py
│   │   ├── 20251025_4a21be86bcbc_add_name_column_to_devices_table.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── flash.py
│   ├── form_helpers.html
│   ├── main.py
│   ├── templating.py
│   ├── test_main.py
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
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── asset.py
│   │   ├── audit_log.py
│   │   ├── dictionary.py
│   │   ├── supplier.py
│   │   ├── tag.py
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
│   ├── test_data/
│   │   ├── device_fixture.json
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
├── templates/
│   ├── add_asset.html
│   ├── assets_list.html
│   ├── audit_logs.html
│   ├── base.html
│   ├── dashboard.html
│   ├── edit_asset.html
│   ├── error.html
│   ├── pagination.html
│   ├── includes/
│   │   ├── flash_messages.html
│   │   ├── form_helpers.html
│   ├── modals/
│   │   ├── dictionary_modals.html
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
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_assets.py
│   ├── test_health.py
│   ├── test_simple.py
```
