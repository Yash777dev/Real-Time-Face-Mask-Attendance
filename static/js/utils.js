// utils.js — Toast notifications, fetch wrapper, and modal utils

class Toast {
    static container = null;

    static init() {
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            this.container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:10000;display:flex;flex-direction:column;gap:10px;';
            document.body.appendChild(this.container);
        }
    }

    static show(message, type = 'info', duration = 4000) {
        this.init();

        const toast = document.createElement('div');
        toast.className = 'alert';
        toast.style.cssText = 'min-width:300px;box-shadow:0 4px 16px rgba(0,0,0,0.5);margin:0;';
        toast.innerHTML = `
            <i class="fa-solid fa-circle-info"></i>
            <span style="flex: 1;">${message}</span>
            <button onclick="this.parentElement.remove()" class="alert-dismiss">&times;</button>
        `;

        this.container.appendChild(toast);

        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    static success(msg) { this.show(msg, 'success'); }
    static error(msg) { this.show(msg, 'danger'); }
    static warning(msg) { this.show(msg, 'warning'); }
    static info(msg) { this.show(msg, 'info'); }
}

async function apiFetch(url, options = {}) {
    const defaults = {
        headers: { 'Content-Type': 'application/json' },
    };
    const config = { ...defaults, ...options };

    try {
        const response = await fetch(url, config);
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || `HTTP ${response.status}`);
        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

function confirmAction(title, message, onConfirm, confirmText = 'Confirm', confirmClass = 'btn-primary') {
    const overlay = document.createElement('div');
    overlay.style.cssText = 'position:fixed;inset:0;background:rgba(3,27,27,0.85);backdrop-filter:blur(8px);display:flex;align-items:center;justify-content:center;z-index:9999;';
    overlay.innerHTML = `
        <div style="background:var(--color-dark-green);border:1px solid var(--border-accent);border-radius:var(--radius-lg);padding:32px;max-width:420px;width:90%;box-shadow:var(--shadow-lg);">
            <h3 style="font-size:1.125rem;font-weight:700;margin-bottom:12px;color:var(--color-anti-flash-white);">${title}</h3>
            <p style="color:var(--color-pistachio);font-size:0.9375rem;margin-bottom:24px;">${message}</p>
            <div style="display:flex;gap:12px;justify-content:flex-end;">
                <button class="btn btn-outline" id="modalCancel">Cancel</button>
                <button class="btn ${confirmClass}" id="modalConfirm">${confirmText}</button>
            </div>
        </div>
    `;

    document.body.appendChild(overlay);

    overlay.querySelector('#modalCancel').onclick = () => overlay.remove();
    overlay.querySelector('#modalConfirm').onclick = () => {
        overlay.remove();
        onConfirm();
    };
    overlay.onclick = (e) => { if (e.target === overlay) overlay.remove(); };
}

function validateRequired(form) {
    let valid = true;
    form.querySelectorAll('[required]').forEach(input => {
        if (!input.value.trim()) {
            input.style.borderColor = 'var(--color-caribbean-green)';
            valid = false;
        } else {
            input.style.borderColor = '';
        }
    });
    return valid;
}

function animateNumber(element, target, duration = 1000) {
    const start = parseInt(element.textContent) || 0;
    const increment = (target - start) / (duration / 16);
    let current = start;

    const timer = setInterval(() => {
        current += increment;
        if ((increment > 0 && current >= target) || (increment < 0 && current <= target)) {
            element.textContent = target;
            clearInterval(timer);
        } else {
            element.textContent = Math.round(current);
        }
    }, 16);
}
