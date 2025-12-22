/**
 * Audio Recorder using Web Audio API
 * @module recording/recorder
 */

/**
 * @typedef {Object} RecorderState
 * @property {boolean} isRecording
 * @property {boolean} isPaused
 * @property {number} duration - Duration in seconds
 * @property {Float32Array|null} waveformData
 */

let mediaRecorder = null;
let audioContext = null;
let analyser = null;
let chunks = [];
let startTime = 0;
let durationInterval = null;

let onStateChange = null;
let onDataAvailable = null;

const MAX_DURATION_SECONDS = 600; // 10 minutes max

/**
 * Initialize the recorder
 * @param {Object} callbacks
 * @param {Function} callbacks.onStateChange - Called when recording state changes
 * @param {Function} callbacks.onDataAvailable - Called when recording data is ready
 */
export function initRecorder(callbacks) {
    onStateChange = callbacks.onStateChange || (() => {});
    onDataAvailable = callbacks.onDataAvailable || (() => {});
}

/**
 * Get current recording state
 * @returns {RecorderState}
 */
export function getRecorderState() {
    return {
        isRecording: mediaRecorder?.state === 'recording',
        isPaused: mediaRecorder?.state === 'paused',
        duration: startTime ? Math.floor((Date.now() - startTime) / 1000) : 0,
        waveformData: getWaveformData()
    };
}

/**
 * Get waveform data from analyser
 * @returns {Float32Array|null}
 */
function getWaveformData() {
    if (!analyser) return null;
    
    const dataArray = new Float32Array(analyser.fftSize);
    analyser.getFloatTimeDomainData(dataArray);
    return dataArray;
}

/**
 * Start recording
 * @returns {Promise<void>}
 */
export async function startRecording() {
    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ 
            audio: {
                echoCancellation: true,
                noiseSuppression: true,
                sampleRate: 44100
            } 
        });
        
        // Setup Web Audio API for visualization
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256;
        
        const source = audioContext.createMediaStreamSource(stream);
        source.connect(analyser);
        
        // Setup MediaRecorder
        const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus') 
            ? 'audio/webm;codecs=opus' 
            : 'audio/webm';
            
        mediaRecorder = new MediaRecorder(stream, { mimeType });
        chunks = [];
        
        mediaRecorder.ondataavailable = (e) => {
            if (e.data.size > 0) {
                chunks.push(e.data);
            }
        };
        
        mediaRecorder.onstop = () => {
            const blob = new Blob(chunks, { type: mimeType });
            onDataAvailable(blob);
            cleanup();
        };
        
        // Start recording
        mediaRecorder.start(1000); // Collect data every second
        startTime = Date.now();
        
        // Track duration
        durationInterval = setInterval(() => {
            const duration = Math.floor((Date.now() - startTime) / 1000);
            
            // Auto-stop at max duration
            if (duration >= MAX_DURATION_SECONDS) {
                stopRecording();
                return;
            }
            
            onStateChange(getRecorderState());
        }, 100);
        
        onStateChange(getRecorderState());
        
    } catch (error) {
        console.error('Failed to start recording:', error);
        throw new Error('Microphone access denied');
    }
}

/**
 * Stop recording
 */
export function stopRecording() {
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop();
        
        // Stop all tracks
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
}

/**
 * Pause recording
 */
export function pauseRecording() {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.pause();
        onStateChange(getRecorderState());
    }
}

/**
 * Resume recording
 */
export function resumeRecording() {
    if (mediaRecorder && mediaRecorder.state === 'paused') {
        mediaRecorder.resume();
        onStateChange(getRecorderState());
    }
}

/**
 * Cancel recording without saving
 */
export function cancelRecording() {
    chunks = [];
    if (mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stream.getTracks().forEach(track => track.stop());
    }
    cleanup();
}

/**
 * Cleanup resources
 */
function cleanup() {
    if (durationInterval) {
        clearInterval(durationInterval);
        durationInterval = null;
    }
    
    if (audioContext) {
        audioContext.close();
        audioContext = null;
    }
    
    analyser = null;
    mediaRecorder = null;
    startTime = 0;
    
    onStateChange(getRecorderState());
}

/**
 * Format duration to MM:SS
 * @param {number} seconds
 * @returns {string}
 */
export function formatDuration(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}
