/**
 * BVH Loader for Three.js
 * Loads and parses BVH motion capture data for 3D skeletal animation
 */

class BVHLoader {
    constructor() {
        this.skeleton = null;
        this.clip = null;
        this.frames = [];
        this.frameTime = 1/30;
    }

    async load(url) {
        try {
            const response = await fetch(url);
            const text = await response.text();
            return this.parse(text);
        } catch (error) {
            console.error('Error loading BVH file:', error);
            throw error;
        }
    }

    parse(text) {
        const lines = text.split('\n');
        let lineIdx = 0;

        // Parse hierarchy
        if (lines[lineIdx].trim() !== 'HIERARCHY') {
            throw new Error('Invalid BVH file: missing HIERARCHY');
        }
        lineIdx++;

        const skeleton = this.parseJoint(lines, lineIdx);
        lineIdx = skeleton.lineIdx;

        // Parse motion data
        while (lineIdx < lines.length && lines[lineIdx].trim() !== 'MOTION') {
            lineIdx++;
        }

        if (lineIdx >= lines.length) {
            throw new Error('Invalid BVH file: missing MOTION section');
        }
        lineIdx++;

        // Parse frame info
        const frameMatch = lines[lineIdx].match(/Frames:\s*(\d+)/);
        if (!frameMatch) {
            throw new Error('Invalid BVH file: missing frame count');
        }
        const frameCount = parseInt(frameMatch[1]);
        lineIdx++;

        const timeMatch = lines[lineIdx].match(/Frame Time:\s*([\d.]+)/);
        if (!timeMatch) {
            throw new Error('Invalid BVH file: missing frame time');
        }
        this.frameTime = parseFloat(timeMatch[1]);
        lineIdx++;

        // Parse frame data
        const frames = [];
        for (let i = 0; i < frameCount && lineIdx < lines.length; i++) {
            const line = lines[lineIdx].trim();
            if (line) {
                const values = line.split(/\s+/).map(parseFloat);
                frames.push(values);
            }
            lineIdx++;
        }

        // Create Three.js objects
        const bones = this.createBones(skeleton.joint);
        const threeSkeleton = new THREE.Skeleton(bones);
        const clip = this.createAnimationClip(skeleton.joint, frames);

        return {
            skeleton: threeSkeleton,
            clip: clip,
            frames: frames,
            frameTime: this.frameTime,
            duration: frameCount * this.frameTime
        };
    }

    parseJoint(lines, startLine) {
        let lineIdx = startLine;
        const line = lines[lineIdx].trim();
        
        let jointType, jointName;
        if (line.startsWith('ROOT')) {
            jointType = 'ROOT';
            jointName = line.split(' ')[1];
        } else if (line.startsWith('JOINT')) {
            jointType = 'JOINT';
            jointName = line.split(' ')[1];
        } else {
            throw new Error(`Invalid joint declaration: ${line}`);
        }

        lineIdx++;

        // Expect opening brace
        if (lines[lineIdx].trim() !== '{') {
            throw new Error('Expected opening brace after joint declaration');
        }
        lineIdx++;

        const joint = {
            name: jointName,
            type: jointType,
            offset: [0, 0, 0],
            channels: [],
            children: []
        };

        // Parse joint properties
        while (lineIdx < lines.length) {
            const line = lines[lineIdx].trim();
            
            if (line.startsWith('OFFSET')) {
                const offset = line.split(/\s+/).slice(1).map(parseFloat);
                joint.offset = offset;
            } else if (line.startsWith('CHANNELS')) {
                const parts = line.split(/\s+/);
                const channelCount = parseInt(parts[1]);
                joint.channels = parts.slice(2, 2 + channelCount);
            } else if (line.startsWith('JOINT')) {
                const childResult = this.parseJoint(lines, lineIdx);
                joint.children.push(childResult.joint);
                lineIdx = childResult.lineIdx - 1; // -1 because we'll increment at the end
            } else if (line.startsWith('End Site')) {
                lineIdx++;
                // Skip end site for now
                let braceCount = 0;
                while (lineIdx < lines.length) {
                    const endLine = lines[lineIdx].trim();
                    if (endLine === '{') braceCount++;
                    else if (endLine === '}') {
                        braceCount--;
                        if (braceCount === 0) break;
                    }
                    lineIdx++;
                }
            } else if (line === '}') {
                lineIdx++;
                break;
            }
            
            lineIdx++;
        }

        return { joint: joint, lineIdx: lineIdx };
    }

    createBones(joint, parentBone = null, bones = []) {
        const bone = new THREE.Bone();
        bone.name = joint.name;
        bone.position.fromArray(joint.offset);

        if (parentBone) {
            parentBone.add(bone);
        }

        bones.push(bone);

        // Create children
        for (const child of joint.children) {
            this.createBones(child, bone, bones);
        }

        return bones;
    }

    createAnimationClip(rootJoint, frames) {
        const tracks = [];
        
        if (frames.length === 0) {
            return new THREE.AnimationClip('motion', 0, tracks);
        }

        const duration = frames.length * this.frameTime;
        const times = [];
        for (let i = 0; i < frames.length; i++) {
            times.push(i * this.frameTime);
        }

        // Create tracks for each joint
        this.createTracksForJoint(rootJoint, frames, times, tracks, 0);

        return new THREE.AnimationClip('motion', duration, tracks);
    }

    createTracksForJoint(joint, frames, times, tracks, channelOffset) {
        let offset = channelOffset;

        // Create position and rotation tracks based on channels
        if (joint.channels.includes('Xposition')) {
            const positions = [];
            for (const frame of frames) {
                const x = frame[offset] || 0;
                const y = frame[offset + 1] || 0;
                const z = frame[offset + 2] || 0;
                positions.push(x, y, z);
            }
            tracks.push(new THREE.VectorKeyframeTrack(
                joint.name + '.position', times, positions
            ));
            offset += 3;
        }

        if (joint.channels.includes('Zrotation')) {
            const rotations = [];
            for (const frame of frames) {
                // BVH uses ZXY rotation order in degrees
                const z = THREE.MathUtils.degToRad(frame[offset] || 0);
                const x = THREE.MathUtils.degToRad(frame[offset + 1] || 0);
                const y = THREE.MathUtils.degToRad(frame[offset + 2] || 0);
                
                const euler = new THREE.Euler(x, y, z, 'ZXY');
                const quat = new THREE.Quaternion().setFromEuler(euler);
                rotations.push(quat.x, quat.y, quat.z, quat.w);
            }
            tracks.push(new THREE.QuaternionKeyframeTrack(
                joint.name + '.quaternion', times, rotations
            ));
            offset += 3;
        }

        // Process children
        for (const child of joint.children) {
            offset = this.createTracksForJoint(child, frames, times, tracks, offset);
        }

        return offset;
    }
}

// Create skeleton geometry for visualization
class SkeletonHelper extends THREE.LineSegments {
    constructor(skeleton) {
        const bones = skeleton.bones;
        const geometry = new THREE.BufferGeometry();
        const vertices = [];
        const colors = [];

        const color1 = new THREE.Color(0xff0000); // Red for main bones
        const color2 = new THREE.Color(0x00ff00); // Green for end points

        // Create lines between connected bones
        for (let i = 0; i < bones.length; i++) {
            const bone = bones[i];
            
            if (bone.parent && bone.parent.isBone) {
                vertices.push(0, 0, 0);
                vertices.push(0, 0, 0);
                
                colors.push(color1.r, color1.g, color1.b);
                colors.push(color2.r, color2.g, color2.b);
            }
        }

        geometry.setAttribute('position', new THREE.Float32BufferAttribute(vertices, 3));
        geometry.setAttribute('color', new THREE.Float32BufferAttribute(colors, 3));

        const material = new THREE.LineBasicMaterial({
            vertexColors: true,
            linewidth: 2
        });

        super(geometry, material);

        this.skeleton = skeleton;
        this.bones = bones;
        this.matrix = skeleton.boneInverses[0].clone().invert();
    }

    updateMatrixWorld(force) {
        const bones = this.bones;
        const geometry = this.geometry;
        const position = geometry.attributes.position;

        let j = 0;

        for (let i = 0; i < bones.length; i++) {
            const bone = bones[i];

            if (bone.parent && bone.parent.isBone) {
                // Start point (parent position)
                bone.parent.getWorldPosition(this.tempVector1 = new THREE.Vector3());
                position.setXYZ(j, this.tempVector1.x, this.tempVector1.y, this.tempVector1.z);

                // End point (current bone position)
                bone.getWorldPosition(this.tempVector2 = new THREE.Vector3());
                position.setXYZ(j + 1, this.tempVector2.x, this.tempVector2.y, this.tempVector2.z);

                j += 2;
            }
        }

        geometry.attributes.position.needsUpdate = true;

        super.updateMatrixWorld(force);
    }
}