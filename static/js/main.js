/**
 * WattWise - Main Global JavaScript
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Live Topbar Clock
    initLiveClock();

    // 2. Mobile Sidebar Toggle
    initMobileNav();

    // 3. Reset Data Modal / Handler
    initDataReset();
});

function initLiveClock() {
    const clockEl = document.getElementById('topbar-clock');
    if (!clockEl) return;

    function update() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
        clockEl.textContent = timeStr;
    }
    update();
    setInterval(update, 1000);
}

function initMobileNav() {
    const toggleBtn = document.getElementById('mobile-toggle-btn');
    const sidebar = document.getElementById('app-sidebar');
    if (!toggleBtn || !sidebar) return;

    toggleBtn.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });

    // Close when clicking outside on mobile
    document.addEventListener('click', (e) => {
        if (window.innerWidth <= 768 && sidebar.classList.contains('open')) {
            if (!sidebar.contains(e.target) && !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        }
    });
}

function initDataReset() {
    const resetBtn = document.getElementById('reset-demo-btn');
    if (!resetBtn) return;

    resetBtn.addEventListener('click', async () => {
        if (!confirm('Re-seed the database with 35 days of fresh realistic sample data?')) return;
        
        try {
            resetBtn.disabled = true;
            resetBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Resetting...';
            
            const res = await fetch('/api/reset-data', { method: 'POST' });
            const data = await res.json();
            
            if (res.ok && data.status === 'success') {
                showToast(data.message, 'success');
                setTimeout(() => window.location.reload(), 1200);
            } else {
                showToast(data.message || 'Error resetting data', 'error');
            }
        } catch (err) {
            showToast('Failed to connect to server.', 'error');
        } finally {
            resetBtn.disabled = false;
            resetBtn.innerHTML = '<i class="fas fa-rotate-left"></i> Reset Demo Data';
        }
    });
}

/**
 * Universal Toast Notification System
 */
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;

    let icon = 'fa-circle-info';
    if (type === 'success') icon = 'fa-circle-check';
    if (type === 'error') icon = 'fa-triangle-exclamation';

    toast.innerHTML = `
        <i class="fas ${icon}" style="font-size: 1.1rem;"></i>
        <div style="flex: 1;">${message}</div>
        <button style="background:none; border:none; color:var(--text-dim); cursor:pointer;" onclick="this.parentElement.remove()">
            <i class="fas fa-xmark"></i>
        </button>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        if (toast.parentElement) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }
    }, 4500);
}
