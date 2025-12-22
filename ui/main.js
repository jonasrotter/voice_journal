/**
 * Main Application Entry Point
 * @module main
 */

import { registerRoutes, initRouter, navigateTo, getCurrentPath } from './router.js';
import { initAuthState, subscribeAuthState, isLoggedIn, getUser } from './auth/state.js';
import { isAuthenticated } from './api/client.js';
import { renderLoginForm } from './auth/Login.js';
import { renderHeader } from './components/Header.js';
import { renderRecordingPanel } from './recording/RecordingPanel.js';
import { renderEntriesList, pollEntryUpdates } from './entries/EntriesList.js';
import { renderSettings } from './settings/Settings.js';
import { showToast } from './components/toast.js';

const app = document.getElementById('app');
let entriesList = null;
let stopPolling = null;

/**
 * Render home page (dashboard)
 */
function renderHomePage() {
    if (!isLoggedIn()) {
        navigateTo('/login');
        return;
    }
    
    app.innerHTML = `
        <div id="header-container"></div>
        <div id="recording-container"></div>
        <div id="entries-container"></div>
    `;
    
    // Render components
    renderHeader(document.getElementById('header-container'));
    
    renderRecordingPanel(
        document.getElementById('recording-container'),
        (newEntry) => {
            // Refresh entries when new one is created
            if (entriesList) {
                entriesList.refresh();
            }
        }
    );
    
    entriesList = renderEntriesList(document.getElementById('entries-container'));
    
    // Start polling for updates
    if (stopPolling) stopPolling();
    stopPolling = pollEntryUpdates((entries) => {
        // Check for any processing entries that completed
        // This is handled by the entries list internal state
    }, 5000);
}

/**
 * Render login page
 */
function renderLoginPage() {
    if (isLoggedIn()) {
        navigateTo('/');
        return;
    }
    
    // Stop polling if active
    if (stopPolling) {
        stopPolling();
        stopPolling = null;
    }
    
    renderLoginForm(app);
}

/**
 * Render settings page
 */
function renderSettingsPage() {
    if (!isLoggedIn()) {
        navigateTo('/login');
        return;
    }
    
    renderSettings(app);
}

/**
 * Initialize application
 */
async function init() {
    // Show loading state
    app.innerHTML = `
        <div class="loading" style="min-height: 100vh;">
            <div class="spinner"></div>
        </div>
    `;
    
    // Try to restore auth state
    const authenticated = await initAuthState();
    
    // Register routes
    registerRoutes({
        '/': renderHomePage,
        '/login': renderLoginPage,
        '/settings': renderSettingsPage,
        '*': () => {
            app.innerHTML = `
                <div class="empty-state" style="min-height: 80vh; display: flex; flex-direction: column; align-items: center; justify-content: center;">
                    <h1>404</h1>
                    <p>Page not found</p>
                    <button class="btn btn-primary" onclick="navigateTo('/')" style="margin-top: 20px;">
                        Go Home
                    </button>
                </div>
            `;
        }
    });
    
    // Subscribe to auth changes
    subscribeAuthState((user) => {
        if (!user && getCurrentPath() !== '/login') {
            navigateTo('/login');
        }
    });
    
    // Initialize router
    initRouter();
    
    // If not authenticated and not on login page, redirect
    if (!authenticated && getCurrentPath() !== '/login') {
        navigateTo('/login');
    }
}

// Start app
init().catch(error => {
    console.error('Failed to initialize app:', error);
    app.innerHTML = `
        <div class="empty-state" style="min-height: 80vh; display: flex; flex-direction: column; align-items: center; justify-content: center;">
            <h1>Error</h1>
            <p>Failed to load application</p>
            <button class="btn btn-primary" onclick="location.reload()" style="margin-top: 20px;">
                Retry
            </button>
        </div>
    `;
});

// Make navigateTo available globally for inline handlers
window.navigateTo = navigateTo;
