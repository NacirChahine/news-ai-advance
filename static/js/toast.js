/**
 * Toast Notification System
 * Displays floating notifications in the bottom-left corner
 */

class ToastManager {
    constructor() {
        this.container = null;
        this.toasts = [];
        this.init();
    }

    /**
     * Initialize the toast container
     */
    init() {
        // Create container if it doesn't exist
        if (!document.querySelector('.toast-container')) {
            this.container = document.createElement('div');
            this.container.className = 'toast-container';
            this.container.setAttribute('role', 'region');
            this.container.setAttribute('aria-label', 'Notifications');
            document.body.appendChild(this.container);
        } else {
            this.container = document.querySelector('.toast-container');
        }
    }

    /**
     * Show a toast notification
     * @param {string} message - The message to display
     * @param {string} type - Type of toast: 'success', 'error', 'warning', 'info'
     * @param {number} duration - Duration in milliseconds (0 = no auto-dismiss)
     */
    show(message, type = 'info', duration = 5000) {
        const toast = this.createToast(message, type);
        this.container.appendChild(toast);
        this.toasts.push(toast);

        // Trigger reflow for animation
        toast.offsetHeight;

        // Auto-dismiss after duration
        if (duration > 0) {
            setTimeout(() => {
                this.dismiss(toast);
            }, duration);
        }

        return toast;
    }

    /**
     * Create a toast element
     * @param {string} message - The message to display
     * @param {string} type - Type of toast
     * @returns {HTMLElement} The toast element
     */
    createToast(message, type) {
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'polite');
        toast.setAttribute('aria-atomic', 'true');

        // Get icon based on type
        const icon = this.getIcon(type);

        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-icon">${icon}</span>
                <span class="toast-message">${this.escapeHtml(message)}</span>
            </div>
            <button class="toast-close" aria-label="Close notification">
                <i class="fas fa-times"></i>
            </button>
        `;

        // Add close button event
        const closeBtn = toast.querySelector('.toast-close');
        closeBtn.addEventListener('click', () => {
            this.dismiss(toast);
        });

        return toast;
    }

    /**
     * Get icon for toast type
     * @param {string} type - Toast type
     * @returns {string} HTML for icon
     */
    getIcon(type) {
        const icons = {
            success: '<i class="fas fa-check-circle"></i>',
            error: '<i class="fas fa-exclamation-circle"></i>',
            warning: '<i class="fas fa-exclamation-triangle"></i>',
            info: '<i class="fas fa-info-circle"></i>'
        };
        return icons[type] || icons.info;
    }

    /**
     * Dismiss a toast
     * @param {HTMLElement} toast - The toast element to dismiss
     */
    dismiss(toast) {
        if (!toast || !toast.parentElement) return;

        toast.classList.add('removing');
        
        // Remove after animation completes
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
            // Remove from tracking array
            const index = this.toasts.indexOf(toast);
            if (index > -1) {
                this.toasts.splice(index, 1);
            }
        }, 300); // Match animation duration
    }

    /**
     * Dismiss all toasts
     */
    dismissAll() {
        this.toasts.forEach(toast => this.dismiss(toast));
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped text
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Convenience methods for different toast types
     */
    success(message, duration = 5000) {
        return this.show(message, 'success', duration);
    }

    error(message, duration = 7000) {
        return this.show(message, 'error', duration);
    }

    warning(message, duration = 6000) {
        return this.show(message, 'warning', duration);
    }

    info(message, duration = 5000) {
        return this.show(message, 'info', duration);
    }
}

// Create global instance
const toast = new ToastManager();

// Make it available globally
window.toast = toast;

/**
 * Process Django messages on page load
 */
document.addEventListener('DOMContentLoaded', function() {
    // Check if there are Django messages to display
    const djangoMessages = document.querySelectorAll('[data-django-message]');
    
    djangoMessages.forEach(function(messageElement) {
        const message = messageElement.getAttribute('data-django-message');
        const messageType = messageElement.getAttribute('data-django-message-type');
        
        // Map Django message tags to toast types
        let toastType = 'info';
        if (messageType === 'success') toastType = 'success';
        else if (messageType === 'error' || messageType === 'danger') toastType = 'error';
        else if (messageType === 'warning') toastType = 'warning';
        else if (messageType === 'info') toastType = 'info';
        
        // Show the toast
        toast.show(message, toastType);
        
        // Remove the message element from DOM
        messageElement.remove();
    });
});

/**
 * Example usage:
 * 
 * // Show a success toast
 * toast.success('Profile updated successfully!');
 * 
 * // Show an error toast
 * toast.error('An error occurred. Please try again.');
 * 
 * // Show a warning toast
 * toast.warning('Your session will expire soon.');
 * 
 * // Show an info toast
 * toast.info('New features are available!');
 * 
 * // Show a custom toast with specific duration
 * toast.show('Custom message', 'success', 3000);
 * 
 * // Show a toast that doesn't auto-dismiss
 * toast.show('Important message', 'error', 0);
 * 
 * // Dismiss all toasts
 * toast.dismissAll();
 */

