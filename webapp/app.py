#!/usr/bin/env python3
"""
Baseball Motion Capture Web Application
Displays 3D skeletal animation from motion data (CSV or TXT files)

Author: AI Assistant
"""

from flask import Flask, render_template, send_file, jsonify, request
import os
import json
import sys

# Import both parsers
from data_parser import create_parser_from_files
from csv_data_parser import create_csv_parser_from_files

app = Flask(__name__)

# Configuration
app.config['DEBUG'] = True
app.config['MOCAP_DATA_PATH'] = '../'

def get_parser_and_files():
    """Determine which parser to use based on available files"""
    data_path = app.config['MOCAP_DATA_PATH']
    
    # Check for CSV files first (preferred format)
    csv_centers = os.path.join(data_path, 'jointcenterscooper.csv')
    csv_rotations = os.path.join(data_path, 'jointrotationscooper.csv')
    
    if os.path.exists(csv_centers) and os.path.exists(csv_rotations):
        return 'csv', csv_centers, csv_rotations
    
    # Fall back to TXT files
    txt_centers = os.path.join(data_path, 'jointcenterscooper.txt')
    txt_rotations = os.path.join(data_path, 'jointrotationscooper.txt')
    
    if os.path.exists(txt_centers) and os.path.exists(txt_rotations):
        return 'txt', txt_centers, txt_rotations
    
    return None, None, None

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
    """Get complete motion data as JSON (supports both CSV and TXT)"""
    try:
        # Determine which files are available
        file_format, centers_file, rotations_file = get_parser_and_files()
        
        if not file_format:
            return jsonify({
                'error': 'No motion capture data files found. Please provide either CSV or TXT files.',
                'expected_files': {
                    'csv': ['jointcenterscooper.csv', 'jointrotationscooper.csv'],
                    'txt': ['jointcenterscooper.txt', 'jointrotationscooper.txt']
                }
            }), 404
        
        # Create appropriate parser based on file format
        debug_mode = request.args.get('debug', 'false').lower() == 'true'
        
        if file_format == 'csv':
            parser = create_csv_parser_from_files(centers_file, rotations_file, debug=debug_mode)
        else:
            parser = create_parser_from_files(centers_file, rotations_file, debug=debug_mode)
        
        # Convert to JSON format
        motion_data = parser.to_json_format()
        
        if 'error' in motion_data:
            return jsonify(motion_data), 500
        
        # Add file format info
        motion_data['fileFormat'] = file_format.upper()
        
        return jsonify(motion_data)
        
    except FileNotFoundError as e:
        return jsonify({'error': f'File not found: {str(e)}'}), 404
    except Exception as e:
        return jsonify({'error': f'Error loading motion data: {str(e)}'}), 500

@app.route('/api/motion-summary')
def get_motion_summary():
    """Get motion data summary without full frame data (for quick info)"""
    try:
        # Determine which files are available
        file_format, centers_file, rotations_file = get_parser_and_files()
        
        if not file_format:
            return jsonify({'error': 'Motion capture data files not found'}), 404
        
        # Create appropriate parser
        if file_format == 'csv':
            parser = create_csv_parser_from_files(centers_file, rotations_file, debug=False)
        else:
            parser = create_parser_from_files(centers_file, rotations_file, debug=False)
        
        summary = parser.get_motion_summary()
        
        if 'error' in summary:
            return jsonify(summary), 500
        
        # Add file format info
        summary['fileFormat'] = file_format.upper()
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': f'Error getting motion summary: {str(e)}'}), 500

@app.route('/api/motion-frame/<int:frame_number>')
def get_motion_frame(frame_number):
    """Get data for a specific frame"""
    try:
        # Determine which files are available
        file_format, centers_file, rotations_file = get_parser_and_files()
        
        if not file_format:
            return jsonify({'error': 'Motion capture data files not found'}), 404
        
        # Create appropriate parser
        if file_format == 'csv':
            parser = create_csv_parser_from_files(centers_file, rotations_file, debug=False)
        else:
            parser = create_parser_from_files(centers_file, rotations_file, debug=False)
        
        # Get specific frame
        frame_data = parser.get_frame_data(frame_number)
        
        return jsonify({
            'frameNumber': frame_number,
            'frameData': frame_data,
            'fileFormat': file_format.upper()
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
    """Convert mocap data to BVH on demand (supports both CSV and TXT)"""
    try:
        # Import the converters
        sys.path.append('..')
        
        # Determine which files are available
        file_format, centers_file, rotations_file = get_parser_and_files()
        
        if not file_format:
            return jsonify({'error': 'Mocap data files not found'}), 404
        
        if file_format == 'csv':
            from mocap_to_bvh_csv import CSVBVHConverter
            converter = CSVBVHConverter()
        else:
            from mocap_to_bvh import BVHConverter
            converter = BVHConverter()
        
        converter.load_mocap_data(centers_file, rotations_file)
        
        output_file = os.path.join(app.config['MOCAP_DATA_PATH'], 'cooper_baseball_motion.bvh')
        converter.write_bvh(output_file)
        
        return jsonify({
            'success': True,
            'message': f'BVH file generated successfully from {file_format.upper()} files',
            'file': output_file,
            'frames': len(converter.frames),
            'sourceFormat': file_format.upper(),
            'note': 'BVH generation is deprecated. Use JSON motion data instead.'
        })
        
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

@app.route('/api/convert-txt-to-csv', methods=['POST'])
def convert_txt_to_csv():
    """Convert TXT files to CSV format"""
    try:
        # Import the converter
        sys.path.append('..')
        from txt_to_csv_converter import convert_mocap_files_to_csv
        
        # Check if TXT files exist
        txt_centers = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointcenterscooper.txt')
        txt_rotations = os.path.join(app.config['MOCAP_DATA_PATH'], 'jointrotationscooper.txt')
        
        if not os.path.exists(txt_centers) or not os.path.exists(txt_rotations):
            return jsonify({'error': 'TXT files not found for conversion'}), 404
        
        # Get option for adding headers
        add_headers = request.json.get('addHeaders', False) if request.json else False
        
        # Change to the data directory to run conversion
        original_dir = os.getcwd()
        os.chdir(app.config['MOCAP_DATA_PATH'])
        
        try:
            convert_mocap_files_to_csv(add_descriptive_headers=add_headers)
            
            # Check if CSV files were created
            csv_centers = 'jointcenterscooper.csv'
            csv_rotations = 'jointrotationscooper.csv'
            
            if os.path.exists(csv_centers) and os.path.exists(csv_rotations):
                return jsonify({
                    'success': True,
                    'message': 'Successfully converted TXT files to CSV format',
                    'files': {
                        'centers': csv_centers,
                        'rotations': csv_rotations
                    },
                    'withHeaders': add_headers
                })
            else:
                return jsonify({'error': 'CSV files were not created'}), 500
                
        finally:
            os.chdir(original_dir)
        
    except Exception as e:
        return jsonify({'error': f'Conversion failed: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    try:
        # Check for both CSV and TXT files
        data_path = app.config['MOCAP_DATA_PATH']
        
        csv_centers = os.path.join(data_path, 'jointcenterscooper.csv')
        csv_rotations = os.path.join(data_path, 'jointrotationscooper.csv')
        txt_centers = os.path.join(data_path, 'jointcenterscooper.txt')
        txt_rotations = os.path.join(data_path, 'jointrotationscooper.txt')
        
        csv_exists = os.path.exists(csv_centers) and os.path.exists(csv_rotations)
        txt_exists = os.path.exists(txt_centers) and os.path.exists(txt_rotations)
        
        # Determine active format
        active_format = None
        if csv_exists:
            active_format = 'CSV'
        elif txt_exists:
            active_format = 'TXT'
        
        return jsonify({
            'status': 'healthy',
            'data_files': {
                'csv': {
                    'joint_centers': os.path.exists(csv_centers),
                    'joint_rotations': os.path.exists(csv_rotations)
                },
                'txt': {
                    'joint_centers': os.path.exists(txt_centers),
                    'joint_rotations': os.path.exists(txt_rotations)
                }
            },
            'activeFormat': active_format,
            'api_version': '3.0',
            'features': {
                'csv_support': True,
                'txt_support': True,
                'auto_format_detection': True,
                'txt_to_csv_conversion': True
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Baseball Motion Capture Web Application...")
    print("Version 3.0 - Now with CSV Support!")
    print("\nNew Features:")
    print("- Automatic detection of CSV or TXT files")
    print("- CSV files take priority over TXT files")
    print("- Convert TXT to CSV via API: POST /api/convert-txt-to-csv")
    print("- JSON-based motion data API at /api/motion-data")
    print("- Frame-specific data at /api/motion-frame/<frame_number>")
    print("- Motion summary at /api/motion-summary")
    print("- Health check at /api/health")
    print("")
    
    # Check available files
    file_format, centers_file, rotations_file = get_parser_and_files()
    if file_format:
        print(f"Using {file_format.upper()} files for motion data")
    else:
        print("WARNING: No motion capture data files found!")
        print("Please provide either:")
        print("  - CSV files: jointcenterscooper.csv, jointrotationscooper.csv")
        print("  - TXT files: jointcenterscooper.txt, jointrotationscooper.txt")
    
    print("\nAccess the application at: http://localhost:5000")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)