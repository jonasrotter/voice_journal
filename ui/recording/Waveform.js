/**
 * Waveform Visualizer Component
 * @module recording/Waveform
 */

const NUM_BARS = 40;

/**
 * Render waveform visualizer
 * @param {HTMLElement} container
 */
export function renderWaveform(container) {
    container.innerHTML = `
        <div class="waveform-container">
            <div class="waveform" id="waveform">
                ${Array(NUM_BARS).fill(0).map((_, i) => 
                    `<div class="waveform-bar" id="bar-${i}" style="height: 4px;"></div>`
                ).join('')}
            </div>
        </div>
    `;
}

/**
 * Update waveform with audio data
 * @param {Float32Array|null} data
 */
export function updateWaveform(data) {
    if (!data) {
        // Reset to idle state
        for (let i = 0; i < NUM_BARS; i++) {
            const bar = document.getElementById(`bar-${i}`);
            if (bar) {
                bar.style.height = '4px';
            }
        }
        return;
    }
    
    // Calculate average values for each bar
    const step = Math.floor(data.length / NUM_BARS);
    
    for (let i = 0; i < NUM_BARS; i++) {
        const start = i * step;
        let sum = 0;
        
        for (let j = start; j < start + step && j < data.length; j++) {
            sum += Math.abs(data[j]);
        }
        
        const average = sum / step;
        const height = Math.max(4, Math.min(50, average * 500));
        
        const bar = document.getElementById(`bar-${i}`);
        if (bar) {
            bar.style.height = `${height}px`;
        }
    }
}

/**
 * Animate waveform with idle animation
 * @param {boolean} active
 */
export function animateIdle(active) {
    if (!active) return;
    
    for (let i = 0; i < NUM_BARS; i++) {
        const bar = document.getElementById(`bar-${i}`);
        if (bar) {
            const delay = i * 50;
            bar.style.transition = 'height 0.3s ease';
            setTimeout(() => {
                bar.style.height = `${4 + Math.random() * 10}px`;
            }, delay);
        }
    }
}
