# D:/LOCALPYHTON/PROGECTITBASE/ITBase-/generate_structure.py

import os
from pathlib import Path

# --- НАСТРОЙКИ ---
# Папки, которые нужно полностью игнорировать
IGNORED_DIRS = {
    "venv",
    "__pycache__",
    ".git",
    ".idea",
    ".vscode",
    ".pytest_cache",
    "site",  # для mkdocs
    "dist",
    "build",
    "__MACOSX__",
    "itbase.egg-info",
}

# Файлы, которые нужно игнорировать
IGNORED_FILES = {
    ".DS_Store",
    "project_structure.txt", # Игнорируем старый файл
    "generate_structure.py",  # Игнорируем сам скрипт
    ".coverage",
    "coverage.xml",
}

# Расширения файлов, которые нужно игнорировать
IGNORED_EXTENSIONS = {
    ".pyc",
    ".log",
    ".swp"
}

# Файл, в который будет сохранен результат
OUTPUT_FILE = "PROJECT_STRUCTURE.md"
# --- КОНЕЦ НАСТРОЕК ---


def generate_tree(root_dir: Path):
    """
    Генерирует строки для дерева каталогов, пропуская ненужные файлы/папки.
    """
    tree_lines = []
    
    # os.walk - это генератор, который рекурсивно обходит дерево каталогов
    for dirpath_str, dirnames, filenames in os.walk(root_dir):
        dirpath = Path(dirpath_str)

        # --- Фильтрация папок ---
        # Это самый важный трюк: мы изменяем список dirnames "на лету".
        # os.walk использует этот измененный список для дальнейшего обхода.
        # Если мы удалим папку из dirnames, os.walk в нее просто не пойдет.
        dirnames[:] = [d for d in dirnames if d not in IGNORED_DIRS]

        # Не обрабатываем саму корневую папку, начинаем с ее содержимого
        if dirpath == root_dir:
            # Но сортируем папки и файлы для консистентного вывода
            dirnames.sort()
            filenames.sort()
        
        # Определяем уровень вложенности для отрисовки отступов
        # relative_to() вычисляет относительный путь
        level = len(dirpath.relative_to(root_dir).parts)
        
        # --- Отрисовка папок ---
        if level > 0:
            indent = "│   " * (level - 1) + "├── "
            tree_lines.append(f"{indent}{dirpath.name}/")

        # --- Фильтрация и отрисовка файлов ---
        sub_indent = "│   " * level + "├── "
        
        # Фильтруем файлы по имени и расширению
        valid_files = sorted([
            f for f in filenames 
            if f not in IGNORED_FILES and Path(f).suffix not in IGNORED_EXTENSIONS
        ])

        for f in valid_files:
            tree_lines.append(f"{sub_indent}{f}")
            
    return tree_lines


if __name__ == "__main__":
    # Начинаем с текущей директории, где лежит скрипт
    start_path = Path(".")
    
    print(f"[*] Сканирую структуру проекта, начиная с '{start_path.resolve()}'...")
    
    try:
        tree_output = generate_tree(start_path)
        
        # Собираем финальный markdown файл
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("# Структура проекта ITBase\n\n")
            f.write("```text\n")
            f.write(f"{start_path.resolve().name}/\n") # Печатаем имя корневой папки
            for line in tree_output:
                f.write(line + "\n")
            f.write("```\n")
            
        print(f"[+] Структура проекта успешно сохранена в файл: {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"[!] Произошла ошибка: {e}")