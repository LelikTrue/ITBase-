import json
from fastapi.templating import Jinja2Templates
from .config import TEMPLATES_DIR
from .flash import get_flashed_messages

# Инициализация Jinja2Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def to_pretty_json(value):
    """Formats a dictionary to a pretty JSON string with non-ASCII support."""
    return json.dumps(value, ensure_ascii=False, indent=2)

# Добавляем глобальные функции и фильтры в окружение Jinja2
templates.env.globals['get_flashed_messages'] = get_flashed_messages
templates.env.filters['to_pretty_json'] = to_pretty_json