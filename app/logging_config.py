# app/logging_config.py

import logging


class EndpointFilter(logging.Filter):
    """
    Фильтр для исключения логов доступа к определенным эндпоинтам.
    """

    def __init__(self, path: str):
        super().__init__()
        self._path = path

    def filter(self, record: logging.LogRecord) -> bool:
        # Проверяем, что сообщение лога не содержит указанный путь
        return record.getMessage().find(self._path) == -1