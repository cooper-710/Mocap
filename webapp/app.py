#!/usr/bin/env python3
"""
Baseball Motion Capture CSV Upload Web Application
Handles CSV file uploads for joint centers and rotations data, processes them for 3D visualization

Author: AI Assistant
"""

from flask import Flask, render_template, send_file, jsonify, request
import os
import json
import sys
from werkzeug.utils import secure_filename
from data_parser import CSVDataParser, create_parser_from_content, create_parser_from_files

app = Flask(__name__)

# Configuration
app.config['DEBUG'] = True
app.config['MOCAP_DATA_PATH'] = '../'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Global storage for uploaded CSV data (in production, use proper session management)
uploaded_csv_data = {}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def clear_uploaded_data():
    """Clear uploaded CSV data"""
    global uploaded_csv_data
    uploaded_csv_data.clear()

@app.route('/')
def index():
    """Main page with CSV upload interface"""
    return render_template('index.html')

@app.route('/api/upload-csv', methods=['POST'])
def upload_csv():
    """Handle CSV file uploads"""
    try:
        # Check if files are present
        if 'joint_centers' not in request.files or 'joint_rotations' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Both joint centers and joint rotations CSV files are required'
            }), 400
        
        centers_file = request.files['joint_centers']
        rotations_file = request.files['joint_rotations']
        
        # Check if files were selected
        if centers_file.filename == '' or rotations_file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400
        
        # Validate file extensions
        if not (allowed_file(centers_file.filename) and allowed_file(rotations_file.filename)):
            return jsonify({
                'success': False,
                'error': 'Only CSV files are allowed'
            }), 400
        
        # Read file contents
        centers_content = centers_file.read().decode('utf-8')
        rotations_content = rotations_file.read().decode('utf-8')
        
        # Create parser and validate files
        parser = CSVDataParser(debug_mode=True)
        
        # Validate CSV files
        centers_validation = parser.validate_csv_file(centers_content, "Joint Centers")
        rotations_validation = parser.validate_csv_file(rotations_content, "Joint Rotations")
        
        if not centers_validation['valid']:
            return jsonify({
                'success': False,
                'error': centers_validation['error']
            }), 400
        
        if not rotations_validation['valid']:
            return jsonify({
                'success': False,
                'error': rotations_validation['error']
            }), 400
        
        # Store the CSV data
        parser.store_uploaded_files(centers_content, rotations_content)
        
        # Store globally for other endpoints (in production, use proper session management)
        global uploaded_csv_data
        uploaded_csv_data['parser'] = parser
        uploaded_csv_data['centers_content'] = centers_content
        uploaded_csv_data['rotations_content'] = rotations_content
        
        # Get motion summary
        summary = parser.get_motion_summary()
        
        return jsonify({
            'success': True,
            'message': 'CSV files uploaded and processed successfully',
            'validation': {
                'centers': centers_validation,
                'rotations': rotations_validation
            },
            'summary': summary
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error processing CSV files: {str(e)}'
        }), 500

@app.route('/api/motion-data')
def get_motion_data():
    """Get complete motion data as JSON from uploaded CSV files"""
    try:
        global uploaded_csv_data
        
        # Check if CSV data has been uploaded
        if 'parser' not in uploaded_csv_data:
            # Fallback to TXT files if available (backward compatibility)
            joint_centers_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointcenterscooper.txt')
            joint_rotations_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointrotationscooper.txt')
            
            if os.path.exists(joint_centers_file) and os.path.exists(joint_rotations_file):
                # Legacy TXT file support - convert to CSV format
                from data_parser import create_parser_from_files
                parser = create_parser_from_files(joint_centers_file, joint_rotations_file, debug=False)
            else:
                return jsonify({
                    'error': 'No motion data available. Please upload CSV files first.'
                }), 404
        else:
            parser = uploaded_csv_data['parser']
        
        # Convert to JSON format
        motion_data = parser.to_json_format()
        
        if 'error' in motion_data:
            return jsonify(motion_data), 500
        
        return jsonify(motion_data)
        
    except Exception as e:
        return jsonify({'error': f'Error loading motion data: {str(e)}'}), 500

@app.route('/api/motion-summary')
def get_motion_summary():
    """Get motion data summary without full frame data"""
    try:
        global uploaded_csv_data
        
        if 'parser' not in uploaded_csv_data:
            return jsonify({
                'error': 'No motion data available. Please upload CSV files first.'
            }), 404
        
        parser = uploaded_csv_data['parser']
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
        global uploaded_csv_data
        
        if 'parser' not in uploaded_csv_data:
            return jsonify({
                'error': 'No motion data available. Please upload CSV files first.'
            }), 404
        
        parser = uploaded_csv_data['parser']
        
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

@app.route('/api/validate-csv', methods=['POST'])
def validate_csv():
    """Validate CSV files without storing them"""
    try:
        if 'joint_centers' not in request.files or 'joint_rotations' not in request.files:
            return jsonify({
                'valid': False,
                'error': 'Both CSV files are required for validation'
            }), 400
        
        centers_file = request.files['joint_centers']
        rotations_file = request.files['joint_rotations']
        
        # Read file contents
        centers_content = centers_file.read().decode('utf-8')
        rotations_content = rotations_file.read().decode('utf-8')
        
        # Create parser for validation
        parser = CSVDataParser(debug_mode=False)
        
        # Validate both files
        centers_validation = parser.validate_csv_file(centers_content, "Joint Centers")
        rotations_validation = parser.validate_csv_file(rotations_content, "Joint Rotations")
        
        return jsonify({
            'valid': centers_validation['valid'] and rotations_validation['valid'],
            'centers': centers_validation,
            'rotations': rotations_validation
        })
        
    except Exception as e:
        return jsonify({
            'valid': False,
            'error': f'Validation error: {str(e)}'
        }), 500

@app.route('/api/clear-data', methods=['POST'])
def clear_data():
    """Clear uploaded CSV data"""
    try:
        clear_uploaded_data()
        return jsonify({
            'success': True,
            'message': 'Uploaded data cleared successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error clearing data: {str(e)}'
        }), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        global uploaded_csv_data
        has_uploaded_data = 'parser' in uploaded_csv_data
        
        # Check if legacy TXT files are available as fallback
        joint_centers_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointcenterscooper.txt')
        joint_rotations_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointrotationscooper.txt')
        
        centers_exists = os.path.exists(joint_centers_file)
        rotations_exists = os.path.exists(joint_rotations_file)
        
        return jsonify({
            'status': 'healthy',
            'csv_upload_ready': True,
            'uploaded_data_available': has_uploaded_data,
            'legacy_files': {
                'joint_centers': centers_exists,
                'joint_rotations': rotations_exists
            },
            'api_version': '3.0',
            'format': 'CSV Upload + JSON',
            'max_file_size': app.config['MAX_CONTENT_LENGTH']
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# Legacy endpoints for backward compatibility
@app.route('/api/bvh')
def serve_bvh():
    """DEPRECATED: Serve the BVH file for backward compatibility"""
    bvh_path = os.path.abspath(os.path.join(app.config['MOCAP_DATA_PATH'], 'cooper_baseball_motion.bvh'))
    if os.path.exists(bvh_path):
        return send_file(bvh_path, mimetype='text/plain')
    else:
        return jsonify({
            'error': 'BVH file not found. This endpoint is deprecated. Use CSV upload instead.'
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
            return jsonify({'error': 'Legacy mocap data files not found. Use CSV upload instead.'}), 404
        
        converter.load_mocap_data(joint_centers_file, joint_rotations_file)
        
        output_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'cooper_baseball_motion.bvh')
        converter.write_bvh(output_file)
        
        return jsonify({
            'success': True,
            'message': 'BVH file generated successfully',
            'file': output_file,
            'frames': len(converter.frames),
            'note': 'BVH generation is deprecated. Use CSV upload with JSON motion data instead.'
        })
        
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

if __name__ == '__main__':
    print("Starting Baseball Motion Capture CSV Upload Web Application...")
    print("New CSV Upload Features:")
    print("- CSV file upload at /api/upload-csv")
    print("- CSV validation at /api/validate-csv") 
    print("- JSON motion data API at /api/motion-data")
    print("- Frame-specific data at /api/motion-frame/<frame_number>")
    print("- Motion summary at /api/motion-summary")
    print("- Health check at /api/health")
    print("- Clear data at /api/clear-data")
    print("")
    print("Access the application at: http://localhost:5000")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)