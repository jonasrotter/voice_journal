/**
 * Entry Card Component
 * @module entries/EntryCard
 */

import { getAudioUrl, getAudioStreamUrl, fetchAudioBlobUrl, deleteEntry, reprocessEntry } from '../api/client.js';
import { showToast } from '../components/toast.js';
import { EntryStatus } from '../api/types.js';

// Cache for audio blob URLs to avoid re-fetching
const audioBlobCache = new Map();

/**
 * Preload audio blob URLs for all visible entry cards
 * This runs in the background after entries are rendered,
 * making the play button work instantly when clicked.
 */
async function preloadAudioForEntries() {
    const audioElements = document.querySelectorAll('.audio-player audio');
    
    // Preload in parallel (limit to 3 concurrent to avoid overwhelming the server)
    const concurrencyLimit = 3;
    const queue = Array.from(audioElements);
    
    async function processNext() {
        if (queue.length === 0) return;
        
        const audio = queue.shift();
        const entryId = audio.dataset.entryId;
        const loadingDiv = audio.parentElement?.querySelector('.audio-loading');
        
        // Skip if already cached or has blob source
        if (audioBlobCache.has(entryId) || (audio.src && audio.src.startsWith('blob:'))) {
            if (audioBlobCache.has(entryId) && !audio.src.startsWith('blob:')) {
                audio.src = audioBlobCache.get(entryId);
            }
            return processNext();
        }
        
        try {
            // Show subtle loading indicator
            if (loadingDiv) loadingDiv.style.display = 'block';
            
            const blobUrl = await fetchAudioBlobUrl(entryId);
            audioBlobCache.set(entryId, blobUrl);
            
            // Set audio source so player is ready
            audio.src = blobUrl;
        } catch (error) {
            console.warn(`Failed to preload audio for entry ${entryId}:`, error.message);
            // Don't show error toast during preload - will show on play attempt
        } finally {
            if (loadingDiv) loadingDiv.style.display = 'none';
        }
        
        return processNext();
    }
    
    // Start concurrent workers
    const workers = [];
    for (let i = 0; i < Math.min(concurrencyLimit, queue.length); i++) {
        workers.push(processNext());
    }
    
    await Promise.all(workers);
}

/**
 * Get MIME type from audio URL
 * @param {string} audioUrl
 * @returns {string}
 */
function getAudioMimeType(audioUrl) {
    const ext = audioUrl.split('.').pop()?.toLowerCase() || '';
    const mimeTypes = {
        'wav': 'audio/wav',
        'mp3': 'audio/mpeg',
        'webm': 'audio/webm',
        'ogg': 'audio/ogg',
        'm4a': 'audio/mp4',
        'flac': 'audio/flac'
    };
    return mimeTypes[ext] || 'audio/wav';
}

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
    // Get MIME type from original URL for proper audio playback
    const audioMimeType = getAudioMimeType(entry.audio_url);
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
            
            <div class="audio-player" data-entry-id="${entry.id}">
                <audio controls preload="none" data-entry-id="${entry.id}" data-mime-type="${audioMimeType}" style="width: 100%;">
                    Your browser does not support audio playback.
                </audio>
                <div class="audio-loading" data-entry-id="${entry.id}" style="display: none; font-size: 12px; color: var(--color-text-secondary); margin-top: 8px;">
                    ⏳ Loading audio...
                </div>
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
    // Preload audio for all visible entries
    preloadAudioForEntries();
    
    // Audio lazy loading fallback - load audio when user clicks play (if not preloaded)
    document.querySelectorAll('.audio-player audio').forEach(audio => {
        const entryId = audio.dataset.entryId;
        const audioPlayer = audio.parentElement;
        const loadingDiv = audioPlayer.querySelector('.audio-loading');
        let isLoading = false;
        
        audio.addEventListener('play', async (e) => {
            // If already has blob source or currently loading, skip
            if ((audio.src && audio.src.startsWith('blob:')) || isLoading) return;
            
            // Pause until loaded
            audio.pause();
            isLoading = true;
            
            // Show loading
            if (loadingDiv) loadingDiv.style.display = 'block';
            
            try {
                // Check cache first
                let blobUrl;
                if (audioBlobCache.has(entryId)) {
                    blobUrl = audioBlobCache.get(entryId);
                } else {
                    blobUrl = await fetchAudioBlobUrl(entryId);
                    audioBlobCache.set(entryId, blobUrl);
                }
                
                // Set source and play
                audio.src = blobUrl;
                audio.play().catch(err => {
                    console.warn('Autoplay blocked:', err);
                });
            } catch (error) {
                console.error('Failed to load audio:', error);
                showToast('Failed to load audio: ' + error.message, 'error');
            } finally {
                isLoading = false;
                if (loadingDiv) loadingDiv.style.display = 'none';
            }
        });
    });
    
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
