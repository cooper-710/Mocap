#!/usr/bin/env python3
"""
Baseball Motion Capture Web Application
Displays 3D skeletal animation from BVH data

Author: AI Assistant
"""

from flask import Flask, render_template, send_file, jsonify, request
import os
import json
import sys

app = Flask(__name__)

# Configuration
app.config['DEBUG'] = True
app.config['BVH_FILE_PATH'] = '../cooper_baseball_motion.bvh'
app.config['MOCAP_DATA_PATH'] = '../'

@app.route('/')
def index():
    """Main page with 3D motion viewer"""
    return render_template('index.html')

@app.route('/viewer')
def viewer():
    """3D Motion Viewer page"""
    return render_template('viewer.html')

@app.route('/api/bvh')
def serve_bvh():
    """Serve the BVH file for the viewer"""
    bvh_path = os.path.abspath(app.config['BVH_FILE_PATH'])
    if os.path.exists(bvh_path):
        return send_file(bvh_path, mimetype='text/plain')
    else:
        return jsonify({'error': 'BVH file not found'}), 404

@app.route('/api/motion-data')
def get_motion_data():
    """Get motion data information"""
    bvh_path = os.path.abspath(app.config['BVH_FILE_PATH'])
    if not os.path.exists(bvh_path):
        return jsonify({'error': 'BVH file not found'}), 404
    
    # Parse BVH file to extract basic info
    try:
        with open(bvh_path, 'r') as f:
            content = f.read()
            
        lines = content.split('\n')
        motion_start = -1
        frame_count = 0
        frame_time = 0.033333  # Default 30 FPS
        
        for i, line in enumerate(lines):
            if line.strip() == 'MOTION':
                motion_start = i
            elif line.startswith('Frames:'):
                frame_count = int(line.split(':')[1].strip())
            elif line.startswith('Frame Time:'):
                frame_time = float(line.split(':')[1].strip())
        
        return jsonify({
            'frame_count': frame_count,
            'frame_time': frame_time,
            'duration': frame_count * frame_time,
            'fps': 1.0 / frame_time if frame_time > 0 else 30
        })
        
    except Exception as e:
        return jsonify({'error': f'Error parsing BVH file: {str(e)}'}), 500

@app.route('/api/convert-mocap', methods=['POST'])
def convert_mocap():
    """Convert mocap data to BVH on demand"""
    try:
        # Import the converter
        sys.path.append('..')
        from mocap_to_bvh import BVHConverter
        
        converter = BVHConverter()
        joint_centers_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointcenterscooper.txt')
        joint_rotations_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointrotationscooper.txt')
        
        if not os.path.exists(joint_centers_file) or not os.path.exists(joint_rotations_file):
            return jsonify({'error': 'Mocap data files not found'}), 404
        
        converter.load_mocap_data(joint_centers_file, joint_rotations_file)
        
        output_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'cooper_baseball_motion.bvh')
        converter.write_bvh(output_file)
        
        return jsonify({
            'success': True,
            'message': 'BVH file generated successfully',
            'file': output_file,
            'frames': len(converter.frames)
        })
        
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("Starting Baseball Motion Capture Web Application...")
    print("Access the application at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)