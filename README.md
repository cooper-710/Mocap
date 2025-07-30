# Baseball Motion Capture CSV Import Web Application

A comprehensive web application for uploading and visualizing baseball motion capture data from CSV files in 3D. This project processes CSV files containing joint center and rotation data, providing real-time 3D skeletal animation visualization.

## 🎯 Features

### CSV Import & Processing
- **Dual CSV File Upload**: Upload separate CSV files for joint centers and rotations data
- **Real-time Validation**: Instant CSV file validation with detailed feedback
- **Drag & Drop Support**: Intuitive file upload with drag-and-drop functionality
- **Data Preview**: Live preview of uploaded CSV file contents
- **Error Handling**: Comprehensive validation and error reporting

### 3D Visualization
- **Real-time 3D Animation**: Interactive skeletal animation viewer using Three.js
- **Multiple View Modes**: Front, side, top, and free camera views with smooth transitions
- **Visual Controls**: Toggle skeleton bones, joint spheres, ground plane, and coordinate axes
- **Animation Controls**: Play, pause, reset, frame scrubbing, and speed adjustment (0.1x to 3.0x)

### Modern Web Interface
- **Responsive Design**: Clean, modern interface that works on desktop and mobile
- **Split-Panel Layout**: Dedicated upload panel and 3D viewer panel
- **Real-time Feedback**: Live status messages and processing updates
- **Keyboard Shortcuts**: Space for play/pause, arrow keys for frame navigation

## 📁 Project Structure

```
baseball-mocap-csv/
├── webapp/                           # Main web application
│   ├── app.py                       # Flask backend with CSV upload endpoints
│   ├── data_parser.py               # CSV parsing and motion data processing
│   ├── templates/
│   │   └── index.html               # Main CSV upload interface
│   └── static/
│       └── js/
│           ├── csv-uploader.js      # CSV file upload handling
│           ├── motion-viewer.js     # 3D visualization engine
│           └── app.js               # Main application controller
├── requirements.txt                 # Python dependencies including pandas
├── mocap_to_bvh.py                  # Legacy BVH converter (deprecated)
├── cooper_baseball_motion.bvh       # Legacy BVH file (reference)
├── jointcenterscooper.txt           # Legacy TXT file (fallback)
├── jointrotationscooper.txt         # Legacy TXT file (fallback)
└── README.md                        # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### 2. Start the Web Application

```bash
# Navigate to webapp directory
cd webapp

# Start Flask server
python app.py
```

### 3. Upload CSV Files

1. Open your browser to `http://localhost:5000`
2. Upload your joint centers CSV file (position data)
3. Upload your joint rotations CSV file (rotation data)
4. Click "Process & Visualize Motion Data"
5. Watch your 3D motion animation!

## 📊 CSV File Format

### Joint Centers CSV
Contains position data for each joint across time frames:
- **Columns**: Numeric data representing X, Y, Z coordinates
- **Rows**: Each row represents a time frame
- **Format**: Comma-separated values with numeric data
- **Example structure**: `X1, Y1, Z1, X2, Y2, Z2, ...` (multiple joints per row)

### Joint Rotations CSV  
Contains rotation data for each joint across time frames:
- **Columns**: Numeric data representing rotation angles (degrees or radians)
- **Rows**: Each row represents a time frame
- **Format**: Comma-separated values with numeric data
- **Example structure**: `RX1, RY1, RZ1, RX2, RY2, RZ2, ...` (multiple joints per row)

### Data Requirements
- Both CSV files must have the same number of rows (frames)
- Files must contain numeric data (no text/categorical data)
- Minimum 3 columns per file (X,Y,Z or RX,RY,RZ)
- Maximum file size: 50MB per file

## 🎮 Controls

### Mouse Controls
- **Left Click + Drag**: Rotate camera around subject
- **Mouse Wheel**: Zoom in/out
- **Right Click + Drag**: Pan camera

### Keyboard Shortcuts
- **Space**: Play/Pause animation
- **← →**: Previous/Next frame
- **Ctrl + ←**: Reset to first frame

### UI Controls
- **Play/Pause/Reset**: Animation control buttons
- **Frame Slider**: Scrub through animation frames
- **Speed Slider**: Adjust playback speed (0.1x to 3.0x)

## 🔧 API Endpoints

### CSV Upload
- `POST /api/upload-csv`: Upload and process CSV files
- `POST /api/validate-csv`: Validate CSV files without storing
- `POST /api/clear-data`: Clear uploaded data

### Motion Data
- `GET /api/motion-data`: Get complete motion data as JSON
- `GET /api/motion-summary`: Get motion metadata summary
- `GET /api/motion-frame/<frame>`: Get specific frame data

### Health & Status
- `GET /api/health`: Application health check
- `GET /`: Main CSV upload interface

## 🏗️ Technical Architecture

### Backend (Python/Flask)
- **Flask**: Web framework with file upload support
- **Pandas**: CSV parsing and data manipulation
- **NumPy**: Numerical computations and data processing
- **Data Parser**: Custom CSV processing with validation

### Frontend (JavaScript/HTML5)
- **Three.js**: 3D graphics and animation engine
- **Vanilla JavaScript**: No framework dependencies
- **HTML5 File API**: Modern file upload with drag-and-drop
- **CSS Grid/Flexbox**: Responsive layout design

### Data Flow
1. **Upload**: User selects two CSV files via web interface
2. **Validation**: Files are validated for format and content
3. **Processing**: CSV data is parsed into motion capture format
4. **Visualization**: 3D skeleton is created and animated frame-by-frame
5. **Interaction**: Real-time controls for playback and viewing

## 📈 Performance

- **File Size**: Supports CSV files up to 50MB each
- **Frame Rate**: Smooth 30 FPS animation playback
- **Responsiveness**: Real-time UI updates and smooth interactions
- **Memory**: Efficient data structures for large motion capture datasets

## 🔄 Migration from Legacy TXT Files

This application replaces the previous TXT file workflow with modern CSV uploads:

### Previous Workflow (Deprecated)
1. ✗ Place TXT files in specific directories
2. ✗ Run Python scripts manually
3. ✗ Generate BVH files as intermediate format
4. ✗ Load BVH files into web viewer

### New CSV Workflow (Current)
1. ✅ Upload CSV files via web interface
2. ✅ Automatic validation and processing
3. ✅ Direct JSON-based motion data
4. ✅ Instant 3D visualization

### Backward Compatibility
- Legacy TXT files still supported as fallback
- Existing BVH conversion endpoints maintained
- Automatic detection of data source type

## 🐛 Troubleshooting

### Common Issues

**CSV Upload Fails**
- Ensure files are valid CSV format
- Check that files contain only numeric data
- Verify both files have the same number of rows

**3D Viewer Not Loading**
- Check browser console for JavaScript errors
- Ensure WebGL is supported in your browser
- Try refreshing the page after upload

**Animation Not Playing**
- Verify CSV files were processed successfully
- Check that frame data contains valid coordinates
- Use browser developer tools to check for errors

### Browser Support
- **Chrome**: Fully supported
- **Firefox**: Fully supported  
- **Safari**: Supported (WebGL required)
- **Edge**: Supported

## 🚀 Deployment

### Local Development
```bash
cd webapp
python app.py
# Access at http://localhost:5000
```

### Production Deployment
```bash
# Using Gunicorn
cd webapp
gunicorn app:app --bind 0.0.0.0:5000

# Using Docker (optional)
docker build -t baseball-mocap .
docker run -p 5000:5000 baseball-mocap
```

### Environment Variables
- `PORT`: Server port (default: 5000)
- `FLASK_ENV`: Environment mode (development/production)

## 📝 License

This project is provided as-is for motion capture analysis and visualization. Modify and distribute as needed for your research or applications.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/csv-enhancement`)
3. Commit changes (`git commit -am 'Add CSV processing improvement'`)
4. Push branch (`git push origin feature/csv-enhancement`)
5. Create Pull Request

---

**Built with Python Flask, Three.js, and modern web technologies for seamless motion capture visualization.**