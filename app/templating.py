import json
from datetime import datetime
from fastapi.templating import Jinja2Templates
from .config import TEMPLATES_DIR
from .flash import get_flashed_messages

# Инициализация Jinja2Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

def to_pretty_json(value):
    """Formats a dictionary to a pretty JSON string with non-ASCII support."""
    return json.dumps(value, ensure_ascii=False, indent=2)

def format_diff(value):
    """Форматирует diff для отображения в шаблоне."""
    if not value or not isinstance(value, dict) or 'diff' not in value:
        return to_pretty_json(value)
    
    diff = value.get('diff', {})
    if not diff:
        return to_pretty_json(value)
    
    result = []
    result.append("<table class='table table-sm table-bordered diff-table'>")
    result.append("<thead><tr><th>Поле</th><th>Старое значение</th><th>Новое значение</th></tr></thead>")
    result.append("<tbody>")
    
    # Сортируем поля для более логичного отображения
    sorted_fields = sorted(diff.keys())
    
    for field in sorted_fields:
        changes = diff[field]
        old_val = changes.get('old', '')
        new_val = changes.get('new', '')
        
        # Форматируем значения для отображения
        if old_val is None:
            old_val = '<em>пусто</em>'
        if new_val is None:
            new_val = '<em>пусто</em>'
        
        # Форматируем даты для лучшего отображения
        if field in ["Дата покупки", "Дата окончания гарантии"] and old_val and not old_val == '<em>пусто</em>':
            try:
                date_obj = datetime.fromisoformat(old_val)
                old_val = date_obj.strftime("%d.%m.%Y")
            except (ValueError, TypeError):
                pass
                
        if field in ["Дата покупки", "Дата окончания гарантии"] and new_val and not new_val == '<em>пусто</em>':
            try:
                date_obj = datetime.fromisoformat(new_val)
                new_val = date_obj.strftime("%d.%m.%Y")
            except (ValueError, TypeError):
                pass
        
        # Форматируем цену для лучшего отображения
        if field == "Цена":
            if old_val and old_val != '<em>пусто</em>':
                try:
                    old_val = f"{float(old_val):,.2f} ₽".replace(",", " ").replace(".", ",")
                except (ValueError, TypeError):
                    pass
            if new_val and new_val != '<em>пусто</em>':
                try:
                    new_val = f"{float(new_val):,.2f} ₽".replace(",", " ").replace(".", ",")
                except (ValueError, TypeError):
                    pass
            
        result.append(f"<tr>")
        result.append(f"<td><strong>{field}</strong></td>")
        result.append(f"<td class='bg-light'>{old_val}</td>")
        result.append(f"<td class='bg-success bg-opacity-25'>{new_val}</td>")
        result.append(f"</tr>")
    
    result.append("</tbody></table>")
    return "".join(result)

# Добавляем глобальные функции и фильтры в окружение Jinja2
templates.env.globals['get_flashed_messages'] = get_flashed_messages
templates.env.filters['to_pretty_json'] = to_pretty_json
templates.env.filters['format_diff'] = format_diff