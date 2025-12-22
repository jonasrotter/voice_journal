/**
 * Header Component
 * @module components/Header
 */

import { logout } from '../api/client.js';
import { getUser } from '../auth/state.js';
import { navigateTo } from '../router.js';

/**
 * Render header
 * @param {HTMLElement} container
 */
export function renderHeader(container) {
    const user = getUser();
    
    container.innerHTML = `
        <header class="header">
            <h1>🎙️ Voice Journal</h1>
            <div class="user-menu">
                <span class="user-email">${user?.email || ''}</span>
                <button class="btn btn-secondary" id="settings-btn">
                    ⚙️
                </button>
                <button class="btn btn-secondary" id="logout-btn">
                    Logout
                </button>
            </div>
        </header>
    `;
    
    document.getElementById('logout-btn').addEventListener('click', () => {
        logout();
        navigateTo('/login');
    });
    
    document.getElementById('settings-btn').addEventListener('click', () => {
        navigateTo('/settings');
    });
}
