/**
 * Recording Panel Component
 * @module recording/RecordingPanel
 */

import { 
    initRecorder, 
    startRecording, 
    stopRecording, 
    cancelRecording,
    formatDuration,
    getRecorderState
} from './recorder.js';
import { renderWaveform, updateWaveform } from './Waveform.js';
import { uploadEntry } from '../api/client.js';
import { showToast } from '../components/toast.js';

/**
 * Render recording panel
 * @param {HTMLElement} container
 * @param {Function} onEntryCreated - Callback when entry is created
 */
export function renderRecordingPanel(container, onEntryCreated) {
    let isRecording = false;
    let duration = 0;
    let isUploading = false;
    
    function render() {
        container.innerHTML = `
            <div class="recording-section">
                <h2>${isRecording ? 'Recording...' : 'Record New Entry'}</h2>
                
                <div class="recording-controls">
                    <div id="waveform-container"></div>
                    
                    <div class="recording-time" id="recording-time">
                        ${formatDuration(duration)}
                    </div>
                    
                    <button 
                        class="btn-record ${isRecording ? 'recording' : ''}" 
                        id="record-btn"
                        ${isUploading ? 'disabled' : ''}
                        aria-label="${isRecording ? 'Stop recording' : 'Start recording'}"
                    >
                        ${isRecording ? '⏹️' : '🎙️'}
                    </button>
                    
                    <p class="recording-hint">
                        ${isUploading 
                            ? 'Uploading...' 
                            : isRecording 
                                ? 'Tap to stop recording' 
                                : 'Tap to start recording'}
                    </p>
                    
                    ${isRecording ? `
                        <button class="btn btn-secondary" id="cancel-btn">
                            Cancel
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
        
        // Render waveform
        const waveformContainer = document.getElementById('waveform-container');
        renderWaveform(waveformContainer);
        
        setupEventHandlers();
    }
    
    function setupEventHandlers() {
        const recordBtn = document.getElementById('record-btn');
        const cancelBtn = document.getElementById('cancel-btn');
        
        recordBtn.addEventListener('click', handleRecordClick);
        
        if (cancelBtn) {
            cancelBtn.addEventListener('click', handleCancel);
        }
    }
    
    async function handleRecordClick() {
        if (isUploading) return;
        
        if (isRecording) {
            stopRecording();
        } else {
            try {
                await startRecording();
            } catch (error) {
                showToast(error.message, 'error');
            }
        }
    }
    
    function handleCancel() {
        cancelRecording();
        isRecording = false;
        duration = 0;
        render();
    }
    
    function handleStateChange(state) {
        isRecording = state.isRecording;
        duration = state.duration;
        
        // Update time display
        const timeEl = document.getElementById('recording-time');
        if (timeEl) {
            timeEl.textContent = formatDuration(duration);
        }
        
        // Update waveform
        if (state.isRecording) {
            updateWaveform(state.waveformData);
        }
        
        // Update record button state
        const recordBtn = document.getElementById('record-btn');
        if (recordBtn) {
            recordBtn.className = `btn-record ${isRecording ? 'recording' : ''}`;
            recordBtn.innerHTML = isRecording ? '⏹️' : '🎙️';
        }
        
        // Show/hide cancel button
        if (!isRecording && !isUploading) {
            render();
        }
    }
    
    async function handleDataAvailable(blob) {
        isUploading = true;
        isRecording = false;
        duration = 0;
        render();
        
        try {
            const result = await uploadEntry(blob);
            showToast('Entry uploaded! Processing...', 'success');
            
            if (onEntryCreated) {
                onEntryCreated(result);
            }
        } catch (error) {
            showToast(`Upload failed: ${error.message}`, 'error');
        } finally {
            isUploading = false;
            render();
        }
    }
    
    // Initialize recorder
    initRecorder({
        onStateChange: handleStateChange,
        onDataAvailable: handleDataAvailable
    });
    
    render();
}
