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
    if (!tbody) return;
    
    tbody.innerHTML = '';
    
    if (!risks || risks.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted">Нет данных</td></tr>';
        return;
    }
    
    risks.forEach(risk => {
        const tr = document.createElement('tr');
        
        let badgeClass = 'bg-warning text-dark';
        let issueText = risk.issue;
        
        if (risk.criticality === 'HIGH') badgeClass = 'bg-danger text-white';
        
        const issueMap = {
            'CRITICAL_WEAR': 'Критический износ',
            'WARRANTY_EXPIRED': 'Гарантия истекла',
            'OLD_ASSET': 'Устарело'
        };
        issueText = issueMap[issueText] || issueText;

        // XSS Protection via escapeHtml
        tr.innerHTML = `
            <td><a href="/assets/${risk.id}" class="text-decoration-none">${escapeHtml(risk.inventory_number)}</a></td>
            <td>${escapeHtml(risk.name)}</td>
            <td><span class="badge ${badgeClass}">${issueText}</span></td>
            <td class="text-center">${risk.criticality === 'HIGH' ? '🔴' : '🟡'}</td>
            <td>${risk.date_val ? new Date(risk.date_val).toLocaleDateString('ru-RU') : '-'}</td>
            <td>
                <a href="/assets/${risk.id}/edit" class="btn btn-sm btn-outline-primary">
                    <i class="bi bi-pencil"></i>
                </a>
            </td>
        `;
        tbody.appendChild(tr);
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
