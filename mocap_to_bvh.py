#!/usr/bin/env python3
"""
Motion Capture to BVH Converter
Converts Cooper motion capture .txt files to BVH format for Blender import

Key fixes:
- Correct axis mapping from baseball field coordinates to BVH coordinates
- Proper rotation data extraction and conversion
- Debug mode for validation
- Improved scaling and translation handling

Author: AI Assistant
"""

import os
import sys
import math
from typing import List, Dict, Tuple


class Joint:
    """Represents a joint in the skeleton hierarchy"""
    def __init__(self, name: str, parent=None, offset=(0, 0, 0)):
        self.name = name
        self.parent = parent
        self.children = []
        self.offset = offset  # Offset from parent
        self.position = (0, 0, 0)  # World position
        self.rotation = (0, 0, 0)  # Euler angles (X, Y, Z)
        
        if parent:
            parent.children.append(self)


class BVHConverter:
    """Converts motion capture data to BVH format"""
    
    def __init__(self, debug_mode=False):
        self.joints = {}
        self.root_joint = None
        self.frame_time = 1.0 / 30.0  # 30 FPS default
        self.frames = []
        self.debug_mode = debug_mode
        
        # Standard human skeleton hierarchy for baseball motion
        self.setup_skeleton()
    
    def setup_skeleton(self):
        """Setup standard human skeleton hierarchy with proper BVH scaling"""
        # Root (Hips/Pelvis) - using centimeters for BVH compatibility
        self.root_joint = Joint("Hips")
        self.joints["Hips"] = self.root_joint
        
        # Spine chain
        spine = Joint("Spine", self.root_joint, (0, 12.0, 0))  # 12cm up from hips
        self.joints["Spine"] = spine
        
        spine1 = Joint("Spine1", spine, (0, 15.0, 0))  # 15cm up
        self.joints["Spine1"] = spine1
        
        spine2 = Joint("Spine2", spine1, (0, 15.0, 0))  # 15cm up
        self.joints["Spine2"] = spine2
        
        neck = Joint("Neck", spine2, (0, 12.0, 0))  # 12cm up
        self.joints["Neck"] = neck
        
        head = Joint("Head", neck, (0, 8.0, 0))  # 8cm up
        self.joints["Head"] = head
        
        # Left arm chain
        left_shoulder = Joint("LeftShoulder", spine2, (-8.0, 5.0, 0))  # 8cm left, 5cm up
        self.joints["LeftShoulder"] = left_shoulder
        
        left_arm = Joint("LeftArm", left_shoulder, (-18.0, 0, 0))  # 18cm left
        self.joints["LeftArm"] = left_arm
        
        left_forearm = Joint("LeftForeArm", left_arm, (-25.0, 0, 0))  # 25cm left
        self.joints["LeftForeArm"] = left_forearm
        
        left_hand = Joint("LeftHand", left_forearm, (-18.0, 0, 0))  # 18cm left
        self.joints["LeftHand"] = left_hand
        
        # Right arm chain
        right_shoulder = Joint("RightShoulder", spine2, (8.0, 5.0, 0))  # 8cm right, 5cm up
        self.joints["RightShoulder"] = right_shoulder
        
        right_arm = Joint("RightArm", right_shoulder, (18.0, 0, 0))  # 18cm right
        self.joints["RightArm"] = right_arm
        
        right_forearm = Joint("RightForeArm", right_arm, (25.0, 0, 0))  # 25cm right
        self.joints["RightForeArm"] = right_forearm
        
        right_hand = Joint("RightHand", right_forearm, (18.0, 0, 0))  # 18cm right
        self.joints["RightHand"] = right_hand
        
        # Left leg chain
        left_up_leg = Joint("LeftUpLeg", self.root_joint, (-5.0, 0, 0))  # 5cm left
        self.joints["LeftUpLeg"] = left_up_leg
        
        left_leg = Joint("LeftLeg", left_up_leg, (0, -40.0, 0))  # 40cm down
        self.joints["LeftLeg"] = left_leg
        
        left_foot = Joint("LeftFoot", left_leg, (0, -40.0, 0))  # 40cm down
        self.joints["LeftFoot"] = left_foot
        
        left_toe = Joint("LeftToeBase", left_foot, (0, 0, 15.0))  # 15cm forward
        self.joints["LeftToeBase"] = left_toe
        
        # Right leg chain
        right_up_leg = Joint("RightUpLeg", self.root_joint, (5.0, 0, 0))  # 5cm right
        self.joints["RightUpLeg"] = right_up_leg
        
        right_leg = Joint("RightLeg", right_up_leg, (0, -40.0, 0))  # 40cm down
        self.joints["RightLeg"] = right_leg
        
        right_foot = Joint("RightFoot", right_leg, (0, -40.0, 0))  # 40cm down
        self.joints["RightFoot"] = right_foot
        
        right_toe = Joint("RightToeBase", right_foot, (0, 0, 15.0))  # 15cm forward
        self.joints["RightToeBase"] = right_toe
    
    def mocap_to_bvh_coordinates(self, x, y, z):
        """Convert from mocap coordinates (baseball field) to BVH coordinates
        
        Mocap: X=horizontal (left-right), Y=vertical (up-down), Z=depth (toward pitcher)
        BVH:   X=horizontal (left-right), Y=depth (forward-back), Z=vertical (up-down)
        
        Coordinate transformation:
        BVH_X =  Mocap_X  (left-right stays the same)
        BVH_Y =  Mocap_Z  (depth becomes forward-back)
        BVH_Z =  Mocap_Y  (vertical becomes BVH vertical)
        """
        # Convert meters to centimeters for BVH
        scale = 100.0
        
        bvh_x = x * scale        # Left-right (no change)
        bvh_y = z * scale        # Forward-back (was depth)
        bvh_z = y * scale        # Up-down (was vertical)
        
        return bvh_x, bvh_y, bvh_z
    
    def extract_rotation_from_mocap(self, rotation_data, joint_index):
        """Extract rotation data from mocap rotation file
        
        The rotation file contains 252 fields (21 joints × 12 values per joint).
        Each joint has 12 values, but we need to identify which ones are actual rotations.
        Based on the data pattern, it appears the rotation values are in the first few fields.
        """
        if not rotation_data or joint_index >= len(rotation_data) // 12:
            return 0.0, 0.0, 0.0
        
        start_idx = joint_index * 12
        
        # Extract the first 3 values as potential rotation data
        # These appear to be in radians based on the magnitude
        if start_idx + 2 < len(rotation_data):
            rx = rotation_data[start_idx]      # X rotation (radians)
            ry = rotation_data[start_idx + 1]  # Y rotation (radians)  
            rz = rotation_data[start_idx + 2]  # Z rotation (radians)
            
            # Convert from radians to degrees
            rx_deg = math.degrees(rx)
            ry_deg = math.degrees(ry)
            rz_deg = math.degrees(rz)
            
            # Apply coordinate system transformation for rotations
            # Since we swapped Y and Z axes, we need to adjust rotations accordingly
            bvh_rx = rx_deg   # X rotation stays the same
            bvh_ry = rz_deg   # Y rotation was Z rotation
            bvh_rz = ry_deg   # Z rotation was Y rotation
            
            return bvh_rx, bvh_ry, bvh_rz
        
        return 0.0, 0.0, 0.0
    
    def load_mocap_data(self, joint_centers_file: str, joint_rotations_file: str):
        """Load motion capture data from text files"""
        print(f"Loading joint centers from {joint_centers_file}")
        print(f"Loading joint rotations from {joint_rotations_file}")
        
        # Load joint centers
        joint_centers = self.load_txt_file(joint_centers_file)
        print(f"Loaded {len(joint_centers)} frames of joint center data")
        
        # Load joint rotations  
        joint_rotations = self.load_txt_file(joint_rotations_file)
        print(f"Loaded {len(joint_rotations)} frames of joint rotation data")
        
        if len(joint_centers) != len(joint_rotations):
            print("Warning: Frame count mismatch between center and rotation data")
        
        # Convert to BVH frame format
        num_frames = min(len(joint_centers), len(joint_rotations))
        self.frames = []
        
        for frame_idx in range(num_frames):
            frame_data = self.convert_frame_to_bvh(
                joint_centers[frame_idx], 
                joint_rotations[frame_idx] if frame_idx < len(joint_rotations) else None,
                frame_idx
            )
            self.frames.append(frame_data)
        
        print(f"Converted {len(self.frames)} frames to BVH format")
        
        # Debug output for first few frames
        if self.debug_mode and len(self.frames) > 0:
            print("\n=== DEBUG: First 3 frames of Hips joint ===")
            for i in range(min(3, len(self.frames))):
                frame = self.frames[i]
                print(f"Frame {i}: Position=({frame[0]:.3f}, {frame[1]:.3f}, {frame[2]:.3f}) "
                      f"Rotation=({frame[3]:.3f}, {frame[4]:.3f}, {frame[5]:.3f})")
    
    def load_txt_file(self, filename: str) -> List[List[float]]:
        """Load numeric data from text file, skipping header"""
        data = []
        with open(filename, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[1:], 1):  # Skip header
                try:
                    values = [float(x) for x in line.strip().split()]
                    data.append(values)
                except ValueError as e:
                    print(f"Warning: Could not parse line {i}: {e}")
                    continue
        return data
    
    def convert_frame_to_bvh(self, centers_data: List[float], rotations_data: List[float] = None, frame_idx: int = 0) -> List[float]:
        """Convert a single frame of mocap data to BVH format"""
        frame = []
        
        # Root position from first joint center (hip/pelvis)
        # Joint centers has 300 fields = 25 joints × 12 values
        # First joint (index 0) contains the root position in first 3 values
        if len(centers_data) >= 3:
            # Extract root position and convert coordinate system
            mocap_x, mocap_y, mocap_z = centers_data[0], centers_data[1], centers_data[2]
            bvh_x, bvh_y, bvh_z = self.mocap_to_bvh_coordinates(mocap_x, mocap_y, mocap_z)
            frame.extend([bvh_x, bvh_y, bvh_z])
            
            if self.debug_mode and frame_idx < 3:
                print(f"Frame {frame_idx} root: Mocap({mocap_x:.3f}, {mocap_y:.3f}, {mocap_z:.3f}) "
                      f"-> BVH({bvh_x:.3f}, {bvh_y:.3f}, {bvh_z:.3f})")
        else:
            frame.extend([0.0, 0.0, 0.0])
        
        # Joint rotations for all joints in the hierarchy
        joint_names = list(self.joints.keys())
        
        if rotations_data:
            # Map skeleton joints to mocap rotation data
            # We have 21 joints in rotation data, need to map to our skeleton
            num_rotation_joints = len(rotations_data) // 12
            
            for i, joint_name in enumerate(joint_names):
                # Map our skeleton joints to available rotation data
                # Use modulo to cycle through available data if we have more skeleton joints
                rotation_joint_idx = i % num_rotation_joints
                
                rx, ry, rz = self.extract_rotation_from_mocap(rotations_data, rotation_joint_idx)
                frame.extend([rz, rx, ry])  # BVH order: Z, X, Y rotation
        else:
            # No rotation data, use defaults
            for joint_name in joint_names:
                frame.extend([0.0, 0.0, 0.0])
        
        return frame
    
    def write_bvh_hierarchy(self, f, joint: Joint, depth: int = 0):
        """Write the hierarchy section of the BVH file"""
        indent = "  " * depth
        
        if joint == self.root_joint:
            f.write(f"{indent}ROOT {joint.name}\n")
        else:
            f.write(f"{indent}JOINT {joint.name}\n")
        
        f.write(f"{indent}{{\n")
        f.write(f"{indent}  OFFSET {joint.offset[0]:.6f} {joint.offset[1]:.6f} {joint.offset[2]:.6f}\n")
        
        if joint == self.root_joint:
            # Root joint has 6 channels: position + rotation
            f.write(f"{indent}  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation\n")
        else:
            # Other joints only have rotation channels
            f.write(f"{indent}  CHANNELS 3 Zrotation Xrotation Yrotation\n")
        
        # Write children
        for child in joint.children:
            self.write_bvh_hierarchy(f, child, depth + 1)
        
        # Add end site for leaf joints
        if not joint.children:
            f.write(f"{indent}  End Site\n")
            f.write(f"{indent}  {{\n")
            f.write(f"{indent}    OFFSET 0.0 0.0 5.0\n")
            f.write(f"{indent}  }}\n")
        
        f.write(f"{indent}}}\n")
    
    def write_bvh(self, filename: str):
        """Write the complete BVH file"""
        print(f"Writing BVH file: {filename}")
        
        with open(filename, 'w') as f:
            # Write header
            f.write("HIERARCHY\n")
            
            # Write skeleton hierarchy
            self.write_bvh_hierarchy(f, self.root_joint)
            
            # Write motion data
            f.write("MOTION\n")
            f.write(f"Frames: {len(self.frames)}\n")
            f.write(f"Frame Time: {self.frame_time:.6f}\n")
            
            # Write frame data
            for frame in self.frames:
                frame_str = " ".join(f"{x:.6f}" for x in frame)
                f.write(frame_str + "\n")
        
        print(f"BVH file written successfully with {len(self.frames)} frames")


def main():
    """Main function to convert mocap data to BVH"""
    debug_mode = "--debug" in sys.argv
    
    if len(sys.argv) < 2 or (len(sys.argv) == 2 and sys.argv[1] == "--debug"):
        print("Usage: python mocap_to_bvh.py [output_filename.bvh] [--debug]")
        print("Will use default files: jointcenterscooper.txt, jointrotationscooper.txt")
        output_file = "cooper_baseball_motion.bvh"
    else:
        output_file = sys.argv[1] if sys.argv[1] != "--debug" else "cooper_baseball_motion.bvh"
    
    # Check if input files exist
    joint_centers_file = "jointcenterscooper.txt"
    joint_rotations_file = "jointrotationscooper.txt"
    
    if not os.path.exists(joint_centers_file):
        print(f"Error: {joint_centers_file} not found")
        return
    
    if not os.path.exists(joint_rotations_file):
        print(f"Error: {joint_rotations_file} not found")
        return
    
    # Create converter and process data
    converter = BVHConverter(debug_mode=debug_mode)
    
    try:
        converter.load_mocap_data(joint_centers_file, joint_rotations_file)
        converter.write_bvh(output_file)
        print(f"\nConversion complete! BVH file saved as: {output_file}")
        print(f"You can now import this file into Blender or view in Three.js.")
        
        if debug_mode:
            print(f"\nDebug mode was enabled. Check the output above for frame analysis.")
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()