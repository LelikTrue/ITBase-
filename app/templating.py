import json
from fastapi.templating import Jinja2Templates
from markupsafe import Markup

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
    """Formats a 'diff' dictionary into an HTML table for better readability."""
    if not isinstance(details, dict) or 'diff' not in details:
        return to_pretty_json(details)

    diff_data = details['diff']
    rows = []
    for field, changes in diff_data.items():
        old_val = changes.get('old', '<em>N/A</em>')
        new_val = changes.get('new', '<em>N/A</em>')
        rows.append(f"""
        <tr>
            <td><strong>{field}</strong></td>
            <td class="bg-light text-muted">{old_val or '<em>пусто</em>'}</td>
            <td class="bg-success bg-opacity-25">{new_val or '<em>пусто</em>'}</td>
        </tr>
        """)
    
    table_html = f"""
    <table class="table table-bordered table-sm diff-table">
        <thead class="table-light">
            <tr>
                <th>Поле</th>
                <th>Старое значение</th>
                <th>Новое значение</th>
            </tr>
        </thead>
        <tbody>
            {''.join(rows)}
        </tbody>
    </table>
    """
    return Markup(table_html)

def format_create_data(details):
    """Formats data for a 'create' action into a simple HTML list."""
    if not isinstance(details, dict):
        return to_pretty_json(details)
    
    items = []
    for key, value in details.items():
        items.append(f'<li><strong>{key}:</strong> {value}</li>')
    
    return Markup(f'<ul class="list-unstyled mb-0">{"".join(items)}</ul>')

# Register the custom filters with the Jinja2 environment
templates.env.filters['to_pretty_json'] = to_pretty_json
templates.env.filters['format_diff'] = format_diff
templates.env.filters['format_create_data'] = format_create_data