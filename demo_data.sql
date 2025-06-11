-- Отключаем проверку внешних ключей для возможности вставки в любом порядке
SET session_replication_role = 'replica';

-- Очистка таблиц (осторожно, удалит все существующие данные!)
TRUNCATE TABLE "Attachment", "Device", "ActionLog", "DeviceModel", "Employee", 
"Department", "Location", "Manufacturer", "AssetType", "DeviceStatus" 
RESTART IDENTITY CASCADE;

-- Включаем проверку внешних ключей
SET session_replication_role = 'origin';

-- Заполнение типов активов
INSERT INTO "AssetType" ("name", "description") VALUES
('Ноутбук', 'Переносные компьютеры'),
('Монитор', 'Мониторы и дисплеи'),
('Принтер', 'Принтеры и МФУ'),
('Сканер', 'Сканеры документов'),
('Телефон', 'Стационарные телефоны'),
('Смартфон', 'Мобильные телефоны');

-- Заполнение статусов устройств
INSERT INTO "DeviceStatus" ("name", "description") VALUES
('В эксплуатации', 'Устройство активно используется'),
('На складе', 'Устройство находится на складе'),
('В ремонте', 'Устройство находится в ремонте'),
('Списано', 'Устройство списано с баланса'),
('Резерв', 'Устройство в резерве');

-- Заполнение отделов
INSERT INTO "Department" ("name", "description") VALUES
('IT-отдел', 'Отдел информационных технологий'),
('Бухгалтерия', 'Бухгалтерский отдел'),
('Отдел кадров', 'Отдел по работе с персоналом'),
('Отдел продаж', 'Коммерческий отдел'),
('Склад', 'Складское хозяйство'),
('Администрация', 'Руководство компании');

-- Заполнение местоположений
INSERT INTO "Location" ("name", "description") VALUES
('Главный офис', 'Центральный офис, ул. Центральная, 1'),
('Склад №1', 'Основной склад на ул. Складская, 10'),
('Филиал Северный', 'Филиал в северном районе'),
('Удаленные сотрудники', 'Удаленные рабочие места');

-- Заполнение производителей
INSERT INTO "Manufacturer" ("name", "description") VALUES
('Dell', 'Dell Technologies Inc.'),
('HP', 'Hewlett-Packard'),
('Lenovo', 'Lenovo Group Ltd.'),
('Asus', 'ASUSTeK Computer Inc.'),
('Acer', 'Acer Inc.'),
('Xiaomi', 'Xiaomi Corporation'),
('Samsung', 'Samsung Electronics'),
('Apple', 'Apple Inc.');

-- Заполнение сотрудников
INSERT INTO "Employee" ("first_name", "last_name", "patronymic", "employee_id", "email", "phone_number") VALUES
('Иван', 'Иванов', 'Иванович', 'EMP001', E'i.ivanov@example.com', '+79001234567'),
('Петр', 'Петров', 'Петрович', 'EMP002', E'p.petrov@example.com', '+79007654321'),
('Сергей', 'Сергеев', 'Сергеевич', 'EMP003', E's.sergeev@example.com', '+79009876543'),
('Анна', 'Сидорова', 'Алексеевна', 'EMP004', E'a.sidorova@example.com', '+79005554433'),
('Мария', 'Кузнецова', 'Сергеевна', 'EMP005', E'm.kuznetsova@example.com', '+79001112233'),
('Алексей', 'Смирнов', 'Дмитриевич', 'EMP006', E'a.smirnov@example.com', '+79002223344');

-- Заполнение моделей устройств
INSERT INTO "DeviceModel" ("name", "manufacturer_id", "asset_type_id", "description") VALUES
('Latitude 5520', 1, 1, 'Бизнес-ноутбук 15.6\" FHD, Intel Core i5-1145G7, 16GB, 512GB SSD'),
('EliteBook 840 G8', 2, 1, 'Ультрабук 14\" FHD, Intel Core i7-1165G7, 16GB, 1TB SSD'),
('ThinkPad X1 Carbon', 3, 1, 'Ультрабук 14\" WQHD, Intel Core i7-1185G7, 32GB, 1TB SSD'),
('UltraSharp U2720Q', 1, 2, 'Монитор 27\" 4K UHD, IPS, HDR, USB-C'),
('LaserJet Pro MFP M428fdw', 2, 3, 'Лазерное МФУ A4, Wi-Fi, Ethernet, двусторонняя печать'),
('PIXMA TS8340', 4, 3, 'Струйный принтер A4, Wi-Fi, двусторонняя печать, сканер');

-- Заполнение устройств
INSERT INTO "Device" (
    "inventory_number", "serial_number", "mac_address", "ip_address", "notes",
    "source", "purchase_date", "warranty_end_date", "price", "expected_lifespan_years",
    "current_wear_percentage", "device_model_id", "asset_type_id", "status_id",
    "department_id", "location_id", "employee_id", "added_at"
) VALUES
('INV-001', 'SN12345678', '00:1A:2B:3C:4D:5E', '192.168.1.10', 'Основной рабочий ноутбук',
 'purchase', '2022-01-15', '2025-01-15', 120000.00, 4, 15.5, 1, 1, 1, 1, 1, 1, NOW()),

('INV-002', 'SN23456789', '00:1B:2C:3D:4E:5F', '192.168.1.11', 'Для бухгалтерии',
 'purchase', '2022-02-20', '2025-02-20', 150000.00, 4, 10.0, 2, 1, 1, 2, 1, 2, NOW()),

('INV-003', 'SN34567890', '00:1C:2D:3E:4F:60', '192.168.1.12', 'Руководство',
 'purchase', '2022-03-10', '2025-03-10', 180000.00, 4, 5.0, 3, 1, 1, 6, 1, 3, NOW()),

('INV-004', 'SN45678901', NULL, NULL, 'Основной монитор',
 'purchase', '2022-01-20', '2025-01-20', 45000.00, 5, 8.0, 4, 2, 1, 1, 1, 1, NOW()),

('INV-005', 'SN56789012', '00:1D:2E:3F:40:61', '192.168.1.20', 'Офисный принтер',
 'purchase', '2021-12-15', '2024-12-15', 35000.00, 5, 25.0, 5, 3, 1, 1, 1, NULL, NOW()),

('INV-006', 'SN67890123', NULL, NULL, 'Резервный монитор',
 'purchase', '2022-02-01', '2025-02-01', 42000.00, 5, 2.0, 4, 2, 2, NULL, 2, NULL, NOW());

-- Обновляем временные метки на текущее время
UPDATE "AssetType" SET "created_at" = NOW(), "updated_at" = NOW();
UPDATE "DeviceStatus" SET "created_at" = NOW(), "updated_at" = NOW();
UPDATE "Department" SET "created_at" = NOW(), "updated_at" = NOW();
UPDATE "Location" SET "created_at" = NOW(), "updated_at" = NOW();
UPDATE "Manufacturer" SET "created_at" = NOW(), "updated_at" = NOW();
UPDATE "Employee" SET "created_at" = NOW(), "updated_at" = NOW();
UPDATE "DeviceModel" SET "created_at" = NOW(), "updated_at" = NOW();
UPDATE "Device" SET "updated_at" = NOW() WHERE "updated_at" IS NULL;
UPDATE "Attachment" SET "created_at" = NOW(), "uploaded_at" = NOW(), "updated_at" = NOW();
UPDATE "ActionLog" SET "created_at" = NOW(), "updated_at" = NOW(), "timestamp" = NOW();