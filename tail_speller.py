#!/usr/bin/env python3
"""
Tail Speller Module for Cat Butt Oracle

Handles precise, lifelike tail movements to spell out messages on the ouija board.
Uses sophisticated movement profiles with randomness to create organic, cat-like motion.
"""

import json
import math
import random
import time
from typing import Dict, List, Tuple, Optional
from fluidnc.connection import FluidNCConnection
from fluidnc.streamer import GCodeStreamer


class TailSpeller:
    """
    Manages tail movements for spelling messages on the ouija board.
    
    Features:
    - Loads letter coordinates from JSON file
    - Generates smooth, lifelike movement paths
    - Applies randomness for organic motion
    - Precise letter targeting with dramatic timing
    """
    
    # Movement parameters - easily tunable
    HOME_X = 0.0
    HOME_Y = 0.0
    LIFT_HEIGHT = 5.0  # mm to lift tail during moves
    Y_RANDOMNESS = 0.5  # mm random variation in Y path
    WAYPOINT_RESOLUTION = 0.1  # mm between waypoints
    TAP_DISTANCE = 1.5  # mm before destination to accelerate
    
    # Timing parameters
    SETTLE_TIME = 0.5  # seconds to pause at each letter
    LETTER_PAUSE = 1.2  # seconds between letters
    
    # Movement speeds (mm/min)
    LIFT_SPEED = 1200
    APPROACH_SPEED = 800
    TAP_SPEED = 1500
    
    def __init__(self, coordinates_file: str = "ouija_letter_positions.json"):
        """
        Initialize the tail speller.
        
        Args:
            coordinates_file: Path to JSON file with letter coordinates
        """
        self.coordinates_file = coordinates_file
        self.letter_positions = {}
        self.current_x = self.HOME_X
        self.current_y = self.HOME_Y
        self.fluidnc = None
        self.streamer = None
        
        # Load letter coordinates
        self._load_coordinates()
        
    def _load_coordinates(self):
        """Load letter positions from JSON file."""
        try:
            with open(self.coordinates_file, 'r') as f:
                self.letter_positions = json.load(f)
            print(f"Loaded {len(self.letter_positions)} letter positions")
        except FileNotFoundError:
            print(f"Warning: Coordinates file {self.coordinates_file} not found")
            self.letter_positions = {}
        except json.JSONDecodeError as e:
            print(f"Error loading coordinates: {e}")
            self.letter_positions = {}
    
    def connect(self):
        """Establish connection to FluidNC controller."""
        try:
            self.fluidnc = FluidNCConnection()
            self.fluidnc.connect()
            self.streamer = GCodeStreamer(self.fluidnc)
            print("Connected to FluidNC controller")
            return True
        except Exception as e:
            print(f"Failed to connect to FluidNC: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from FluidNC controller."""
        if self.fluidnc:
            self.fluidnc.disconnect()
            print("Disconnected from FluidNC")
    
    def go_home(self):
        """Move tail to home position."""
        print("Moving to home position...")
        self._move_to_position(self.HOME_X, self.HOME_Y, speed=self.APPROACH_SPEED)
        self.current_x = self.HOME_X
        self.current_y = self.HOME_Y
    
    def spell_message(self, message: str):
        """
        Spell out a complete message by moving the tail to each letter.
        
        Args:
            message: String message to spell out
        """
        if not self.streamer:
            print("Error: Not connected to FluidNC controller")
            return
        
        message = message.upper().strip()
        print(f"Spelling message: '{message}'")
        
        for i, letter in enumerate(message):
            if letter == ' ':
                # Handle spaces with a longer pause
                print("  [SPACE]")
                time.sleep(self.LETTER_PAUSE * 1.5)
                continue
            
            if letter not in self.letter_positions:
                print(f"  Warning: Letter '{letter}' not found in coordinates, skipping")
                continue
            
            print(f"  Spelling letter: {letter}")
            self._move_to_letter(letter)
            
            # Pause between letters (except after last letter)
            if i < len(message) - 1:
                time.sleep(self.LETTER_PAUSE)
        
        print("Message complete, returning home")
        self.go_home()
    
    def _move_to_letter(self, letter: str):
        """
        Move tail to a specific letter using lifelike motion.
        
        Args:
            letter: Letter to move to
        """
        if letter not in self.letter_positions:
            return
        
        target_x = self.letter_positions[letter]['x']
        target_y = self.letter_positions[letter]['y']
        
        # Generate movement path with lift → approach → tap
        self._execute_lifelike_movement(target_x, target_y)
        
        # Update current position
        self.current_x = target_x
        self.current_y = target_y
        
        # Settle at the letter
        time.sleep(self.SETTLE_TIME)
    
    def _execute_lifelike_movement(self, target_x: float, target_y: float):
        """
        Execute a lifelike movement to target coordinates.
        
        Movement sequence:
        1. Lift Y by LIFT_HEIGHT
        2. Move X to target while lowering Y (with randomness)
        3. X arrives first, then Y accelerates for final "tap"
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
        """
        start_x = self.current_x
        start_y = self.current_y
        
        # Phase 1: Lift tail
        lift_y = start_y + self.LIFT_HEIGHT
        print(f"    Lifting to Y={lift_y:.2f}")
        self._move_to_position(start_x, lift_y, speed=self.LIFT_SPEED)
        
        # Phase 2: Generate approach path with randomness
        path_points = self._generate_approach_path(
            start_x, lift_y, target_x, target_y
        )
        
        # Phase 3: Execute path with timing coordination
        self._execute_path(path_points)
    
    def _generate_approach_path(self, start_x: float, start_y: float, 
                              target_x: float, target_y: float) -> List[Tuple[float, float, float]]:
        """
        Generate waypoints for approach path with Y randomness.
        
        Returns:
            List of (x, y, speed) tuples for each waypoint
        """
        dx = target_x - start_x
        dy = target_y - start_y
        
        # Calculate total distance and number of waypoints
        total_distance = math.sqrt(dx**2 + dy**2)
        num_waypoints = int(total_distance / self.WAYPOINT_RESOLUTION)
        
        if num_waypoints < 2:
            num_waypoints = 2
        
        path_points = []
        
        for i in range(num_waypoints + 1):
            # Linear interpolation for base path
            t = i / num_waypoints
            base_x = start_x + dx * t
            base_y = start_y + dy * t
            
            # Add Y randomness (except at start and end)
            if 0 < i < num_waypoints:
                y_offset = random.uniform(-self.Y_RANDOMNESS, self.Y_RANDOMNESS)
                actual_y = base_y + y_offset
            else:
                actual_y = base_y
            
            # Determine speed based on position in path
            if i < num_waypoints * 0.8:  # Normal approach speed
                speed = self.APPROACH_SPEED
            else:  # Accelerate for final tap
                speed = self.TAP_SPEED
            
            path_points.append((base_x, actual_y, speed))
        
        return path_points
    
    def _execute_path(self, path_points: List[Tuple[float, float, float]]):
        """
        Execute a series of waypoints with appropriate timing.
        
        Args:
            path_points: List of (x, y, speed) waypoints
        """
        for x, y, speed in path_points:
            self._move_to_position(x, y, speed=speed)
    
    def _move_to_position(self, x: float, y: float, speed: float):
        """
        Move to a specific position using G-code.
        
        Args:
            x: Target X coordinate
            y: Target Y coordinate  
            speed: Movement speed in mm/min
        """
        if not self.streamer:
            return
        
        # Generate G-code for coordinated move
        gcode = f"G1 X{x:.3f} Y{y:.3f} F{speed:.0f}"
        
        try:
            self.streamer.send_line(gcode)
            self.streamer.wait_for_completion()
        except Exception as e:
            print(f"Error executing move: {e}")


def test_speller():
    """Test function for the tail speller."""
    speller = TailSpeller()
    
    if not speller.connect():
        print("Failed to connect to controller")
        return
    
    try:
        # Test with a simple message
        speller.spell_message("HELLO")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        speller.disconnect()


if __name__ == "__main__":
    test_speller()