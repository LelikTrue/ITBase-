/**
 * Displays a Bootstrap 5 toast-like notification.
 * @param {string} message The message to display.
 * @param {string} type The type of notification ('success', 'danger', 'warning', 'info').
 */
function showNotification(message, type = 'info') {
    const alertClass = `alert-${type}`;
    const iconClass = {
        success: 'bi-check-circle-fill',
        danger: 'bi-exclamation-triangle-fill',
        warning: 'bi-exclamation-triangle-fill',
        info: 'bi-info-circle-fill'
    }[type] || 'bi-info-circle-fill';

    const notification = document.createElement('div');
    notification.className = `alert ${alertClass} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        <i class="bi ${iconClass} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    document.body.appendChild(notification);

    // Automatically remove after 5 seconds
    const bsAlert = new bootstrap.Alert(notification);
    setTimeout(() => bsAlert.close(), 5000);
}