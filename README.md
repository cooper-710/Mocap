# Baseball Motion Capture Viewer (CSV Version)

A 3D web application for viewing baseball motion capture data from CSV files. This application displays skeletal animations using Three.js and provides an interactive 3D viewer for analyzing baseball motion data.

## Features

- **3D Skeletal Animation**: Real-time 3D visualization of motion capture data
- **CSV Data Support**: Works with CSV files containing joint centers and rotations
- **Interactive Controls**: Play, pause, reset, and frame-by-frame navigation
- **Multiple View Angles**: Front, side, top, and free camera views
- **Motion Analysis**: Duration, FPS, and frame count information
- **Modern Web Interface**: Responsive design with intuitive controls

## Data Format

The application expects two CSV files:

### 1. `joint_centers.csv`
Contains joint position data with the following structure:
```csv
frame,X1,Y1,Z1,Length1,vX1,vY1,vZ1,vAbs1,aX1,aY1,aZ1,aAbs1,X2,Y2,Z2,...
0,0.28431338,-0.01509073,1.05814362,0.00000000,3.84870529,0.28641033,...
1,0.29259282,0.00704067,1.06826925,0.09034911,-0.10746998,0.16801105,...
```

### 2. `joint_rotations.csv`
Contains joint rotation data with the same structure:
```csv
frame,X1,Y1,Z1,Length1,vX1,vY1,vZ1,vAbs1,aX1,aY1,aZ1,aAbs1,X2,Y2,Z2,...
0,0.00000000,0.00000000,0.00000000,0.00000000,0.00000000,0.00000000,...
1,0.00000000,0.00000000,0.00000000,0.00000000,0.00000000,0.00000000,...
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd baseball-motion-capture
   ```

2. **Install dependencies**:
   ```bash
   pip3 install --break-system-packages flask numpy
   ```

3. **Prepare your data**:
   - Place your `joint_centers.csv` and `joint_rotations.csv` files in the root directory
   - Ensure the CSV files follow the expected format

## Usage

### Starting the Application

1. **Run the Flask application**:
   ```bash
   cd webapp
   python3 app.py
   ```

2. **Access the web interface**:
   - Open your browser and navigate to `http://localhost:5000`
   - The 3D viewer will load automatically

### API Endpoints

- **`/`**: Main 3D viewer interface
- **`/api/health`**: Health check and system status
- **`/api/motion-summary`**: Motion data summary (frames, duration, etc.)
- **`/api/motion-data`**: Complete motion data in JSON format
- **`/api/motion-frame/<frame_number>`**: Data for a specific frame

### Example API Usage

```bash
# Health check
curl http://localhost:5000/api/health

# Motion summary
curl http://localhost:5000/api/motion-summary

# Complete motion data
curl http://localhost:5000/api/motion-data
```

## Controls

### Animation Controls
- **Play/Pause**: Start or stop animation playback
- **Reset**: Return to the first frame
- **Frame Slider**: Navigate to specific frames
- **Speed Control**: Adjust playback speed (0.1x to 3.0x)

### View Controls
- **Front View**: View from the front
- **Side View**: View from the side
- **Top View**: View from above
- **Free View**: Free camera movement

### Display Options
- **Show Skeleton**: Toggle bone connections
- **Show Joints**: Toggle joint markers
- **Show Ground**: Toggle ground plane
- **Show Trajectory**: Toggle motion path

## Technical Details

### Architecture
- **Backend**: Flask web server with CSV data parser
- **Frontend**: Three.js 3D graphics library
- **Data Format**: JSON API for motion data
- **Coordinate System**: Meters to centimeters conversion for visualization

### Data Processing
- **CSV Parser**: Handles joint centers and rotations from CSV files
- **Coordinate Conversion**: Converts motion capture coordinates to Three.js format
- **Frame Processing**: Extracts position and rotation data for each joint
- **Skeleton Construction**: Builds 3D skeleton from joint connections

### Joint Structure
The system supports 22 joints:
- **Spine**: Hips, Spine, Spine1, Spine2, Neck, Head
- **Arms**: Left/Right Shoulder, Arm, ForeArm, Hand
- **Legs**: Left/Right UpLeg, Leg, Foot, ToeBase

## Development

### Project Structure
```
├── webapp/
│   ├── app.py                 # Flask application
│   ├── csv_data_parser.py     # CSV data parser
│   ├── templates/
│   │   └── index.html        # Main web interface
│   └── static/
│       ├── css/              # Stylesheets
│       └── js/               # JavaScript files
├── joint_centers.csv         # Joint position data
├── joint_rotations.csv       # Joint rotation data
└── README.md                # This file
```

### Adding New Data
1. Prepare your CSV files following the expected format
2. Place them in the root directory
3. Restart the Flask application
4. The new data will be automatically loaded

### Customization
- **Joint Names**: Modify `JOINT_NAMES` in `csv_data_parser.py`
- **Bone Connections**: Update `BONE_CONNECTIONS` for different skeleton structures
- **Coordinate System**: Adjust `mocap_to_threejs_coordinates()` for different coordinate systems
- **Visualization**: Modify Three.js code in `static/js/motion-viewer.js`

## Troubleshooting

### Common Issues

1. **CSV files not found**:
   - Ensure `joint_centers.csv` and `joint_rotations.csv` are in the root directory
   - Check file permissions

2. **Flask not installed**:
   ```bash
   pip3 install --break-system-packages flask
   ```

3. **Port already in use**:
   - Change the port in `app.py` or kill the existing process
   - Default port is 5000

4. **Data not loading**:
   - Check CSV file format
   - Verify file paths in the application
   - Check browser console for JavaScript errors

### Debug Mode
Enable debug mode for detailed logging:
```bash
curl "http://localhost:5000/api/motion-data?debug=true"
```

## License

This project is open source and available under the MIT License.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## Version History

- **v3.0**: CSV-based data processing
- **v2.0**: JSON motion data API
- **v1.0**: Original TXT-based system

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the API documentation
3. Examine the example CSV files
4. Enable debug mode for detailed error messages