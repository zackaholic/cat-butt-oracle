#!/usr/bin/env python3
"""
Tail Speller Module for Cat Butt Oracle

Handles coordinated tail movements to spell out messages on the ouija board.
Uses simple coordinated X/Y motion with lift timing.
"""

import json
import time
from typing import Dict, Optional
from fluidnc.connection import FluidNCConnection
from fluidnc.streamer import FluidNCStreamer


class TailSpeller:
    """
    Manages tail movements for spelling messages on the ouija board.
    
    Simple coordinated motion:
    - X moves at constant velocity
    - Y lifts at 1/4 of X motion, then descends to arrive with X
    """
    
    # Movement parameters
    HOME_X = 0.0
    HOME_Y = 0.0
    LIFT_HEIGHT = 4.0  # mm to lift tail during moves
    
    # Timing parameters
    SETTLE_TIME = 0.8  # seconds to pause at each letter
    LETTER_PAUSE = 0.7  # seconds between letters
    STEP_RATE = 30  # Hz - position updates per second
    
    # Movement speed
    X_SPEED = 200  # mm/min for X motion (determines timing)
    
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
    
    def connect(self, port: str = None):
        """Establish connection to FluidNC controller."""
        try:
            self.streamer = FluidNCStreamer(port=port)
            if self.streamer.connect():
                print("Connected to FluidNC controller")
                return True
            else:
                print("Failed to connect to FluidNC controller")
                return False
        except Exception as e:
            print(f"Failed to connect to FluidNC: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from FluidNC controller."""
        if self.streamer:
            self.streamer.disconnect()
            print("Disconnected from FluidNC")
    
    def go_home(self):
        """Move tail to home position."""
        print("Moving to home position...")
        self._move_to_position(self.HOME_X, self.HOME_Y, speed=self.X_SPEED)
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
        Move tail to a specific letter using simple coordinated motion.
        
        Args:
            letter: Letter to move to
        """
        if letter not in self.letter_positions:
            return
        
        target_x = self.letter_positions[letter]['x']
        target_y = self.letter_positions[letter]['y']
        
        # Check if we're already at this position (repeated letter)
        if (abs(self.current_x - target_x) < 0.1 and 
            abs(self.current_y - target_y) < 0.1):
            print(f"    Tapping letter '{letter}' (repeat)")
            self._execute_tap_motion()
        else:
            # Execute coordinated movement to new position
            self._execute_coordinated_movement(target_x, target_y)
        
        # Update current position
        self.current_x = target_x
        self.current_y = target_y
        
        # Settle at the letter
        time.sleep(self.SETTLE_TIME)
    
    def _execute_coordinated_movement(self, target_x: float, target_y: float):
        """
        Execute coordinated X/Y movement using time-based interpolation.
        
        Breaks movement into small steps with proper timing coordination.
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
        """
        start_x = self.current_x
        start_y = self.current_y
        
        # Calculate movement parameters
        x_distance = abs(target_x - start_x)
        total_time = (x_distance / self.X_SPEED) * 60  # Convert mm/min to seconds
        
        print(f"    Moving from ({start_x:.2f}, {start_y:.2f}) to ({target_x:.2f}, {target_y:.2f})")
        print(f"    X distance: {x_distance:.2f}mm, Total time: {total_time:.2f}s")
        
        if total_time < 0.2:  # Very short moves - just go direct
            self._move_to_position(target_x, target_y, speed=self.X_SPEED)
            return
        
        # Time-based interpolation with small steps
        step_interval = 1.0 / self.STEP_RATE  # Time between updates
        num_steps = int(total_time / step_interval)
        
        for step in range(num_steps + 1):
            t = step / num_steps  # Progress from 0 to 1
            elapsed_time = step * step_interval
            
            # X position: linear interpolation
            current_x = start_x + (target_x - start_x) * t
            
            # Y position: coordinated lift timing
            if elapsed_time < (total_time * 0.25):
                # Phase 1: Stay at start Y
                current_y = start_y
            elif elapsed_time < (total_time * 0.625):  # 1/4 to 5/8 of time
                # Phase 2: Lift to LIFT_HEIGHT
                lift_progress = (elapsed_time - total_time * 0.25) / (total_time * 0.375)
                current_y = start_y + self.LIFT_HEIGHT * lift_progress
            else:
                # Phase 3: Descend to target
                lift_y = start_y + self.LIFT_HEIGHT
                descend_progress = (elapsed_time - total_time * 0.625) / (total_time * 0.375)
                current_y = lift_y + (target_y - lift_y) * descend_progress
            
            # Send position update
            self._move_to_position(current_x, current_y, speed=self.X_SPEED * 3)  # Higher speed for small moves
            
            # Wait for next step (except on last step)
            if step < num_steps:
                time.sleep(step_interval)
    
    def _execute_tap_motion(self):
        """
        Execute a simple tap motion for repeated letters.
        Lifts Y up and brings it back down.
        """
        current_x = self.current_x
        current_y = self.current_y
        lift_y = current_y + self.LIFT_HEIGHT
        
        # Calculate timing for tap motion
        tap_time = 0.5  # Total time for tap motion in seconds
        step_interval = 1.0 / self.STEP_RATE
        num_steps = int(tap_time / step_interval)
        
        for step in range(num_steps + 1):
            t = step / num_steps  # Progress from 0 to 1
            
            # Y motion: up then down
            if t <= 0.5:
                # First half: lift up
                progress = t * 2  # 0 to 1 over first half
                y_pos = current_y + self.LIFT_HEIGHT * progress
            else:
                # Second half: bring down
                progress = (t - 0.5) * 2  # 0 to 1 over second half
                y_pos = lift_y - self.LIFT_HEIGHT * progress
            
            # Send position update (X stays constant)
            self._move_to_position(current_x, y_pos, speed=self.X_SPEED * 2)
            
            # Wait for next step (except on last step)
            if step < num_steps:
                time.sleep(step_interval)
    
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
            self.streamer.send_command(gcode)
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
        speller.spell_message("ROTTEN")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        speller.disconnect()


if __name__ == "__main__":
    test_speller()
