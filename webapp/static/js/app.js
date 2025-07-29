/**
 * Main Application JavaScript
 * Handles UI interactions and coordinates the motion viewer
 */

class BaseballMotionApp {
    constructor() {
        this.viewer = null;
        this.motionData = null;
        this.updateInterval = null;
        
        this.init();
    }

    init() {
        // Initialize the 3D viewer
        this.viewer = new MotionViewer('threejs-canvas');
        
        // Setup UI event listeners
        this.setupEventListeners();
        
        // Load motion data
        this.loadMotionData();
    }

    setupEventListeners() {
        // Animation controls
        document.getElementById('play-btn').addEventListener('click', () => this.play());
        document.getElementById('pause-btn').addEventListener('click', () => this.pause());
        document.getElementById('reset-btn').addEventListener('click', () => this.reset());
        
        // Frame slider
        const frameSlider = document.getElementById('frame-slider');
        frameSlider.addEventListener('input', (e) => this.setFrame(parseInt(e.target.value)));
        
        // Speed slider
        const speedSlider = document.getElementById('speed-slider');
        speedSlider.addEventListener('input', (e) => {
            const speed = parseFloat(e.target.value);
            this.setSpeed(speed);
            document.getElementById('speed-display').textContent = speed.toFixed(1);
        });
        
        // View controls
        document.getElementById('front-view').addEventListener('click', () => this.setView('front'));
        document.getElementById('side-view').addEventListener('click', () => this.setView('side'));
        document.getElementById('top-view').addEventListener('click', () => this.setView('top'));
        document.getElementById('free-view').addEventListener('click', () => this.setView('free'));
        
        // Visibility toggles
        document.getElementById('show-skeleton').addEventListener('change', (e) => {
            this.viewer.toggleSkeleton(e.target.checked);
        });
        
        document.getElementById('show-joints').addEventListener('change', (e) => {
            this.viewer.toggleJoints(e.target.checked);
        });
        
        document.getElementById('show-ground').addEventListener('change', (e) => {
            this.viewer.toggleGround(e.target.checked);
        });
        
        document.getElementById('show-trajectory').addEventListener('change', (e) => {
            // TODO: Implement trajectory visualization
            console.log('Trajectory toggle:', e.target.checked);
        });
        
        // Action buttons
        document.getElementById('convert-btn').addEventListener('click', () => this.regenerateBVH());
        document.getElementById('export-btn').addEventListener('click', () => this.exportData());
        
        // Start UI update loop
        this.startUIUpdates();
    }

    async loadMotionData() {
        try {
            this.viewer.showLoading();
            
            // Load motion data info
            const response = await fetch('/api/motion-data');
            this.motionData = await response.json();
            
            if (this.motionData.error) {
                throw new Error(this.motionData.error);
            }
            
            // Update UI with motion info
            this.updateMotionInfo();
            
            // Load BVH data into viewer
            const bvhData = await this.viewer.loadBVH('/api/bvh');
            
            // Update frame slider
            const frameSlider = document.getElementById('frame-slider');
            frameSlider.max = bvhData.frames.length - 1;
            frameSlider.value = 0;
            
            console.log('Motion data loaded successfully');
            
        } catch (error) {
            console.error('Error loading motion data:', error);
            this.showMessage('Failed to load motion data: ' + error.message, 'error');
        }
    }

    updateMotionInfo() {
        if (!this.motionData) return;
        
        document.getElementById('duration').textContent = this.motionData.duration.toFixed(2);
        document.getElementById('fps').textContent = this.motionData.fps.toFixed(1);
        document.getElementById('total-frames-info').textContent = this.motionData.frame_count;
        document.getElementById('total-frames').textContent = this.motionData.frame_count;
    }

    play() {
        this.viewer.play();
        this.updatePlayButton(true);
    }

    pause() {
        this.viewer.pause();
        this.updatePlayButton(false);
    }

    reset() {
        this.viewer.stop();
        this.setFrame(0);
        this.updatePlayButton(false);
    }

    setFrame(frameNumber) {
        this.viewer.setFrame(frameNumber);
        document.getElementById('frame-display').textContent = frameNumber;
        document.getElementById('frame-slider').value = frameNumber;
    }

    setSpeed(speed) {
        this.viewer.setSpeed(speed);
    }

    setView(viewMode) {
        this.viewer.setViewMode(viewMode);
        
        // Update button states
        document.querySelectorAll('#controls-panel .control-group:nth-child(2) .btn').forEach(btn => {
            btn.classList.remove('primary');
        });
        document.getElementById(viewMode + '-view').classList.add('primary');
    }

    updatePlayButton(isPlaying) {
        const playBtn = document.getElementById('play-btn');
        if (isPlaying) {
            playBtn.textContent = '⏸ Playing';
            playBtn.classList.remove('primary');
        } else {
            playBtn.textContent = '▶ Play';
            playBtn.classList.add('primary');
        }
    }

    async regenerateBVH() {
        try {
            const convertBtn = document.getElementById('convert-btn');
            const originalText = convertBtn.textContent;
            convertBtn.textContent = '🔄 Converting...';
            convertBtn.disabled = true;
            
            const response = await fetch('/api/convert-mocap', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            const result = await response.json();
            
            if (result.error) {
                throw new Error(result.error);
            }
            
            this.showMessage('BVH file regenerated successfully!', 'success');
            
            // Reload the motion data
            await this.loadMotionData();
            
        } catch (error) {
            console.error('Error regenerating BVH:', error);
            this.showMessage('Failed to regenerate BVH: ' + error.message, 'error');
        } finally {
            const convertBtn = document.getElementById('convert-btn');
            convertBtn.textContent = '🔄 Regenerate BVH';
            convertBtn.disabled = false;
        }
    }

    exportData() {
        // Create a simple export of the current frame data
        if (!this.motionData) {
            this.showMessage('No motion data available to export', 'error');
            return;
        }
        
        const exportData = {
            motion_info: this.motionData,
            current_frame: this.viewer.getCurrentFrame(),
            total_frames: this.viewer.getTotalFrames(),
            timestamp: new Date().toISOString()
        };
        
        const blob = new Blob([JSON.stringify(exportData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'baseball_motion_data.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        this.showMessage('Motion data exported successfully!', 'success');
    }

    startUIUpdates() {
        this.updateInterval = setInterval(() => {
            if (this.viewer) {
                const currentFrame = this.viewer.getCurrentFrame();
                const isPlaying = this.viewer.getIsPlaying();
                
                // Update frame display
                document.getElementById('frame-display').textContent = currentFrame;
                document.getElementById('frame-slider').value = currentFrame;
                
                // Update play button state
                this.updatePlayButton(isPlaying);
            }
        }, 100); // Update every 100ms
    }

    showMessage(text, type = 'info') {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.message');
        existingMessages.forEach(msg => msg.remove());
        
        // Create new message
        const message = document.createElement('div');
        message.className = `message ${type}`;
        message.textContent = text;
        
        // Insert at the top of controls panel
        const controlsPanel = document.getElementById('controls-panel');
        controlsPanel.insertBefore(message, controlsPanel.firstChild);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (message.parentNode) {
                message.remove();
            }
        }, 5000);
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    window.baseballApp = new BaseballMotionApp();
});