#!/usr/bin/env python3
"""
TXT to CSV Converter for Baseball Motion Capture Data

This script converts the original TXT format motion capture files to CSV format
for use with the new CSV-based motion capture viewer.

Usage:
    python3 convert_txt_to_csv.py [input_centers.txt] [input_rotations.txt] [output_centers.csv] [output_rotations.csv]
"""

import sys
import os
import csv

def parse_txt_file(filename):
    """Parse TXT file and return list of frame data"""
    if not os.path.exists(filename):
        raise FileNotFoundError(f"File not found: {filename}")
    
    frames = []
    with open(filename, 'r') as f:
        lines = f.readlines()
        
        # Skip header lines (first few lines with column names)
        data_lines = []
        for line in lines:
            if line.strip() and not line.startswith('X') and not line.startswith(' '):
                data_lines.append(line)
        
        # Process each frame
        for i, line in enumerate(data_lines):
            try:
                values = [float(x) for x in line.strip().split()]
                if values:  # Skip empty lines
                    frames.append(values)
            except ValueError as e:
                print(f"Warning: Could not parse line {i+1}: {e}")
                continue
    
    return frames

def create_csv_headers(num_joints, data_type):
    """Create CSV headers for the specified number of joints"""
    headers = ['frame']
    
    for joint_num in range(1, num_joints + 1):
        if data_type == 'centers':
            # 12 values per joint: X, Y, Z, Length, v(X), v(Y), v(Z), v(abs), a(X), a(Y), a(Z), a(abs)
            headers.extend([
                f'X{joint_num}', f'Y{joint_num}', f'Z{joint_num}', f'Length{joint_num}',
                f'vX{joint_num}', f'vY{joint_num}', f'vZ{joint_num}', f'vAbs{joint_num}',
                f'aX{joint_num}', f'aY{joint_num}', f'aZ{joint_num}', f'aAbs{joint_num}'
            ])
        else:  # rotations
            # Same structure for rotations
            headers.extend([
                f'X{joint_num}', f'Y{joint_num}', f'Z{joint_num}', f'Length{joint_num}',
                f'vX{joint_num}', f'vY{joint_num}', f'vZ{joint_num}', f'vAbs{joint_num}',
                f'aX{joint_num}', f'aY{joint_num}', f'aZ{joint_num}', f'aAbs{joint_num}'
            ])
    
    return headers

def write_csv_file(filename, frames, headers):
    """Write frame data to CSV file"""
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for frame_num, frame_data in enumerate(frames):
            row = [frame_num] + frame_data
            writer.writerow(row)

def main():
    """Main conversion function"""
    if len(sys.argv) != 5:
        print("Usage: python3 convert_txt_to_csv.py [input_centers.txt] [input_rotations.txt] [output_centers.csv] [output_rotations.csv]")
        print("\nExample:")
        print("  python3 convert_txt_to_csv.py jointcenterscooper.txt jointrotationscooper.txt joint_centers.csv joint_rotations.csv")
        sys.exit(1)
    
    input_centers = sys.argv[1]
    input_rotations = sys.argv[2]
    output_centers = sys.argv[3]
    output_rotations = sys.argv[4]
    
    print("Converting TXT motion capture files to CSV format...")
    print(f"Input centers: {input_centers}")
    print(f"Input rotations: {input_rotations}")
    print(f"Output centers: {output_centers}")
    print(f"Output rotations: {output_rotations}")
    print()
    
    try:
        # Parse centers data
        print("Parsing joint centers data...")
        centers_frames = parse_txt_file(input_centers)
        print(f"Found {len(centers_frames)} frames of centers data")
        
        # Parse rotations data
        print("Parsing joint rotations data...")
        rotations_frames = parse_txt_file(input_rotations)
        print(f"Found {len(rotations_frames)} frames of rotations data")
        
        # Determine number of joints based on data structure
        if centers_frames:
            num_centers_joints = len(centers_frames[0]) // 12  # 12 values per joint
            print(f"Detected {num_centers_joints} joints in centers data")
        
        if rotations_frames:
            num_rotations_joints = len(rotations_frames[0]) // 12  # 12 values per joint
            print(f"Detected {num_rotations_joints} joints in rotations data")
        
        # Create headers
        centers_headers = create_csv_headers(num_centers_joints, 'centers')
        rotations_headers = create_csv_headers(num_rotations_joints, 'rotations')
        
        # Write CSV files
        print("\nWriting centers CSV file...")
        write_csv_file(output_centers, centers_frames, centers_headers)
        
        print("Writing rotations CSV file...")
        write_csv_file(output_rotations, rotations_frames, rotations_headers)
        
        print("\nConversion completed successfully!")
        print(f"Centers CSV: {output_centers} ({len(centers_frames)} frames)")
        print(f"Rotations CSV: {output_rotations} ({len(rotations_frames)} frames)")
        print("\nYou can now use these CSV files with the motion capture viewer.")
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()