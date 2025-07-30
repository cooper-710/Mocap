#!/usr/bin/env python3
"""
TXT to CSV Converter for Motion Capture Data
Converts existing TXT mocap files to CSV format for easier processing
"""

import csv
import os
import sys
from typing import List, Dict

def read_txt_file(filename: str) -> tuple[List[str], List[List[str]]]:
    """Read TXT file and return header and data rows"""
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # First line is header
    header = lines[0].strip().split() if lines else []
    
    # Rest are data rows
    data = []
    for line in lines[1:]:
        row = line.strip().split()
        if row:  # Skip empty lines
            data.append(row)
    
    return header, data

def write_csv_file(filename: str, header: List[str], data: List[List[str]], delimiter: str = ','):
    """Write data to CSV file with header"""
    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, delimiter=delimiter)
        
        # Write header if provided
        if header:
            writer.writerow(header)
        
        # Write data rows
        for row in data:
            writer.writerow(row)

def convert_txt_to_csv(input_file: str, output_file: str = None, delimiter: str = ','):
    """Convert TXT file to CSV format"""
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found")
        return False
    
    # Generate output filename if not provided
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.csv"
    
    try:
        # Read TXT file
        header, data = read_txt_file(input_file)
        
        # Write CSV file
        write_csv_file(output_file, header, data, delimiter)
        
        print(f"Successfully converted '{input_file}' to '{output_file}'")
        print(f"- Header columns: {len(header)}")
        print(f"- Data rows: {len(data)}")
        if data:
            print(f"- Columns per row: {len(data[0])}")
        
        return True
        
    except Exception as e:
        print(f"Error converting file: {e}")
        return False

def generate_header_for_mocap(file_type: str, num_columns: int) -> List[str]:
    """Generate descriptive headers for mocap files"""
    if file_type == "centers":
        # Joint centers: 25 joints × 12 values
        headers = []
        joint_names = [f"Joint{i+1}" for i in range(25)]
        field_names = ["X", "Y", "Z", "Length", "vX", "vY", "vZ", "vAbs", "aX", "aY", "aZ", "aAbs"]
        
        for joint in joint_names:
            for field in field_names:
                headers.append(f"{joint}_{field}")
        
        return headers[:num_columns]  # Trim to actual column count
        
    elif file_type == "rotations":
        # Joint rotations: 21 joints × 12 values
        headers = []
        joint_names = [f"Joint{i+1}" for i in range(21)]
        field_names = ["RotX", "RotY", "RotZ", "Field4", "Field5", "Field6", 
                      "Field7", "Field8", "Field9", "Field10", "Field11", "Field12"]
        
        for joint in joint_names:
            for field in field_names:
                headers.append(f"{joint}_{field}")
        
        return headers[:num_columns]  # Trim to actual column count
    
    else:
        # Generic headers
        return [f"Field{i+1}" for i in range(num_columns)]

def convert_mocap_files_to_csv(add_descriptive_headers: bool = False):
    """Convert the standard mocap TXT files to CSV format"""
    files_to_convert = [
        ("jointcenterscooper.txt", "jointcenterscooper.csv", "centers"),
        ("jointrotationscooper.txt", "jointrotationscooper.csv", "rotations"),
        ("baseballspecificcooper.txt", "baseballspecificcooper.csv", "specific")
    ]
    
    for input_file, output_file, file_type in files_to_convert:
        if os.path.exists(input_file):
            print(f"\nConverting {input_file}...")
            
            if add_descriptive_headers:
                # Read the file first to check column count
                header, data = read_txt_file(input_file)
                if data and len(data[0]) > 0:
                    num_columns = len(data[0])
                    descriptive_header = generate_header_for_mocap(file_type, num_columns)
                    
                    # Write with descriptive headers
                    write_csv_file(output_file, descriptive_header, data)
                    print(f"Added descriptive headers to {output_file}")
                else:
                    convert_txt_to_csv(input_file, output_file)
            else:
                convert_txt_to_csv(input_file, output_file)
        else:
            print(f"Warning: {input_file} not found, skipping...")

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) > 1:
        if sys.argv[1] == "--convert-all":
            # Convert all standard mocap files
            add_headers = "--with-headers" in sys.argv
            convert_mocap_files_to_csv(add_descriptive_headers=add_headers)
        else:
            # Convert specific file
            input_file = sys.argv[1]
            output_file = sys.argv[2] if len(sys.argv) > 2 else None
            delimiter = sys.argv[3] if len(sys.argv) > 3 else ','
            
            convert_txt_to_csv(input_file, output_file, delimiter)
    else:
        print("TXT to CSV Converter for Motion Capture Data")
        print("\nUsage:")
        print("  python txt_to_csv_converter.py <input.txt> [output.csv] [delimiter]")
        print("  python txt_to_csv_converter.py --convert-all [--with-headers]")
        print("\nExamples:")
        print("  python txt_to_csv_converter.py jointcenterscooper.txt")
        print("  python txt_to_csv_converter.py jointcenterscooper.txt centers.csv")
        print("  python txt_to_csv_converter.py data.txt data.csv ';'")
        print("  python txt_to_csv_converter.py --convert-all")
        print("  python txt_to_csv_converter.py --convert-all --with-headers")

if __name__ == "__main__":
    main()