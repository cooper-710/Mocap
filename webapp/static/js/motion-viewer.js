/**
 * Motion Capture Viewer using Three.js
 * Displays 3D anatomical skeleton animation from JSON motion data
 */

import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

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

        // Skeleton
        this.gltfSkeleton = null;   // The anatomical skeleton model
        this.boneMap = {};          // Map mocap joint names → skeleton bone objects

        // Ground
        this.groundPlane = null;

        // Clock for animation
        this.clock = new THREE.Clock();

        this.init();
    }

    /* ---------------- Initialization ---------------- */

    init() {
        this.setupScene();
        this.setupCamera();
        this.setupRenderer();
        this.setupLights();
        this.setupControls();
        this.setupGround();

        // Load the anatomical skeleton
        this.loadGLTFSkeleton();

        // Start render loop
        this.animate();

        window.addEventListener('resize', () => this.onWindowResize(), false);
    }

    setupScene() {
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x222222);

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
        const ambientLight = new THREE.AmbientLight(0x404040, 0.6);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(50, 100, 50);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        this.scene.add(directionalLight);

        const pointLight = new THREE.PointLight(0xffffff, 0.5, 200);
        pointLight.position.set(0, 80, 0);
        this.scene.add(pointLight);
    }

    setupControls() {
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
        this.scene.add(this.groundPlane);
    }

    /* ---------------- GLTF Skeleton ---------------- */

    loadGLTFSkeleton() {
        const loader = new GLTFLoader();
        loader.load('/static/models/skeleton.glb', (gltf) => {
            this.gltfSkeleton = gltf.scene;

            // Scale & position
            this.gltfSkeleton.scale.set(0.01, 0.01, 0.01);
            this.gltfSkeleton.position.set(0, 0, 0);

            // Optional glow
            this.gltfSkeleton.traverse((child) => {
                if (child.isMesh) {
                    child.material.emissive = new THREE.Color(0x00ffff);
                    child.material.emissiveIntensity = 0.4;
                }
            });

            this.scene.add(this.gltfSkeleton);

            // Build bone map (so we can animate bones later)
            this.gltfSkeleton.traverse((bone) => {
                if (bone.isBone) {
                    this.boneMap[bone.name] = bone;
                }
            });

        }, undefined, (error) => {
            console.error('Error loading GLTF skeleton:', error);
        });
    }

    /* ---------------- Motion Data ---------------- */

    async loadMotionData(url) {
        try {
            this.showLoading();
            const response = await fetch(url);
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            this.motionData = await response.json();
            if (this.motionData.error) throw new Error(this.motionData.error);

            this.setupAnimation();
            this.hideLoading();

            console.log('Motion data loaded:', {
                joints: this.motionData.jointNames.length,
                frames: this.motionData.totalFrames
            });

            return this.motionData;
        } catch (error) {
            console.error('Error loading motion data:', error);
            this.showError('Failed to load motion data: ' + error.message);
            throw error;
        }
    }

    setupAnimation() {
        if (!this.motionData || !this.motionData.frames || this.motionData.frames.length === 0) {
            throw new Error('Invalid motion data');
        }

        this.totalFrames = this.motionData.totalFrames;
        this.frameRate = this.motionData.frameRate;
        this.currentFrame = 0;

        this.setFrame(0);
    }

    /* ---------------- Frame Updates ---------------- */

    setFrame(frameNumber) {
        if (!this.motionData || !this.motionData.frames) return;

        frameNumber = Math.max(0, Math.min(frameNumber, this.totalFrames - 1));
        this.currentFrame = frameNumber;

        const frameData = this.motionData.frames[frameNumber];
        this.updateSkeleton(frameData);
    }

    updateSkeleton(frameData) {
        if (!this.gltfSkeleton || !frameData) return;

        // TODO: Map mocap joints → skeleton bones here
        // Example (replace with your actual joint/bone names):
        /*
        const hip = this.boneMap['Hips'];
        const mocapHip = frameData['HipCenter'];
        if (hip && mocapHip) {
            hip.position.set(mocapHip.x, mocapHip.y, mocapHip.z);
        }
        */
    }

    /* ---------------- Playback ---------------- */

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

    setSpeed(speed) {
        this.animationSpeed = Math.max(0.1, Math.min(speed, 5.0));
    }

    animate() {
        requestAnimationFrame(() => this.animate());

        if (this.isPlaying && this.motionData && this.totalFrames > 0) {
            const currentTime = this.clock.getElapsedTime();
            const deltaTime = currentTime - this.lastFrameTime;
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

    /* ---------------- UI Helpers ---------------- */

    showLoading() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) loadingElement.style.display = 'flex';
    }

    hideLoading() {
        const loadingElement = document.getElementById('loading');
        if (loadingElement) loadingElement.style.display = 'none';
    }

    showError(message) {
        this.hideLoading();
        console.error(message);
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
        setTimeout(() => {
            if (errorElement.parentNode) errorElement.remove();
        }, 10000);
    }

    /* ---------------- Getters ---------------- */

    getCurrentFrame() { return this.currentFrame; }
    getTotalFrames() { return this.totalFrames; }
    getIsPlaying() { return this.isPlaying; }
    getMotionData() { return this.motionData; }
}

export default MotionViewer;
