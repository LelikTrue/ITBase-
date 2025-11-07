// static/js/tom-select-init.js
document.addEventListener('DOMContentLoaded', function() {
    const tagSelectEl = document.getElementById('tag-select');
    if (tagSelectEl) {
        // --- НАЧАЛО ИЗМЕНЕНИЯ ---
        let existingTagOptions = [];
        let existingTagItems = [];

        // Читаем новый data-атрибут
        const existingTagsDataAttr = tagSelectEl.dataset.existingTagsData;
        if (existingTagsDataAttr) {
            try {
                // Сразу получаем готовые опции
                existingTagOptions = JSON.parse(existingTagsDataAttr);
                // Из них получаем массив ID для начального выбора
                existingTagItems = existingTagOptions.map(tag => tag.id);
            } catch (e) {
                console.error("Failed to parse existing tags JSON:", e);
            }
        }
        // --- КОНЕЦ ИЗМЕНЕНИЯ ---

        new TomSelect(tagSelectEl, {
            valueField: 'id',     // Поле из JSON, которое будет значением
            labelField: 'name',   // Поле из JSON, которое будет текстом для отображения
            searchField: 'name',  // Поле, по которому будет идти поиск
            
            // Включаем удаленный поиск
            load: function(query, callback) {
                if (!query.length) return callback();
                
                // Формируем URL для нашего API (предполагая, что он существует)
                // Если API для поиска тегов еще не создан, его нужно будет добавить.
                const url = `/api/v1/tags/search?q=${encodeURIComponent(query)}`;
                
                fetch(url)
                    .then(response => response.json())
                    .then(json => {
                        callback(json); // Передаем полученные данные в TomSelect
                    }).catch(() => {
                        callback(); // В случае ошибки, просто ничего не показываем
                    });
            },
            
            create: false, // Запрещаем создание новых тегов "на лету" в этом виджете
            items: existingTagItems,    // Передаем ID для выбора: [1, 5, 12]
            options: existingTagOptions, // Передаем полные объекты: [{'id':1, 'name':'Тег1'}, ...]

            placeholder: 'Начните вводить для поиска тегов...',
            render: {
                // Кастомный рендеринг, чтобы было видно, когда ничего не найдено
                no_results: function(data, escape) {
                    return '<div class="no-results">Тег не найден.</div>';
                },
            }
        });
    }
});