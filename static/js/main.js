/* 
 * Main JavaScript for YourDoctorHere
 * Handles dynamic UI elements like Toast notifications for Django messages.
 */

document.addEventListener('DOMContentLoaded', () => {
    // Look for hidden message elements rendered by Django
    const messagesData = document.querySelectorAll('.django-message-data');
    
    messagesData.forEach(msg => {
        const type = msg.dataset.type; // e.g., 'success', 'error', 'info'
        const text = msg.innerText;
        showToast(type, text);
    });

    // Initialize password toggles
    initPasswordToggles();
});

function initPasswordToggles() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        // Wrap the input if it's not already wrapped
        if (!input.parentElement.classList.contains('password-wrapper')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'password-wrapper';
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(input);

            const toggleBtn = document.createElement('button');
            toggleBtn.type = 'button';
            toggleBtn.className = 'password-toggle';
            toggleBtn.innerHTML = '<span class="material-icons">visibility_off</span>';
            
            toggleBtn.addEventListener('click', () => {
                if (input.type === 'password') {
                    input.type = 'text';
                    toggleBtn.innerHTML = '<span class="material-icons">visibility</span>';
                } else {
                    input.type = 'password';
                    toggleBtn.innerHTML = '<span class="material-icons">visibility_off</span>';
                }
            });
            
            wrapper.appendChild(toggleBtn);
        }
    });
}

/**
 * Creates and displays a toast notification.
 * @param {string} type - The type of toast (success, error, warning, info)
 * @param {string} message - The message body
 */
function showToast(type, message) {
    // Ensure the toast container exists
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        document.body.appendChild(container);
    }

    // Map Django message tags to our CSS classes and Material icons
    let toastClass = 'toast-info';
    let icon = 'info'; // Default material icon name

    if (type.includes('success')) {
        toastClass = 'toast-success';
        icon = 'check_circle';
    } else if (type.includes('error')) {
        toastClass = 'toast-error';
        icon = 'error';
    } else if (type.includes('warning')) {
        toastClass = 'toast-warning';
        icon = 'warning';
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast ${toastClass}`;

    // Create inner HTML structure with icon and message
    toast.innerHTML = `
        <span class="material-icons">${icon}</span>
        <div style="flex-grow: 1;">${message}</div>
        <button class="toast-close" aria-label="Close">
            <span class="material-icons" style="font-size: 1rem;">close</span>
        </button>
    `;

    // Add to container
    container.appendChild(toast);

    // Setup close button functionality
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        hideToast(toast);
    });

    // Auto dismiss after 4 seconds
    setTimeout(() => {
        hideToast(toast);
    }, 4000);
}

/**
 * Handles the removal animation of a toast
 * @param {HTMLElement} toast - The toast element to hide
 */
function hideToast(toast) {
    if (!toast.classList.contains('hiding')) {
        toast.classList.add('hiding');
        // Wait for the animation to finish before removing from DOM
        setTimeout(() => {
            if (toast.parentElement) {
                toast.parentElement.removeChild(toast);
            }
        }, 300);
    }
}
