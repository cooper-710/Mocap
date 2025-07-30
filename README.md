# Baseball Motion Capture Web Application

A comprehensive web application for converting and visualizing baseball motion capture data in 3D. This project supports both CSV and TXT format motion capture files, converts them to BVH format for Blender import, and provides a real-time 3D skeletal animation viewer.

## 🎯 Features

### Motion Capture File Support
- **CSV Support (New!)**: Primary format for motion capture data
- **TXT Support**: Legacy format still fully supported
- **Automatic Format Detection**: Application automatically detects and uses available format
- **CSV Priority**: When both formats exist, CSV files are used

### Motion Capture Conversion
- **CSV/TXT to BVH Converter**: Converts motion capture files to industry-standard BVH format
- **Blender Compatibility**: Generated BVH files are optimized for seamless Blender import
- **Standard Skeleton**: Uses anatomically correct human skeleton hierarchy optimized for baseball motions

### 3D Visualization
- **Real-time 3D Animation**: Interactive skeletal animation viewer using Three.js
- **Multiple View Modes**: Front, side, top, and free camera views
- **Visual Controls**: Toggle skeleton bones, joint spheres, ground plane, and trajectory
- **Animation Controls**: Play, pause, reset, frame scrubbing, and speed adjustment

### Web Interface
- **Modern UI**: Clean, responsive interface with baseball-themed styling
- **Real-time Controls**: Interactive sliders and buttons for animation control
- **Motion Statistics**: Display frame count, duration, FPS, and other metadata
- **Export Functionality**: Export motion data and analysis results

## 📁 Project Structure

```
baseball-mocap/
├── mocap_to_bvh.py              # TXT to BVH converter
├── mocap_to_bvh_csv.py          # CSV to BVH converter (New!)
├── txt_to_csv_converter.py      # Utility to convert TXT to CSV
├── cooper_baseball_motion.bvh    # Generated BVH file
├── jointcenterscooper.txt        # Input: Joint center positions (TXT)
├── jointrotationscooper.txt      # Input: Joint rotations (TXT)
├── jointcenterscooper.csv        # Input: Joint center positions (CSV)
├── jointrotationscooper.csv      # Input: Joint rotations (CSV)
├── baseballspecificcooper.txt    # Input: Baseball-specific measurements
├── webapp/                       # Web application
│   ├── app.py                   # Flask backend server
│   ├── data_parser.py           # TXT data parser
│   ├── csv_data_parser.py       # CSV data parser (New!)
│   ├── templates/
│   │   └── index.html           # Main web interface
│   └── static/
│       ├── css/
│       │   └── style.css        # Application styling
│       └── js/
│           ├── bvh-loader.js    # BVH file parser for Three.js
│           ├── motion-viewer.js # 3D visualization engine
│           └── app.js           # Main application logic
└── README.md                    # This file
```

## 🚀 Quick Start

### 1. Convert TXT to CSV (Optional but Recommended)

If you have TXT files and want to use the newer CSV format:

```bash
python3 txt_to_csv_converter.py --convert-all
# Or with descriptive headers:
python3 txt_to_csv_converter.py --convert-all --with-headers
```

### 2. Convert Motion Capture Data to BVH

For CSV files:
```bash
python3 mocap_to_bvh_csv.py [output_filename.bvh]
```

For TXT files:
```bash
python3 mocap_to_bvh.py [output_filename.bvh]
```

This will generate `cooper_baseball_motion.bvh` ready for Blender import.

### 3. Import to Blender

1. Open Blender
2. Go to `File > Import > Motion Capture (.bvh)`
3. Select the generated `.bvh` file
4. The skeletal animation will be imported and ready for use

### 4. Launch Web Application

Start the web application to view and analyze the motion data:

```bash
cd webapp
python3 app.py
```

Open your browser to `http://localhost:5000` to access the 3D motion viewer.

## 🎮 Using the Web Application

### Animation Controls
- **Play/Pause**: Control animation playback
- **Frame Slider**: Scrub through animation frames
- **Speed Control**: Adjust playback speed (0.1x to 3.0x)
- **Reset**: Return to first frame

### View Controls
- **Camera Views**: Switch between front, side, top, and free views
- **Mouse Controls**: Click and drag to rotate camera, scroll to zoom
- **Visual Toggles**: Show/hide skeleton, joints, ground plane

### Data Analysis
- **Motion Statistics**: View frame count, duration, and FPS
- **Real-time Display**: Current frame and playback status
- **Export**: Download motion data in JSON format

## 📊 Data Format

### CSV Format (Recommended)
CSV files provide better compatibility and easier data manipulation:
- Supports multiple delimiters (comma, semicolon, tab)
- Automatic header detection
- Compatible with Excel, pandas, and other data tools

### Input Files
- **jointcenterscooper.csv/txt**: 300 fields (25 joints × 12 values: X,Y,Z,Length,v(X),v(Y),v(Z),v(abs),a(X),a(Y),a(Z),a(abs))
- **jointrotationscooper.csv/txt**: 252 fields (21 joints × 12 values)
- **baseballspecificcooper.txt**: 63 fields (baseball-specific measurements)

### Output BVH
- Standard hierarchical joint structure
- 900 frames of animation data
- 30 FPS frame rate
- Compatible with Blender, Maya, and other 3D software

## 🔄 API Endpoints

The web application provides several API endpoints:

- `GET /api/motion-data` - Get complete motion data as JSON
- `GET /api/motion-summary` - Get motion summary without frame data
- `GET /api/motion-frame/<frame>` - Get specific frame data
- `POST /api/convert-mocap` - Convert mocap files to BVH
- `POST /api/convert-txt-to-csv` - Convert TXT files to CSV format
- `GET /api/health` - Health check and file status

## 🎯 Baseball Motion Analysis

The application is specifically designed for baseball motion analysis:

### Supported Motions
- Pitching mechanics
- Batting swings  
- Fielding movements
- Running and base stealing

### Key Features for Baseball
- Anatomically accurate skeleton for baseball-specific movements
- Optimized joint hierarchy for upper body analysis
- Support for full-body motion capture including leg movement
- Coordinate system aligned with baseball field orientation

## 🛠️ Technical Details

### Technologies Used
- **Backend**: Python, Flask
- **3D Graphics**: Three.js, WebGL
- **Data Processing**: Custom BVH parser and skeletal animation system
- **UI**: Modern CSS with responsive design

### System Requirements
- Python 3.7+
- Modern web browser with WebGL support
- 4GB RAM recommended for large motion datasets

### Browser Compatibility
- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## 🔧 Customization

### Skeleton Modification
Edit the `setup_skeleton()` method in `mocap_to_bvh_csv.py` or `mocap_to_bvh.py` to customize the joint hierarchy for different sports or applications.

### Visual Styling
Modify `webapp/static/css/style.css` to customize the application appearance and branding.

### Animation Features
Extend `motion-viewer.js` to add new visualization features like:
- Trajectory plotting
- Force vector display
- Comparative motion analysis
- Performance metrics overlay

## 📈 Future Enhancements

- **Multi-athlete Comparison**: Side-by-side motion analysis
- **Performance Metrics**: Automated biomechanical analysis
- **Video Synchronization**: Sync motion data with video footage
- **Machine Learning**: Motion pattern recognition and analysis
- **Real-time Capture**: Integration with live motion capture systems

## 🤝 Contributing

This project was developed as a comprehensive motion capture analysis tool. Feel free to extend and modify for your specific needs.

## 📄 License

This project is provided as-is for educational and research purposes.

---

**Built with ❤️ for baseball motion analysis and 3D visualization**