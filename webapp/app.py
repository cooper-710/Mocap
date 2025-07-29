#!/usr/bin/env python3
"""
Baseball Motion Capture Web Application
Displays 3D skeletal animation from JSON motion data (converted from TXT files)

Author: AI Assistant
"""

from flask import Flask, render_template, send_file, jsonify, request
import os
import json
import sys
from data_parser import create_parser_from_files

app = Flask(__name__)

# Configuration
app.config['DEBUG'] = True
app.config['MOCAP_DATA_PATH'] = '../'

@app.route('/')
def index():
    """Main page with 3D motion viewer"""
    return render_template('index.html')

@app.route('/viewer')
def viewer():
    """3D Motion Viewer page"""
    return render_template('viewer.html')

@app.route('/api/motion-data')
def get_motion_data():
    """Get complete motion data as JSON (replaces /api/bvh)"""
    try:
        # Define file paths
        joint_centers_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointcenterscooper.txt')
        joint_rotations_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointrotationscooper.txt')
        
        # Check if files exist
        if not os.path.exists(joint_centers_file):
            return jsonify({'error': f'Joint centers file not found: {joint_centers_file}'}), 404
        
        if not os.path.exists(joint_rotations_file):
            return jsonify({'error': f'Joint rotations file not found: {joint_rotations_file}'}), 404
        
        # Create data parser and load motion data
        debug_mode = request.args.get('debug', 'false').lower() == 'true'
        parser = create_parser_from_files(joint_centers_file, joint_rotations_file, debug=debug_mode)
        
        # Convert to JSON format
        motion_data = parser.to_json_format()
        
        if 'error' in motion_data:
            return jsonify(motion_data), 500
        
        return jsonify(motion_data)
        
    except FileNotFoundError as e:
        return jsonify({'error': f'File not found: {str(e)}'}), 404
    except Exception as e:
        return jsonify({'error': f'Error loading motion data: {str(e)}'}), 500

@app.route('/api/motion-summary')
def get_motion_summary():
    """Get motion data summary without full frame data (for quick info)"""
    try:
        # Define file paths
        joint_centers_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointcenterscooper.txt')
        joint_rotations_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointrotationscooper.txt')
        
        # Check if files exist
        if not os.path.exists(joint_centers_file) or not os.path.exists(joint_rotations_file):
            return jsonify({'error': 'Motion capture data files not found'}), 404
        
        # Create parser and get summary
        parser = create_parser_from_files(joint_centers_file, joint_rotations_file, debug=False)
        summary = parser.get_motion_summary()
        
        if 'error' in summary:
            return jsonify(summary), 500
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': f'Error getting motion summary: {str(e)}'}), 500

@app.route('/api/motion-frame/<int:frame_number>')
def get_motion_frame(frame_number):
    """Get data for a specific frame"""
    try:
        # Define file paths
        joint_centers_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointcenterscooper.txt')
        joint_rotations_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointrotationscooper.txt')
        
        # Create parser
        parser = create_parser_from_files(joint_centers_file, joint_rotations_file, debug=False)
        
        # Get specific frame
        frame_data = parser.get_frame_data(frame_number)
        
        return jsonify({
            'frameNumber': frame_number,
            'frameData': frame_data
        })
        
    except IndexError:
        return jsonify({'error': f'Frame {frame_number} out of range'}), 400
    except Exception as e:
        return jsonify({'error': f'Error getting frame data: {str(e)}'}), 500

# Legacy endpoint for backward compatibility (now deprecated)
@app.route('/api/bvh')
def serve_bvh():
    """DEPRECATED: Serve the BVH file for backward compatibility"""
    bvh_path = os.path.abspath(os.path.join(app.config['MOCAP_DATA_PATH'], 'cooper_baseball_motion.bvh'))
    if os.path.exists(bvh_path):
        return send_file(bvh_path, mimetype='text/plain')
    else:
        return jsonify({
            'error': 'BVH file not found. This endpoint is deprecated. Use /api/motion-data instead.'
        }), 404

@app.route('/api/convert-mocap', methods=['POST'])
def convert_mocap():
    """Convert mocap data to BVH on demand (legacy support)"""
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
            'frames': len(converter.frames),
            'note': 'BVH generation is deprecated. Use JSON motion data instead.'
        })
        
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check if motion data files are accessible
        joint_centers_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointcenterscooper.txt')
        joint_rotations_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointrotationscooper.txt')
        
        centers_exists = os.path.exists(joint_centers_file)
        rotations_exists = os.path.exists(joint_rotations_file)
        
        return jsonify({
            'status': 'healthy',
            'data_files': {
                'joint_centers': centers_exists,
                'joint_rotations': rotations_exists
            },
            'api_version': '2.0',
            'format': 'JSON'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Baseball Motion Capture Web Application...")
    print("New Features:")
    print("- JSON-based motion data API at /api/motion-data")
    print("- Frame-specific data at /api/motion-frame/<frame_number>")
    print("- Motion summary at /api/motion-summary")
    print("- Health check at /api/health")
    print("")
    print("Access the application at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)