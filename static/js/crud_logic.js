/**
 * Initializes generic CRUD logic for a dictionary page.
 * @param {object} options - Configuration options.
 * @param {string} options.entityName - Singular name of the entity (e.g., 'Отдел').
 * @param {string} options.apiEndpoint - Base URL for the API (e.g., '/admin/departments').
 */
function initializeCrud(options) {
    const { entityName, apiEndpoint } = options;
    let deleteItemId = null;
    const addModalEl = document.getElementById('addModal');
    const deleteModalEl = document.getElementById('deleteModal');
    const addModal = addModalEl ? new bootstrap.Modal(addModalEl) : null;
    const deleteModal = deleteModalEl ? new bootstrap.Modal(deleteModalEl) : null;
    const searchInput = document.getElementById('searchInput');
    const itemsTable = document.getElementById('itemsTable');

    // --- Internal Functions (no longer global) ---
    function clearSearch() {
        if (searchInput) searchInput.value = '';
        document.querySelectorAll('#itemsTable tbody tr').forEach(row => row.style.display = '');
    }

    function refreshTable() {
        window.location.reload();
    }

    function editRow(id) {
        const row = document.getElementById(`row-${id}`);
        if (row) row.classList.add('edit-mode');
    }

    function cancelEdit(id) {
        const row = document.getElementById(`row-${id}`);
        if (row) row.classList.remove('edit-mode');
    }

    async function saveRow(id) {
        const row = document.getElementById(`row-${id}`);
        if (!row) return;

        const formData = new FormData();
        const inputs = row.querySelectorAll('.edit-form input, .edit-form textarea, .edit-form select');
        let hasError = false;

        inputs.forEach(input => {
            if (input.name) {
                if (input.required && !input.value.trim()) {
                    showNotification(`Поле "${input.labels?.[0]?.textContent.replace('*','').trim() || input.name}" не может быть пустым.`, 'danger');
                    hasError = true;
                }
                formData.append(input.name, input.value.trim());
            }
        });

        if (hasError) return;

        try {
            const response = await fetch(`${apiEndpoint}/${id}`, {
                method: 'PUT',
                body: formData
            });
            
            if (response.ok) {
                showNotification('Успешно сохранено', 'success');
                setTimeout(() => window.location.reload(), 1000);
            } else {
                const error = await response.json();
                showNotification(error.detail || 'Ошибка при обновлении', 'danger');
            }
        } catch (error) {
            showNotification('Ошибка сети при обновлении', 'danger');
        }
    }

    function showDeleteModal(id, name) {
        deleteItemId = id;
        if (deleteModal) {
            const itemNameEl = document.getElementById('deleteItemName');
            if (itemNameEl) itemNameEl.textContent = name || `запись #${id}`;
            deleteModal.show();
        }
    }

    async function confirmDelete() {
        if (!deleteItemId || !deleteModal) return;
        
        try {
            const response = await fetch(`${apiEndpoint}/${deleteItemId}`, { method: 'DELETE' });
            deleteModal.hide();

            if (response.ok) {
                showNotification(`${entityName} успешно удален(а).`, 'success');
                const row = document.getElementById(`row-${deleteItemId}`);
                if (row) row.remove();
            } else {
                const error = await response.json();
                showNotification(error.detail || `Ошибка при удалении ${entityName.toLowerCase()}.`, 'danger');
            }
        } catch (error) {
            showNotification(`Сетевая ошибка при удалении ${entityName.toLowerCase()}.`, 'danger');
        } finally {
            deleteItemId = null;
        }
    }

    // --- Event Delegation for all buttons ---
    document.addEventListener('click', function(e) {
        const target = e.target;

        // Header buttons
        if (target.closest('.btn-clear-search')) {
            e.preventDefault();
            clearSearch();
        } else if (target.closest('.btn-refresh')) {
            e.preventDefault();
            refreshTable();
        }
        // Table row buttons
        else if (target.closest('.btn-edit')) {
            e.preventDefault();
            editRow(target.closest('.btn-edit').dataset.id);
        } else if (target.closest('.btn-cancel')) {
            e.preventDefault();
            cancelEdit(target.closest('.btn-cancel').dataset.id);
        } else if (target.closest('.btn-save')) {
            e.preventDefault();
            saveRow(target.closest('.btn-save').dataset.id);
        } else if (target.closest('.btn-delete')) {
            e.preventDefault();
            const btn = target.closest('.btn-delete');
            showDeleteModal(btn.dataset.id, btn.dataset.name);
        }
        // Modal confirm button
        else if (target.id === 'confirmDelete') {
            e.preventDefault();
            confirmDelete();
        }
    });

    // --- Other Event Handlers ---
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = itemsTable?.querySelectorAll('tbody tr');
            
            rows?.forEach(row => {
                const rowText = Array.from(row.cells)
                    .slice(0, -1) 
                    .map(cell => cell.textContent.toLowerCase())
                    .join(' ');
                row.style.display = rowText.includes(searchTerm) ? '' : 'none';
            });
        });
    }
    
    const addForm = document.getElementById('addForm');
    if (addForm) {
        addForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const formData = new FormData(this);
            let hasError = false;

            this.querySelectorAll('input[required], select[required]').forEach(input => {
                if (!formData.get(input.name)?.trim()) {
                    showNotification(`Поле "${input.labels[0]?.textContent.replace('*','').trim() || input.name}" не может быть пустым.`, 'danger');
                    hasError = true;
                }
            });

            if (hasError) return;
            try {
                const response = await fetch(apiEndpoint, {
                    method: 'POST',
                    body: formData
                });
                if (addModal) addModal.hide();

                if (response.ok) { 
                    showNotification(`${entityName} успешно добавлен(а).`, 'success'); 
                    setTimeout(() => window.location.reload(), 1000); 
                } else { 
                    const error = await response.json(); 
                    showNotification(error.detail || `Ошибка при добавлении ${entityName.toLowerCase()}.`, 'danger'); 
                }
            } catch (error) { 
                showNotification(`Сетевая ошибка при добавлении ${entityName.toLowerCase()}.`, 'danger'); 
            }
        });
    }

    if (addModalEl) {
        addModalEl.addEventListener('hidden.bs.modal', () => addForm?.reset());
    }
}