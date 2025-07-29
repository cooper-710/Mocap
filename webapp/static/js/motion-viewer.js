/**
 * Motion Capture Viewer using Three.js
 * Displays 3D skeletal animation from JSON motion data (no BVH)
 */

class MotionViewer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        
        // Animation data
        this.motionData = null;
        this.currentFrame = 0;
        this.totalFrames = 0;
        this.frameRate = 30.0;
        this.animationSpeed = 1.0;
        this.isPlaying = false;
        this.lastFrameTime = 0;
        
        // Visualization objects
        this.jointSpheres = new Map(); // Map<jointName, THREE.Mesh>
        this.boneLines = new Map();    // Map<boneName, THREE.Line>
        this.groundPlane = null;
        this.trajectoryLine = null;
        
        // Settings
        this.showSkeleton = true;
        this.showJoints = true;
        this.showGround = false;
        this.showTrajectory = false;
        
        // Performance
        this.clock = new THREE.Clock();
        
        this.init();
    }

    init() {
        this.setupScene();
        this.setupCamera();
        this.setupRenderer();
        this.setupLights();
        this.setupControls();
        this.setupGround();
        
        // Start render loop
        this.animate();
        
        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize(), false);
    }

    setupScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x222222);
        
        // Add coordinate system helper
        const axesHelper = new THREE.AxesHelper(50);
        this.scene.add(axesHelper);
    }

    setupCamera() {
        const aspect = this.canvas.clientWidth / this.canvas.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        this.camera.position.set(100, 100, 100);
        this.camera.lookAt(0, 50, 0);
    }

    setupRenderer() {
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true
        });
        this.renderer.setSize(this.canvas.clientWidth, this.canvas.clientHeight);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    }

    setupLights() {
        // Ambient light
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);

        // Directional light (sun)
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(50, 100, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 500;
        directionalLight.shadow.camera.left = -100;
        directionalLight.shadow.camera.right = 100;
        directionalLight.shadow.camera.top = 100;
        directionalLight.shadow.camera.bottom = -100;
        this.scene.add(directionalLight);

        // Point light for better illumination
        const pointLight = new THREE.PointLight(0xffffff, 0.5, 200);
        pointLight.position.set(0, 80, 0);
        this.scene.add(pointLight);
    }

    setupControls() {
        // Basic mouse controls for camera movement
        this.setupBasicControls();
    }

    setupBasicControls() {
        let isMouseDown = false;
        let mouseX = 0, mouseY = 0;
        let targetX = 0, targetY = 0;

        this.canvas.addEventListener('mousedown', (event) => {
            isMouseDown = true;
            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        this.canvas.addEventListener('mousemove', (event) => {
            if (!isMouseDown) return;

            const deltaX = event.clientX - mouseX;
            const deltaY = event.clientY - mouseY;

            targetX += deltaX * 0.01;
            targetY += deltaY * 0.01;

            // Rotate camera around the scene
            const radius = 150;
            this.camera.position.x = Math.cos(targetX) * radius;
            this.camera.position.z = Math.sin(targetX) * radius;
            this.camera.position.y = Math.max(10, 100 + targetY * 50);
            
            this.camera.lookAt(0, 50, 0);

            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        this.canvas.addEventListener('mouseup', () => {
            isMouseDown = false;
        });

        // Zoom with mouse wheel
        this.canvas.addEventListener('wheel', (event) => {
            const scale = event.deltaY > 0 ? 1.1 : 0.9;
            this.camera.position.multiplyScalar(scale);
            this.camera.lookAt(0, 50, 0);
            event.preventDefault();
        });
    }

    setupGround() {
        const groundGeometry = new THREE.PlaneGeometry(200, 200);
        const groundMaterial = new THREE.MeshLambertMaterial({ 
            color: 0x444444,
            transparent: true,
            opacity: 0.3
        });
        this.groundPlane = new THREE.Mesh(groundGeometry, groundMaterial);
        this.groundPlane.rotation.x = -Math.PI / 2;
        this.groundPlane.position.y = 0;
        this.groundPlane.receiveShadow = true;
        this.groundPlane.visible = this.showGround;
        this.scene.add(this.groundPlane);
    }

    async loadMotionData(url) {
        try {
            this.showLoading();
            
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.motionData = await response.json();
            
            if (this.motionData.error) {
                throw new Error(this.motionData.error);
            }
            
            this.setupAnimation();
            this.hideLoading();
            
            console.log('Motion data loaded successfully:', {
                joints: this.motionData.jointNames.length,
                bones: this.motionData.boneConnections.length,
                frames: this.motionData.totalFrames,
                duration: this.motionData.duration
            });
            
            return this.motionData;
            
        } catch (error) {
            console.error('Error loading motion data:', error);
            this.showError('Failed to load motion data: ' + error.message);
            throw error;
        }
    }

    setupAnimation() {
        // Clear existing visualization
        this.clearVisualization();
        
        if (!this.motionData || !this.motionData.frames || this.motionData.frames.length === 0) {
            throw new Error('Invalid motion data');
        }
        
        // Set animation properties
        this.totalFrames = this.motionData.totalFrames;
        this.frameRate = this.motionData.frameRate;
        this.currentFrame = 0;
        
        // Create joint spheres
        this.createJointSpheres();
        
        // Create bone connections
        this.createBoneConnections();
        
        // Set initial frame
        this.setFrame(0);
        
        console.log(`Animation setup complete: ${this.totalFrames} frames at ${this.frameRate} FPS`);
    }

    createJointSpheres() {
        this.clearJointSpheres();
        
        const sphereGeometry = new THREE.SphereGeometry(2.0, 12, 8);
        
        this.motionData.jointNames.forEach(jointName => {
            // Different colors for different body parts
            let color = 0x00ff88; // Default green
            
            if (jointName.includes('Head') || jointName.includes('Neck')) {
                color = 0xff4444; // Red for head/neck
            } else if (jointName.includes('Left')) {
                color = 0x4444ff; // Blue for left side
            } else if (jointName.includes('Right')) {
                color = 0xffaa00; // Orange for right side
            } else if (jointName.includes('Spine') || jointName.includes('Hips')) {
                color = 0xff88ff; // Magenta for spine
            }
            
            const sphereMaterial = new THREE.MeshLambertMaterial({ color });
            const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
            sphere.castShadow = true;
            sphere.visible = this.showJoints;
            
            this.jointSpheres.set(jointName, sphere);
            this.scene.add(sphere);
        });
    }

    createBoneConnections() {
        this.clearBoneConnections();
        
        const lineMaterial = new THREE.LineBasicMaterial({ 
            color: 0xffffff,
            linewidth: 3
        });
        
        this.motionData.boneConnections.forEach(([parentJoint, childJoint]) => {
            const lineGeometry = new THREE.BufferGeometry();
            const positions = new Float32Array(6); // 2 points × 3 coordinates
            lineGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
            
            const line = new THREE.Line(lineGeometry, lineMaterial);
            line.visible = this.showSkeleton;
            
            const boneName = `${parentJoint}-${childJoint}`;
            this.boneLines.set(boneName, line);
            this.scene.add(line);
        });
    }

    clearVisualization() {
        this.clearJointSpheres();
        this.clearBoneConnections();
    }

    clearJointSpheres() {
        this.jointSpheres.forEach(sphere => {
            this.scene.remove(sphere);
        });
        this.jointSpheres.clear();
    }

    clearBoneConnections() {
        this.boneLines.forEach(line => {
            this.scene.remove(line);
        });
        this.boneLines.clear();
    }

    updateVisualization(frameData) {
        if (!frameData) return;
        
        // Update joint positions
        for (const [jointName, jointData] of Object.entries(frameData)) {
            const sphere = this.jointSpheres.get(jointName);
            if (sphere && jointData) {
                sphere.position.set(jointData.x, jointData.y, jointData.z);
                
                // Apply rotation if available
                if (jointData.rx !== undefined) {
                    sphere.rotation.set(
                        THREE.MathUtils.degToRad(jointData.rx),
                        THREE.MathUtils.degToRad(jointData.ry),
                        THREE.MathUtils.degToRad(jointData.rz)
                    );
                }
            }
        }
        
        // Update bone connections
        this.motionData.boneConnections.forEach(([parentJoint, childJoint]) => {
            const parentData = frameData[parentJoint];
            const childData = frameData[childJoint];
            const boneName = `${parentJoint}-${childJoint}`;
            const line = this.boneLines.get(boneName);
            
            if (line && parentData && childData) {
                const positions = line.geometry.attributes.position.array;
                
                // Parent position
                positions[0] = parentData.x;
                positions[1] = parentData.y;
                positions[2] = parentData.z;
                
                // Child position
                positions[3] = childData.x;
                positions[4] = childData.y;
                positions[5] = childData.z;
                
                line.geometry.attributes.position.needsUpdate = true;
            }
        });
    }

    play() {
        this.isPlaying = true;
        this.lastFrameTime = this.clock.getElapsedTime();
    }

    pause() {
        this.isPlaying = false;
    }

    stop() {
        this.isPlaying = false;
        this.setFrame(0);
    }

    setFrame(frameNumber) {
        if (!this.motionData || !this.motionData.frames) return;
        
        frameNumber = Math.max(0, Math.min(frameNumber, this.totalFrames - 1));
        this.currentFrame = frameNumber;
        
        const frameData = this.motionData.frames[frameNumber];
        this.updateVisualization(frameData);
    }

    setSpeed(speed) {
        this.animationSpeed = Math.max(0.1, Math.min(speed, 5.0));
    }

    setViewMode(mode) {
        switch (mode) {
            case 'front':
                this.camera.position.set(0, 50, 150);
                this.camera.lookAt(0, 50, 0);
                break;
            case 'side':
                this.camera.position.set(150, 50, 0);
                this.camera.lookAt(0, 50, 0);
                break;
            case 'top':
                this.camera.position.set(0, 200, 0);
                this.camera.lookAt(0, 0, 0);
                break;
            case 'free':
            default:
                this.camera.position.set(100, 100, 100);
                this.camera.lookAt(0, 50, 0);
                break;
        }
    }

    toggleSkeleton(show) {
        this.showSkeleton = show;
        this.boneLines.forEach(line => {
            line.visible = show;
        });
    }

    toggleJoints(show) {
        this.showJoints = show;
        this.jointSpheres.forEach(sphere => {
            sphere.visible = show;
        });
    }

    toggleGround(show) {
        this.showGround = show;
        if (this.groundPlane) {
            this.groundPlane.visible = show;
        }
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        // Handle frame animation
        if (this.isPlaying && this.motionData && this.totalFrames > 0) {
            const currentTime = this.clock.getElapsedTime();
            const deltaTime = currentTime - this.lastFrameTime;
            
            // Calculate frames to advance based on frame rate and speed
            const frameAdvance = deltaTime * this.frameRate * this.animationSpeed;
            
            if (frameAdvance >= 1.0) {
                const newFrame = (this.currentFrame + Math.floor(frameAdvance)) % this.totalFrames;
                this.setFrame(newFrame);
                this.lastFrameTime = currentTime;
            }
        }

        this.renderer.render(this.scene, this.camera);
    }

    onWindowResize() {
        const width = this.canvas.clientWidth;
        const height = this.canvas.clientHeight;

        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();

        this.renderer.setSize(width, height);
    }

    showLoading() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'flex';
        }
    }

    hideLoading() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) {
            loadingElement.style.display = 'none';
        }
    }

    showError(message) {
        this.hideLoading();
        console.error(message);
        
        // Show error in UI instead of alert
        const errorElement = document.createElement('div');
        errorElement.className = 'error-message';
        errorElement.textContent = message;
        errorElement.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(255, 0, 0, 0.9);
            color: white;
            padding: 20px;
            border-radius: 8px;
            max-width: 400px;
            text-align: center;
            z-index: 1000;
        `;
        
        document.body.appendChild(errorElement);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (errorElement.parentNode) {
                errorElement.remove();
            }
        }, 10000);
    }

    // Getter methods for compatibility
    getCurrentFrame() {
        return this.currentFrame;
    }

    getTotalFrames() {
        return this.totalFrames;
    }

    getIsPlaying() {
        return this.isPlaying;
    }

    getMotionData() {
        return this.motionData;
    }
}