// AWS SAA Exam App - Main JavaScript

// Global App Object
window.ExamApp = {
    // Global state
    state: {
        currentSession: null,
        currentQuestion: null,
        autoSave: true,
        notifications: true
    },

    // Initialize app
    init() {
        this.setupEventListeners();
        this.setupHTMXHandlers();
        this.setupKeyboardShortcuts();
        this.setupAutoSave();
        this.setupNotifications();
    },

    // Setup event listeners
    setupEventListeners() {
        // File upload validation
        document.addEventListener('change', (e) => {
            if (e.target.type === 'file' && e.target.accept.includes('pdf')) {
                this.validateFileUpload(e.target);
            }
        });

        // Form submission handling
        document.addEventListener('submit', (e) => {
            if (e.target.classList.contains('exam-form')) {
                this.handleFormSubmission(e);
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            this.handleKeyboardShortcuts(e);
        });
    },

    // Setup HTMX handlers
    setupHTMXHandlers() {
        // Before request
        document.body.addEventListener('htmx:beforeRequest', (e) => {
            this.showLoading(e.detail.elt);
        });

        // After request
        document.body.addEventListener('htmx:afterRequest', (e) => {
            this.hideLoading(e.detail.elt);
            
            if (e.detail.successful) {
                this.showNotification('작업이 성공적으로 완료되었습니다.', 'success');
            } else {
                this.showNotification('오류가 발생했습니다.', 'error');
            }
        });

        // Response error
        document.body.addEventListener('htmx:responseError', (e) => {
            this.showNotification('서버 오류가 발생했습니다.', 'error');
        });
    },

    // Setup keyboard shortcuts
    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Ctrl/Cmd + S: Save
            if ((e.ctrlKey || e.metaKey) && e.key === 's') {
                e.preventDefault();
                this.saveCurrentResponse();
            }

            // Ctrl/Cmd + Enter: Submit
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                this.submitExam();
            }

            // Arrow keys for navigation
            if (e.key === 'ArrowLeft') {
                this.navigateToPrevious();
            } else if (e.key === 'ArrowRight') {
                this.navigateToNext();
            }

            // Number keys for choice selection
            if (e.key >= '1' && e.key <= '4') {
                this.selectChoice(parseInt(e.key));
            }
        });
    },

    // Setup auto save
    setupAutoSave() {
        if (this.state.autoSave) {
            setInterval(() => {
                this.autoSave();
            }, 30000); // Auto save every 30 seconds
        }
    },

    // Setup notifications
    setupNotifications() {
        if (this.state.notifications && 'Notification' in window) {
            Notification.requestPermission();
        }
    },

    // File upload validation
    validateFileUpload(input) {
        const file = input.files[0];
        if (file) {
            // Check file type
            if (!file.type.includes('pdf')) {
                this.showNotification('PDF 파일만 업로드 가능합니다.', 'error');
                input.value = '';
                return false;
            }

            // Check file size (max 50MB)
            if (file.size > 50 * 1024 * 1024) {
                this.showNotification('파일 크기는 50MB 이하여야 합니다.', 'error');
                input.value = '';
                return false;
            }

            this.showNotification('파일이 선택되었습니다.', 'success');
            return true;
        }
        return false;
    },

    // Handle form submission
    handleFormSubmission(e) {
        const form = e.target;
        const submitButton = form.querySelector('button[type="submit"]');
        
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.innerHTML = '<svg class="animate-spin h-4 w-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>처리 중...';
        }
    },

    // Handle keyboard shortcuts
    handleKeyboardShortcuts(e) {
        // Prevent shortcuts in input fields
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }

        // Navigation shortcuts
        switch (e.key) {
            case 'ArrowLeft':
                e.preventDefault();
                this.navigateToPrevious();
                break;
            case 'ArrowRight':
                e.preventDefault();
                this.navigateToNext();
                break;
            case '1':
            case '2':
            case '3':
            case '4':
                e.preventDefault();
                this.selectChoice(parseInt(e.key));
                break;
        }
    },

    // Save current response
    saveCurrentResponse() {
        const form = document.querySelector('form[data-save-response]');
        if (form) {
            const formData = new FormData(form);
            fetch(form.action, {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    this.showNotification('응답이 저장되었습니다.', 'success');
                } else {
                    this.showNotification('저장 중 오류가 발생했습니다.', 'error');
                }
            })
            .catch(error => {
                console.error('Save error:', error);
                this.showNotification('저장 중 오류가 발생했습니다.', 'error');
            });
        }
    },

    // Auto save
    autoSave() {
        if (this.state.currentSession && this.state.currentQuestion) {
            this.saveCurrentResponse();
        }
    },

    // Navigate to previous question
    navigateToPrevious() {
        const prevButton = document.querySelector('[data-navigate="prev"]');
        if (prevButton && !prevButton.disabled) {
            prevButton.click();
        }
    },

    // Navigate to next question
    navigateToNext() {
        const nextButton = document.querySelector('[data-navigate="next"]');
        if (nextButton && !nextButton.disabled) {
            nextButton.click();
        }
    },

    // Select choice by number
    selectChoice(choiceNumber) {
        const choices = document.querySelectorAll('input[name="choice"]');
        if (choices[choiceNumber - 1]) {
            choices[choiceNumber - 1].checked = true;
            choices[choiceNumber - 1].dispatchEvent(new Event('change'));
        }
    },

    // Submit exam
    submitExam() {
        if (confirm('정말로 시험을 제출하시겠습니까?')) {
            const submitForm = document.querySelector('form[data-submit-exam]');
            if (submitForm) {
                submitForm.submit();
            }
        }
    },

    // Show loading state
    showLoading(element) {
        if (element) {
            element.classList.add('loading');
            element.disabled = true;
        }
    },

    // Hide loading state
    hideLoading(element) {
        if (element) {
            element.classList.remove('loading');
            element.disabled = false;
        }
    },

    // Show notification
    showNotification(message, type = 'info') {
        if (!this.state.notifications) return;

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `fixed top-4 right-4 z-50 p-4 rounded-lg shadow-lg transition-all duration-300 transform translate-x-full`;
        
        // Set notification styles based on type
        switch (type) {
            case 'success':
                notification.classList.add('bg-green-500', 'text-white');
                break;
            case 'error':
                notification.classList.add('bg-red-500', 'text-white');
                break;
            case 'warning':
                notification.classList.add('bg-yellow-500', 'text-white');
                break;
            default:
                notification.classList.add('bg-blue-500', 'text-white');
        }

        notification.innerHTML = `
            <div class="flex items-center">
                <span class="mr-2">${this.getNotificationIcon(type)}</span>
                <span>${message}</span>
                <button onclick="this.parentElement.parentElement.remove()" class="ml-4 text-white hover:text-gray-200">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                    </svg>
                </button>
            </div>
        `;

        // Add to page
        document.body.appendChild(notification);

        // Animate in
        setTimeout(() => {
            notification.classList.remove('translate-x-full');
        }, 100);

        // Auto remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('translate-x-full');
            setTimeout(() => {
                if (notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, 5000);

        // Browser notification
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification('AWS SAA 시험 앱', {
                body: message,
                icon: '/static/images/icon.png'
            });
        }
    },

    // Get notification icon
    getNotificationIcon(type) {
        switch (type) {
            case 'success':
                return '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>';
            case 'error':
                return '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';
            case 'warning':
                return '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"></path></svg>';
            default:
                return '<svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>';
        }
    },

    // Utility functions
    formatTime(seconds) {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = seconds % 60;
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    },

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    debounce(func, wait) {
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
};

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.ExamApp.init();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.ExamApp;
}
