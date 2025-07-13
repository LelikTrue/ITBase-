#!/usr/bin/env python3
"""
Скрипт для сохранения текущего рабочего состояния проекта
"""
import subprocess
import sys
from datetime import datetime
from pathlib import Path

def run_command(command, check=True):
    """Выполняет команду и возвращает результат"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=check)
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.CalledProcessError as e:
        return None, e.stderr

def check_git_status():
    """Проверяет статус git репозитория"""
    stdout, stderr = run_command("git status --porcelain", check=False)
    if stderr:
        print("❌ Ошибка при проверке git статуса:", stderr)
        return False
    
    if stdout:
        print("📝 Найдены изменения для коммита:")
        print(stdout)
        return True
    else:
        print("✅ Нет изменений для коммита")
        return False

def update_current_state():
    """Обновляет файл CURRENT_STATE.md с текущей датой"""
    state_file = Path("CURRENT_STATE.md")
    if not state_file.exists():
        print("❌ Файл CURRENT_STATE.md не найден")
        return False
    
    try:
        content = state_file.read_text(encoding='utf-8')
        current_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Заменяем placeholder даты
        content = content.replace("$(date)", current_date)
        content = content.replace("**Последнее обновление**: $(date)", f"**Последнее обновление**: {current_date}")
        
        state_file.write_text(content, encoding='utf-8')
        print("✅ Файл CURRENT_STATE.md обновлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка при обновлении CURRENT_STATE.md: {e}")
        return False

def create_commit():
    """Создает git коммит с текущими изменениями"""
    # Добавляем все файлы
    stdout, stderr = run_command("git add .")
    if stderr:
        print("❌ Ошибка при добавлении файлов:", stderr)
        return False
    
    # Создаем коммит
    commit_message = f"feat: сохранение рабочего состояния проекта - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if stderr and "nothing to commit" not in stderr:
        print("❌ Ошибка при создании коммита:", stderr)
        return False
    
    print(f"✅ Коммит создан: {commit_message}")
    return True

def create_tag():
    """Создает git тег для текущего состояния"""
    tag_name = f"working-state-{datetime.now().strftime('%Y%m%d-%H%M')}"
    tag_message = "Рабочее состояние проекта с упрощенными скриптами разработки"
    
    stdout, stderr = run_command(f'git tag -a {tag_name} -m "{tag_message}"')
    if stderr:
        print("❌ Ошибка при создании тега:", stderr)
        return False
    
    print(f"✅ Тег создан: {tag_name}")
    return True

def show_summary():
    """Показывает сводку изменений"""
    print("\n" + "=" * 50)
    print("📊 СВОДКА СОХРАНЕННОГО СОСТОЯНИЯ")
    print("=" * 50)
    
    # Показываем последний коммит
    stdout, stderr = run_command("git log -1 --oneline")
    if stdout:
        print(f"📝 Последний коммит: {stdout}")
    
    # Показываем теги
    stdout, stderr = run_command("git tag --sort=-creatordate | head -3")
    if stdout:
        print("🏷️  Последние теги:")
        for tag in stdout.split('\n'):
            if tag.strip():
                print(f"   - {tag}")
    
    # Показываем статистику файлов
    stdout, stderr = run_command("find . -name '*.py' | wc -l", check=False)
    if stdout:
        print(f"📁 Python файлов: {stdout}")
    
    print("\n🎯 Что сохранено:")
    print("   ✅ Исправления импортов и подключения к БД")
    print("   ✅ Скрипты для упрощения разработки")
    print("   ✅ Документация для разработчиков")
    print("   ✅ Makefile с полезными командами")
    print("   ✅ Текущее рабочее состояние")

def main():
    """Основная функция"""
    print("💾 Сохранение рабочего состояния проекта ITBase")
    print("=" * 50)
    
    # Проверяем, что мы в git репозитории
    stdout, stderr = run_command("git rev-parse --git-dir", check=False)
    if stderr:
        print("❌ Не найден git репозиторий. Инициализируйте git:")
        print("   git init")
        print("   git remote add origin <URL>")
        return 1
    
    # Обновляем файл состояния
    if not update_current_state():
        return 1
    
    # Проверяем статус
    if not check_git_status():
        print("ℹ️  Нет изменений для сохранения")
        return 0
    
    # Создаем коммит
    if not create_commit():
        return 1
    
    # Создаем тег
    if "--tag" in sys.argv:
        create_tag()
    
    # Показываем сводку
    show_summary()
    
    print("\n🎉 Состояние проекта успешно сохранено!")
    print("\n💡 Следующие шаги:")
    print("   - git push origin main  # Отправить изменения на сервер")
    print("   - git push --tags       # Отправить теги")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())