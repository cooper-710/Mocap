#!/usr/bin/env python3
"""
Motion Capture to BVH Converter
Converts Cooper motion capture .txt files to BVH format for Blender import

Author: AI Assistant
"""

import os
import sys
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
    
    def __init__(self):
        self.joints = {}
        self.root_joint = None
        self.frame_time = 1.0 / 30.0  # 30 FPS default
        self.frames = []
        
        # Standard human skeleton hierarchy for baseball motion
        self.setup_skeleton()
    
    def setup_skeleton(self):
        """Setup standard human skeleton hierarchy"""
        # Root
        self.root_joint = Joint("Hips")
        self.joints["Hips"] = self.root_joint
        
        # Spine
        spine = Joint("Spine", self.root_joint, (0, 5.0, 0))
        self.joints["Spine"] = spine
        
        spine1 = Joint("Spine1", spine, (0, 5.0, 0))
        self.joints["Spine1"] = spine1
        
        spine2 = Joint("Spine2", spine1, (0, 5.0, 0))
        self.joints["Spine2"] = spine2
        
        neck = Joint("Neck", spine2, (0, 5.0, 0))
        self.joints["Neck"] = neck
        
        head = Joint("Head", neck, (0, 3.0, 0))
        self.joints["Head"] = head
        
        # Left arm
        left_shoulder = Joint("LeftShoulder", spine2, (-3.0, 3.0, 0))
        self.joints["LeftShoulder"] = left_shoulder
        
        left_arm = Joint("LeftArm", left_shoulder, (-7.0, 0, 0))
        self.joints["LeftArm"] = left_arm
        
        left_forearm = Joint("LeftForeArm", left_arm, (-12.0, 0, 0))
        self.joints["LeftForeArm"] = left_forearm
        
        left_hand = Joint("LeftHand", left_forearm, (-8.0, 0, 0))
        self.joints["LeftHand"] = left_hand
        
        # Right arm
        right_shoulder = Joint("RightShoulder", spine2, (3.0, 3.0, 0))
        self.joints["RightShoulder"] = right_shoulder
        
        right_arm = Joint("RightArm", right_shoulder, (7.0, 0, 0))
        self.joints["RightArm"] = right_arm
        
        right_forearm = Joint("RightForeArm", right_arm, (12.0, 0, 0))
        self.joints["RightForeArm"] = right_forearm
        
        right_hand = Joint("RightHand", right_forearm, (8.0, 0, 0))
        self.joints["RightHand"] = right_hand
        
        # Left leg
        left_up_leg = Joint("LeftUpLeg", self.root_joint, (-2.0, 0, 0))
        self.joints["LeftUpLeg"] = left_up_leg
        
        left_leg = Joint("LeftLeg", left_up_leg, (0, -18.0, 0))
        self.joints["LeftLeg"] = left_leg
        
        left_foot = Joint("LeftFoot", left_leg, (0, -18.0, 0))
        self.joints["LeftFoot"] = left_foot
        
        left_toe = Joint("LeftToeBase", left_foot, (0, 0, 8.0))
        self.joints["LeftToeBase"] = left_toe
        
        # Right leg
        right_up_leg = Joint("RightUpLeg", self.root_joint, (2.0, 0, 0))
        self.joints["RightUpLeg"] = right_up_leg
        
        right_leg = Joint("RightLeg", right_up_leg, (0, -18.0, 0))
        self.joints["RightLeg"] = right_leg
        
        right_foot = Joint("RightFoot", right_leg, (0, -18.0, 0))
        self.joints["RightFoot"] = right_foot
        
        right_toe = Joint("RightToeBase", right_foot, (0, 0, 8.0))
        self.joints["RightToeBase"] = right_toe
    
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
            frame_data = self.convert_frame_to_bvh(joint_centers[frame_idx], 
                                                  joint_rotations[frame_idx] if frame_idx < len(joint_rotations) else None)
            self.frames.append(frame_data)
        
        print(f"Converted {len(self.frames)} frames to BVH format")
    
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
    
    def convert_frame_to_bvh(self, centers_data: List[float], rotations_data: List[float] = None) -> List[float]:
        """Convert a single frame of mocap data to BVH format"""
        # BVH frame format: root position + rotations for all joints
        frame = []
        
        # Root position (first joint center)
        if len(centers_data) >= 3:
            frame.extend([centers_data[0], centers_data[1], centers_data[2]])
        else:
            frame.extend([0.0, 0.0, 0.0])
        
        # Joint rotations - map available rotation data to skeleton joints
        joint_names = list(self.joints.keys())
        
        if rotations_data:
            # Estimate rotations based on available data
            num_rotation_joints = len(rotations_data) // 12  # 12 values per joint
            rotation_per_joint = 3  # X, Y, Z rotations
            
            for i, joint_name in enumerate(joint_names):
                # Map mocap data to joint rotations
                if i < num_rotation_joints and (i * 12 + 2) < len(rotations_data):
                    # Use first 3 values as rotation (convert from mocap coordinate system)
                    rx = rotations_data[i * 12] * 57.2958  # Convert to degrees
                    ry = rotations_data[i * 12 + 1] * 57.2958
                    rz = rotations_data[i * 12 + 2] * 57.2958
                    frame.extend([rx, ry, rz])
                else:
                    # Default rotation
                    frame.extend([0.0, 0.0, 0.0])
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
            f.write(f"{indent}  CHANNELS 6 Xposition Yposition Zposition Zrotation Xrotation Yrotation\n")
        else:
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
    if len(sys.argv) < 2:
        print("Usage: python mocap_to_bvh.py [output_filename.bvh]")
        print("Will use default files: jointcenterscooper.txt, jointrotationscooper.txt")
        output_file = "cooper_baseball_motion.bvh"
    else:
        output_file = sys.argv[1]
    
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
    converter = BVHConverter()
    
    try:
        converter.load_mocap_data(joint_centers_file, joint_rotations_file)
        converter.write_bvh(output_file)
        print(f"\nConversion complete! BVH file saved as: {output_file}")
        print(f"You can now import this file into Blender.")
        
    except Exception as e:
        print(f"Error during conversion: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()