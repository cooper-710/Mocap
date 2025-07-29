/**
 * Motion Capture Viewer using Three.js
 * Displays 3D skeletal animation from BVH data
 */

class MotionViewer {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        
        // Animation
        this.mixer = null;
        this.action = null;
        this.clock = new THREE.Clock();
        this.isPlaying = false;
        this.currentFrame = 0;
        this.totalFrames = 0;
        this.animationSpeed = 1.0;
        
        // Visualization objects
        this.skeletonMesh = null;
        this.skeletonHelper = null;
        this.jointSpheres = [];
        this.groundPlane = null;
        this.trajectoryLine = null;
        
        // Settings
        this.showSkeleton = true;
        this.showJoints = true;
        this.showGround = false;
        this.showTrajectory = false;
        
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
        // Note: You might need to include OrbitControls separately
        // For now, we'll implement basic mouse controls
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

    async loadBVH(url) {
        try {
            const loader = new BVHLoader();
            const bvhData = await loader.load(url);
            
            this.setupAnimation(bvhData);
            this.hideLoading();
            
            return bvhData;
        } catch (error) {
            console.error('Error loading BVH:', error);
            this.showError('Failed to load motion data: ' + error.message);
            throw error;
        }
    }

    setupAnimation(bvhData) {
        // Remove existing skeleton
        if (this.skeletonMesh) {
            this.scene.remove(this.skeletonMesh);
        }
        if (this.skeletonHelper) {
            this.scene.remove(this.skeletonHelper);
        }
        this.clearJointSpheres();

        // Create skeleton visualization
        const bones = bvhData.skeleton.bones;
        
        // Create skeleton helper for bone connections
        this.skeletonHelper = new SkeletonHelper(bvhData.skeleton);
        this.skeletonHelper.visible = this.showSkeleton;
        this.scene.add(this.skeletonHelper);

        // Create joint spheres
        this.createJointSpheres(bones);

        // Setup animation
        this.mixer = new THREE.AnimationMixer(bvhData.skeleton.bones[0]);
        this.action = this.mixer.clipAction(bvhData.clip);
        this.action.setLoop(THREE.LoopRepeat);
        
        this.totalFrames = bvhData.frames.length;
        this.animationDuration = bvhData.duration;
        
        console.log(`Loaded animation: ${this.totalFrames} frames, ${this.animationDuration.toFixed(2)} seconds`);
    }

    createJointSpheres(bones) {
        this.clearJointSpheres();
        
        const sphereGeometry = new THREE.SphereGeometry(1.5, 8, 6);
        const sphereMaterial = new THREE.MeshLambertMaterial({ color: 0x00ff88 });

        bones.forEach(bone => {
            const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
            sphere.castShadow = true;
            sphere.visible = this.showJoints;
            this.jointSpheres.push(sphere);
            this.scene.add(sphere);
        });
    }

    clearJointSpheres() {
        this.jointSpheres.forEach(sphere => {
            this.scene.remove(sphere);
        });
        this.jointSpheres = [];
    }

    updateJointSpheres() {
        if (!this.skeletonHelper || !this.skeletonHelper.skeleton) return;
        
        const bones = this.skeletonHelper.skeleton.bones;
        
        bones.forEach((bone, index) => {
            if (index < this.jointSpheres.length) {
                const worldPos = new THREE.Vector3();
                bone.getWorldPosition(worldPos);
                this.jointSpheres[index].position.copy(worldPos);
            }
        });
    }

    play() {
        if (this.action) {
            this.action.play();
            this.isPlaying = true;
        }
    }

    pause() {
        if (this.action) {
            this.action.paused = true;
            this.isPlaying = false;
        }
    }

    stop() {
        if (this.action) {
            this.action.stop();
            this.isPlaying = false;
            this.currentFrame = 0;
        }
    }

    setFrame(frameNumber) {
        if (this.action && this.animationDuration) {
            const time = (frameNumber / this.totalFrames) * this.animationDuration;
            this.action.time = time;
            this.currentFrame = frameNumber;
            
            if (this.mixer) {
                this.mixer.update(0); // Update without advancing time
            }
        }
    }

    setSpeed(speed) {
        this.animationSpeed = speed;
        if (this.action) {
            this.action.timeScale = speed;
        }
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
        if (this.skeletonHelper) {
            this.skeletonHelper.visible = show;
        }
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

        const deltaTime = this.clock.getDelta();

        if (this.mixer && this.isPlaying) {
            this.mixer.update(deltaTime);
            
            // Update current frame
            if (this.action) {
                const progress = this.action.time / this.animationDuration;
                this.currentFrame = Math.floor(progress * this.totalFrames);
            }
        }

        // Update joint spheres positions
        this.updateJointSpheres();

        // Update skeleton helper
        if (this.skeletonHelper) {
            this.skeletonHelper.updateMatrixWorld(true);
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
        document.getElementById('loading').style.display = 'flex';
    }

    hideLoading() {
        document.getElementById('loading').style.display = 'none';
    }

    showError(message) {
        this.hideLoading();
        console.error(message);
        // You could add a proper error display here
        alert('Error: ' + message);
    }

    getCurrentFrame() {
        return this.currentFrame;
    }

    getTotalFrames() {
        return this.totalFrames;
    }

    getIsPlaying() {
        return this.isPlaying;
    }
}