# Migration Guide: TXT to CSV Motion Capture System

This guide helps you migrate from the old TXT-based motion capture system to the new CSV-based system.

## What Changed

### Old System (v2.0)
- Used `jointcenterscooper.txt` and `jointrotationscooper.txt` files
- Space-separated data format
- Limited to specific file names
- Harder to process and analyze

### New System (v3.0)
- Uses `joint_centers.csv` and `joint_rotations.csv` files
- Standard CSV format with headers
- Flexible file naming
- Easy to process with standard tools (Excel, Python, etc.)

## Migration Steps

### 1. Convert Your Data

Use the provided conversion script to convert your TXT files to CSV:

```bash
python3 convert_txt_to_csv.py jointcenterscooper.txt jointrotationscooper.txt joint_centers.csv joint_rotations.csv
```

### 2. Update Your Workflow

#### Old Workflow:
```bash
# Old system
cd webapp
python3 app.py  # Used TXT files automatically
```

#### New Workflow:
```bash
# New system
cd webapp
python3 app.py  # Uses CSV files automatically
```

### 3. API Changes

#### Old API Response:
```json
{
  "status": "healthy",
  "data_files": {
    "joint_centers": true,
    "joint_rotations": true
  },
  "api_version": "2.0",
  "format": "JSON"
}
```

#### New API Response:
```json
{
  "status": "healthy",
  "data_files": {
    "joint_centers_csv": true,
    "joint_rotations_csv": true
  },
  "api_version": "3.0",
  "format": "JSON",
  "data_source": "CSV"
}
```

## Benefits of the New System

### 1. Standard Format
- CSV files can be opened in Excel, Google Sheets, or any spreadsheet software
- Easy to edit, filter, and analyze data
- Standard format supported by all programming languages

### 2. Better Data Structure
- Clear column headers (X1, Y1, Z1, etc.)
- Frame numbers included in the data
- Consistent data types and formatting

### 3. Improved Processing
- Faster parsing with standard CSV libraries
- Better error handling and validation
- Easier to integrate with data analysis tools

### 4. Flexibility
- Can handle different numbers of joints
- Easy to add new data fields
- Compatible with various motion capture systems

## File Format Comparison

### Old TXT Format:
```
 X       Y       Z       Length  v(X)    v(Y)    v(Z)    v(abs)  a(X)    a(Y)
a(Z)     a(abs)  X       Y       Z       Length  v(X)    v(Y)    v(Z)    v(abs)
a(X)     a(Y)    a(Z)    a(abs)  X       Y       Z       Length  v(X)    v(Y)
...
0.28431338      -0.01509073     1.05814362      0.00000000      3.84870529     0
.28641033       1.94342744      4.32105017      -629.74517822   312.03567505   -
234.23468018    -364.29885864   0.36461636      -0.06458537     0.98345876     0
```

### New CSV Format:
```csv
frame,X1,Y1,Z1,Length1,vX1,vY1,vZ1,vAbs1,aX1,aY1,aZ1,aAbs1,X2,Y2,Z2,...
0,0.28431338,-0.01509073,1.05814362,0.00000000,3.84870529,0.28641033,...
1,0.29259282,0.00704067,1.06826925,0.09034911,-0.10746998,0.16801105,...
```

## Data Structure

### Joint Centers CSV:
- **Frame**: Frame number (0, 1, 2, ...)
- **X1, Y1, Z1**: Position of joint 1
- **Length1**: Length measurement for joint 1
- **vX1, vY1, vZ1**: Velocity components for joint 1
- **vAbs1**: Absolute velocity for joint 1
- **aX1, aY1, aZ1**: Acceleration components for joint 1
- **aAbs1**: Absolute acceleration for joint 1
- **...**: Repeat for joints 2-25

### Joint Rotations CSV:
- Same structure as centers, but for rotation data
- Supports up to 21 joints
- Rotation values are in radians

## Troubleshooting Migration

### Common Issues:

1. **"File not found" errors**:
   - Ensure CSV files are in the root directory
   - Check file permissions
   - Verify file names match expected format

2. **Data parsing errors**:
   - Check CSV format with a text editor
   - Ensure no extra commas or quotes
   - Verify all numeric values are valid

3. **Performance issues**:
   - Large CSV files may take longer to load
   - Consider reducing frame count for testing
   - Check available memory

### Debug Mode:
Enable debug mode to see detailed parsing information:
```bash
curl "http://localhost:5000/api/motion-data?debug=true"
```

## Backward Compatibility

The old TXT files are still supported for conversion, but the web application now expects CSV files. The conversion script provides a smooth migration path.

## Testing Your Migration

1. **Convert your data**:
   ```bash
   python3 convert_txt_to_csv.py your_centers.txt your_rotations.txt centers.csv rotations.csv
   ```

2. **Start the application**:
   ```bash
   cd webapp
   python3 app.py
   ```

3. **Test the API**:
   ```bash
   curl http://localhost:5000/api/health
   curl http://localhost:5000/api/motion-summary
   ```

4. **View in browser**:
   - Open `http://localhost:5000`
   - Verify 3D animation works correctly

## Support

If you encounter issues during migration:

1. Check the troubleshooting section above
2. Verify your CSV files with a text editor
3. Test with the provided sample data first
4. Enable debug mode for detailed error messages
5. Check the browser console for JavaScript errors

## Future Enhancements

The CSV-based system enables several future improvements:

- **Real-time data streaming**: Easy to update CSV files during capture
- **Multiple athlete support**: Separate CSV files per athlete
- **Data analysis integration**: Direct import to analysis tools
- **Cloud storage**: Standard format for cloud-based processing
- **Machine learning**: Easy data preparation for ML models