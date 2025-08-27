// Main JavaScript file for Zillow Property Manager

// Utility functions
function showLoading(element) {
    if (element) {
        element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
        element.disabled = true;
    }
}

function hideLoading(element, originalText) {
    if (element) {
        element.innerHTML = originalText;
        element.disabled = false;
    }
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the main container
    const container = document.querySelector('main .container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function formatPhoneNumber(phone) {
    if (!phone) return '';
    
    // Remove all non-digits
    const cleaned = phone.replace(/\D/g, '');
    
    // Format based on length
    if (cleaned.length === 10) {
        return `(${cleaned.slice(0,3)}) ${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
    } else if (cleaned.length === 11 && cleaned.startsWith('1')) {
        return `+1 (${cleaned.slice(1,4)}) ${cleaned.slice(4,7)}-${cleaned.slice(7)}`;
    }
    
    return phone;
}

function formatPrice(price) {
    if (!price) return '';
    
    // Remove non-numeric characters except decimal point
    const cleaned = price.replace(/[^\d.]/g, '');
    const num = parseFloat(cleaned);
    
    if (isNaN(num)) return price;
    
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    }).format(num);
}

function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// DataTable utilities
function initializeDataTable(tableId, options = {}) {
    const defaultOptions = {
        responsive: true,
        pageLength: 25,
        language: {
            search: "Search:",
            lengthMenu: "Show _MENU_ entries",
            info: "Showing _START_ to _END_ of _TOTAL_ entries",
            paginate: {
                first: "First",
                last: "Last",
                next: "Next",
                previous: "Previous"
            }
        },
        dom: '<"row"<"col-sm-12 col-md-6"l><"col-sm-12 col-md-6"f>>' +
             '<"row"<"col-sm-12"tr>>' +
             '<"row"<"col-sm-12 col-md-5"i><"col-sm-12 col-md-7"p>>'
    };
    
    return $(tableId).DataTable({
        ...defaultOptions,
        ...options
    });
}

// API utilities
async function apiCall(url, options = {}) {
    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        }
    };
    
    try {
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error('API call failed:', error);
        return { success: false, error: error.message };
    }
}

// Modal utilities
function showModal(modalId, content = null) {
    const modal = new bootstrap.Modal(document.getElementById(modalId));
    
    if (content) {
        const modalBody = document.querySelector(`#${modalId} .modal-body`);
        if (modalBody) {
            modalBody.innerHTML = content;
        }
    }
    
    modal.show();
    return modal;
}

function hideModal(modalId) {
    const modal = bootstrap.Modal.getInstance(document.getElementById(modalId));
    if (modal) {
        modal.hide();
    }
}

// Form utilities
function serializeForm(form) {
    const formData = new FormData(form);
    const data = {};
    
    for (let [key, value] of formData.entries()) {
        data[key] = value;
    }
    
    return data;
}

function validateForm(form) {
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    let isValid = true;
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            input.classList.add('is-invalid');
            isValid = false;
        } else {
            input.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Search and filter utilities
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function filterTable(table, searchTerm, columnIndex = null) {
    if (columnIndex !== null) {
        table.column(columnIndex).search(searchTerm).draw();
    } else {
        table.search(searchTerm).draw();
    }
}

// Export utilities
function exportToCSV(data, filename) {
    const csvContent = convertToCSV(data);
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
}

function convertToCSV(data) {
    if (!data || data.length === 0) return '';
    
    const headers = Object.keys(data[0]);
    const csvRows = [headers.join(',')];
    
    for (const row of data) {
        const values = headers.map(header => {
            const value = row[header];
            return `"${String(value).replace(/"/g, '""')}"`;
        });
        csvRows.push(values.join(','));
    }
    
    return csvRows.join('\n');
}

// Toast notification utilities
function showToast(message, type = 'info', duration = 5000) {
    // Create unique ID for the toast
    const toastId = 'toast-' + Date.now();
    
    // Create toast HTML
    const toastHTML = `
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'primary'} text-white">
                <i class="fas fa-${type === 'error' ? 'exclamation-triangle' : type === 'success' ? 'check-circle' : type === 'warning' ? 'exclamation-circle' : 'info-circle'} me-2"></i>
                <strong class="me-auto">${type.charAt(0).toUpperCase() + type.slice(1)}</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        </div>
    `;
    
    // Add toast to container
    const toastContainer = document.querySelector('.toast-container');
    if (toastContainer) {
        toastContainer.insertAdjacentHTML('beforeend', toastHTML);
        
        // Initialize and show the toast
        const toastElement = document.getElementById(toastId);
        const toast = new bootstrap.Toast(toastElement, {
            autohide: true,
            delay: duration
        });
        
        toast.show();
        
        // Remove toast element after it's hidden
        toastElement.addEventListener('hidden.bs.toast', function() {
            if (toastElement.parentNode) {
                toastElement.remove();
            }
        });
    }
}

// Convenience functions for different toast types
function showSuccessToast(message, duration = 5000) {
    showToast(message, 'success', duration);
}

function showErrorToast(message, duration = 5000) {
    showToast(message, 'error', duration);
}

function showWarningToast(message, duration = 5000) {
    showToast(message, 'warning', duration);
}

function showInfoToast(message, duration = 5000) {
    showToast(message, 'info', duration);
}

// Legacy function for backward compatibility
function showNotification(message, type = 'info', duration = 3000) {
    showToast(message, type, duration);
}

// Page utilities
function refreshPage() {
    window.location.reload();
}

function goToPage(url) {
    window.location.href = url;
}

function goBack() {
    window.history.back();
}

// Responsive utilities
function isMobile() {
    return window.innerWidth <= 768;
}

function isTablet() {
    return window.innerWidth > 768 && window.innerWidth <= 1024;
}

function isDesktop() {
    return window.innerWidth > 1024;
}

// Initialize common functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
    alerts.forEach(alert => {
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    });
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Add loading states to buttons with data-loading attribute
    const loadingButtons = document.querySelectorAll('[data-loading]');
    loadingButtons.forEach(button => {
        button.addEventListener('click', function() {
            const originalText = this.innerHTML;
            showLoading(this);
            
            // Re-enable after a delay (you can customize this)
            setTimeout(() => {
                hideLoading(this, originalText);
            }, 2000);
        });
    });
});

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    showErrorToast('An error occurred. Please try again.');
});

// Export functions to global scope for use in templates
window.ZillowManager = {
    showLoading,
    hideLoading,
    showAlert,
    formatPhoneNumber,
    formatPrice,
    formatDate,
    initializeDataTable,
    apiCall,
    showModal,
    hideModal,
    serializeForm,
    validateForm,
    debounce,
    filterTable,
    exportToCSV,
    showToast,
    showSuccessToast,
    showErrorToast,
    showWarningToast,
    showInfoToast,
    showNotification, // Legacy function
    refreshPage,
    goToPage,
    goBack,
    isMobile,
    isTablet,
    isDesktop
};
