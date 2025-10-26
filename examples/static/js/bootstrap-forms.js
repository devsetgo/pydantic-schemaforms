/**
 * Bootstrap Forms JavaScript
 * Enhanced form functionality for Pydantic Forms Demo
 */

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeFormValidation();
    initializeFormEnhancements();
    initializeRangeSliders();
    initializeFileInputs();
    initializeFormSubmission();
});

/**
 * Initialize Bootstrap form validation
 */
function initializeFormValidation() {
    // Get all forms with validation
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                    
                    // Scroll to the field if needed
                    firstInvalid.scrollIntoView({
                        behavior: 'smooth',
                        block: 'center'
                    });
                }
            }
            
            form.classList.add('was-validated');
        }, false);
        
        // Real-time validation on input
        const inputs = form.querySelectorAll('input, select, textarea');
        inputs.forEach(function(input) {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                // Clear invalid state when user starts typing
                if (this.classList.contains('is-invalid')) {
                    this.classList.remove('is-invalid');
                    this.classList.add('is-valid');
                }
            });
        });
    });
}

/**
 * Validate individual field
 */
function validateField(field) {
    if (field.checkValidity()) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
    }
}

/**
 * Enhanced form interactions
 */
function initializeFormEnhancements() {
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(function(textarea) {
        textarea.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    });
    
    // Enhanced focus states
    const formControls = document.querySelectorAll('.form-control, .form-select');
    formControls.forEach(function(control) {
        control.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        control.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
    
    // Password visibility toggle
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(function(input) {
        addPasswordToggle(input);
    });
}

/**
 * Add password visibility toggle
 */
function addPasswordToggle(passwordInput) {
    const wrapper = document.createElement('div');
    wrapper.className = 'input-group';
    
    passwordInput.parentNode.insertBefore(wrapper, passwordInput);
    wrapper.appendChild(passwordInput);
    
    const toggleButton = document.createElement('button');
    toggleButton.className = 'btn btn-outline-secondary';
    toggleButton.type = 'button';
    toggleButton.innerHTML = '<i class="bi bi-eye"></i>';
    toggleButton.setAttribute('aria-label', 'Toggle password visibility');
    
    const buttonWrapper = document.createElement('span');
    buttonWrapper.className = 'input-group-text';
    buttonWrapper.appendChild(toggleButton);
    wrapper.appendChild(buttonWrapper);
    
    toggleButton.addEventListener('click', function() {
        const type = passwordInput.type === 'password' ? 'text' : 'password';
        passwordInput.type = type;
        
        const icon = toggleButton.querySelector('i');
        icon.className = type === 'password' ? 'bi bi-eye' : 'bi bi-eye-slash';
    });
}

/**
 * Initialize range sliders with value display
 */
function initializeRangeSliders() {
    const rangeInputs = document.querySelectorAll('input[type="range"]');
    
    rangeInputs.forEach(function(range) {
        // Update value display in real-time
        range.addEventListener('input', function() {
            const valueDisplay = document.getElementById(this.id + '_value');
            if (valueDisplay) {
                valueDisplay.textContent = this.value;
            }
            
            // Update progress bar effect
            const progress = ((this.value - this.min) / (this.max - this.min)) * 100;
            this.style.background = `linear-gradient(to right, var(--bs-primary) 0%, var(--bs-primary) ${progress}%, #dee2e6 ${progress}%, #dee2e6 100%)`;
        });
        
        // Trigger initial update
        range.dispatchEvent(new Event('input'));
    });
}

/**
 * Enhanced file input functionality
 */
function initializeFileInputs() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(function(input) {
        input.addEventListener('change', function() {
            const files = this.files;
            const label = this.parentElement.querySelector('.form-label');
            
            if (files.length > 0) {
                const fileNames = Array.from(files).map(file => file.name).join(', ');
                
                // Create or update file list display
                let fileList = this.parentElement.querySelector('.file-list');
                if (!fileList) {
                    fileList = document.createElement('div');
                    fileList.className = 'file-list mt-2';
                    this.parentElement.appendChild(fileList);
                }
                
                fileList.innerHTML = `
                    <div class="alert alert-info alert-sm">
                        <i class="bi bi-file-earmark"></i> 
                        Selected: ${fileNames}
                    </div>
                `;
            }
        });
        
        // Drag and drop enhancement
        addDragDropToFileInput(input);
    });
}

/**
 * Add drag and drop functionality to file inputs
 */
function addDragDropToFileInput(fileInput) {
    const dropZone = document.createElement('div');
    dropZone.className = 'file-drop-zone';
    dropZone.innerHTML = `
        <div class="text-center p-4 border-2 border-dashed rounded">
            <i class="bi bi-cloud-upload fs-1 text-muted"></i>
            <p class="mb-2">Drag files here or click to browse</p>
            <p class="small text-muted">Supported formats: ${fileInput.accept || 'All files'}</p>
        </div>
    `;
    
    fileInput.parentNode.insertBefore(dropZone, fileInput);
    fileInput.style.display = 'none';
    
    // Handle click to open file dialog
    dropZone.addEventListener('click', function() {
        fileInput.click();
    });
    
    // Handle drag and drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropZone.classList.add('drag-over');
    }
    
    function unhighlight() {
        dropZone.classList.remove('drag-over');
    }
    
    dropZone.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        fileInput.dispatchEvent(new Event('change'));
    }
}

/**
 * Form submission handling with loading states
 */
function initializeFormSubmission() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(function(form) {
        form.addEventListener('submit', function(event) {
            const submitButton = form.querySelector('button[type="submit"]');
            
            if (submitButton && form.checkValidity()) {
                // Add loading state
                const originalContent = submitButton.innerHTML;
                submitButton.innerHTML = '<i class="bi bi-hourglass-split"></i> Processing...';
                submitButton.disabled = true;
                
                // Re-enable after a timeout (in case form doesn't redirect)
                setTimeout(function() {
                    submitButton.innerHTML = originalContent;
                    submitButton.disabled = false;
                }, 5000);
            }
        });
    });
}

/**
 * Utility function to show toast notifications
 */
function showToast(message, type = 'info') {
    const toastContainer = getOrCreateToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast element after it's hidden
    toast.addEventListener('hidden.bs.toast', function() {
        toast.remove();
    });
}

/**
 * Get or create toast container
 */
function getOrCreateToastContainer() {
    let container = document.getElementById('toast-container');
    
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '1055';
        document.body.appendChild(container);
    }
    
    return container;
}

/**
 * Form field validation helpers
 */
const ValidationHelpers = {
    /**
     * Validate email format
     */
    isValidEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },
    
    /**
     * Validate phone number
     */
    isValidPhone: function(phone) {
        const phoneRegex = /^[\+]?[\d\s\-\(\)]{10,}$/;
        return phoneRegex.test(phone);
    },
    
    /**
     * Validate URL format
     */
    isValidUrl: function(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    },
    
    /**
     * Check password strength
     */
    checkPasswordStrength: function(password) {
        const checks = {
            length: password.length >= 8,
            lowercase: /[a-z]/.test(password),
            uppercase: /[A-Z]/.test(password),
            number: /\d/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };
        
        const score = Object.values(checks).filter(Boolean).length;
        
        return {
            score: score,
            strength: score < 2 ? 'weak' : score < 4 ? 'medium' : 'strong',
            checks: checks
        };
    }
};

// Export for use in other scripts
window.PydanticForms = {
    showToast: showToast,
    ValidationHelpers: ValidationHelpers
};