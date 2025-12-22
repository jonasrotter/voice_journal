/**
 * Simple Client-Side Router
 * @module router
 */

let routes = {};
let currentRoute = null;
let onRouteChange = null;

/**
 * Register routes
 * @param {Object} routeMap - Map of paths to handler functions
 */
export function registerRoutes(routeMap) {
    routes = routeMap;
}

/**
 * Navigate to a route
 * @param {string} path
 */
export function navigateTo(path) {
    window.history.pushState({}, '', path);
    handleRoute();
}

/**
 * Get current path
 * @returns {string}
 */
export function getCurrentPath() {
    return window.location.pathname;
}

/**
 * Handle current route
 */
export function handleRoute() {
    const path = getCurrentPath();
    const handler = routes[path] || routes['*'];
    
    currentRoute = path;
    
    if (handler) {
        handler(path);
    }
    
    if (onRouteChange) {
        onRouteChange(path);
    }
}

/**
 * Set route change callback
 * @param {Function} callback
 */
export function setRouteChangeHandler(callback) {
    onRouteChange = callback;
}

/**
 * Initialize router
 */
export function initRouter() {
    // Handle browser back/forward
    window.addEventListener('popstate', handleRoute);
    
    // Initial route
    handleRoute();
}
