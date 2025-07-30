#!/usr/bin/env python3
"""
CSV Motion Capture Data Parser
Parses Cooper CSV files and provides structured motion data for JSON API

This module handles:
- Parsing joint centers and rotations from CSV files
- Defining anatomical joint names and bone connections
- Converting coordinate systems (CSV → Three.js)
- Providing frame-by-frame motion data
"""

import math
import os
import csv
from typing import List, Dict, Tuple, Any

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
    """Parser for Cooper motion capture CSV files"""
    
    def __init__(self, debug_mode=False):
        self.debug_mode = debug_mode
        self.joint_centers_data = []
        self.joint_rotations_data = []
        self.frame_rate = 30.0  # Default 30 FPS
        
    def load_csv_file(self, filename: str) -> List[Dict[str, float]]:
        """Load data from CSV file"""
        if not os.path.exists(filename):
            raise FileNotFoundError(f"File not found: {filename}")
            
        data = []
        with open(filename, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert all values to float, skipping the frame column
                frame_data = {}
                for key, value in row.items():
                    if key != 'frame':
                        try:
                            # Ensure value is a string before converting to float
                            if isinstance(value, list):
                                value = value[0] if value else '0.0'
                            frame_data[key] = float(str(value))
                        except (ValueError, TypeError) as e:
                            if self.debug_mode:
                                print(f"Warning: Could not parse value '{value}' for key '{key}': {e}")
                            frame_data[key] = 0.0
                data.append(frame_data)
        return data
    
    def load_motion_data(self, joint_centers_file: str, joint_rotations_file: str):
        """Load motion capture data from CSV files"""
        if self.debug_mode:
            print(f"Loading joint centers from {joint_centers_file}")
            print(f"Loading joint rotations from {joint_rotations_file}")
        
        self.joint_centers_data = self.load_csv_file(joint_centers_file)
        self.joint_rotations_data = self.load_csv_file(joint_rotations_file)
        
        if self.debug_mode:
            print(f"Loaded {len(self.joint_centers_data)} frames of joint center data")
            print(f"Loaded {len(self.joint_rotations_data)} frames of joint rotation data")
        
        if len(self.joint_centers_data) != len(self.joint_rotations_data):
            print("Warning: Frame count mismatch between center and rotation data")
    
    def mocap_to_threejs_coordinates(self, x: float, y: float, z: float) -> Tuple[float, float, float]:
        """Convert from mocap coordinates to Three.js coordinates
        
        Mocap CSV: X=horizontal (left-right), Y=vertical (up-down), Z=depth (forward-back)
        Three.js:  X=horizontal (left-right), Y=vertical (up-down), Z=depth (forward-back)
        
        The coordinate systems actually match! But we need to:
        1. Convert units (meters to centimeters for better scale)
        2. Ensure proper orientation
        """
        # Convert meters to centimeters for better visualization scale
        scale = 100.0
        
        # Direct mapping since coordinate systems align
        threejs_x = x * scale    # Left-right (same)
        threejs_y = y * scale    # Up-down (same) 
        threejs_z = z * scale    # Forward-back (same)
        
        return threejs_x, threejs_y, threejs_z
    
    def extract_joint_position(self, centers_data: Dict[str, float], joint_index: int) -> Tuple[float, float, float]:
        """Extract position for a specific joint from centers data
        
        Centers data has fields like X1,Y1,Z1,Length1,vX1,vY1,vZ1,vAbs1,aX1,aY1,aZ1,aAbs1,X2,Y2,Z2,...
        Each joint has: X, Y, Z, Length, v(X), v(Y), v(Z), v(abs), a(X), a(Y), a(Z), a(abs)
        We only need the first 3 values (X, Y, Z) for position
        """
        if joint_index >= 25:  # 25 joints in centers data
            return 0.0, 0.0, 0.0
        
        joint_num = joint_index + 1
        x_key = f"X{joint_num}"
        y_key = f"Y{joint_num}"
        z_key = f"Z{joint_num}"
        
        x = centers_data.get(x_key, 0.0)
        y = centers_data.get(y_key, 0.0)
        z = centers_data.get(z_key, 0.0)
        
        return self.mocap_to_threejs_coordinates(x, y, z)
    
    def extract_joint_rotation(self, rotations_data: Dict[str, float], joint_index: int) -> Tuple[float, float, float]:
        """Extract rotation for a specific joint from rotations data
        
        Rotations data has fields like X1,Y1,Z1,Length1,vX1,vY1,vZ1,vAbs1,aX1,aY1,aZ1,aAbs1,X2,Y2,Z2,...
        The first 3 values appear to be rotation angles in radians
        """
        if joint_index >= 21:  # 21 joints in rotations data
            return 0.0, 0.0, 0.0
        
        joint_num = joint_index + 1
        x_key = f"X{joint_num}"
        y_key = f"Y{joint_num}"
        z_key = f"Z{joint_num}"
        
        rx = rotations_data.get(x_key, 0.0)
        ry = rotations_data.get(y_key, 0.0)
        rz = rotations_data.get(z_key, 0.0)
        
        # Convert radians to degrees
        rx_deg = math.degrees(rx)
        ry_deg = math.degrees(ry)
        rz_deg = math.degrees(rz)
        
        return rx_deg, ry_deg, rz_deg
    
    def get_frame_data(self, frame_index: int) -> Dict[str, Dict[str, float]]:
        """Get position and rotation data for all joints in a specific frame"""
        if frame_index >= len(self.joint_centers_data) or frame_index >= len(self.joint_rotations_data):
            raise IndexError(f"Frame {frame_index} out of range")
        
        centers_frame = self.joint_centers_data[frame_index]
        rotations_frame = self.joint_rotations_data[frame_index]
        
        frame_data = {}
        
        for i, joint_name in enumerate(JOINT_NAMES):
            # Get position (use modulo to cycle through available data)
            position_joint_idx = i % 25  # 25 joints in centers data
            x, y, z = self.extract_joint_position(centers_frame, position_joint_idx)
            
            # Get rotation (use modulo to cycle through available data) 
            rotation_joint_idx = i % 21  # 21 joints in rotations data
            rx, ry, rz = self.extract_joint_rotation(rotations_frame, rotation_joint_idx)
            
            frame_data[joint_name] = {
                "position": {"x": x, "y": y, "z": z},
                "rotation": {"x": rx, "y": ry, "z": rz}
            }
        
        return frame_data
    
    def get_all_frames_data(self) -> List[Dict[str, Dict[str, float]]]:
        """Get motion data for all frames"""
        if not self.joint_centers_data or not self.joint_rotations_data:
            raise ValueError("Motion data not loaded. Call load_motion_data() first.")
        
        num_frames = min(len(self.joint_centers_data), len(self.joint_rotations_data))
        frames_data = []
        
        for frame_idx in range(num_frames):
            frame_data = self.get_frame_data(frame_idx)
            frames_data.append(frame_data)
        
        return frames_data
    
    def get_motion_summary(self) -> Dict[str, Any]:
        """Get summary information about the motion data"""
        if not self.joint_centers_data or not self.joint_rotations_data:
            return {
                "error": "Motion data not loaded"
            }
        
        num_frames = min(len(self.joint_centers_data), len(self.joint_rotations_data))
        duration = num_frames / self.frame_rate
        
        return {
            "jointNames": JOINT_NAMES,
            "boneConnections": BONE_CONNECTIONS,
            "jointOffsets": JOINT_OFFSETS,
            "totalFrames": num_frames,
            "frameRate": self.frame_rate,
            "duration": duration,
            "fps": self.frame_rate
        }
    
    def to_json_format(self) -> Dict[str, Any]:
        """Convert all motion data to JSON format for API response"""
        summary = self.get_motion_summary()
        
        if "error" in summary:
            return summary
        
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
            "fps": summary["fps"]
        }


def create_csv_parser_from_files(centers_file: str, rotations_file: str, debug=False) -> CSVDataParser:
    """Convenience function to create and load a CSVDataParser"""
    parser = CSVDataParser(debug_mode=debug)
    parser.load_motion_data(centers_file, rotations_file)
    return parser


if __name__ == "__main__":
    # Test the CSV data parser
    centers_file = "../joint_centers.csv"
    rotations_file = "../joint_rotations.csv"
    
    if os.path.exists(centers_file) and os.path.exists(rotations_file):
        parser = create_csv_parser_from_files(centers_file, rotations_file, debug=True)
        
        # Test first frame
        frame_0 = parser.get_frame_data(0)
        print("\nFirst frame data (sample joints):")
        for joint_name in ["Hips", "Head", "LeftHand", "RightHand"]:
            if joint_name in frame_0:
                data = frame_0[joint_name]
                print(f"{joint_name}: pos=({data['position']['x']:.1f}, {data['position']['y']:.1f}, {data['position']['z']:.1f}) "
                      f"rot=({data['rotation']['x']:.1f}, {data['rotation']['y']:.1f}, {data['rotation']['z']:.1f})")
        
        # Test JSON format
        json_data = parser.to_json_format()
        print(f"\nJSON summary:")
        print(f"- Joints: {len(json_data['jointNames'])}")
        print(f"- Bones: {len(json_data['boneConnections'])}")
        print(f"- Frames: {json_data['totalFrames']}")
        print(f"- Duration: {json_data['duration']:.1f}s")
    else:
        print("Test files not found")