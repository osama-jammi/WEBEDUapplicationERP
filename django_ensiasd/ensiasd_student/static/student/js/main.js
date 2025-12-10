/**
 * ENSIASD Student Portal - Main JavaScript
 * =========================================
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Auto-hide alerts after 5 seconds
    var alerts = document.querySelectorAll('.alert:not(.alert-info):not(.alert-warning)');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });
    
    // Form validation - NE PAS BLOQUER la soumission des formulaires valides
    var forms = document.querySelectorAll('form:not(.no-validation)');
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            // Seulement empêcher si le formulaire est invalide
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Loading state for buttons
    var submitButtons = document.querySelectorAll('button[type="submit"]');
    submitButtons.forEach(function(button) {
        var form = button.closest('form');
        if (form) {
            form.addEventListener('submit', function(e) {
                // Seulement si le formulaire est valide
                if (form.checkValidity()) {
                    button.disabled = true;
                    var originalText = button.innerHTML;
                    button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Chargement...';
                    
                    // Re-enable after 10 seconds (safety)
                    setTimeout(function() {
                        button.disabled = false;
                        button.innerHTML = originalText;
                    }, 10000);
                }
            });
        }
    });
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            var target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Confirmation dialogs
    var dangerButtons = document.querySelectorAll('[data-confirm]');
    dangerButtons.forEach(function(button) {
        button.addEventListener('click', function(event) {
            var message = button.dataset.confirm || 'Êtes-vous sûr?';
            if (!confirm(message)) {
                event.preventDefault();
            }
        });
    });
    
    // Print functionality
    var printButtons = document.querySelectorAll('[data-print]');
    printButtons.forEach(function(button) {
        button.addEventListener('click', function() {
            window.print();
        });
    });
    
    // Session timeout warning (23 hours)
    var sessionWarningShown = false;
    setTimeout(function() {
        if (!sessionWarningShown) {
            sessionWarningShown = true;
            alert('Votre session va expirer bientôt. Veuillez vous reconnecter.');
        }
    }, 23 * 60 * 60 * 1000);
    
});

/**
 * Utility functions
 */

// Format date to French locale
function formatDate(dateString) {
    var options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('fr-FR', options);
}

// Format number to French locale
function formatNumber(number, decimals = 2) {
    return number.toLocaleString('fr-FR', { 
        minimumFractionDigits: decimals, 
        maximumFractionDigits: decimals 
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    var toastContainer = document.getElementById('toast-container');
    if (!toastContainer) {
        toastContainer = document.createElement('div');
        toastContainer.id = 'toast-container';
        toastContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(toastContainer);
    }
    
    var toastId = 'toast-' + Date.now();
    var toastHTML = `
        <div id="${toastId}" class="toast align-items-center text-white bg-${type}" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    toastContainer.insertAdjacentHTML('beforeend', toastHTML);
    var toast = new bootstrap.Toast(document.getElementById(toastId));
    toast.show();
}

// AJAX helper
async function apiRequest(url, method = 'GET', data = null) {
    var options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        var response = await fetch(url, options);
        var result = await response.json();
        
        if (!response.ok) {
            throw new Error(result.error || 'Erreur serveur');
        }
        
        return result;
    } catch (error) {
        showToast(error.message, 'danger');
        throw error;
    }
}

// Get cookie by name
function getCookie(name) {
    var value = "; " + document.cookie;
    var parts = value.split("; " + name + "=");
    if (parts.length === 2) {
        return parts.pop().split(";").shift();
    }
    return null;
}

// Debounce function
function debounce(func, wait) {
    var timeout;
    return function executedFunction(...args) {
        var later = function() {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}