/**
 * Settings Page Component
 * @module settings/Settings
 */

import { getUser } from '../auth/state.js';
import { updateCurrentUser } from '../api/client.js';
import { showToast } from '../components/toast.js';
import { navigateTo } from '../router.js';

/**
 * Render settings page
 * @param {HTMLElement} container
 */
export function renderSettings(container) {
    const user = getUser();
    
    container.innerHTML = `
        <div style="max-width: 600px; margin: 0 auto;">
            <div style="display: flex; align-items: center; margin-bottom: 30px;">
                <button class="btn btn-secondary" id="back-btn" style="margin-right: 16px;">
                    ← Back
                </button>
                <h1>Settings</h1>
            </div>
            
            <div class="auth-form" style="max-width: 100%;">
                <h2>Account</h2>
                <p style="color: var(--color-text-secondary); margin-bottom: 20px;">
                    Email: ${user?.email || 'Unknown'}
                </p>
                
                <h2 style="margin-top: 30px;">Privacy</h2>
                
                <div class="form-group">
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer;">
                        <input 
                            type="checkbox" 
                            id="ai-opt-out"
                            style="width: 20px; height: 20px;"
                        >
                        <span>Opt out of AI processing</span>
                    </label>
                    <p style="color: var(--color-text-secondary); font-size: 13px; margin-top: 8px; margin-left: 32px;">
                        When enabled, your voice entries will only be stored without transcription or analysis.
                    </p>
                </div>
                
                <div class="form-group" style="margin-top: 20px;">
                    <label style="display: flex; align-items: center; gap: 12px; cursor: pointer;">
                        <input 
                            type="checkbox" 
                            id="local-storage-only"
                            style="width: 20px; height: 20px;"
                        >
                        <span>Local storage only (experimental)</span>
                    </label>
                    <p style="color: var(--color-text-secondary); font-size: 13px; margin-top: 8px; margin-left: 32px;">
                        Store recordings locally on your device only. This feature is experimental.
                    </p>
                </div>
                
                <h2 style="margin-top: 30px;">Data</h2>
                
                <button class="btn btn-secondary" id="export-btn" style="margin-bottom: 12px; width: 100%;">
                    📥 Export All Data
                </button>
                
                <button class="btn btn-danger" id="delete-account-btn" style="width: 100%;">
                    🗑️ Delete Account
                </button>
                <p style="color: var(--color-text-secondary); font-size: 13px; margin-top: 8px;">
                    This will permanently delete your account and all entries. This cannot be undone.
                </p>
            </div>
        </div>
    `;
    
    // Setup event handlers
    document.getElementById('back-btn').addEventListener('click', () => {
        navigateTo('/');
    });
    
    document.getElementById('export-btn').addEventListener('click', () => {
        showToast('Export feature coming soon', 'info');
    });
    
    document.getElementById('delete-account-btn').addEventListener('click', () => {
        if (confirm('Are you sure you want to delete your account? This cannot be undone.')) {
            if (confirm('This will permanently delete all your data. Are you absolutely sure?')) {
                showToast('Account deletion feature coming soon', 'info');
            }
        }
    });
    
    document.getElementById('ai-opt-out').addEventListener('change', (e) => {
        localStorage.setItem('ai_opt_out', e.target.checked);
        showToast(`AI processing ${e.target.checked ? 'disabled' : 'enabled'}`, 'info');
    });
    
    document.getElementById('local-storage-only').addEventListener('change', (e) => {
        localStorage.setItem('local_storage_only', e.target.checked);
        showToast(`Local storage ${e.target.checked ? 'enabled' : 'disabled'}`, 'info');
    });
    
    // Load saved preferences
    const aiOptOut = localStorage.getItem('ai_opt_out') === 'true';
    const localOnly = localStorage.getItem('local_storage_only') === 'true';
    
    document.getElementById('ai-opt-out').checked = aiOptOut;
    document.getElementById('local-storage-only').checked = localOnly;
}
