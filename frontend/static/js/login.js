// Login Page Authentication Manager
class LoginManager {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        // Always show login form - don't auto-redirect authenticated users
    }
    
    setupEventListeners() {
        // Login form
        const loginForm = document.getElementById('loginFormElement');
        if (loginForm) {
            loginForm.addEventListener('submit', (e) => this.handleLogin(e));
        }
        
        // Register form
        const registerForm = document.getElementById('registerFormElement');
        if (registerForm) {
            registerForm.addEventListener('submit', (e) => this.handleRegister(e));
        }

        // Admin register form
        const adminRegisterForm = document.getElementById('adminRegisterFormElement');
        if (adminRegisterForm) {
            adminRegisterForm.addEventListener('submit', (e) => this.handleAdminRegister(e));
        }
        
        // Toggle between login and register
        const showRegister = document.getElementById('showRegister');
        if (showRegister) {
            showRegister.addEventListener('click', (e) => {
                e.preventDefault();
                this.showRegisterForm();
            });
        }
        
        const showLogin = document.getElementById('showLogin');
        if (showLogin) {
            showLogin.addEventListener('click', (e) => {
                e.preventDefault();
                this.showLoginForm();
            });
        }

        // Admin registration toggle
        const showAdminRegister = document.getElementById('showAdminRegister');
        if (showAdminRegister) {
            showAdminRegister.addEventListener('click', (e) => {
                e.preventDefault();
                this.showAdminRegisterForm();
            });
        }

        const showLoginFromAdmin = document.getElementById('showLoginFromAdmin');
        if (showLoginFromAdmin) {
            showLoginFromAdmin.addEventListener('click', (e) => {
                e.preventDefault();
                this.showLoginForm();
            });
        }

        const showRegularRegister = document.getElementById('showRegularRegister');
        if (showRegularRegister) {
            showRegularRegister.addEventListener('click', (e) => {
                e.preventDefault();
                this.showRegisterForm();
            });
        }
    }
    
    
    async handleLogin(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const loginData = {
            email: formData.get('email'),
            password: formData.get('password')
        };
        
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(loginData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Welcome back!', 'success');
                // Redirect to main app
                setTimeout(() => {
                    window.location.href = '/app';
                }, 1000);
            } else {
                this.showToast(data.error || 'Login failed', 'error');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showToast('Network error. Please try again.', 'error');
        }
    }
    
    async handleRegister(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');
        
        // Validate password strength
        const passwordValidation = this.validatePassword(password);
        if (!passwordValidation.valid) {
            this.showToast(passwordValidation.message, 'error');
            return;
        }
        
        if (password !== confirmPassword) {
            this.showToast('Passwords do not match', 'error');
            return;
        }
        
        const registerData = {
            name: formData.get('name'),
            email: formData.get('email'),
            password: password
        };
        
        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(registerData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Account created successfully!', 'success');
                // Redirect to main app
                setTimeout(() => {
                    window.location.href = '/app';
                }, 1000);
            } else {
                this.showToast(data.error || 'Registration failed', 'error');
            }
        } catch (error) {
            console.error('Registration error:', error);
            this.showToast('Network error. Please try again.', 'error');
        }
    }
    
    async handleAdminRegister(e) {
        e.preventDefault();
        
        const formData = new FormData(e.target);
        const password = formData.get('password');
        const confirmPassword = formData.get('confirmPassword');
        const adminKey = formData.get('adminKey');
        
        // Validate password strength
        const passwordValidation = this.validatePassword(password);
        if (!passwordValidation.valid) {
            this.showToast(passwordValidation.message, 'error');
            return;
        }
        
        if (password !== confirmPassword) {
            this.showToast('Passwords do not match', 'error');
            return;
        }

        if (!adminKey.trim()) {
            this.showToast('Admin registration key is required', 'error');
            return;
        }
        
        const adminRegisterData = {
            name: formData.get('name'),
            email: formData.get('email'),
            password: password,
            admin_key: adminKey
        };
        
        try {
            const response = await fetch('/api/auth/register-admin', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                credentials: 'include',
                body: JSON.stringify(adminRegisterData)
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showToast('Admin account created successfully!', 'success');
                // Redirect to main app
                setTimeout(() => {
                    window.location.href = '/app';
                }, 1000);
            } else {
                this.showToast(data.error || 'Admin registration failed', 'error');
            }
        } catch (error) {
            console.error('Admin registration error:', error);
            this.showToast('Network error. Please try again.', 'error');
        }
    }
    
    showLoginForm() {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const adminRegisterForm = document.getElementById('adminRegisterForm');
        const loginTitle = document.getElementById('loginTitle');
        const loginSubtitle = document.getElementById('loginSubtitle');
        
        if (loginForm) loginForm.style.display = 'block';
        if (registerForm) registerForm.style.display = 'none';
        if (adminRegisterForm) adminRegisterForm.style.display = 'none';
        if (loginTitle) loginTitle.textContent = 'Welcome Back';
        if (loginSubtitle) loginSubtitle.textContent = 'Please sign in to continue';
        
        // Clear forms
        const loginFormElement = document.getElementById('loginFormElement');
        if (loginFormElement) loginFormElement.reset();
    }
    
    showRegisterForm() {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const adminRegisterForm = document.getElementById('adminRegisterForm');
        const loginTitle = document.getElementById('loginTitle');
        const loginSubtitle = document.getElementById('loginSubtitle');
        
        if (loginForm) loginForm.style.display = 'none';
        if (registerForm) registerForm.style.display = 'block';
        if (adminRegisterForm) adminRegisterForm.style.display = 'none';
        if (loginTitle) loginTitle.textContent = 'Join AMMINA';
        if (loginSubtitle) loginSubtitle.textContent = 'Create your account to get started';
        
        // Clear forms
        const registerFormElement = document.getElementById('registerFormElement');
        if (registerFormElement) registerFormElement.reset();
    }

    showAdminRegisterForm() {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const adminRegisterForm = document.getElementById('adminRegisterForm');
        const loginTitle = document.getElementById('loginTitle');
        const loginSubtitle = document.getElementById('loginSubtitle');
        
        if (loginForm) loginForm.style.display = 'none';
        if (registerForm) registerForm.style.display = 'none';
        if (adminRegisterForm) adminRegisterForm.style.display = 'block';
        if (loginTitle) loginTitle.textContent = 'Admin Registration';
        if (loginSubtitle) loginSubtitle.textContent = 'Create an admin account with special privileges';
        
        // Clear forms
        const adminRegisterFormElement = document.getElementById('adminRegisterFormElement');
        if (adminRegisterFormElement) adminRegisterFormElement.reset();
    }
    
    validatePassword(password) {
        const rules = {
            minLength: password.length >= 8,
            hasUppercase: /[A-Z]/.test(password),
            hasLowercase: /[a-z]/.test(password),
            hasNumber: /\d/.test(password),
            hasSpecial: /[!@#$%^&*(),.?":{}|<>]/.test(password)
        };
        
        if (!rules.minLength) {
            return { valid: false, message: 'Password must be at least 8 characters long' };
        }
        if (!rules.hasUppercase) {
            return { valid: false, message: 'Password must contain at least one uppercase letter' };
        }
        if (!rules.hasLowercase) {
            return { valid: false, message: 'Password must contain at least one lowercase letter' };
        }
        if (!rules.hasNumber) {
            return { valid: false, message: 'Password must contain at least one number' };
        }
        if (!rules.hasSpecial) {
            return { valid: false, message: 'Password must contain at least one special character (!@#$%^&*)' };
        }
        
        return { valid: true, message: 'Password is strong' };
    }
    
    showToast(message, type = 'info') {
        if (window.showToast) {
            window.showToast(message, type);
        } else {
            // Enhanced fallback with better error display
            console.log(`${type.toUpperCase()}: ${message}`);
            
            // Create a temporary toast-like element
            const toast = document.createElement('div');
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 1rem 1.5rem;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                z-index: 9999;
                animation: slideIn 0.3s ease;
                max-width: 300px;
                word-wrap: break-word;
            `;
            
            if (type === 'error') {
                toast.style.background = '#ef4444';
            } else if (type === 'success') {
                toast.style.background = '#10b981';
            } else {
                toast.style.background = '#6b7280';
            }
            
            toast.textContent = message;
            document.body.appendChild(toast);
            
            // Remove after 4 seconds
            setTimeout(() => {
                toast.remove();
            }, 4000);
        }
    }
}

// Initialize login manager when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new LoginManager();
});