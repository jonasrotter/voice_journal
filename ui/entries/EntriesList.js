/**
 * Entries List Component
 * @module entries/EntriesList
 */

import { getEntries } from '../api/client.js';
import { renderEntryCard, setupEntryCardHandlers } from './EntryCard.js';
import { showToast } from '../components/toast.js';

/**
 * Render entries list
 * @param {HTMLElement} container
 */
export function renderEntriesList(container) {
    let entries = [];
    let isLoading = true;
    let error = null;
    
    async function loadEntries() {
        isLoading = true;
        render();
        
        try {
            const response = await getEntries({ skip: 0, limit: 100 });
            entries = response.entries || [];
            error = null;
        } catch (e) {
            error = e.message;
            entries = [];
        } finally {
            isLoading = false;
            render();
        }
    }
    
    function render() {
        if (isLoading) {
            container.innerHTML = `
                <div class="entries-section">
                    <h2>Your Entries</h2>
                    <div class="loading">
                        <div class="spinner"></div>
                    </div>
                </div>
            `;
            return;
        }
        
        if (error) {
            container.innerHTML = `
                <div class="entries-section">
                    <h2>Your Entries</h2>
                    <div class="empty-state">
                        <p style="color: var(--color-error);">Failed to load entries: ${error}</p>
                        <button class="btn btn-secondary" id="retry-btn" style="margin-top: 16px;">
                            Retry
                        </button>
                    </div>
                </div>
            `;
            
            document.getElementById('retry-btn').addEventListener('click', loadEntries);
            return;
        }
        
        if (entries.length === 0) {
            container.innerHTML = `
                <div class="entries-section">
                    <h2>Your Entries</h2>
                    <div class="empty-state">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                            <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                            <line x1="12" y1="19" x2="12" y2="23"/>
                            <line x1="8" y1="23" x2="16" y2="23"/>
                        </svg>
                        <p>No entries yet</p>
                        <p style="font-size: 14px;">Record your first voice journal entry above!</p>
                    </div>
                </div>
            `;
            return;
        }
        
        // Sort by created_at descending (newest first)
        const sortedEntries = [...entries].sort((a, b) => 
            new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        
        container.innerHTML = `
            <div class="entries-section">
                <h2>Your Entries (${entries.length})</h2>
                <div class="entries-list">
                    ${sortedEntries.map(entry => 
                        renderEntryCard(entry, handleDelete, handleUpdate)
                    ).join('')}
                </div>
            </div>
        `;
        
        setupEntryCardHandlers(handleDelete, handleUpdate);
    }
    
    function handleDelete(entryId) {
        entries = entries.filter(e => e.id !== entryId);
        render();
    }
    
    function handleUpdate(updatedEntry) {
        entries = entries.map(e => e.id === updatedEntry.id ? updatedEntry : e);
        render();
    }
    
    /**
     * Add new entry to list
     * @param {Object} newEntry
     */
    function addEntry(newEntry) {
        // Fetch full entry details
        loadEntries();
    }
    
    // Initial load
    loadEntries();
    
    // Return API for external control
    return {
        refresh: loadEntries,
        addEntry
    };
}

/**
 * Poll for entry updates (for processing status)
 * @param {Function} onUpdate
 * @param {number} intervalMs
 * @returns {Function} Stop polling function
 */
export function pollEntryUpdates(onUpdate, intervalMs = 5000) {
    const interval = setInterval(async () => {
        try {
            const response = await getEntries({ skip: 0, limit: 100 });
            onUpdate(response.entries || []);
        } catch (error) {
            console.error('Failed to poll entries:', error);
        }
    }, intervalMs);
    
    return () => clearInterval(interval);
}
