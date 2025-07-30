/**
 * CSV Uploader Module
 * Handles CSV file uploads, validation, and communication with backend
 */

class CSVUploader {
    constructor() {
        this.centersFile = null;
        this.rotationsFile = null;
        this.uploadedData = null;
        
        this.initializeElements();
        this.bindEvents();
    }
    
    initializeElements() {
        // File input elements
        this.centersInput = document.getElementById('joint-centers-csv');
        this.rotationsInput = document.getElementById('joint-rotations-csv');
        this.uploadBtn = document.getElementById('upload-btn');
        
        // Status elements
        this.statusMessages = document.getElementById('status-messages');
        this.dataPreview = document.getElementById('data-preview');
        this.previewContent = document.getElementById('preview-content');
        
        // Motion viewer elements
        this.motionViewer = document.getElementById('motion-viewer');
        this.motionControls = document.getElementById('motion-controls');
    }
    
    bindEvents() {
        // File input change events
        this.centersInput.addEventListener('change', (e) => {
            this.handleFileSelect(e, 'centers');
        });
        
        this.rotationsInput.addEventListener('change', (e) => {
            this.handleFileSelect(e, 'rotations');
        });
        
        // Upload button click
        this.uploadBtn.addEventListener('click', () => {
            this.uploadFiles();
        });
        
        // Drag and drop events
        this.setupDragAndDrop();
    }
    
    setupDragAndDrop() {
        [this.centersInput, this.rotationsInput].forEach(input => {
            const wrapper = input.parentElement;
            
            wrapper.addEventListener('dragover', (e) => {
                e.preventDefault();
                wrapper.classList.add('drag-over');
            });
            
            wrapper.addEventListener('dragleave', (e) => {
                e.preventDefault();
                wrapper.classList.remove('drag-over');
            });
            
            wrapper.addEventListener('drop', (e) => {
                e.preventDefault();
                wrapper.classList.remove('drag-over');
                
                const files = e.dataTransfer.files;
                if (files.length > 0) {
                    input.files = files;
                    const fileType = input.id.includes('centers') ? 'centers' : 'rotations';
                    this.handleFileSelect({ target: input }, fileType);
                }
            });
        });
    }
    
    handleFileSelect(event, fileType) {
        const file = event.target.files[0];
        
        if (!file) {
            if (fileType === 'centers') {
                this.centersFile = null;
            } else {
                this.rotationsFile = null;
            }
            this.updateUploadButton();
            return;
        }
        
        // Validate file type
        if (!file.name.toLowerCase().endsWith('.csv')) {
            this.showMessage('error', `Please select a CSV file for ${fileType}`);
            event.target.value = '';
            return;
        }
        
        // Store file reference
        if (fileType === 'centers') {
            this.centersFile = file;
            this.showMessage('info', `Joint Centers CSV selected: ${file.name} (${this.formatFileSize(file.size)})`);
        } else {
            this.rotationsFile = file;
            this.showMessage('info', `Joint Rotations CSV selected: ${file.name} (${this.formatFileSize(file.size)})`);
        }
        
        this.updateUploadButton();
        
        // Preview file content
        this.previewCSVFile(file, fileType);
    }
    
    previewCSVFile(file, fileType) {
        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target.result;
            const lines = content.split('\n').slice(0, 5); // First 5 lines
            
            this.showFilePreview(fileType, lines, file);
        };
        reader.readAsText(file);
    }
    
    showFilePreview(fileType, lines, file) {
        const previewHtml = `
            <div class="file-preview">
                <h5>${fileType === 'centers' ? 'Joint Centers' : 'Joint Rotations'} Preview:</h5>
                <p><strong>File:</strong> ${file.name} (${this.formatFileSize(file.size)})</p>
                <div class="preview-lines">
                    ${lines.map((line, index) => 
                        `<div class="preview-line"><strong>Line ${index + 1}:</strong> ${line.substring(0, 100)}${line.length > 100 ? '...' : ''}</div>`
                    ).join('')}
                </div>
            </div>
        `;
        
        // Add to preview content
        const existingPreview = this.previewContent.querySelector(`.file-preview:has(h5:contains("${fileType === 'centers' ? 'Joint Centers' : 'Joint Rotations'}"))`) || 
                                this.previewContent.querySelector('.file-preview h5')?.parentElement;
        
        if (existingPreview) {
            existingPreview.outerHTML = previewHtml;
        } else {
            this.previewContent.innerHTML += previewHtml;
        }
        
        this.dataPreview.style.display = 'block';
    }
    
    updateUploadButton() {
        const hasAllFiles = this.centersFile && this.rotationsFile;
        this.uploadBtn.disabled = !hasAllFiles;
        
        if (hasAllFiles) {
            this.uploadBtn.textContent = '🚀 Process & Visualize Motion Data';
        } else {
            this.uploadBtn.textContent = 'Select both CSV files to continue';
        }
    }
    
    async uploadFiles() {
        if (!this.centersFile || !this.rotationsFile) {
            this.showMessage('error', 'Please select both CSV files');
            return;
        }
        
        // Show loading state
        this.uploadBtn.disabled = true;
        this.uploadBtn.textContent = '⏳ Processing...';
        this.showMessage('info', 'Uploading and processing CSV files...');
        
        try {
            // Create FormData
            const formData = new FormData();
            formData.append('joint_centers', this.centersFile);
            formData.append('joint_rotations', this.rotationsFile);
            
            // Upload files
            const response = await fetch('/api/upload-csv', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.handleUploadSuccess(result);
            } else {
                this.handleUploadError(result.error);
            }
            
        } catch (error) {
            this.handleUploadError(`Upload failed: ${error.message}`);
        }
    }
    
    handleUploadSuccess(result) {
        this.uploadedData = result;
        
        // Show success message
        this.showMessage('success', `✅ ${result.message}`);
        
        // Display validation info
        const validationInfo = `
            <div class="validation-info">
                <h4>📊 File Validation Results</h4>
                <div class="validation-details">
                    <div class="file-validation">
                        <strong>Joint Centers CSV:</strong>
                        <ul>
                            <li>Rows: ${result.validation.centers.rows}</li>
                            <li>Columns: ${result.validation.centers.columns}</li>
                            <li>Numeric Columns: ${result.validation.centers.numeric_columns}</li>
                        </ul>
                    </div>
                    <div class="file-validation">
                        <strong>Joint Rotations CSV:</strong>
                        <ul>
                            <li>Rows: ${result.validation.rotations.rows}</li>
                            <li>Columns: ${result.validation.rotations.columns}</li>
                            <li>Numeric Columns: ${result.validation.rotations.numeric_columns}</li>
                        </ul>
                    </div>
                </div>
                <div class="motion-summary">
                    <h5>Motion Data Summary:</h5>
                    <ul>
                        <li>Total Frames: ${result.summary.totalFrames}</li>
                        <li>Duration: ${result.summary.duration.toFixed(2)} seconds</li>
                        <li>Frame Rate: ${result.summary.frameRate} FPS</li>
                        <li>Joints: ${result.summary.jointNames.length}</li>
                    </ul>
                </div>
            </div>
        `;
        
        this.previewContent.innerHTML = validationInfo;
        this.dataPreview.style.display = 'block';
        
        // Update button
        this.uploadBtn.textContent = '✅ Files Processed Successfully';
        this.uploadBtn.disabled = false;
        
        // Initialize motion viewer
        this.initializeMotionViewer();
        
        // Show motion controls
        this.motionControls.style.display = 'block';
    }
    
    handleUploadError(error) {
        this.showMessage('error', `❌ ${error}`);
        
        // Reset button
        this.uploadBtn.disabled = false;
        this.uploadBtn.textContent = '🚀 Process & Visualize Motion Data';
    }
    
    async initializeMotionViewer() {
        try {
            // Clear the motion viewer placeholder
            this.motionViewer.innerHTML = '';
            
            // Initialize 3D viewer
            if (window.MotionViewer) {
                const viewer = new window.MotionViewer(this.motionViewer);
                await viewer.loadMotionData();
                
                // Connect controls
                this.connectMotionControls(viewer);
            } else {
                this.motionViewer.innerHTML = '<div class="error">Motion viewer not available</div>';
            }
            
        } catch (error) {
            console.error('Error initializing motion viewer:', error);
            this.motionViewer.innerHTML = `<div class="error">Failed to load motion viewer: ${error.message}</div>`;
        }
    }
    
    connectMotionControls(viewer) {
        // Connect play/pause/reset buttons
        const playBtn = document.getElementById('play-btn');
        const pauseBtn = document.getElementById('pause-btn');
        const resetBtn = document.getElementById('reset-btn');
        
        playBtn?.addEventListener('click', () => viewer.play());
        pauseBtn?.addEventListener('click', () => viewer.pause());
        resetBtn?.addEventListener('click', () => viewer.reset());
        
        // Connect sliders
        const frameSlider = document.getElementById('frame-slider');
        const speedSlider = document.getElementById('speed-slider');
        const frameDisplay = document.getElementById('frame-display');
        const speedDisplay = document.getElementById('speed-display');
        
        if (frameSlider && viewer.getTotalFrames) {
            const totalFrames = viewer.getTotalFrames();
            frameSlider.max = totalFrames - 1;
            frameDisplay.textContent = `0 / ${totalFrames}`;
            
            frameSlider.addEventListener('input', (e) => {
                const frame = parseInt(e.target.value);
                viewer.setFrame(frame);
                frameDisplay.textContent = `${frame} / ${totalFrames}`;
            });
        }
        
        if (speedSlider) {
            speedSlider.addEventListener('input', (e) => {
                const speed = parseFloat(e.target.value);
                viewer.setSpeed(speed);
                speedDisplay.textContent = `${speed.toFixed(1)}x`;
            });
        }
    }
    
    showMessage(type, message) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = message;
        
        // Add to status messages
        this.statusMessages.appendChild(messageDiv);
        
        // Auto-remove info messages after 5 seconds
        if (type === 'info') {
            setTimeout(() => {
                messageDiv.remove();
            }, 5000);
        }
        
        // Scroll to bottom
        this.statusMessages.scrollTop = this.statusMessages.scrollHeight;
    }
    
    clearMessages() {
        this.statusMessages.innerHTML = '';
    }
    
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    // Public API methods
    async clearData() {
        try {
            const response = await fetch('/api/clear-data', {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showMessage('success', 'Data cleared successfully');
                this.reset();
            } else {
                this.showMessage('error', `Failed to clear data: ${result.error}`);
            }
        } catch (error) {
            this.showMessage('error', `Error clearing data: ${error.message}`);
        }
    }
    
    reset() {
        // Reset file inputs
        this.centersInput.value = '';
        this.rotationsInput.value = '';
        this.centersFile = null;
        this.rotationsFile = null;
        
        // Reset UI
        this.updateUploadButton();
        this.dataPreview.style.display = 'none';
        this.previewContent.innerHTML = '';
        this.motionControls.style.display = 'none';
        this.motionViewer.innerHTML = 'Upload CSV files to view 3D motion animation';
        
        // Clear uploaded data
        this.uploadedData = null;
    }
}

// Initialize CSV uploader when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.csvUploader = new CSVUploader();
    
    // Add some CSS for drag and drop
    const style = document.createElement('style');
    style.textContent = `
        .drag-over {
            border-color: #007bff !important;
            background-color: #f8f9ff !important;
        }
        
        .file-preview {
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            background: #f8f9fa;
        }
        
        .preview-lines {
            margin-top: 10px;
            font-family: monospace;
            font-size: 0.8em;
        }
        
        .preview-line {
            margin-bottom: 5px;
            padding: 5px;
            background: white;
            border-radius: 3px;
        }
        
        .validation-info {
            font-size: 0.9em;
        }
        
        .validation-details {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin: 15px 0;
        }
        
        .file-validation ul,
        .motion-summary ul {
            margin: 8px 0;
            padding-left: 20px;
        }
        
        .motion-summary {
            grid-column: 1 / -1;
            padding-top: 15px;
            border-top: 1px solid #e9ecef;
        }
    `;
    document.head.appendChild(style);
});

// Export for use in other modules
window.CSVUploader = CSVUploader;