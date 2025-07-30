/**
 * Main Application Controller
 * Coordinates CSV upload and motion visualization
 */

class MotionCaptureApp {
    constructor() {
        this.csvUploader = null;
        this.motionViewer = null;
        this.isInitialized = false;
        
        this.init();
    }
    
    init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initialize());
        } else {
            this.initialize();
        }
    }
    
    initialize() {
        console.log('Initializing Baseball Motion Capture App...');
        
        // Get CSV uploader instance (created by csv-uploader.js)
        this.csvUploader = window.csvUploader;
        
        if (!this.csvUploader) {
            console.error('CSV uploader not found');
            return;
        }
        
        // Override the CSV uploader's motion viewer initialization
        const originalInitializeMotionViewer = this.csvUploader.initializeMotionViewer.bind(this.csvUploader);
        this.csvUploader.initializeMotionViewer = async () => {
            return await this.initializeMotionViewer();
        };
        
        // Setup additional UI handlers
        this.setupUIHandlers();
        
        this.isInitialized = true;
        console.log('App initialized successfully');
    }
    
    async initializeMotionViewer() {
        try {
            const motionViewerContainer = document.getElementById('motion-viewer');
            
            if (!motionViewerContainer) {
                throw new Error('Motion viewer container not found');
            }
            
            // Clear any existing content
            motionViewerContainer.innerHTML = '';
            
            // Create motion viewer
            this.motionViewer = new MotionViewer(motionViewerContainer);
            
            // Load motion data
            const success = await this.motionViewer.loadMotionData();
            
            if (success) {
                // Connect motion controls
                this.connectMotionControls();
                console.log('Motion viewer initialized successfully');
                return true;
            } else {
                throw new Error('Failed to load motion data');
            }
            
        } catch (error) {
            console.error('Error initializing motion viewer:', error);
            
            const motionViewerContainer = document.getElementById('motion-viewer');
            if (motionViewerContainer) {
                motionViewerContainer.innerHTML = `
                    <div style="
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        height: 100%;
                        color: #dc3545;
                        text-align: center;
                        padding: 20px;
                    ">
                        <div>
                            <div style="font-size: 2em; margin-bottom: 10px;">⚠️</div>
                            <div>Failed to initialize motion viewer</div>
                            <div style="font-size: 0.9em; margin-top: 10px; opacity: 0.7;">
                                ${error.message}
                            </div>
                        </div>
                    </div>
                `;
            }
            
            return false;
        }
    }
    
    connectMotionControls() {
        if (!this.motionViewer) {
            console.warn('Motion viewer not available for connecting controls');
            return;
        }
        
        // Play/Pause/Reset buttons
        const playBtn = document.getElementById('play-btn');
        const pauseBtn = document.getElementById('pause-btn');
        const resetBtn = document.getElementById('reset-btn');
        
        if (playBtn) {
            playBtn.addEventListener('click', () => {
                this.motionViewer.play();
                this.updateButtonStates(true);
            });
        }
        
        if (pauseBtn) {
            pauseBtn.addEventListener('click', () => {
                this.motionViewer.pause();
                this.updateButtonStates(false);
            });
        }
        
        if (resetBtn) {
            resetBtn.addEventListener('click', () => {
                this.motionViewer.reset();
                this.updateButtonStates(false);
                this.updateFrameDisplay(0);
            });
        }
        
        // Frame slider
        const frameSlider = document.getElementById('frame-slider');
        const frameDisplay = document.getElementById('frame-display');
        
        if (frameSlider && this.motionViewer.getTotalFrames) {
            const totalFrames = this.motionViewer.getTotalFrames();
            frameSlider.max = totalFrames - 1;
            frameSlider.value = 0;
            
            if (frameDisplay) {
                frameDisplay.textContent = `0 / ${totalFrames}`;
            }
            
            frameSlider.addEventListener('input', (e) => {
                const frame = parseInt(e.target.value);
                this.motionViewer.setFrame(frame);
                this.updateFrameDisplay(frame);
                
                // Pause animation when manually scrubbing
                this.motionViewer.pause();
                this.updateButtonStates(false);
            });
        }
        
        // Speed slider
        const speedSlider = document.getElementById('speed-slider');
        const speedDisplay = document.getElementById('speed-display');
        
        if (speedSlider) {
            speedSlider.addEventListener('input', (e) => {
                const speed = parseFloat(e.target.value);
                this.motionViewer.setSpeed(speed);
                
                if (speedDisplay) {
                    speedDisplay.textContent = `${speed.toFixed(1)}x`;
                }
            });
        }
        
        // Override the motion viewer's frame change callback
        this.motionViewer.onFrameChanged = (frameIndex) => {
            this.updateFrameDisplay(frameIndex);
            
            // Update frame slider without triggering its event
            if (frameSlider) {
                frameSlider.value = frameIndex;
            }
        };
        
        console.log('Motion controls connected');
    }
    
    updateButtonStates(isPlaying) {
        const playBtn = document.getElementById('play-btn');
        const pauseBtn = document.getElementById('pause-btn');
        
        if (playBtn && pauseBtn) {
            if (isPlaying) {
                playBtn.classList.remove('active');
                pauseBtn.classList.add('active');
            } else {
                playBtn.classList.add('active');
                pauseBtn.classList.remove('active');
            }
        }
    }
    
    updateFrameDisplay(frameIndex) {
        const frameDisplay = document.getElementById('frame-display');
        if (frameDisplay && this.motionViewer) {
            const totalFrames = this.motionViewer.getTotalFrames();
            frameDisplay.textContent = `${frameIndex} / ${totalFrames}`;
        }
    }
    
    setupUIHandlers() {
        // Add keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if (!this.motionViewer) return;
            
            switch (e.code) {
                case 'Space':
                    e.preventDefault();
                    if (this.motionViewer.isPlaying) {
                        this.motionViewer.pause();
                        this.updateButtonStates(false);
                    } else {
                        this.motionViewer.play();
                        this.updateButtonStates(true);
                    }
                    break;
                    
                case 'ArrowLeft':
                    e.preventDefault();
                    if (e.ctrlKey || e.metaKey) {
                        this.motionViewer.reset();
                        this.updateButtonStates(false);
                        this.updateFrameDisplay(0);
                    } else {
                        const currentFrame = this.motionViewer.getCurrentFrame();
                        const newFrame = Math.max(0, currentFrame - 1);
                        this.motionViewer.setFrame(newFrame);
                        this.updateFrameDisplay(newFrame);
                    }
                    break;
                    
                case 'ArrowRight':
                    e.preventDefault();
                    const currentFrame = this.motionViewer.getCurrentFrame();
                    const totalFrames = this.motionViewer.getTotalFrames();
                    const newFrame = Math.min(totalFrames - 1, currentFrame + 1);
                    this.motionViewer.setFrame(newFrame);
                    this.updateFrameDisplay(newFrame);
                    break;
            }
        });
        
        // Add view controls if they exist
        const frontViewBtn = document.getElementById('front-view');
        const sideViewBtn = document.getElementById('side-view');
        const topViewBtn = document.getElementById('top-view');
        const freeViewBtn = document.getElementById('free-view');
        
        if (frontViewBtn) frontViewBtn.addEventListener('click', () => this.motionViewer?.setView('front'));
        if (sideViewBtn) sideViewBtn.addEventListener('click', () => this.motionViewer?.setView('side'));
        if (topViewBtn) topViewBtn.addEventListener('click', () => this.motionViewer?.setView('top'));
        if (freeViewBtn) freeViewBtn.addEventListener('click', () => this.motionViewer?.setView('free'));
        
        // Add visibility toggles if they exist
        const skeletonToggle = document.getElementById('show-skeleton');
        const jointsToggle = document.getElementById('show-joints');
        const groundToggle = document.getElementById('show-ground');
        
        if (skeletonToggle) {
            skeletonToggle.addEventListener('change', (e) => {
                if (this.motionViewer) {
                    this.motionViewer.showSkeleton = e.target.checked;
                    this.motionViewer.toggleSkeleton();
                }
            });
        }
        
        if (jointsToggle) {
            jointsToggle.addEventListener('change', (e) => {
                if (this.motionViewer) {
                    this.motionViewer.showJoints = e.target.checked;
                    this.motionViewer.toggleJoints();
                }
            });
        }
        
        if (groundToggle) {
            groundToggle.addEventListener('change', (e) => {
                if (this.motionViewer) {
                    this.motionViewer.showGround = e.target.checked;
                    this.motionViewer.toggleGround();
                }
            });
        }
        
        console.log('UI handlers setup complete');
    }
    
    // Public API methods
    reset() {
        if (this.motionViewer) {
            this.motionViewer.dispose();
            this.motionViewer = null;
        }
        
        if (this.csvUploader) {
            this.csvUploader.reset();
        }
        
        this.updateButtonStates(false);
    }
    
    getMotionViewer() {
        return this.motionViewer;
    }
    
    getCSVUploader() {
        return this.csvUploader;
    }
}

// Initialize the application
const app = new MotionCaptureApp();

// Make app globally available for debugging
window.motionCaptureApp = app;

// Add some helpful keyboard shortcut info
console.log('Baseball Motion Capture App loaded!');
console.log('Keyboard shortcuts:');
console.log('  Space: Play/Pause');
console.log('  ← →: Previous/Next frame');
console.log('  Ctrl+←: Reset to first frame');

// Export for use in other modules
window.MotionCaptureApp = MotionCaptureApp;