# app/db/initial_data_storage.py
"""Хранилище начальных данных для заполнения базы."""

ASSET_TYPES = [
    {"name": "Компьютер", "prefix": "PC", "description": "Настольные и портативные компьютеры"},
    {"name": "Монитор", "prefix": "MON", "description": "Мониторы и дисплеи"},
    {"name": "Принтер", "prefix": "PRN", "description": "Принтеры и МФУ"},
    {"name": "Сетевое оборудование", "prefix": "NETW", "description": "Роутеры, коммутаторы, точки доступа"},
    {"name": "Сервер", "prefix": "SERV", "description": "Серверное оборудование"},
    {"name": "Мобильное устройство", "prefix": "MOB", "description": "Телефоны, планшеты"},
    {"name": "Периферия", "prefix": "PERI", "description": "Клавиатуры, мыши, веб-камеры"},
    {"name": "Аудио/Видео", "prefix": "AV", "description": "Колонки, наушники, проекторы"},
]

MANUFACTURERS = [
    {"name": "Dell", "description": "Dell Technologies"},
    {"name": "HP", "description": "Hewlett-Packard"},
    {"name": "Lenovo", "description": "Lenovo Group"},
    {"name": "ASUS", "description": "ASUSTeK Computer"},
    {"name": "Acer", "description": "Acer Inc."},
    {"name": "Apple", "description": "Apple Inc."},
    {"name": "Samsung", "description": "Samsung Electronics"},
    {"name": "LG", "description": "LG Electronics"},
    {"name": "Canon", "description": "Canon Inc."},
    {"name": "Epson", "description": "Seiko Epson"},
    {"name": "Cisco", "description": "Cisco Systems"},
    {"name": "D-Link", "description": "D-Link Corporation"},
    {"name": "TP-Link", "description": "TP-Link Technologies"},
    {"name": "Logitech", "description": "Logitech International"},
    {"name": "Microsoft", "description": "Microsoft Corporation"},
]

STATUSES = [
    {"name": "В эксплуатации", "description": "Устройство активно используется"},
    {"name": "В резерве", "description": "Устройство готово к использованию"},
    {"name": "На ремонте", "description": "Устройство находится в ремонте"},
    {"name": "Списан", "description": "Устройство списано"},
    {"name": "На складе", "description": "Устройство на складе"},
    {"name": "Утерян", "description": "Устройство было утеряно"},
    {"name": "Украден", "description": "Устройство было украдено"},
]

DEPARTMENTS = [
    {"name": "ИТ отдел", "description": "Отдел информационных технологий"},
    {"name": "Бухгалтерия", "description": "Бухгалтерский отдел"},
    {"name": "Отдел кадров", "description": "Управление персоналом"},
    {"name": "Отдел продаж", "description": "Отдел по работе с клиентами"},
    {"name": "Отдел маркетинга", "description": "Отдел маркетинга и рекламы"},
    {"name": "Администрация", "description": "Руководящий состав"},
    {"name": "Производственный отдел", "description": "Основное производство"},
    {"name": "Служба безопасности", "description": "Обеспечение безопасности"},
    {"name": "Отдел логистики", "description": "Управление поставками и складом"},
    {"name": "Юридический отдел", "description": "Правовое сопровождение"},
]

LOCATIONS = [
    {"name": "Офис 1 этаж", "description": "Первый этаж главного офиса"},
    {"name": "Офис 2 этаж", "description": "Второй этаж главного офиса"},
    {"name": "Серверная", "description": "Серверная комната"},
    {"name": "Склад", "description": "Основной склад"},
    {"name": "Удаленная работа", "description": "Сотрудник работает удаленно"},
    {"name": "Переговорная 1", "description": "Основная переговорная комната"},
    {"name": "Зона отдыха", "description": "Кухня и зона отдыха"},
    {"name": "Архив", "description": "Помещение для хранения документов"},
]

EMPLOYEES = [
    {"first_name": "Иван", "last_name": "Иванов", "patronymic": "Иванович", "employee_id": "EMP001"},
    {"first_name": "Петр", "last_name": "Петров", "patronymic": "Петрович", "employee_id": "EMP002"},
    {"first_name": "Анна", "last_name": "Сидорова", "patronymic": "Сергеевна", "employee_id": "EMP003"},
    {"first_name": "Елена", "last_name": "Кузнецова", "patronymic": "Олеговна", "employee_id": "EMP004"},
    {"first_name": "Дмитрий", "last_name": "Васильев", "patronymic": "Игоревич", "employee_id": "EMP005"},
]

def get_device_models(manufacturers_map: dict, asset_types_map: dict) -> list[dict]:
    """Возвращает список моделей устройств, используя ID из переданных словарей."""
    return [
        {"name": "OptiPlex 7090", "manufacturer_id": manufacturers_map.get("Dell"), "asset_type_id": asset_types_map.get("Компьютер")},
        {"name": "ThinkPad T14", "manufacturer_id": manufacturers_map.get("Lenovo"), "asset_type_id": asset_types_map.get("Компьютер")},
        {"name": "EliteBook 850", "manufacturer_id": manufacturers_map.get("HP"), "asset_type_id": asset_types_map.get("Компьютер")},
        {"name": "UltraSharp U2419H", "manufacturer_id": manufacturers_map.get("Dell"), "asset_type_id": asset_types_map.get("Монитор")},
        {"name": "LaserJet Pro M404n", "manufacturer_id": manufacturers_map.get("HP"), "asset_type_id": asset_types_map.get("Принтер")},
    ]