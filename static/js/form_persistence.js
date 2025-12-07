/**
 * Form Persistence System
 * Сохраняет данные формы в LocalStorage перед уходом со страницы.
 * Восстанавливает при возвращении.
 */

const FormPersistence = {
    // Генерируем уникальный ключ на основе пути страницы
    getKey: function(formId) {
        // Используем путь URL для уникальности (чтобы /edit/214 и /edit/215 не конфликтовали)
        return 'form_draft_' + window.location.pathname + '_' + formId;
    },

    save: function(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        const formData = new FormData(form);
        const data = {};
        
        // Сериализуем данные
        for (const [key, value] of formData.entries()) {
            // Игнорируем файлы и csrf токены
            if (key === 'csrf_token') continue;
            if (value instanceof File) continue;
            data[key] = value;
        }

        const storageKey = this.getKey(formId);
        localStorage.setItem(storageKey, JSON.stringify(data));
        console.log('[FormPersistence] Saved form:', storageKey);
    },

    restore: function(formId) {
        const form = document.getElementById(formId);
        if (!form) return;

        const storageKey = this.getKey(formId);
        const rawData = localStorage.getItem(storageKey);
        if (!rawData) return;

        const data = JSON.parse(rawData);
        
        // Заполняем поля
        Object.keys(data).forEach(key => {
            const input = form.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = data[key] === 'on' || data[key] === true;
                } else if (input.type === 'radio') {
                    const radio = form.querySelector(`[name="${key}"][value="${data[key]}"]`);
                    if (radio) radio.checked = true;
                } else if (input.tagName === 'SELECT') {
                    input.value = data[key];
                    // Триггерим событие change для зависимых селектов
                    input.dispatchEvent(new Event('change', { bubbles: true }));
                } else {
                    input.value = data[key];
                }
            }
        });

        console.log('[FormPersistence] Restored form:', storageKey);
    },
    
    clear: function(formId) {
        const storageKey = this.getKey(formId);
        localStorage.removeItem(storageKey);
        console.log('[FormPersistence] Cleared form:', storageKey);
    }
};

// Автоматическая привязка
document.addEventListener('DOMContentLoaded', function() {
    // 1. Восстанавливаем данные при загрузке страницы
    const mainForm = document.querySelector('form.persist-data');
    if (mainForm) {
        FormPersistence.restore(mainForm.id);
        
        // При успешном submit чистим хранилище
        mainForm.addEventListener('submit', function() {
            FormPersistence.clear(mainForm.id);
        });
    }

    // 2. При клике на ссылки "Добавить справочник" сохраняем текущую форму
    document.querySelectorAll('.save-state-link').forEach(link => {
        link.addEventListener('click', function() {
            if (mainForm) FormPersistence.save(mainForm.id);
        });
    });
});
