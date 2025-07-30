#!/usr/bin/env python3
"""
Motion Capture CSV Data Parser
Parses CSV files containing joint centers and rotations data for 3D motion visualization

This module handles:
- Parsing joint centers and rotations from CSV files
- Defining anatomical joint names and bone connections
- Converting coordinate systems (CSV → Three.js)
- Providing frame-by-frame motion data
- CSV file validation and error handling
"""

import math
import os
import pandas as pd
import numpy as np
from typing import List, Dict, Tuple, Any, Optional
from io import StringIO

# Define the anatomical joint structure
JOINT_NAMES = [
    "Hips",           # Root joint (pelvis)
    "Spine",          # Lower spine
    "Spine1",         # Mid spine 
    "Spine2",         # Upper spine
    "Neck",           # Neck
    "Head",           # Head
    "LeftShoulder",   # Left shoulder
    "LeftArm",        # Left upper arm
    "LeftForeArm",    # Left forearm
    "LeftHand",       # Left hand
    "RightShoulder",  # Right shoulder
    "RightArm",       # Right upper arm
    "RightForeArm",   # Right forearm
    "RightHand",      # Right hand
    "LeftUpLeg",      # Left thigh
    "LeftLeg",        # Left shin
    "LeftFoot",       # Left foot
    "LeftToeBase",    # Left toe
    "RightUpLeg",     # Right thigh
    "RightLeg",       # Right shin
    "RightFoot",      # Right foot
    "RightToeBase"    # Right toe
]

# Define bone connections (parent-child relationships)
BONE_CONNECTIONS = [
    ["Hips", "Spine"],
    ["Spine", "Spine1"],
    ["Spine1", "Spine2"],
    ["Spine2", "Neck"],
    ["Neck", "Head"],
    ["Spine2", "LeftShoulder"],
    ["LeftShoulder", "LeftArm"],
    ["LeftArm", "LeftForeArm"],
    ["LeftForeArm", "LeftHand"],
    ["Spine2", "RightShoulder"],
    ["RightShoulder", "RightArm"],
    ["RightArm", "RightForeArm"],
    ["RightForeArm", "RightHand"],
    ["Hips", "LeftUpLeg"],
    ["LeftUpLeg", "LeftLeg"],
    ["LeftLeg", "LeftFoot"],
    ["LeftFoot", "LeftToeBase"],
    ["Hips", "RightUpLeg"],
    ["RightUpLeg", "RightLeg"],
    ["RightLeg", "RightFoot"],
    ["RightFoot", "RightToeBase"]
]

# Joint offsets in centimeters (for skeleton construction)
JOINT_OFFSETS = {
    "Hips": [0, 0, 0],           # Root position
    "Spine": [0, 12, 0],         # 12cm up
    "Spine1": [0, 15, 0],        # 15cm up  
    "Spine2": [0, 15, 0],        # 15cm up
    "Neck": [0, 12, 0],          # 12cm up
    "Head": [0, 8, 0],           # 8cm up
    "LeftShoulder": [-8, 5, 0],  # 8cm left, 5cm up
    "LeftArm": [-18, 0, 0],      # 18cm left
    "LeftForeArm": [-25, 0, 0],  # 25cm left
    "LeftHand": [-18, 0, 0],     # 18cm left
    "RightShoulder": [8, 5, 0],  # 8cm right, 5cm up
    "RightArm": [18, 0, 0],      # 18cm right
    "RightForeArm": [25, 0, 0],  # 25cm right
    "RightHand": [18, 0, 0],     # 18cm right
    "LeftUpLeg": [-5, 0, 0],     # 5cm left
    "LeftLeg": [0, -40, 0],      # 40cm down
    "LeftFoot": [0, -40, 0],     # 40cm down
    "LeftToeBase": [0, 0, 15],   # 15cm forward
    "RightUpLeg": [5, 0, 0],     # 5cm right
    "RightLeg": [0, -40, 0],     # 40cm down
    "RightFoot": [0, -40, 0],    # 40cm down
    "RightToeBase": [0, 0, 15]   # 15cm forward
}


class CSVDataParser:
    """Parser for motion capture CSV files"""
    
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.joint_centers_df = None
        self.joint_rotations_df = None
        self.frame_rate = 30.0  # Default 30 FPS
        self.uploaded_files = {}
        
    def validate_csv_file(self, file_content: str, file_type: str) -> Dict[str, Any]:
        """Validate CSV file format and structure"""
        try:
            # Try to parse the CSV content
            df = pd.read_csv(StringIO(file_content))
            
            if df.empty:
                return {"valid": False, "error": f"{file_type} CSV file is empty"}
            
            # Check for minimum required columns
            min_cols = 3  # At least X, Y, Z coordinates
            if len(df.columns) < min_cols:
                return {
                    "valid": False, 
                    "error": f"{file_type} CSV must have at least {min_cols} columns (X, Y, Z coordinates)"
                }
            
            # Check for numeric data
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) == 0:
                return {
                    "valid": False,
                    "error": f"{file_type} CSV must contain numeric data"
                }
            
            return {
                "valid": True,
                "rows": len(df),
                "columns": len(df.columns),
                "numeric_columns": len(numeric_cols),
                "preview": df.head(3).to_dict('records') if len(df) > 0 else []
            }
            
        except pd.errors.EmptyDataError:
            return {"valid": False, "error": f"{file_type} CSV file is empty"}
        except pd.errors.ParserError as e:
            return {"valid": False, "error": f"Failed to parse {file_type} CSV: {str(e)}"}
        except Exception as e:
            return {"valid": False, "error": f"Error validating {file_type} CSV: {str(e)}"}
    
    def load_csv_from_content(self, file_content: str, file_type: str) -> pd.DataFrame:
        """Load CSV data from file content string"""
        try:
            df = pd.read_csv(StringIO(file_content))
            
            if self.debug_mode:
                print(f"Loaded {file_type} CSV: {len(df)} rows, {len(df.columns)} columns")
                print(f"Columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            raise ValueError(f"Failed to load {file_type} CSV: {str(e)}")
    
    def store_uploaded_files(self, centers_content: str, rotations_content: str):
        """Store uploaded CSV file contents"""
        self.uploaded_files['centers'] = centers_content
        self.uploaded_files['rotations'] = rotations_content
        
        # Load the dataframes
        self.joint_centers_df = self.load_csv_from_content(centers_content, "Joint Centers")
        self.joint_rotations_df = self.load_csv_from_content(rotations_content, "Joint Rotations")
        
        if self.debug_mode:
            print(f"Stored CSV files successfully")
            print(f"Centers shape: {self.joint_centers_df.shape}")
            print(f"Rotations shape: {self.joint_rotations_df.shape}")
    
    def load_csv_files(self, joint_centers_file: str, joint_rotations_file: str):
        """Load motion capture data from CSV files (for backward compatibility)"""
        if self.debug_mode:
            print(f"Loading joint centers from {joint_centers_file}")
            print(f"Loading joint rotations from {joint_rotations_file}")
        
        if not os.path.exists(joint_centers_file):
            raise FileNotFoundError(f"Joint centers file not found: {joint_centers_file}")
        
        if not os.path.exists(joint_rotations_file):
            raise FileNotFoundError(f"Joint rotations file not found: {joint_rotations_file}")
        
        self.joint_centers_df = pd.read_csv(joint_centers_file)
        self.joint_rotations_df = pd.read_csv(joint_rotations_file)
        
        if self.debug_mode:
            print(f"Loaded {len(self.joint_centers_df)} frames of joint center data")
            print(f"Loaded {len(self.joint_rotations_df)} frames of joint rotation data")
    
    def mocap_to_threejs_coordinates(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """Convert from mocap coordinates to Three.js coordinates
        
        CSV data: X=horizontal (left-right), Y=vertical (up-down), Z=depth (forward-back)
        Three.js: X=horizontal (left-right), Y=vertical (up-down), Z=depth (forward-back)
        
        Scale and orient for proper visualization
        """
        # Convert to appropriate scale for visualization
        scale = 100.0  # Scale up for better visualization
        
        # Direct mapping since coordinate systems align
        threejs_x = float(x) * scale
        threejs_y = float(y) * scale
        threejs_z = float(z) * scale
        
        return threejs_x, threejs_y, threejs_z
    
    def extract_joint_position_from_row(self, row: pd.Series, joint_index: int) -> Tuple[float, float, float]:
        """Extract position for a specific joint from a CSV row
        
        Assumes CSV has columns that can be interpreted as positional data
        Takes the first 3 numeric columns as X, Y, Z coordinates for each joint
        """
        try:
            # Get numeric columns only
            numeric_data = row.select_dtypes(include=[np.number])
            
            if len(numeric_data) < 3:
                return 0.0, 0.0, 0.0
            
            # For multiple joints, assume data is arranged as:
            # Joint1_X, Joint1_Y, Joint1_Z, Joint2_X, Joint2_Y, Joint2_Z, ...
            start_idx = joint_index * 3
            
            if start_idx + 2 >= len(numeric_data):
                # If not enough data for this joint, use modulo to cycle through available data
                start_idx = (joint_index * 3) % max(3, len(numeric_data) - 2)
            
            x = numeric_data.iloc[start_idx] if start_idx < len(numeric_data) else numeric_data.iloc[0]
            y = numeric_data.iloc[start_idx + 1] if start_idx + 1 < len(numeric_data) else numeric_data.iloc[1 % len(numeric_data)]
            z = numeric_data.iloc[start_idx + 2] if start_idx + 2 < len(numeric_data) else numeric_data.iloc[2 % len(numeric_data)]
            
            return self.mocap_to_threejs_coordinates(x, y, z)
            
        except Exception as e:
            if self.debug_mode:
                print(f"Error extracting position for joint {joint_index}: {e}")
            return 0.0, 0.0, 0.0
    
    def extract_joint_rotation_from_row(self, row: pd.Series, joint_index: int) -> Tuple[float, float, float]:
        """Extract rotation for a specific joint from a CSV row
        
        Assumes the first 3 numeric values are rotation angles
        """
        try:
            # Get numeric columns only
            numeric_data = row.select_dtypes(include=[np.number])
            
            if len(numeric_data) < 3:
                return 0.0, 0.0, 0.0
            
            # For multiple joints, assume data is arranged as:
            # Joint1_RX, Joint1_RY, Joint1_RZ, Joint2_RX, Joint2_RY, Joint2_RZ, ...
            start_idx = joint_index * 3
            
            if start_idx + 2 >= len(numeric_data):
                # If not enough data for this joint, use modulo to cycle through available data
                start_idx = (joint_index * 3) % max(3, len(numeric_data) - 2)
            
            rx = numeric_data.iloc[start_idx] if start_idx < len(numeric_data) else numeric_data.iloc[0]
            ry = numeric_data.iloc[start_idx + 1] if start_idx + 1 < len(numeric_data) else numeric_data.iloc[1 % len(numeric_data)]
            rz = numeric_data.iloc[start_idx + 2] if start_idx + 2 < len(numeric_data) else numeric_data.iloc[2 % len(numeric_data)]
            
            # Convert to degrees if data appears to be in radians
            # Check if values are in reasonable degree range (-360 to 360)
            if abs(rx) <= math.pi and abs(ry) <= math.pi and abs(rz) <= math.pi:
                rx = math.degrees(rx)
                ry = math.degrees(ry)
                rz = math.degrees(rz)
            
            return float(rx), float(ry), float(rz)
            
        except Exception as e:
            if self.debug_mode:
                print(f"Error extracting rotation for joint {joint_index}: {e}")
            return 0.0, 0.0, 0.0
    
    def get_frame_data(self, frame_index: int) -> Dict[str, Dict[str, float]]:
        """Get position and rotation data for all joints in a specific frame"""
        if self.joint_centers_df is None or self.joint_rotations_df is None:
            raise ValueError("CSV data not loaded. Call store_uploaded_files() first.")
        
        if frame_index >= len(self.joint_centers_df) or frame_index >= len(self.joint_rotations_df):
            raise IndexError(f"Frame {frame_index} out of range")
        
        centers_row = self.joint_centers_df.iloc[frame_index]
        rotations_row = self.joint_rotations_df.iloc[frame_index]
        
        frame_data = {}
        
        for i, joint_name in enumerate(JOINT_NAMES):
            # Get position data
            x, y, z = self.extract_joint_position_from_row(centers_row, i)
            
            # Get rotation data
            rx, ry, rz = self.extract_joint_rotation_from_row(rotations_row, i)
            
            frame_data[joint_name] = {
                "position": {"x": x, "y": y, "z": z},
                "rotation": {"x": rx, "y": ry, "z": rz}
            }
        
        return frame_data
    
    def get_all_frames_data(self) -> List[Dict[str, Dict[str, float]]]:
        """Get motion data for all frames"""
        if self.joint_centers_df is None or self.joint_rotations_df is None:
            raise ValueError("CSV data not loaded. Call store_uploaded_files() first.")
        
        num_frames = min(len(self.joint_centers_df), len(self.joint_rotations_df))
        frames_data = []
        
        for frame_idx in range(num_frames):
            frame_data = self.get_frame_data(frame_idx)
            frames_data.append(frame_data)
        
        return frames_data
    
    def get_motion_summary(self) -> Dict[str, Any]:
        """Get summary information about the motion data"""
        if self.joint_centers_df is None or self.joint_rotations_df is None:
            return {"error": "CSV data not loaded"}
        
        num_frames = min(len(self.joint_centers_df), len(self.joint_rotations_df))
        duration = num_frames / self.frame_rate
        
        return {
            "jointNames": JOINT_NAMES,
            "boneConnections": BONE_CONNECTIONS,
            "jointOffsets": JOINT_OFFSETS,
            "totalFrames": num_frames,
            "frameRate": self.frame_rate,
            "duration": duration,
            "fps": self.frame_rate,
            "centersColumns": list(self.joint_centers_df.columns),
            "rotationsColumns": list(self.joint_rotations_df.columns),
            "centersShape": self.joint_centers_df.shape,
            "rotationsShape": self.joint_rotations_df.shape
        }
    
    def to_json_format(self) -> Dict[str, Any]:
        """Convert all motion data to JSON format for API response"""
        summary = self.get_motion_summary()
        
        if "error" in summary:
            return summary
        
        try:
            frames_data = self.get_all_frames_data()
            
            # Simplify frame data format for better performance
            simplified_frames = []
            for frame in frames_data:
                simplified_frame = {}
                for joint_name, joint_data in frame.items():
                    simplified_frame[joint_name] = {
                        "x": joint_data["position"]["x"],
                        "y": joint_data["position"]["y"], 
                        "z": joint_data["position"]["z"],
                        "rx": joint_data["rotation"]["x"],
                        "ry": joint_data["rotation"]["y"],
                        "rz": joint_data["rotation"]["z"]
                    }
                simplified_frames.append(simplified_frame)
            
            return {
                "jointNames": summary["jointNames"],
                "boneConnections": summary["boneConnections"],
                "jointOffsets": summary["jointOffsets"],
                "frames": simplified_frames,
                "frameRate": summary["frameRate"],
                "duration": summary["duration"],
                "totalFrames": summary["totalFrames"],
                "fps": summary["fps"],
                "dataSource": "CSV Upload",
                "centersColumns": summary["centersColumns"],
                "rotationsColumns": summary["rotationsColumns"]
            }
            
        except Exception as e:
            return {"error": f"Error processing motion data: {str(e)}"}


def create_parser_from_files(centers_file: str, rotations_file: str, debug=False) -> CSVDataParser:
    """Convenience function to create and load a DataParser from files"""
    parser = CSVDataParser(debug_mode=debug)
    parser.load_csv_files(centers_file, rotations_file)
    return parser


def create_parser_from_content(centers_content: str, rotations_content: str, debug=False) -> CSVDataParser:
    """Convenience function to create and load a DataParser from CSV content"""
    parser = CSVDataParser(debug_mode=debug)
    parser.store_uploaded_files(centers_content, rotations_content)
    return parser


if __name__ == "__main__":
    # Test the CSV data parser
    print("CSV Motion Capture Data Parser")
    print("Usage: Upload CSV files through the web interface")
    print("For testing, ensure you have CSV files with numeric motion capture data")