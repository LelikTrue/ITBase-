import os
from pathlib import Path

# Базовый каталог приложения
BASE_DIR = Path(__file__).resolve().parent

# Путь к директории с шаблонами
TEMPLATES_DIR = os.path.join(BASE_DIR.parent, "templates")
