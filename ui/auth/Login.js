/**
 * Login Component
 * @module auth/Login
 */

import { login, register } from '../api/client.js';
import { setUser, initAuthState } from './state.js';
import { showToast } from '../components/toast.js';
import { navigateTo } from '../router.js';

/**
 * Render login/register form
 * @param {HTMLElement} container
 */
export function renderLoginForm(container) {
    let isLoginMode = true;
    
    function render() {
        container.innerHTML = `
            <div class="auth-container">
                <form class="auth-form" id="auth-form">
                    <h1>${isLoginMode ? '🎙️ Voice Journal' : 'Create Account'}</h1>
                    
                    <div class="form-group">
                        <label for="email">Email</label>
                        <input 
                            type="email" 
                            id="email" 
                            name="email" 
                            placeholder="your@email.com"
                            required
                            autocomplete="email"
                        >
                    </div>
                    
                    <div class="form-group">
                        <label for="password">Password</label>
                        <input 
                            type="password" 
                            id="password" 
                            name="password" 
                            placeholder="••••••••"
                            required
                            minlength="8"
                            autocomplete="${isLoginMode ? 'current-password' : 'new-password'}"
                        >
                    </div>
                    
                    ${!isLoginMode ? `
                        <div class="form-group">
                            <label for="confirm-password">Confirm Password</label>
                            <input 
                                type="password" 
                                id="confirm-password" 
                                name="confirm-password" 
                                placeholder="••••••••"
                                required
                                minlength="8"
                                autocomplete="new-password"
                            >
                        </div>
                    ` : ''}
                    
                    <div id="form-error" class="error-message" style="display: none;"></div>
                    
                    <button type="submit" class="btn btn-primary" id="submit-btn">
                        ${isLoginMode ? 'Sign In' : 'Create Account'}
                    </button>
                    
                    <p class="text-center mt-20">
                        ${isLoginMode 
                            ? `Don't have an account? <span class="link" id="toggle-mode">Sign up</span>`
                            : `Already have an account? <span class="link" id="toggle-mode">Sign in</span>`
                        }
                    </p>
                </form>
            </div>
        `;
        
        setupEventHandlers();
    }
    
    function setupEventHandlers() {
        const form = document.getElementById('auth-form');
        const toggleBtn = document.getElementById('toggle-mode');
        
        form.addEventListener('submit', handleSubmit);
        toggleBtn.addEventListener('click', () => {
            isLoginMode = !isLoginMode;
            render();
        });
    }
    
    async function handleSubmit(e) {
        e.preventDefault();
        
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const errorEl = document.getElementById('form-error');
        const submitBtn = document.getElementById('submit-btn');
        
        // Validate confirm password for registration
        if (!isLoginMode) {
            const confirmPassword = document.getElementById('confirm-password').value;
            if (password !== confirmPassword) {
                errorEl.textContent = 'Passwords do not match';
                errorEl.style.display = 'block';
                return;
            }
        }
        
        // Disable submit button
        submitBtn.disabled = true;
        submitBtn.textContent = isLoginMode ? 'Signing in...' : 'Creating account...';
        errorEl.style.display = 'none';
        
        try {
            if (isLoginMode) {
                await login(email, password);
                await initAuthState();
                showToast('Welcome back!', 'success');
            } else {
                await register(email, password);
                // Auto-login after registration
                await login(email, password);
                await initAuthState();
                showToast('Account created successfully!', 'success');
            }
            
            navigateTo('/');
        } catch (error) {
            errorEl.textContent = error.message || 'An error occurred';
            errorEl.style.display = 'block';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = isLoginMode ? 'Sign In' : 'Create Account';
        }
    }
    
    render();
}
