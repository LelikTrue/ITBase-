import json
from fastapi.templating import Jinja2Templates
from markupsafe import Markup, escape

templates = Jinja2Templates(directory="templates")

def to_pretty_json(value):
    """Converts a dict to a pretty-printed HTML <pre><code> block."""
    if not isinstance(value, dict):
        return value
    
    formatted_json = json.dumps(
        value, 
        indent=4, 
        ensure_ascii=False,
        sort_keys=True
    )
    # Wrap in <pre><code> for proper display and to allow for styling/highlighting
    html = f'<pre><code class="language-json">{formatted_json}</code></pre>'
    return Markup(html)

def format_diff(details):
    """
    Форматирует данные в HTML-таблицу для лучшей читаемости.
    Поддерживает как старый формат (плоский словарь), так и новый формат с 'diff'.
    """
    # Если details не словарь, выводим ошибку
    if not isinstance(details, dict):
        return Markup('<div class="text-warning p-2"><em>Некорректный формат данных: ожидался словарь</em></div>')
    
    # Проверяем, есть ли вложенный 'diff'
    if 'diff' in details and isinstance(details['diff'], dict):
        diff_data = details['diff']
    else:
        # Если 'diff' нет, используем сам details как diff_data
        diff_data = details
    
    # Если diff_data пуст, выводим сообщение
    if not diff_data:
        return Markup('<div class="text-muted p-2"><em>Нет данных для отображения</em></div>')

    # Случай 4: Собираем таблицу из данных.
    rows = []
    for field, changes in diff_data.items():
        # Убеждаемся, что 'changes' - это словарь, чтобы избежать ошибок
        if isinstance(changes, dict):
            old_val = changes.get('old')
            new_val = changes.get('new')
        else:
            old_val, new_val = ('<em>Ошибка данных</em>', '<em>Ошибка данных</em>')

        # Безопасно отображаем значения, обрабатывая None и пустые строки
        old_display = escape(old_val) if old_val is not None else '<em>пусто</em>'
        new_display = escape(new_val) if new_val is not None else '<em>пусто</em>'

        rows.append(f"""
        <tr>
            <td><strong>{escape(field)}</strong></td>
            <td class="bg-light text-muted">{old_display}</td>
            <td class="bg-success bg-opacity-25">{new_display}</td>
        </tr>
        """)
    
    table_html = f"""
    <table class="table table-bordered table-sm diff-table">
        <thead class="table-light">
            <tr>
                <th style="width: 25%;">Поле</th>
                <th style="width: 37.5%;">Старое значение</th>
                <th style="width: 37.5%;">Новое значение</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """
    return Markup(table_html)

def format_create_data(details):
    """Форматирует данные для действия 'create' в виде простого HTML-списка."""
    if not isinstance(details, dict):
        return Markup('<div class="text-warning p-2"><em>Некорректный формат данных для события создания.</em></div>')
    
    if not details:
        return Markup('<div class="text-muted p-2"><em>Нет данных для отображения.</em></div>')

    items = []
    for key, value in details.items():
        display_value = escape(value) if value is not None else '<em>не задано</em>'
        items.append(f'<li><strong>{escape(key)}:</strong> {display_value}</li>')
    
    return Markup(f'<ul class="list-unstyled mb-0">{"".join(items)}</ul>')

# Register the custom filters with the Jinja2 environment
templates.env.filters['to_pretty_json'] = to_pretty_json
templates.env.filters['format_diff'] = format_diff
templates.env.filters['format_create_data'] = format_create_data