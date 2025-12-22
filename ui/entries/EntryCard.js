/**
 * Entry Card Component
 * @module entries/EntryCard
 */

import { getAudioUrl, deleteEntry, reprocessEntry } from '../api/client.js';
import { showToast } from '../components/toast.js';
import { EntryStatus } from '../api/types.js';

/**
 * Format date to readable string
 * @param {string} isoDate
 * @returns {string}
 */
function formatDate(isoDate) {
    const date = new Date(isoDate);
    return date.toLocaleDateString('en-US', {
        weekday: 'short',
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Get status badge class
 * @param {string} status
 * @returns {string}
 */
function getStatusClass(status) {
    switch (status) {
        case EntryStatus.PROCESSING:
        case EntryStatus.PENDING:
            return 'processing';
        case EntryStatus.PROCESSED:
            return 'processed';
        case EntryStatus.FAILED:
            return 'failed';
        default:
            return '';
    }
}

/**
 * Render entry card
 * @param {import('../api/types').JournalEntry} entry
 * @param {Function} onDelete - Callback when entry is deleted
 * @param {Function} onUpdate - Callback when entry is updated
 * @returns {string} HTML string
 */
export function renderEntryCard(entry, onDelete, onUpdate) {
    const audioUrl = getAudioUrl(entry.audio_url);
    const statusClass = getStatusClass(entry.status);
    const isProcessed = entry.status === EntryStatus.PROCESSED;
    const isFailed = entry.status === EntryStatus.FAILED;
    const isPending = entry.status === EntryStatus.PENDING || entry.status === EntryStatus.PROCESSING;
    
    return `
        <div class="entry-card" data-entry-id="${entry.id}">
            <div class="entry-header">
                <span class="entry-date">${formatDate(entry.created_at)}</span>
                <span class="entry-status ${statusClass}">
                    ${entry.status.charAt(0).toUpperCase() + entry.status.slice(1)}
                </span>
            </div>
            
            ${isProcessed && entry.emotion ? `
                <span class="entry-emotion">${entry.emotion}</span>
            ` : ''}
            
            ${isProcessed && entry.summary ? `
                <p class="entry-summary">${entry.summary}</p>
            ` : ''}
            
            ${isPending ? `
                <p class="entry-summary" style="color: var(--color-text-secondary);">
                    Processing your entry...
                </p>
            ` : ''}
            
            ${isFailed ? `
                <p class="entry-summary" style="color: var(--color-error);">
                    Processing failed. Click reprocess to try again.
                </p>
            ` : ''}
            
            ${isProcessed && entry.transcript ? `
                <details>
                    <summary style="cursor: pointer; color: var(--color-text-secondary); margin-bottom: 8px;">
                        Show transcript
                    </summary>
                    <div class="entry-transcript">${entry.transcript}</div>
                </details>
            ` : ''}
            
            <div class="audio-player">
                <audio controls preload="metadata">
                    <source src="${audioUrl}" type="audio/webm">
                    Your browser does not support audio playback.
                </audio>
            </div>
            
            <div class="entry-actions">
                ${isFailed ? `
                    <button class="btn btn-secondary reprocess-btn" data-id="${entry.id}">
                        🔄 Reprocess
                    </button>
                ` : ''}
                <button class="btn btn-danger delete-btn" data-id="${entry.id}">
                    🗑️ Delete
                </button>
            </div>
        </div>
    `;
}

/**
 * Setup entry card event handlers
 * @param {Function} onDelete
 * @param {Function} onUpdate
 */
export function setupEntryCardHandlers(onDelete, onUpdate) {
    // Delete handlers
    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const entryId = e.target.dataset.id;
            
            if (!confirm('Are you sure you want to delete this entry?')) {
                return;
            }
            
            try {
                await deleteEntry(entryId);
                showToast('Entry deleted', 'success');
                onDelete(entryId);
            } catch (error) {
                showToast(`Failed to delete: ${error.message}`, 'error');
            }
        });
    });
    
    // Reprocess handlers
    document.querySelectorAll('.reprocess-btn').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            const entryId = e.target.dataset.id;
            
            try {
                const updated = await reprocessEntry(entryId);
                showToast('Reprocessing started', 'info');
                onUpdate(updated);
            } catch (error) {
                showToast(`Failed to reprocess: ${error.message}`, 'error');
            }
        });
    });
}
