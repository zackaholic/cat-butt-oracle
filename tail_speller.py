#!/usr/bin/env python3
"""
Tail Speller Module for Cat Butt Oracle

Handles coordinated tail movements to spell out messages on the ouija board.
Uses simple coordinated X/Y motion with lift timing.
"""

import json
import time
import math
from typing import Dict, Optional
from fluidnc.connection import FluidNCConnection
from fluidnc.streamer import FluidNCStreamer

TEST_WORD = "SLEEPY"

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
    LETTER_PAUSE = 0.1  # seconds between letters
    STEP_RATE = 50  # Hz - position updates per second
    
    # Movement speed
    X_SPEED = 500  # mm/min for X motion
    Y_MAX_SPEED = 8.0  # mm/s maximum Y speed (determines timing)
    X_START_RATIO = 0.05   # X starts at this fraction of total time (0.2 = 20%)
    X_FINISH_RATIO = 0.8  # X completes at this fraction of total time (0.7 = 70%)
    
    # Y curve shape parameters
    SMOOTHSTEP_POWER = 1.5  # S-curve steepness (1.0 = standard, >1 = sharper, <1 = gentler)
    LIFT_ASYMMETRY = 0.6    # Lift peak timing (0.5 = center, <0.5 = early peak, >0.5 = late peak)
    
    # Dynamic lift height parameters
    MIN_LIFT_HEIGHT = 3.0   # mm minimum lift height for any move
    MAX_LIFT_HEIGHT = 8.0   # mm maximum lift height for long moves  
    HEIGHT_SCALE_FACTOR = 0.5  # Height increase per mm of X distance

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
        Execute coordinated X/Y movement using Y-speed-controlled timing.
        
        Y movement speed determines overall timing. Lift height scales with X distance.
        
        Args:
            target_x: Target X coordinate
            target_y: Target Y coordinate
        """
        start_x = self.current_x
        start_y = self.current_y
        
        # Calculate dynamic lift height based on X distance
        x_distance = abs(target_x - start_x)
        dynamic_lift_height = self._calculate_lift_height(x_distance)
        
        # Calculate total Y distance (includes dynamic lift arc)
        y_base_distance = abs(target_y - start_y)
        y_lift_distance = 2 * dynamic_lift_height  # Up then down
        total_y_distance = y_base_distance + y_lift_distance
        
        # Calculate timing based on Y movement speed
        total_time = total_y_distance / self.Y_MAX_SPEED
        
        print(f"    Moving from ({start_x:.2f}, {start_y:.2f}) to ({target_x:.2f}, {target_y:.2f})")
        print(f"    X distance: {x_distance:.2f}mm, Lift height: {dynamic_lift_height:.1f}mm")
        print(f"    Y distance: {total_y_distance:.2f}mm, Total time: {total_time:.2f}s")
        
        if total_time < 0.2:  # Very short moves - just go direct
            self._move_to_position(target_x, target_y, speed=self.X_SPEED)
            return
        
        # Store dynamic height for this move
        self._current_move_lift_height = dynamic_lift_height
        
        # Parametric motion planning
        step_interval = 1.0 / self.STEP_RATE  # Time between updates
        num_steps = int(total_time / step_interval)
        
        for step in range(num_steps + 1):
            t = step / num_steps  # Progress parameter from 0 to 1
            
            # X position: S-curve acceleration with timing offsets
            current_x = self._x_position(t, start_x, target_x)
            
            # Y position: Base movement + dynamic lift curve
            current_y = self._y_position(t, start_y, target_y)
            
            # Send position update
            self._move_to_position(current_x, current_y, speed=self.X_SPEED * 3)
            
            # Wait for next step (except on last step)
            if step < num_steps:
                time.sleep(step_interval)
    
    def _x_position(self, t: float, start_x: float, target_x: float) -> float:
        """
        Calculate X position with S-curve acceleration and timing offsets.
        
        X starts at X_START_RATIO, completes at X_FINISH_RATIO with smooth acceleration.
        
        Args:
            t: Progress parameter (0 to 1)
            start_x: Starting X coordinate
            target_x: Target X coordinate
            
        Returns:
            Current X position
        """
        if t < self.X_START_RATIO:
            # X hasn't started yet - hold at start position
            return start_x
        elif t <= self.X_FINISH_RATIO:
            # X moves during middle portion with S-curve acceleration
            x_duration = self.X_FINISH_RATIO - self.X_START_RATIO
            x_raw_progress = (t - self.X_START_RATIO) / x_duration  # 0 to 1 over X movement period
            
            # Apply same smooth acceleration as Y movement
            x_smooth_progress = self._smoothstep(x_raw_progress, self.SMOOTHSTEP_POWER)
            
            return start_x + (target_x - start_x) * x_smooth_progress
        else:
            # X holds at target position
            return target_x
    
    def _y_position(self, t: float, start_y: float, target_y: float) -> float:
        """
        Calculate Y position with configurable S-curve acceleration profile.
        
        Creates smooth acceleration/deceleration for natural motion with tunable shape.
        
        Args:
            t: Progress parameter (0 to 1)
            start_y: Starting Y coordinate
            target_y: Target Y coordinate
            
        Returns:
            Current Y position
        """
        # Base Y movement with S-curve acceleration
        base_y_progress = self._smoothstep(t, self.SMOOTHSTEP_POWER)
        base_y = start_y + (target_y - start_y) * base_y_progress
        
        # Lift curve with asymmetric timing and configurable acceleration
        lift_curve = self._calculate_lift_curve(t)
        
        return base_y + lift_curve
    
    def _calculate_lift_height(self, x_distance: float) -> float:
        """
        Calculate dynamic lift height based on X distance.
        
        Args:
            x_distance: Distance of X movement in mm
            
        Returns:
            Lift height in mm (clamped between min and max)
        """
        # Calculate height based on distance and scale factor
        calculated_height = self.MIN_LIFT_HEIGHT + (x_distance * self.HEIGHT_SCALE_FACTOR)
        
        # Clamp between min and max
        return max(self.MIN_LIFT_HEIGHT, min(self.MAX_LIFT_HEIGHT, calculated_height))
    
    def _calculate_lift_curve(self, t: float) -> float:
        """
        Calculate lift curve with configurable peak timing and dynamic height.
        
        Args:
            t: Progress parameter (0 to 1)
            
        Returns:
            Lift height at time t
        """
        # Use dynamic height for this move (stored during movement execution)
        lift_height = getattr(self, '_current_move_lift_height', self.LIFT_HEIGHT)
        peak_time = self.LIFT_ASYMMETRY
        
        if t <= peak_time:
            # Up phase: 0 to peak_time
            if peak_time > 0:
                up_progress = self._smoothstep(t / peak_time, self.SMOOTHSTEP_POWER)
                return lift_height * up_progress
            else:
                return lift_height
        else:
            # Down phase: peak_time to 1
            remaining_time = 1.0 - peak_time
            if remaining_time > 0:
                down_progress = self._smoothstep((t - peak_time) / remaining_time, self.SMOOTHSTEP_POWER)
                return lift_height * (1 - down_progress)
            else:
                return 0
    
    def _smoothstep(self, t: float, power: float = 1.0) -> float:
        """
        Configurable S-curve acceleration function.
        
        Creates smooth ease-in/ease-out acceleration profile with adjustable steepness.
        
        Args:
            t: Progress parameter (0 to 1)
            power: Curve steepness (1.0 = standard, >1 = sharper, <1 = gentler)
            
        Returns:
            Smoothed progress value (0 to 1)
        """
        # Clamp t to [0, 1]
        t = max(0, min(1, t))
        
        if power == 1.0:
            # Classic smoothstep: 3t² - 2t³
            return t * t * (3 - 2 * t)
        else:
            # Generalized smoothstep using power function
            # This creates sharper (power > 1) or gentler (power < 1) curves
            smoothed = t * t * (3 - 2 * t)  # Base smoothstep
            return math.pow(smoothed, power)
    
    def _execute_tap_motion(self):
        """
        Execute a simple tap motion for repeated letters using Y-speed-controlled timing.
        Lifts Y up and brings it back down at consistent speed.
        """
        current_x = self.current_x
        current_y = self.current_y
        
        # Calculate timing based on Y movement speed (same as coordinated movement)
        y_lift_distance = 2 * self.LIFT_HEIGHT  # Up then down
        tap_time = y_lift_distance / self.Y_MAX_SPEED
        
        print(f"    Tapping at ({current_x:.2f}, {current_y:.2f})")
        print(f"    Tap time: {tap_time:.2f}s (Y-speed controlled)")
        
        step_interval = 1.0 / self.STEP_RATE
        num_steps = int(tap_time / step_interval)
        
        for step in range(num_steps + 1):
            t = step / num_steps  # Progress from 0 to 1
            
            # Y motion: smooth arc using same sine curve as normal movement
            # This creates consistent visual behavior
            lift_curve = self.LIFT_HEIGHT * math.sin(math.pi * t)
            y_pos = current_y + lift_curve
            
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
        speller.spell_message(TEST_WORD)
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        speller.disconnect()


if __name__ == "__main__":
    test_speller()
