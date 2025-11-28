// static/js/dictionary_modals.js
document.addEventListener('DOMContentLoaded', function() {
    // Находим абсолютно все модальные окна справочников на странице
    const modals = document.querySelectorAll('.modal[id$="Modal"]');

    modals.forEach(modal => {
        // Для каждого модального окна настраиваем его логику
        setupModal(modal);
    });
});

/**
 * Настраивает логику для ОДНОГО модального окна.
 * @param {HTMLElement} modal - DOM-элемент модального окна
 */
function setupModal(modal) {
    const prefix = modal.id.replace('Modal', '');
    const saveButton = document.getElementById(`save-${prefix}`);
    const form = document.getElementById(`${prefix}Form`);
    const errorAlert = document.getElementById(`${prefix}Error`);

    if (!saveButton || !form) {
        console.warn(`Пропущены элементы для модального окна с префиксом: ${prefix}`);
        return;
    }

    // Когда нажимается кнопка "Сохранить"...
    saveButton.addEventListener('click', function() {
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const url = `/api/dictionaries/${prefix}`;
        const formData = new FormData(form);

        fetch(url, { method: 'POST', body: formData })
            .then(response => {
                if (!response.ok) { return response.json().then(err => Promise.reject(err)); }
                return response.json();
            })
            .then(savedData => {
                // 1. Скрываем модальное окно
                bootstrap.Modal.getInstance(modal).hide();
                
                // 2. Обновляем все select'ы на странице, которые используют этот справочник
                updatePageSelects(prefix, savedData);
                
                // 3. Показываем уведомление об успехе
                showNotification('success', 'Запись успешно создана!');
            })
            .catch(error => {
                if (errorAlert) {
                    const errorMessage = error.detail || 'Произошла неизвестная ошибка.';
                    errorAlert.textContent = typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage);
                    errorAlert.classList.remove('d-none');
                }
                console.error(`Ошибка при сохранении для ${prefix}:`, error);
            });
    });

    // Когда модальное окно закрывается, очищаем форму
    modal.addEventListener('hidden.bs.modal', function() {
        form.reset();
        if (errorAlert) errorAlert.classList.add('d-none');
    });

    // Особый случай для модального окна "Модели", которому нужно подгружать свои справочники
    if (prefix === 'device-models') {
        modal.addEventListener('show.bs.modal', function() {
            const manufacturerSelect = modal.querySelector('#device-models-manufacturer_id');
            const assetTypeSelect = modal.querySelector('#device-models-asset_type_id');
            if (manufacturerSelect) updateSelectWithOptions(manufacturerSelect, '/api/dictionaries/manufacturers');
            if (assetTypeSelect) updateSelectWithOptions(assetTypeSelect, '/api/dictionaries/asset-types');
        });
    }
}

// --- Вспомогательные функции ---

/**
 * Обновляет все select'ы на странице, которые связаны с обновлённым справочником.
 * Вместо перезагрузки страницы динамически обновляет опции и выбирает новую запись.
 * @param {string} prefix - Префикс справочника (например, 'asset-types', 'manufacturers')
 * @param {Object} newItem - Только что созданная запись с полями {id, name, ...}
 */
function updatePageSelects(prefix, newItem) {
    // Маппинг: какие select'ы на странице нужно обновить для каждого справочника
    const selectorsMap = {
        'asset-types': ['#asset_type_id'],
        'device-models': ['#device_model_id'],
        'device-statuses': ['#status_id'],
        'manufacturers': ['#manufacturer_id'], // если есть на странице
        'departments': ['#department_id'],
        'locations': ['#location_id'],
        'suppliers': ['#supplier_id']
    };
    
    const selectorsToUpdate = selectorsMap[prefix] || [];
    
    selectorsToUpdate.forEach(selector => {
        const selectElement = document.querySelector(selector);
        if (!selectElement) return; // Если элемент не найден на странице, пропускаем
        
        // Загружаем свежие данные из API
        const url = `/api/dictionaries/${prefix}`;
        fetch(url)
            .then(response => response.json())
            .then(items => {
                // Сохраняем оригинальный текст placeholder'а ДО очистки
                const originalPlaceholder = selectElement.querySelector('option[value=""]')?.textContent || 'Выберите...';
                
                // Очищаем select
                selectElement.innerHTML = '';
                
                // Добавляем placeholder с оригинальным текстом
                const placeholder = document.createElement('option');
                placeholder.value = '';
                placeholder.textContent = originalPlaceholder;
                selectElement.appendChild(placeholder);
                
                // Заполняем опциями
                items.forEach(item => {
                    const option = document.createElement('option');
                    option.value = item.id;
                    
                    // Для device-models формат особый: "Название (Производитель)"
                    if (prefix === 'device-models' && item.manufacturer) {
                        option.textContent = `${item.name} (${item.manufacturer.name})`;
                    } else {
                        option.textContent = item.name;
                    }
                    
                    selectElement.appendChild(option);
                });
                
                // Автоматически выбираем только что созданную запись
                selectElement.value = newItem.id;
                
                // Триггерим событие change для обновления зависимых элементов (если есть)
                selectElement.dispatchEvent(new Event('change', { bubbles: true }));
            })
            .catch(error => {
                console.error(`Ошибка при обновлении select ${selector} из ${url}:`, error);
            });
    });
}

/**
 * Функция для подгрузки данных в select'ы ВНУТРИ модального окна "Модели".
 * Она больше не используется для обновления основной страницы.
 */
function updateSelectWithOptions(select, url) {
    fetch(url)
        .then(response => response.json())
        .then(items => {
            select.innerHTML = '';
            const placeholder = document.createElement('option');
            placeholder.value = '';
            placeholder.textContent = 'Выберите...';
            select.appendChild(placeholder);
            items.forEach(item => {
                const option = document.createElement('option');
                option.value = item.id;
                option.textContent = item.name;
                select.appendChild(option);
            });
        })
        .catch(error => console.error(`Ошибка при обновлении select из ${url}:`, error));
}


function showNotification(type, message) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show`;
    notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999;';
    notification.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>`;
    document.body.appendChild(notification);
    // Уведомление само закроется при перезагрузке, но таймер на всякий случай оставим
    setTimeout(() => { 
        const instance = bootstrap.Alert.getOrCreateInstance(notification);
        if (instance) {
            instance.close();
        }
    }, 5000);
}