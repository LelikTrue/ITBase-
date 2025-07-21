/**
 * При отправке формы удаляет пустые поля, чтобы они не попадали в URL.
 * @param {string} formSelector - CSS-селектор для формы.
 */
function cleanEmptyFieldsOnSubmit(formSelector) {
    const form = document.querySelector(formSelector);
    if (form) {
        form.addEventListener('submit', function() {
            const inputs = form.querySelectorAll('input, select');
            inputs.forEach(input => {
                if (input.value === '' || input.value === null) {
                    // Временно удаляем атрибут name, чтобы поле не было отправлено
                    const name = input.getAttribute('name');
                    if (name) input.dataset.originalName = name;
                    input.removeAttribute('name');
                }
            });
        });
    }
}