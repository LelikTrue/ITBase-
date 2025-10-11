from datetime import date, datetime


def safe_int(value: str | None) -> int | None:
    """Безопасно преобразует значение в int, возвращает None, если преобразование невозможно."""
    try:
        return int(value) if value is not None and value.strip() != '' else None
    except (ValueError, TypeError):
        return None

def safe_float(value: str | None) -> float | None:
    """Безопасно преобразует значение в float, возвращает None, если преобразование невозможно."""
    try:
        # Заменяем запятую на точку для корректного преобразования в float
        if value is not None and isinstance(value, str):
            value = value.replace(',', '.')
        return float(value) if value is not None and str(value).strip() != '' else None
    except (ValueError, TypeError):
        return None

def safe_date(value: str | None) -> date | None:
    """Безопасно преобразует строку в объект date, возвращает None, если преобразование невозможно."""
    if value is None or value.strip() == '':
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        return None
