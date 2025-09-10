// UI Utility Functions
class UI {
    static toastContainer = null;
    static toastId = 0;
    
    static init() {
        this.toastContainer = document.getElementById('toastContainer');
        if (!this.toastContainer) {
            console.warn('Toast container not found');
        }
    }
    
    // Toast notifications
    static showToast(message, type = 'info', duration = 5000) {
        if (!this.toastContainer) {
            console.log(`Toast: ${message} (${type})`);
            return;
        }
        
        const toastId = ++this.toastId;
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.id = `toast-${toastId}`;
        
        const icon = this.getToastIcon(type);
        toast.innerHTML = `
            <i class="fas fa-${icon}"></i>
            <span>${message}</span>
            <button class="toast-close" onclick="UI.removeToast(${toastId})">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        this.toastContainer.appendChild(toast);
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.removeToast(toastId);
            }, duration);
        }
        
        return toastId;
    }
    
    static removeToast(toastId) {
        const toast = document.getElementById(`toast-${toastId}`);
        if (toast) {
            toast.style.animation = 'slideOut 0.3s ease-in forwards';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        }
    }
    
    static getToastIcon(type) {
        switch (type) {
            case 'success': return 'check-circle';
            case 'error': return 'exclamation-circle';
            case 'warning': return 'exclamation-triangle';
            case 'info': 
            default: return 'info-circle';
        }
    }
    
    // Loading states
    static showLoading(containerId, message = 'Loading...') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div class="loading-state">
                <i class="fas fa-spinner fa-spin"></i>
                <p>${message}</p>
            </div>
        `;
    }
    
    static showError(containerId, message = 'An error occurred') {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
            </div>
        `;
    }
    
    static showEmpty(containerId, message = 'No data available', actionText = '', actionCallback = null) {
        const container = document.getElementById(containerId);
        if (!container) return;
        
        const actionHtml = actionText && actionCallback ? 
            `<button class="btn-primary" onclick="${actionCallback}">${actionText}</button>` : '';
        
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>${message}</p>
                ${actionHtml}
            </div>
        `;
    }
    
    // Form utilities
    static validateForm(formId, rules = {}) {
        const form = document.getElementById(formId);
        if (!form) return false;
        
        let isValid = true;
        const errors = {};
        
        Object.keys(rules).forEach(fieldName => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            const fieldRules = rules[fieldName];
            
            if (!field) return;
            
            // Clear previous errors
            this.clearFieldError(field);
            
            // Required validation
            if (fieldRules.required && !field.value.trim()) {
                errors[fieldName] = 'This field is required';
                isValid = false;
            }
            
            // Min length validation
            if (fieldRules.minLength && field.value.length < fieldRules.minLength) {
                errors[fieldName] = `Minimum length is ${fieldRules.minLength} characters`;
                isValid = false;
            }
            
            // Max length validation
            if (fieldRules.maxLength && field.value.length > fieldRules.maxLength) {
                errors[fieldName] = `Maximum length is ${fieldRules.maxLength} characters`;
                isValid = false;
            }
            
            // Email validation
            if (fieldRules.email && field.value && !this.isValidEmail(field.value)) {
                errors[fieldName] = 'Please enter a valid email address';
                isValid = false;
            }
            
            // Custom validation
            if (fieldRules.custom && typeof fieldRules.custom === 'function') {
                const customResult = fieldRules.custom(field.value);
                if (customResult !== true) {
                    errors[fieldName] = customResult || 'Invalid value';
                    isValid = false;
                }
            }
            
            // Show error if any
            if (errors[fieldName]) {
                this.showFieldError(field, errors[fieldName]);
            }
        });
        
        return { isValid, errors };
    }
    
    static showFieldError(field, message) {
        field.classList.add('error');
        
        let errorElement = field.parentNode.querySelector('.field-error');
        if (!errorElement) {
            errorElement = document.createElement('div');
            errorElement.className = 'field-error';
            field.parentNode.appendChild(errorElement);
        }
        
        errorElement.textContent = message;
    }
    
    static clearFieldError(field) {
        field.classList.remove('error');
        
        const errorElement = field.parentNode.querySelector('.field-error');
        if (errorElement) {
            errorElement.remove();
        }
    }
    
    // Utility functions
    static isValidEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    }
    
    static formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 B';
        
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }
    
    static formatNumber(number) {
        return new Intl.NumberFormat().format(number);
    }
    
    static formatDate(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
        };
        
        const formatOptions = { ...defaultOptions, ...options };
        return new Intl.DateTimeFormat('en-US', formatOptions).format(new Date(date));
    }
    
    static formatDateTime(date, options = {}) {
        const defaultOptions = {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        };
        
        const formatOptions = { ...defaultOptions, ...options };
        return new Intl.DateTimeFormat('en-US', formatOptions).format(new Date(date));
    }
    
    // Animation utilities
    static fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = performance.now();
        
        function animate(currentTime) {
            let elapsed = currentTime - start;
            let progress = elapsed / duration;
            
            if (progress > 1) progress = 1;
            
            element.style.opacity = progress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    static fadeOut(element, duration = 300, callback = null) {
        let start = performance.now();
        
        function animate(currentTime) {
            let elapsed = currentTime - start;
            let progress = elapsed / duration;
            
            if (progress > 1) progress = 1;
            
            element.style.opacity = 1 - progress;
            
            if (progress < 1) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
                if (callback) callback();
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    // Debounce utility
    static debounce(func, wait, immediate = false) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func(...args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func(...args);
        };
    }
    
    // Throttle utility
    static throttle(func, wait) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, wait);
            }
        };
    }
    
    // Copy to clipboard
    static async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            this.showToast('Copied to clipboard', 'success');
            return true;
        } catch {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                document.execCommand('copy');
                this.showToast('Copied to clipboard', 'success');
                return true;
            } catch {
                this.showToast('Failed to copy to clipboard', 'error');
                return false;
            } finally {
                document.body.removeChild(textArea);
            }
        }
    }
    
    // Scroll utilities
    static scrollToTop(smooth = true) {
        window.scrollTo({
            top: 0,
            behavior: smooth ? 'smooth' : 'auto'
        });
    }
    
    static scrollToElement(elementId, offset = 0, smooth = true) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;
        
        window.scrollTo({
            top: offsetPosition,
            behavior: smooth ? 'smooth' : 'auto'
        });
    }
}

// Initialize UI when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    UI.init();
});

// Add CSS for toast animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideOut {
        0% {
            opacity: 1;
            transform: translateX(0);
        }
        100% {
            opacity: 0;
            transform: translateX(100%);
        }
    }
    
    .field-error {
        color: var(--error-color);
        font-size: 0.875rem;
        margin-top: 0.25rem;
    }
    
    .error {
        border-color: var(--error-color) !important;
        box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.1) !important;
    }
    
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .stat-item {
        display: flex;
        justify-content: space-between;
        padding: 0.75rem;
        background: var(--background-secondary);
        border-radius: var(--border-radius);
    }
    
    .stat-label {
        font-weight: 500;
        color: var(--text-secondary);
    }
    
    .stat-value {
        font-weight: 600;
        color: var(--text-primary);
    }
    
    .stats-section {
        margin-bottom: 2rem;
    }
    
    .stats-section h5 {
        margin-bottom: 1rem;
        color: var(--text-primary);
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 0.5rem;
    }
    
    .categorical-stat {
        margin-bottom: 1rem;
        padding: 1rem;
        background: var(--background-secondary);
        border-radius: var(--border-radius);
    }
    
    .categorical-stat h6 {
        margin-bottom: 0.5rem;
        color: var(--text-primary);
    }
    
    .value-counts {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.5rem;
    }
    
    .value-count-item {
        background: var(--background-primary);
        padding: 0.25rem 0.5rem;
        border-radius: var(--border-radius);
        font-size: 0.875rem;
        border: 1px solid var(--border-color);
    }
    
    .dataset-summary {
        padding: 0.75rem;
        border-bottom: 1px solid var(--border-color);
    }
    
    .dataset-summary:last-child {
        border-bottom: none;
    }
    
    .dataset-summary strong {
        display: block;
        margin-bottom: 0.25rem;
        color: var(--text-primary);
    }
    
    .dataset-summary small {
        color: var(--text-secondary);
    }
    
    .help-content h4 {
        margin-bottom: 1.5rem;
        color: var(--text-primary);
    }
    
    .help-section {
        margin-bottom: 2rem;
    }
    
    .help-section h5 {
        margin-bottom: 1rem;
        color: var(--text-primary);
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 0.5rem;
    }
    
    .help-section ol,
    .help-section ul {
        margin-left: 1.5rem;
    }
    
    .help-section li {
        margin-bottom: 0.5rem;
        line-height: 1.5;
    }
`;

document.head.appendChild(style);