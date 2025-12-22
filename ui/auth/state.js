/**
 * Auth State Management
 * @module auth/state
 */

import { getCurrentUser, isAuthenticated, clearToken } from '../api/client.js';

let currentUser = null;
let authStateListeners = [];

/**
 * Subscribe to auth state changes
 * @param {Function} listener
 * @returns {Function} Unsubscribe function
 */
export function subscribeAuthState(listener) {
    authStateListeners.push(listener);
    return () => {
        authStateListeners = authStateListeners.filter(l => l !== listener);
    };
}

/**
 * Notify all listeners of auth state change
 */
function notifyListeners() {
    authStateListeners.forEach(listener => listener(currentUser));
}

/**
 * Get current user
 * @returns {import('../api/types').User|null}
 */
export function getUser() {
    return currentUser;
}

/**
 * Check if user is logged in
 * @returns {boolean}
 */
export function isLoggedIn() {
    return currentUser !== null;
}

/**
 * Initialize auth state from stored token
 * @returns {Promise<boolean>}
 */
export async function initAuthState() {
    if (!isAuthenticated()) {
        currentUser = null;
        notifyListeners();
        return false;
    }
    
    try {
        currentUser = await getCurrentUser();
        notifyListeners();
        return true;
    } catch (error) {
        console.error('Failed to fetch user:', error);
        clearToken();
        currentUser = null;
        notifyListeners();
        return false;
    }
}

/**
 * Set current user after login
 * @param {import('../api/types').User} user
 */
export function setUser(user) {
    currentUser = user;
    notifyListeners();
}

/**
 * Clear auth state on logout
 */
export function clearAuthState() {
    currentUser = null;
    notifyListeners();
}

// Listen for logout events
window.addEventListener('auth:logout', () => {
    clearAuthState();
});
