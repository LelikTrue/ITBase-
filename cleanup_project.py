#!/usr/bin/env python3
"""
Скрипт для автоматической очистки проекта от лишних файлов
"""
import os
import sys
import shutil
from pathlib import Path

def confirm_action(message):
    """Запрашивает подтверждение действия"""
    while True:
        response = input(f"{message} (y/n): ").lower().strip()
        if response in ['y', 'yes', 'да']:
            return True
        elif response in ['n', 'no', 'нет']:
            return False
        else:
            print("Пожалуйста, введите 'y' или 'n'")

def safe_remove(path, description=""):
    """Безопасно удаляет файл или папку"""
    try:
        if path.exists():
            if path.is_file():
                path.unlink()
                print(f"✅ Удален файл: {path.name} {description}")
            elif path.is_dir():
                shutil.rmtree(path)
                print(f"✅ Удалена папка: {path.name} {description}")
            return True
        else:
            print(f"⚠️  Файл не найден: {path.name}")
            return False
    except Exception as e:
        print(f"❌ Ошибка при удалении {path.name}: {e}")
        return False

def cleanup_root_directory():
    """Очистка корневой директории"""
    print("\n🧹 Очистка корневой директории...")
    
    root_path = Path("../")
    
    # Временные bat-файлы
    temp_files = [
        "temp_alembic_current.bat",
        "temp_create_migration.bat", 
        "temp_delete_migrations.bat",
        "temp_downgrade.bat",
        "temp_final_upgrade.bat",
        "temp_git_log.bat",
        "temp_migration_history.bat",
        "temp_migration_with_env.bat",
        "temp_migration.bat",
        "temp_run_app.bat",
        "temp_stamp_head.bat",
        "temp_upgrade.bat"
    ]
    
    removed_count = 0
    for file_name in temp_files:
        file_path = root_path / file_name
        if safe_remove(file_path, "(временный bat-файл)"):
            removed_count += 1
    
    # Устаревшие ск��ипты
    old_scripts = [
        "clean_db.py",
        "it_asset_db.session.sql"
    ]
    
    for file_name in old_scripts:
        file_path = root_path / file_name
        if safe_remove(file_path, "(устаревший скрипт)"):
            removed_count += 1
    
    # IDE папки (опционально)
    ide_folders = [".qodo", ".vscode"]
    for folder_name in ide_folders:
        folder_path = root_path / folder_name
        if folder_path.exists():
            if confirm_action(f"Удалить папку {folder_name} (настройки IDE)?"):
                if safe_remove(folder_path, "(папка IDE)"):
                    removed_count += 1
    
    print(f"📊 Из корневой директории удалено: {removed_count} элементов")

def cleanup_project_directory():
    """Очистка директории проекта"""
    print("\n🧹 Очистка директории проекта...")
    
    # Устаревшие документы
    old_docs = [
        "issue_summary.md",
        "update_main_instructions.txt", 
        "demo_data.sql",
        "schema.sql"
    ]
    
    removed_count = 0
    for file_name in old_docs:
        file_path = Path(file_name)
        if safe_remove(file_path, "(устаревший документ)"):
            removed_count += 1
    
    # Дублирующие файлы
    duplicate_files = [
        "requirements.txt",
        "setup.py",
        "setup.cfg"
    ]
    
    for file_name in duplicate_files:
        file_path = Path(file_name)
        if safe_remove(file_path, "(дублирующий файл)"):
            removed_count += 1
    
    # Временные файлы разработки (опционально)
    dev_files = [
        "save_state.py",
        "CURRENT_STATE.md", 
        "DEVELOPMENT_REPORT.md",
        "PROBLEM_SOLUTION.md"
    ]
    
    if confirm_action("Удалить временные файлы разработки? (можно оставить для истории)"):
        for file_name in dev_files:
            file_path = Path(file_name)
            if safe_remove(file_path, "(временный файл разработки)"):
                removed_count += 1
    
    print(f"📊 Из проекта удалено: {removed_count} элементов")

def update_gitignore():
    """Обновляет .gitignore"""
    print("\n📝 Обновление .gitignore...")
    
    gitignore_path = Path(".gitignore")
    
    # Добавляем правила для временных файлов
    new_rules = [
        "",
        "# Временные файлы разработки",
        "temp_*.bat",
        "*.session.sql",
        "clean_db.py",
        "",
        "# Документация разработки (опционально)",
        "CURRENT_STATE.md",
        "DEVELOPMENT_REPORT.md", 
        "PROBLEM_SOLUTION.md",
        "save_state.py",
        "cleanup_project.py",
        "CLEANUP_REPORT.md",
        "",
        "# IDE файлы",
        ".qodo/",
        ".vscode/",
        "*.code-workspace"
    ]
    
    try:
        # Читаем существующий .gitignore
        existing_content = ""
        if gitignore_path.exists():
            existing_content = gitignore_path.read_text(encoding='utf-8')
        
        # Проверяем, нужно ли добавлять правила
        if "# Временные файлы разработки" not in existing_content:
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write('\n'.join(new_rules))
            print("✅ .gitignore обновлен")
        else:
            print("⚠️  .gitignore уже содержит правила для временных файлов")
            
    except Exception as e:
        print(f"❌ Ошибка при обновлении .gitignore: {e}")

def show_final_structure():
    """Показывает финальную структуру проекта"""
    print("\n📁 Финальная структура проекта:")
    
    important_items = [
        "app/",
        "templates/", 
        "static/",
        "alembic/",
        "tests/",
        "requirements/",
        ".env.example",
        ".gitignore",
        "alembic.ini",
        "pyproject.toml",
        "README.md",
        "README.dev.md",
        "run_dev.py",
        "setup_dev.py", 
        "init_data.py",
        "Makefile.dev"
    ]
    
    existing_count = 0
    for item in important_items:
        item_path = Path(item)
        if item_path.exists():
            status = "✅"
            existing_count += 1
        else:
            status = "❌"
        print(f"  {status} {item}")
    
    print(f"\n📊 Важных файлов найдено: {existing_count}/{len(important_items)}")

def main():
    """Основная функция"""
    print("🧹 Автоматическая очистка проекта ITBase")
    print("=" * 50)
    
    # Проверяем, что мы в правил��ной директории
    if not Path("app").exists() or not Path("run_dev.py").exists():
        print("❌ Запустите скрипт из корневой директории проекта ITBase")
        return 1
    
    print("⚠️  ВНИМАНИЕ: Этот скрипт удалит лишние файлы из проекта!")
    print("📋 Будут удалены:")
    print("   - Временные bat-файлы")
    print("   - Устаревшие документы")
    print("   - Дублирующие файлы")
    print("   - Опционально: файлы разработки и IDE настройки")
    
    if not confirm_action("\nПродолжить очистку?"):
        print("🛑 Очистка отменена")
        return 0
    
    # Выполняем очистку
    cleanup_root_directory()
    cleanup_project_directory()
    update_gitignore()
    
    print("\n" + "=" * 50)
    print("🎉 Очистка завершена!")
    print("=" * 50)
    
    show_final_structure()
    
    print("\n💡 Рекомендации:")
    print("   1. Проверьте, что приложение запускается: python run_dev.py")
    print("   2. Сделайте коммит изменений: git add . && git commit -m 'cleanup: удалены лишние файлы'")
    print("   3. Проверьте .gitignore на предмет новых правил")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())