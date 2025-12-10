'use strict';

document.addEventListener('DOMContentLoaded', async () => {
    try {
        const response = await fetch('/api/analytics/dashboard');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        renderDashboard(data);
    } catch (error) {
        console.error('Error fetching dashboard data:', error);
        // Можно добавить визуальное уведомление в UI
    }
});

function renderDashboard(data) {
    // --- FIX: Настройка цветов Chart.js для Dark Mode ---
    Chart.defaults.color = '#e0e0e0'; // Светлый текст для всех графиков
    Chart.defaults.borderColor = '#444'; // Темные линии сетки
    // ---------------------------------------------------

    // 1. Финансовые карточки
    updateText('total-cost', formatCurrency(data.financials.total_cost));
    updateText('cost-in-use', formatCurrency(data.financials.cost_in_use));
    updateText('cost-in-stock', formatCurrency(data.financials.cost_in_stock));
    updateText('avg-wear', data.financials.avg_wear_percent.toFixed(1) + '%');

    // 2. Пончиковая диаграмма статусов
    const statusCanvas = document.getElementById('statusChart');
    if (statusCanvas) {
        new Chart(statusCanvas.getContext('2d'), {
            type: 'doughnut',
            data: {
                labels: data.by_status.map(s => s.label),
                datasets: [{
                    data: data.by_status.map(s => s.count),
                    backgroundColor: ['#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b', '#858796'],
                    hoverBorderColor: "rgba(234, 236, 244, 1)",
                }]
            },
            options: {
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                layout: { padding: 20 }
            }
        });
    }

    // 3. Горизонтальный бар-чарт типов
    const typeCanvas = document.getElementById('typeChart');
    if (typeCanvas) {
        new Chart(typeCanvas.getContext('2d'), {
            type: 'bar',
            data: {
                labels: data.by_type.map(t => t.label),
                datasets: [{
                    label: 'Количество',
                    data: data.by_type.map(t => t.count),
                    backgroundColor: "#4e73df",
                    hoverBackgroundColor: "#2e59d9",
                    borderColor: "#4e73df",
                }]
            },
            options: {
                indexAxis: 'y',
                maintainAspectRatio: false,
                scales: {
                    x: { grid: { display: false }, ticks: { maxTicksLimit: 6 } },
                    y: { grid: { borderDash: [2] } }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // 4. Таблица рисков
    renderRisksTable(data.risks);
}

function updateText(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function formatCurrency(value) {
    return new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'RUB', maximumFractionDigits: 0 }).format(value);
}

function renderRisksTable(risks) {
    const tbody = document.querySelector('#riskTable tbody');
    const cardsContainer = document.getElementById('riskCards');
    
    if (tbody) tbody.innerHTML = '';
    if (cardsContainer) cardsContainer.innerHTML = '';
    
    if (!risks || risks.length === 0) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Нет данных</td></tr>';
        if (cardsContainer) cardsContainer.innerHTML = '<div class="text-center text-muted p-3">Нет данных</div>';
        return;
    }
    
    risks.forEach(risk => {
        let badgeClass = 'bg-warning text-dark';
        let issueText = risk.issue;
        
        if (risk.criticality === 'HIGH') badgeClass = 'bg-danger text-white';
        
        const issueMap = {
            'CRITICAL_WEAR': 'Критический износ',
            'WARRANTY_EXPIRED': 'Гарантия истекла',
            'OLD_ASSET': 'Устарело'
        };
        issueText = issueMap[issueText] || issueText;

        // --- Desktop Table Row ---
        if (tbody) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><a href="/edit/${risk.id}" class="text-decoration-none text-primary-d">${escapeHtml(risk.inventory_number)}</a></td>
                <td>${escapeHtml(risk.name)}</td>
                <td><span class="badge ${badgeClass}">${issueText}</span></td>
                <td class="text-center">${risk.criticality === 'HIGH' ? '🔴' : '🟡'}</td>
                <td>${risk.date_val ? new Date(risk.date_val).toLocaleDateString('ru-RU') : '-'}</td>
                <td>
                    <a href="/edit/${risk.id}" class="btn btn-sm btn-outline-light">
                        <i class="bi bi-pencil"></i>
                    </a>
                </td>
            `;
            tbody.appendChild(tr);
        }

        // --- Mobile Card ---
        if (cardsContainer) {
            const card = document.createElement('div');
            card.className = 'card mb-3 shadow-sm';
            card.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <h5 class="card-title fw-bold mb-0 text-primary-d">${escapeHtml(risk.name)}</h5>
                        <span class="badge bg-secondary">#${escapeHtml(risk.inventory_number)}</span>
                    </div>
                    <div class="mb-2">
                        <span class="badge ${badgeClass} mb-1">${issueText}</span>
                        ${risk.criticality === 'HIGH' ? '<span class="badge bg-danger">CRITICAL</span>' : ''}
                    </div>
                    <div class="mb-2 text-muted small">
                        <i class="bi bi-calendar-event"></i> ${risk.date_val ? new Date(risk.date_val).toLocaleDateString('ru-RU') : '-'}
                    </div>
                    <a href="/edit/${risk.id}" class="btn btn-sm btn-outline-primary w-100">
                        <i class="bi bi-pencil"></i> Редактировать
                    </a>
                </div>
            `;
            cardsContainer.appendChild(card);
        }
    });
}

function escapeHtml(text) {
    if (!text) return '';
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
