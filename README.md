# Baseball Motion Capture Web Application

A comprehensive web application for converting and visualizing baseball motion capture data in 3D. This project converts `.txt` mocap data to BVH format for Blender import and provides a real-time 3D skeletal animation viewer.

## 🎯 Features

### Motion Capture Conversion
- **TXT to BVH Converter**: Converts Cooper motion capture `.txt` files to industry-standard BVH format
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
├── mocap_to_bvh.py              # Motion capture to BVH converter
├── cooper_baseball_motion.bvh    # Generated BVH file
├── jointcenterscooper.txt        # Input: Joint center positions
├── jointrotationscooper.txt      # Input: Joint rotations
├── baseballspecificcooper.txt    # Input: Baseball-specific measurements
├── webapp/                       # Web application
│   ├── app.py                   # Flask backend server
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

### 1. Convert Motion Capture Data

Convert your `.txt` mocap files to BVH format:

```bash
python3 mocap_to_bvh.py [output_filename.bvh]
```

This will generate `cooper_baseball_motion.bvh` ready for Blender import.

### 2. Import to Blender

1. Open Blender
2. Go to `File > Import > Motion Capture (.bvh)`
3. Select the generated `.bvh` file
4. The skeletal animation will be imported and ready for use

### 3. Launch Web Application

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

### Input Files
- **jointcenterscooper.txt**: 300 fields (25 joints × 12 values: X,Y,Z,Length,v(X),v(Y),v(Z),v(abs),a(X),a(Y),a(Z),a(abs))
- **jointrotationscooper.txt**: 252 fields (21 joints × 12 values)
- **baseballspecificcooper.txt**: 63 fields (baseball-specific measurements)

### Output BVH
- Standard hierarchical joint structure
- 900 frames of animation data
- 30 FPS frame rate
- Compatible with Blender, Maya, and other 3D software

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
Edit the `setup_skeleton()` method in `mocap_to_bvh.py` to customize the joint hierarchy for different sports or applications.

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