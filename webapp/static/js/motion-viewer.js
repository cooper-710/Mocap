/**
 * Motion Capture Viewer using Three.js
 * Displays 3D skeletal animation from JSON motion data (CSV-based)
 */

class MotionViewer {
    constructor(container) {
        this.container = container;
        this.canvas = null;
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
        this.showGround = true;
        this.showTrajectory = false;
        
        // Performance
        this.clock = new THREE.Clock();
        
        this.init();
    }

    init() {
        this.setupCanvas();
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

    setupCanvas() {
        // Create canvas element
        this.canvas = document.createElement('canvas');
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.display = 'block';
        this.container.appendChild(this.canvas);
    }

    setupScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a1a);
        
        // Add coordinate system helper
        const axesHelper = new THREE.AxesHelper(50);
        this.scene.add(axesHelper);
    }

    setupCamera() {
        const aspect = this.container.clientWidth / this.container.clientHeight;
        this.camera = new THREE.PerspectiveCamera(45, aspect, 0.1, 1000);
        this.camera.position.set(200, 150, 200);
        this.camera.lookAt(0, 100, 0);
    }

    setupRenderer() {
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true
        });
        this.renderer.setSize(this.container.clientWidth, this.container.clientHeight);
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
        directionalLight.position.set(50, 200, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 0.5;
        directionalLight.shadow.camera.far = 500;
        directionalLight.shadow.camera.left = -200;
        directionalLight.shadow.camera.right = 200;
        directionalLight.shadow.camera.top = 200;
        directionalLight.shadow.camera.bottom = -200;
        this.scene.add(directionalLight);

        // Additional fill light
        const fillLight = new THREE.DirectionalLight(0x4080ff, 0.3);
        fillLight.position.set(-50, 50, -50);
        this.scene.add(fillLight);
    }

    setupControls() {
        // OrbitControls for camera movement
        this.controls = new THREE.OrbitControls(this.camera, this.canvas);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.05;
        this.controls.target.set(0, 100, 0);
        this.controls.minDistance = 50;
        this.controls.maxDistance = 500;
        this.controls.maxPolarAngle = Math.PI * 0.9;
    }

    setupGround() {
        // Ground plane
        const groundGeometry = new THREE.PlaneGeometry(400, 400);
        const groundMaterial = new THREE.MeshLambertMaterial({ 
            color: 0x2a2a2a,
            transparent: true,
            opacity: 0.8
        });
        this.groundPlane = new THREE.Mesh(groundGeometry, groundMaterial);
        this.groundPlane.rotation.x = -Math.PI / 2;
        this.groundPlane.receiveShadow = true;
        this.groundPlane.visible = this.showGround;
        this.scene.add(this.groundPlane);

        // Grid helper
        const gridHelper = new THREE.GridHelper(400, 40, 0x666666, 0x333333);
        gridHelper.visible = this.showGround;
        this.scene.add(gridHelper);
    }

    async loadMotionData() {
        try {
            console.log('Loading motion data from CSV upload...');
            
            const response = await fetch('/api/motion-data');
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            this.motionData = await response.json();
            
            if (this.motionData.error) {
                throw new Error(this.motionData.error);
            }
            
            console.log('Motion data loaded:', {
                frames: this.motionData.totalFrames,
                joints: this.motionData.jointNames.length,
                duration: this.motionData.duration
            });
            
            // Initialize visualization
            this.totalFrames = this.motionData.totalFrames;
            this.frameRate = this.motionData.frameRate;
            
            this.createSkeleton();
            this.updateFrame(0);
            
            return true;
            
        } catch (error) {
            console.error('Failed to load motion data:', error);
            this.showError(`Failed to load motion data: ${error.message}`);
            return false;
        }
    }

    createSkeleton() {
        if (!this.motionData) return;
        
        // Clear existing skeleton
        this.clearSkeleton();
        
        // Create joint spheres
        this.motionData.jointNames.forEach(jointName => {
            const geometry = new THREE.SphereGeometry(2, 16, 16);
            const material = new THREE.MeshPhongMaterial({ 
                color: 0x00ff88,
                transparent: true,
                opacity: 0.8
            });
            const sphere = new THREE.Mesh(geometry, material);
            sphere.castShadow = true;
            sphere.visible = this.showJoints;
            this.scene.add(sphere);
            this.jointSpheres.set(jointName, sphere);
        });
        
        // Create bone connections
        this.motionData.boneConnections.forEach(([parentJoint, childJoint]) => {
            const geometry = new THREE.BufferGeometry().setFromPoints([
                new THREE.Vector3(0, 0, 0),
                new THREE.Vector3(0, 0, 0)
            ]);
            const material = new THREE.LineBasicMaterial({ 
                color: 0x00aaff,
                linewidth: 3
            });
            const line = new THREE.Line(geometry, material);
            line.visible = this.showSkeleton;
            this.scene.add(line);
            
            const boneName = `${parentJoint}-${childJoint}`;
            this.boneLines.set(boneName, line);
        });
        
        console.log(`Created skeleton with ${this.jointSpheres.size} joints and ${this.boneLines.size} bones`);
    }

    clearSkeleton() {
        // Remove joint spheres
        this.jointSpheres.forEach(sphere => {
            this.scene.remove(sphere);
            sphere.geometry.dispose();
            sphere.material.dispose();
        });
        this.jointSpheres.clear();
        
        // Remove bone lines
        this.boneLines.forEach(line => {
            this.scene.remove(line);
            line.geometry.dispose();
            line.material.dispose();
        });
        this.boneLines.clear();
    }

    updateFrame(frameIndex) {
        if (!this.motionData || !this.motionData.frames || frameIndex >= this.motionData.frames.length) {
            return;
        }
        
        this.currentFrame = frameIndex;
        const frameData = this.motionData.frames[frameIndex];
        
        // Update joint positions and rotations
        this.motionData.jointNames.forEach(jointName => {
            const sphere = this.jointSpheres.get(jointName);
            if (sphere && frameData[jointName]) {
                const data = frameData[jointName];
                sphere.position.set(data.x, data.y, data.z);
                
                // Apply rotation (convert degrees to radians)
                sphere.rotation.set(
                    THREE.MathUtils.degToRad(data.rx),
                    THREE.MathUtils.degToRad(data.ry),
                    THREE.MathUtils.degToRad(data.rz)
                );
            }
        });
        
        // Update bone connections
        this.motionData.boneConnections.forEach(([parentJoint, childJoint]) => {
            const boneName = `${parentJoint}-${childJoint}`;
            const line = this.boneLines.get(boneName);
            const parentSphere = this.jointSpheres.get(parentJoint);
            const childSphere = this.jointSpheres.get(childJoint);
            
            if (line && parentSphere && childSphere) {
                const positions = line.geometry.attributes.position;
                positions.setXYZ(0, parentSphere.position.x, parentSphere.position.y, parentSphere.position.z);
                positions.setXYZ(1, childSphere.position.x, childSphere.position.y, childSphere.position.z);
                positions.needsUpdate = true;
            }
        });
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        
        // Update controls
        if (this.controls) {
            this.controls.update();
        }
        
        // Update animation
        if (this.isPlaying && this.motionData) {
            const currentTime = this.clock.getElapsedTime();
            const deltaTime = currentTime - this.lastFrameTime;
            const frameDuration = 1.0 / (this.frameRate * this.animationSpeed);
            
            if (deltaTime >= frameDuration) {
                this.currentFrame = (this.currentFrame + 1) % this.totalFrames;
                this.updateFrame(this.currentFrame);
                this.lastFrameTime = currentTime;
                
                // Notify frame change
                this.onFrameChanged(this.currentFrame);
            }
        }
        
        // Render scene
        if (this.renderer && this.scene && this.camera) {
            this.renderer.render(this.scene, this.camera);
        }
    }

    onFrameChanged(frameIndex) {
        // Override this method to handle frame changes
        // Used by UI controls to update frame display
    }

    // Animation controls
    play() {
        this.isPlaying = true;
        this.lastFrameTime = this.clock.getElapsedTime();
        console.log('Animation started');
    }

    pause() {
        this.isPlaying = false;
        console.log('Animation paused');
    }

    reset() {
        this.isPlaying = false;
        this.currentFrame = 0;
        if (this.motionData) {
            this.updateFrame(0);
        }
        console.log('Animation reset');
    }

    setFrame(frameIndex) {
        if (frameIndex >= 0 && frameIndex < this.totalFrames) {
            this.currentFrame = frameIndex;
            this.updateFrame(frameIndex);
        }
    }

    setSpeed(speed) {
        this.animationSpeed = Math.max(0.1, Math.min(3.0, speed));
        console.log(`Animation speed set to ${this.animationSpeed}x`);
    }

    // View controls
    setView(viewType) {
        if (!this.camera) return;
        
        const distance = 200;
        const target = new THREE.Vector3(0, 100, 0);
        
        switch (viewType) {
            case 'front':
                this.camera.position.set(0, 100, distance);
                break;
            case 'side':
                this.camera.position.set(distance, 100, 0);
                break;
            case 'top':
                this.camera.position.set(0, distance + 100, 0);
                break;
            case 'free':
            default:
                this.camera.position.set(distance, 150, distance);
                break;
        }
        
        this.camera.lookAt(target);
        if (this.controls) {
            this.controls.target.copy(target);
            this.controls.update();
        }
    }

    // Visibility controls
    toggleSkeleton() {
        this.showSkeleton = !this.showSkeleton;
        this.boneLines.forEach(line => {
            line.visible = this.showSkeleton;
        });
    }

    toggleJoints() {
        this.showJoints = !this.showJoints;
        this.jointSpheres.forEach(sphere => {
            sphere.visible = this.showJoints;
        });
    }

    toggleGround() {
        this.showGround = !this.showGround;
        if (this.groundPlane) {
            this.groundPlane.visible = this.showGround;
        }
    }

    // Utility methods
    getTotalFrames() {
        return this.totalFrames;
    }

    getCurrentFrame() {
        return this.currentFrame;
    }

    getFrameRate() {
        return this.frameRate;
    }

    getDuration() {
        return this.totalFrames / this.frameRate;
    }

    showError(message) {
        this.container.innerHTML = `
            <div style="
                display: flex;
                align-items: center;
                justify-content: center;
                height: 100%;
                color: #dc3545;
                font-size: 1.1em;
                text-align: center;
                padding: 20px;
            ">
                <div>
                    <div style="font-size: 2em; margin-bottom: 10px;">⚠️</div>
                    <div>${message}</div>
                </div>
            </div>
        `;
    }

    onWindowResize() {
        if (this.camera && this.renderer) {
            const width = this.container.clientWidth;
            const height = this.container.clientHeight;
            
            this.camera.aspect = width / height;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(width, height);
        }
    }

    // Cleanup
    dispose() {
        // Cancel animation
        this.isPlaying = false;
        
        // Clear skeleton
        this.clearSkeleton();
        
        // Dispose of Three.js resources
        if (this.renderer) {
            this.renderer.dispose();
        }
        
        if (this.controls) {
            this.controls.dispose();
        }
        
        // Clear container
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

// Export for use in other modules
window.MotionViewer = MotionViewer;