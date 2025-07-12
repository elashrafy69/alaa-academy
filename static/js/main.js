/**
 * JavaScript متقدم لأكاديمية علاء عبد الحميد
 * يتضمن تفاعلات متقدمة وتحسينات للأداء
 */

// ===== Utility Functions =====
const Utils = {
    // Debounce function for performance
    debounce: function(func, wait, immediate) {
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
    },

    // Throttle function
    throttle: function(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Check if element is in viewport
    isInViewport: function(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    },

    // Smooth scroll to element
    scrollToElement: function(element, offset = 0) {
        const elementPosition = element.getBoundingClientRect().top;
        const offsetPosition = elementPosition + window.pageYOffset - offset;

        window.scrollTo({
            top: offsetPosition,
            behavior: 'smooth'
        });
    },

    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Get CSRF token
    getCSRFToken: function() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    },

    // Show notification
    showNotification: function(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas fa-${this.getNotificationIcon(type)} me-2"></i>
                <span>${message}</span>
                <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
        `;

        // Add to page
        let container = document.querySelector('.notifications-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'notifications-container';
            document.body.appendChild(container);
        }
        container.appendChild(notification);

        // Auto remove
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, duration);
    },

    getNotificationIcon: function(type) {
        const icons = {
            'success': 'check-circle',
            'error': 'exclamation-triangle',
            'warning': 'exclamation-circle',
            'info': 'info-circle'
        };
        return icons[type] || 'info-circle';
    }
};

// ===== Main Application Class =====
class AcademyApp {
    constructor() {
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.initializeComponents();
        this.setupLazyLoading();
        this.setupScrollEffects();
        this.setupFormValidation();
        this.setupSearchFunctionality();
    }

    setupEventListeners() {
        // DOM Content Loaded
        document.addEventListener('DOMContentLoaded', () => {
            this.onDOMReady();
        });

        // Window events
        window.addEventListener('scroll', Utils.throttle(() => {
            this.onScroll();
        }, 100));

        window.addEventListener('resize', Utils.debounce(() => {
            this.onResize();
        }, 250));

        // Navigation toggle for mobile
        const navToggle = document.querySelector('.navbar-toggle');
        if (navToggle) {
            navToggle.addEventListener('click', () => {
                this.toggleMobileNav();
            });
        }
    }

    onDOMReady() {
        // Initialize tooltips
        this.initTooltips();
        
        // Initialize modals
        this.initModals();
        
        // Initialize progress bars
        this.initProgressBars();
        
        // Initialize counters
        this.initCounters();
        
        // Setup theme toggle
        this.setupThemeToggle();
    }

    onScroll() {
        // Update navbar on scroll
        this.updateNavbarOnScroll();
        
        // Trigger animations for elements in viewport
        this.triggerViewportAnimations();
        
        // Update reading progress
        this.updateReadingProgress();
    }

    onResize() {
        // Recalculate layouts
        this.recalculateLayouts();
    }

    // ===== Component Initialization =====
    initializeComponents() {
        // Initialize course cards
        this.initCourseCards();
        
        // Initialize video players
        this.initVideoPlayers();
        
        // Initialize file uploads
        this.initFileUploads();
        
        // Initialize charts
        this.initCharts();
    }

    initCourseCards() {
        const courseCards = document.querySelectorAll('.course-card');
        courseCards.forEach(card => {
            // Add hover effects
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-5px)';
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
            });
            
            // Add click tracking
            card.addEventListener('click', (e) => {
                if (!e.target.closest('a, button')) {
                    const link = card.querySelector('.course-link');
                    if (link) {
                        window.location.href = link.href;
                    }
                }
            });
        });
    }

    initVideoPlayers() {
        const videoContainers = document.querySelectorAll('.video-container');
        videoContainers.forEach(container => {
            const video = container.querySelector('video');
            if (video) {
                // Add custom controls
                this.addVideoControls(video);
                
                // Track progress
                video.addEventListener('timeupdate', () => {
                    this.updateVideoProgress(video);
                });
            }
        });
    }

    initFileUploads() {
        const uploadAreas = document.querySelectorAll('.file-upload-area');
        uploadAreas.forEach(area => {
            this.setupDragAndDrop(area);
        });
    }

    // ===== Lazy Loading =====
    setupLazyLoading() {
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                });
            });

            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });
        }
    }

    // ===== Scroll Effects =====
    setupScrollEffects() {
        const animatedElements = document.querySelectorAll('.animate-on-scroll');
        
        if ('IntersectionObserver' in window) {
            const animationObserver = new IntersectionObserver((entries) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        entry.target.classList.add('animated');
                    }
                });
            }, {
                threshold: 0.1
            });

            animatedElements.forEach(el => {
                animationObserver.observe(el);
            });
        }
    }

    updateNavbarOnScroll() {
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            if (window.scrollY > 100) {
                navbar.classList.add('navbar-scrolled');
            } else {
                navbar.classList.remove('navbar-scrolled');
            }
        }
    }

    // ===== Form Validation =====
    setupFormValidation() {
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });

            // Real-time validation
            const inputs = form.querySelectorAll('input, textarea, select');
            inputs.forEach(input => {
                input.addEventListener('blur', () => {
                    this.validateField(input);
                });
            });
        });
    }

    validateForm(form) {
        let isValid = true;
        const inputs = form.querySelectorAll('input[required], textarea[required], select[required]');
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isValid = false;
            }
        });

        return isValid;
    }

    validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        let isValid = true;
        let message = '';

        // Required validation
        if (field.hasAttribute('required') && !value) {
            isValid = false;
            message = 'هذا الحقل مطلوب';
        }

        // Email validation
        if (type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                message = 'يرجى إدخال بريد إلكتروني صحيح';
            }
        }

        // Password validation
        if (type === 'password' && value) {
            if (value.length < 8) {
                isValid = false;
                message = 'كلمة المرور يجب أن تكون 8 أحرف على الأقل';
            }
        }

        // Update field appearance
        this.updateFieldValidation(field, isValid, message);
        return isValid;
    }

    updateFieldValidation(field, isValid, message) {
        const container = field.closest('.form-group') || field.parentElement;
        const feedback = container.querySelector('.invalid-feedback') || 
                        this.createFeedbackElement(container);

        if (isValid) {
            field.classList.remove('is-invalid');
            field.classList.add('is-valid');
            feedback.style.display = 'none';
        } else {
            field.classList.remove('is-valid');
            field.classList.add('is-invalid');
            feedback.textContent = message;
            feedback.style.display = 'block';
        }
    }

    createFeedbackElement(container) {
        const feedback = document.createElement('div');
        feedback.className = 'invalid-feedback';
        container.appendChild(feedback);
        return feedback;
    }

    // ===== Search Functionality =====
    setupSearchFunctionality() {
        const searchInputs = document.querySelectorAll('.search-input');
        searchInputs.forEach(input => {
            input.addEventListener('input', Utils.debounce((e) => {
                this.performSearch(e.target.value, e.target.dataset.searchTarget);
            }, 300));
        });
    }

    performSearch(query, target) {
        if (!query.trim()) {
            this.clearSearchResults(target);
            return;
        }

        // Show loading
        this.showSearchLoading(target);

        // Perform search (implement based on your needs)
        fetch(`/api/search/?q=${encodeURIComponent(query)}&target=${target}`)
            .then(response => response.json())
            .then(data => {
                this.displaySearchResults(data, target);
            })
            .catch(error => {
                console.error('Search error:', error);
                this.showSearchError(target);
            });
    }

    // ===== Theme Toggle =====
    setupThemeToggle() {
        const themeToggle = document.querySelector('.theme-toggle');
        if (themeToggle) {
            themeToggle.addEventListener('click', () => {
                this.toggleTheme();
            });
        }

        // Load saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-theme', savedTheme);
        }
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
    }

    // ===== Progress Tracking =====
    updateVideoProgress(video) {
        const progress = (video.currentTime / video.duration) * 100;
        const progressBar = video.closest('.video-container')?.querySelector('.progress-bar');
        
        if (progressBar) {
            progressBar.style.width = progress + '%';
        }

        // Save progress to server
        this.saveVideoProgress(video.dataset.contentId, video.currentTime);
    }

    saveVideoProgress(contentId, position) {
        if (!contentId) return;

        fetch('/api/save-progress/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': Utils.getCSRFToken()
            },
            body: JSON.stringify({
                content_id: contentId,
                position: position
            })
        }).catch(error => {
            console.error('Error saving progress:', error);
        });
    }
}

// ===== Initialize Application =====
const app = new AcademyApp();

// ===== Global Functions =====
window.showNotification = Utils.showNotification;
window.scrollToElement = Utils.scrollToElement;
