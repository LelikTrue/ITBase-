/**
 * Функции для работы с модальными окнами справочников
 */

// Загрузка данных справочников при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    // Загружаем данные для всех справочников
    loadDictionaryData();
    
    // Инициализируем обработчики событий для модальных окон
    initModalHandlers();
});

/**
 * Загрузка данных для всех справочников
 */
function loadDictionaryData() {
    // Загружаем типы активов
    fetchDictionaryData('/api/dictionaries/asset-types', function(data) {
        populateSelect('asset_type_id', data);
        populateSelect('deviceModelAssetType', data);
    });
    
    // Загружаем модели устройств
    fetchDictionaryData('/api/dictionaries/device-models', function(data) {
        populateSelect('device_model_id', data);
    });
    
    // Загружаем статусы устройств
    fetchDictionaryData('/api/dictionaries/device-statuses', function(data) {
        populateSelect('status_id', data);
    });
    
    // Загружаем производителей
    fetchDictionaryData('/api/dictionaries/manufacturers', function(data) {
        populateSelect('deviceModelManufacturer', data);
    });
    
    // Загружаем отделы
    fetchDictionaryData('/api/dictionaries/departments', function(data) {
        populateSelect('department_id', data);
    });
    
    // Загружаем местоположения
    fetchDictionaryData('/api/dictionaries/locations', function(data) {
        populateSelect('location_id', data);
    });
    
    // Загружаем сотрудников
    fetchDictionaryData('/api/dictionaries/employees', function(data) {
        populateEmployeeSelect('employee_id', data);
    });
}

/**
 * Получение данных справочника с сервера
 * @param {string} url - URL API для получения данных
 * @param {function} callback - Функция обратного вызова для обработки полученных данных
 */
function fetchDictionaryData(url, callback) {
    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ошибка при получении данных: ' + response.statusText);
            }
            return response.json();
        })
        .then(data => {
            callback(data);
        })
        .catch(error => {
            console.error('Ошибка при загрузке данных:', error);
        });
}

/**
 * Заполнение выпадающего списка данными
 * @param {string} selectId - ID элемента select
 * @param {Array} data - Массив объектов для заполнения списка
 */
function populateSelect(selectId, data) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    // Сохраняем текущее выбранное значение
    const currentValue = select.value;
    
    // Получаем первый элемент (обычно это опция "Выберите...")
    const firstOption = select.querySelector('option:first-child');
    
    // Очищаем список
    select.innerHTML = '';
    
    // Добавляем первый элемент обратно
    if (firstOption) {
        select.appendChild(firstOption);
    }
    
    // Добавляем новые опции
    data.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.name;
        select.appendChild(option);
    });
    
    // Восстанавливаем выбранное значение, если оно было
    if (currentValue) {
        select.value = currentValue;
    }
}

/**
 * Заполнение выпадающего списка сотрудников
 * @param {string} selectId - ID элемента select
 * @param {Array} data - Массив объектов для заполнения списка
 */
function populateEmployeeSelect(selectId, data) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    // Сохраняем текущее выбранное значение
    const currentValue = select.value;
    
    // Получаем первый элемент (обычно это опция "Выберите...")
    const firstOption = select.querySelector('option:first-child');
    
    // Очищаем список
    select.innerHTML = '';
    
    // Добавляем первый элемент обратно
    if (firstOption) {
        select.appendChild(firstOption);
    }
    
    // Добавляем новые опции
    data.forEach(item => {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.full_name || `${item.last_name} ${item.first_name} ${item.patronymic || ''}`;
        select.appendChild(option);
    });
    
    // Восстанавливаем выбранное значение, если оно было
    if (currentValue) {
        select.value = currentValue;
    }
}

/**
 * Инициализация обработчиков событий для модальных окон
 */
function initModalHandlers() {
    // Обработчик для типа актива
    initModalHandler('assetType', '/api/dictionaries/asset-types', ['asset_type_id', 'deviceModelAssetType']);
    
    // Обработчик для модели устройства
    initModalHandler('deviceModel', '/api/dictionaries/device-models', ['device_model_id']);
    
    // Обработчик для статуса устройства
    initModalHandler('deviceStatus', '/api/dictionaries/device-statuses', ['status_id']);
    
    // Обработчик для производителя
    initModalHandler('manufacturer', '/api/dictionaries/manufacturers', ['deviceModelManufacturer']);
    
    // Обработчик для отдела
    initModalHandler('department', '/api/dictionaries/departments', ['department_id']);
    
    // Обработчик для местоположения
    initModalHandler('location', '/api/dictionaries/locations', ['location_id']);
    
    // Обработчик для сотрудника
    initModalHandler('employee', '/api/dictionaries/employees', ['employee_id'], true);
    
    // Обработчики для очистки форм при закрытии модальных окон
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('hidden.bs.modal', function() {
            const form = this.querySelector('form');
            if (form) form.reset();
            
            const errorAlert = this.querySelector('.alert');
            if (errorAlert) {
                errorAlert.classList.add('d-none');
                errorAlert.textContent = '';
            }
        });
    });
}

/**
 * Инициализация обработчика для конкретного модального окна
 * @param {string} prefix - Префикс ID элементов (например, 'assetType')
 * @param {string} url - URL API для отправки данных
 * @param {Array} selectIds - Массив ID элементов select, которые нужно обновить после сохранения
 * @param {boolean} isEmployee - Флаг, указывающий, что это модальное окно для сотрудника
 */
function initModalHandler(prefix, url, selectIds, isEmployee = false) {
    const saveButton = document.getElementById(`save${prefix.charAt(0).toUpperCase() + prefix.slice(1)}`);
    const form = document.getElementById(`${prefix}Form`);
    const modal = document.getElementById(`${prefix}Modal`);
    const errorAlert = document.getElementById(`${prefix}Error`);

    if (!saveButton || !form || !modal) return;

    saveButton.addEventListener('click', function() {
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const formData = new FormData(form);

        fetch(url, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            // --- НАЧАЛО КЛЮЧЕВЫХ ИЗМЕНЕНИЙ ---
            if (!response.ok) {
                // Если ответ НЕ успешный, мы парсим JSON с ошибкой...
                return response.json().then(errorData => {
                    // ...и ОТКЛОНЯЕМ промис, передавая в него ПОЛНЫЙ объект ошибки.
                    // Это правильный способ обработки ошибок в fetch.
                    return Promise.reject(errorData);
                });
            }
            // Если ответ успешный, просто парсим JSON.
            return response.json();
            // --- КОНЕЦ КЛЮЧЕВЫХ ИЗМЕНЕНИЙ ---
        })
        .then(data => {
            // Этот блок теперь выполняется ТОЛЬКО для успешных ответов (2xx).
            const modalInstance = bootstrap.Modal.getInstance(modal);
            modalInstance.hide();

            const updateFunction = isEmployee ? populateEmployeeSelect : populateSelect;
            const dataSourceUrl = isEmployee ? '/api/dictionaries/employees' : url;

            fetchDictionaryData(dataSourceUrl, function(items) {
                selectIds.forEach(selectId => {
                    updateFunction(selectId, items);
                    const select = document.getElementById(selectId);
                    if (select) {
                        select.value = data.id;

                        // Обновляем TomSelect, если он используется на этом элементе
                        if (select.tomselect) {
                            select.tomselect.sync();
                            select.tomselect.setValue(data.id, true); // true - не вызывать onchange
                        }

                        select.dispatchEvent(new Event('change'));
                    }
                });
            });

            showNotification('success', data.message || 'Запись успешно создана');
        })
        .catch(error => {
            // --- НАЧАЛО ИСПРАВЛЕНИЙ В CATCH ---
            // Теперь 'error' — это наш объект { detail: [...] } с сервера, а не Error.
            if (errorAlert) {
                let errorMessage = 'Произошла неизвестная ошибка.';

                if (error && error.detail) {
                    if (Array.isArray(error.detail)) {
                        // Стандартная ошибка валидации FastAPI
                        const firstError = error.detail[0];
                        const fieldName = firstError.loc && firstError.loc.length > 1 ? firstError.loc[1] : 'поле';
                        // Используем msg, который приходит от Pydantic
                        errorMessage = `Ошибка в поле '${fieldName}': ${firstError.msg}`;
                    } else if (typeof error.detail === 'string') {
                        // Наша кастомная ошибка (например, DuplicateError)
                        errorMessage = error.detail;
                    }
                } else if (error && error.message) {
                    // Обычная ошибка JavaScript (например, нет сети)
                    errorMessage = error.message;
                }

                errorAlert.textContent = errorMessage;
                errorAlert.classList.remove('d-none');
            }
            console.error('Ошибка при сохранении данных:', error); // Логируем полный объект
            // --- КОНЕЦ ИСПРАВЛЕНИЙ В CATCH ---
        });
    });
}

/**
 * Показать уведомление
 * @param {string} type - Тип уведомления ('success', 'danger', 'warning', 'info')
 * @param {string} message - Текст уведомления
 */
function showNotification(type, message) {
    // Создаем элемент уведомления
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show notification-toast`;
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Добавляем уведомление на страницу
    document.body.appendChild(notification);
    
    // Удаляем уведомление через 5 секунд
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            notification.remove();
        }, 150);
    }, 5000);
}

/**
 * Добавление кнопок "+" рядом с выпадающими списками
 */
function addDictionaryButtons() {
    // Добавляем кнопки рядом с выпадающими списками
    addButtonToSelect('asset_type_id', 'assetTypeModal');
    addButtonToSelect('device_model_id', 'deviceModelModal');
    addButtonToSelect('status_id', 'deviceStatusModal');
    addButtonToSelect('department_id', 'departmentModal');
    addButtonToSelect('location_id', 'locationModal');
    addButtonToSelect('employee_id', 'employeeModal');
}

/**
 * Добавление кнопки "+" рядом с выпадающим списком
 * @param {string} selectId - ID элемента select
 * @param {string} modalId - ID модального окна
 */
function addButtonToSelect(selectId, modalId) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    // Создаем обертку для select и кнопки, если её еще нет
    let wrapper = select.parentElement;
    if (!wrapper.classList.contains('input-group')) {
        // Создаем новую обертку
        wrapper = document.createElement('div');
        wrapper.className = 'input-group';
        
        // Заменяем select на wrapper с select внутри
        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(select);
    }
    
    // Проверяем, есть ли уже кнопка
    if (!wrapper.querySelector('.btn')) {
        // Создаем кнопку
        const button = document.createElement('button');
        button.className = 'btn btn-outline-secondary';
        button.type = 'button';
        button.setAttribute('data-bs-toggle', 'modal');
        button.setAttribute('data-bs-target', `#${modalId}`);
        button.innerHTML = '<i class="bi bi-plus"></i>';
        
        // Добавляем кнопку в обертку
        wrapper.appendChild(button);
    }
}

// Вызываем функцию добавления кнопок при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    addDictionaryButtons();
});