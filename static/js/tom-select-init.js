// static/js/tom-select-init.js
document.addEventListener('DOMContentLoaded', function() {
    const tagSelect = document.getElementById('tag-select');
    if (tagSelect) {
        new TomSelect(tagSelect, {
            valueField: 'id',     // Поле из JSON, которое будет значением
            labelField: 'name',   // Поле из JSON, которое будет текстом
            searchField: 'name',  // Поле, по которому будет идти поиск
            
            // Включаем удаленный поиск
            load: function(query, callback) {
                if (!query.length) return callback();
                
                // Формируем URL для нашего нового API
                const url = `/api/v1/tags/search?q=${encodeURIComponent(query)}`;
                
                fetch(url)
                    .then(response => response.json())
                    .then(json => {
                        callback(json); // Передаем полученные данные в TomSelect
                    }).catch(() => {
                        callback(); // В случае ошибки, просто ничего не показываем
                    });
            },
            
            create: false, // Запрещаем создание новых тегов "на лету"
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