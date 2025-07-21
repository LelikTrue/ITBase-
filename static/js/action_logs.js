console.log('[LOGS] Скрипт страницы журнала действий запущен.');

document.addEventListener('DOMContentLoaded', function() {
    // Используем утилиту для очистки пустых полей формы фильтров перед отправкой
    cleanEmptyFieldsOnSubmit('#actionLogsForm');

    // --- Логика удаления ---
    const deleteModalEl = document.getElementById('deleteConfirmModal');
    if (!deleteModalEl) {
        console.error('[LOGS] КРИТИЧЕСКАЯ ОШИБКА: Модальное окно #deleteConfirmModal не найдено.');
        return;
    }

    const deleteModal = new bootstrap.Modal(deleteModalEl);

    // Используем единый обработчик на всем документе для максимальной надежности
    document.body.addEventListener('click', async function(e) {
        const target = e.target;

        // 1. Обработка клика по иконке удаления в таблице
        const deleteButton = target.closest('.delete-log');
        if (deleteButton) {
            e.preventDefault();
            const logId = deleteButton.dataset.logId;
            const confirmBtn = document.getElementById('confirmDeleteBtn');
            if (logId && confirmBtn) {
                confirmBtn.dataset.logIdToDelete = logId;
                deleteModal.show();
            }
            return;
        }

        // 2. Обработка клика по кнопке "Удалить" в модальном окне
        if (target.id === 'confirmDeleteBtn') {
            e.preventDefault();
            const logIdToDelete = target.dataset.logIdToDelete;
            if (!logIdToDelete) {
                deleteModal.hide();
                return;
            }

            try {
                const response = await fetch(`/admin/action-logs/${logIdToDelete}`, { method: 'DELETE' });
                deleteModal.hide();

                if (!response.ok) {
                    const errorData = await response.json().catch(() => ({ detail: 'Ошибка сервера' }));
                    throw new Error(errorData.detail);
                }

                const rowToRemove = document.querySelector(`.delete-log[data-log-id="${logIdToDelete}"]`)?.closest('tr');
                if (rowToRemove) {
                    const detailsRow = rowToRemove.nextElementSibling;
                    if (detailsRow && detailsRow.classList.contains('collapse-row')) {
                        detailsRow.remove();
                    }
                    rowToRemove.remove();
                    showNotification('Запись лога успешно удалена.', 'success');
                } else {
                    window.location.reload();
                }
            } catch (error) {
                showNotification(`Ошибка при удалении: ${error.message}`, 'danger');
            } finally {
                delete target.dataset.logIdToDelete;
            }
        }
    });
});