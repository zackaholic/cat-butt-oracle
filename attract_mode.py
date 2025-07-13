#!/usr/bin/env python3
"""
Attract Mode Module for Cat Butt Oracle

Handles small twitch movements to attract attention when presence is detected.
Each twitch is a single parametric curve from home → random peak → home.
"""

import random
import threading
import time
import math
from typing import Optional


class AttractMode:
    """
    Manages attract mode behavior with random twitch movements.
    
    Twitches are single parametric curves that start and end at home position,
    with randomized peak positions, timing, and acceleration profiles.
    """
    
    # Twitch movement boundaries
    X_RANGE = 6.0      # mm, ±X movement from home
    Y_MIN = 2.0        # mm, minimum Y peak (for visible movement)  
    Y_MAX = 5.0       # mm, maximum Y peak
    
    # Timing parameters
    SPEED_MIN = 3.0    # mm/s, minimum twitch speed
    SPEED_MAX = 8.0    # mm/s, maximum twitch speed
    PEAK_TIME_MIN = 0.3  # fraction, earliest peak timing
    PEAK_TIME_MAX = 0.7  # fraction, latest peak timing
    CURVE_SHARPNESS_MIN = 0.8  # minimum S-curve steepness
    CURVE_SHARPNESS_MAX = 2.0  # maximum S-curve steepness
    
    # Pause between twitches
    PAUSE_MIN = 0.5    # seconds, minimum pause between twitches
    PAUSE_MAX = 3.0    # seconds, maximum pause between twitches
    
    # Movement parameters
    STEP_RATE = 80     # Hz, position updates per second
    
    def __init__(self, tail_speller):
        """
        Initialize attract mode.
        
        Args:
            tail_speller: TailSpeller instance for movement control
        """
        self.tail_speller = tail_speller
        self.should_stop = threading.Event()
        self.is_running = False
        self.is_moving = False
        self.attract_thread = None
    
    def start(self):
        """Start attract mode in a separate thread."""
        if self.is_running:
            return False
            
        self.should_stop.clear()
        self.is_running = True
        self.attract_thread = threading.Thread(target=self._attract_loop, daemon=True)
        self.attract_thread.start()
        print("Attract mode started")
        return True
    
    def stop(self):
        """
        Request attract mode to stop.
        
        Will complete current twitch and exit cleanly at home position.
        """
        if not self.is_running:
            return
            
        print("Attract mode stop requested...")
        self.should_stop.set()
        
        # Wait for current movement to complete
        if self.attract_thread and self.attract_thread.is_alive():
            self.attract_thread.join(timeout=5.0)  # Max 5 second wait
            
        self.is_running = False
        print("Attract mode stopped")
    
    def _attract_loop(self):
        """Main attract mode loop - runs in separate thread."""
        try:
            while not self.should_stop.is_set():
                # Perform single twitch movement
                self.is_moving = True
                self._execute_twitch()
                self.is_moving = False
                
                # Random pause between twitches
                pause_duration = random.uniform(self.PAUSE_MIN, self.PAUSE_MAX)
                
                # Use wait() to allow immediate exit on stop request
                if self.should_stop.wait(timeout=pause_duration):
                    break  # Stop requested during pause
                    
        except Exception as e:
            print(f"Error in attract mode: {e}")
        finally:
            self.is_running = False
            self.is_moving = False
    
    def _execute_twitch(self):
        """
        Execute a single twitch movement: home → random peak → home.
        
        Uses the same S-curve acceleration system as message spelling.
        """
        # Generate random twitch parameters
        peak_x = random.uniform(-self.X_RANGE, self.X_RANGE)
        peak_y = random.uniform(self.Y_MIN, self.Y_MAX)
        peak_time = random.uniform(self.PEAK_TIME_MIN, self.PEAK_TIME_MAX)
        twitch_speed = random.uniform(self.SPEED_MIN, self.SPEED_MAX)
        curve_sharpness = random.uniform(self.CURVE_SHARPNESS_MIN, self.CURVE_SHARPNESS_MAX)
        
        # Calculate total movement distance and timing
        total_distance = math.sqrt(peak_x**2 + peak_y**2) * 2  # There and back
        total_time = total_distance / twitch_speed
        
        print(f"    Twitch: peak({peak_x:.1f}, {peak_y:.1f}), "
              f"time={total_time:.2f}s, sharpness={curve_sharpness:.1f}")
        
        # Parametric motion execution
        step_interval = 1.0 / self.STEP_RATE
        num_steps = int(total_time / step_interval)
        
        for step in range(num_steps + 1):
            if self.should_stop.is_set():
                # Early exit requested - return to home immediately
                self.tail_speller._move_to_position(0, 0, speed=500)
                return
                
            t = step / num_steps  # Progress parameter from 0 to 1
            
            # Calculate position using twitch curve
            curve_value = self._twitch_curve(t, peak_time, curve_sharpness)
            current_x = peak_x * curve_value
            current_y = peak_y * curve_value
            
            # Safety check: ensure Y never goes negative
            current_y = max(0, current_y)
            
            # Send position update
            self.tail_speller._move_to_position(current_x, current_y, speed=500)
            
            # Wait for next step (except on last step)
            if step < num_steps:
                time.sleep(step_interval)
    
    def _twitch_curve(self, t: float, peak_time: float, sharpness: float) -> float:
        """
        Calculate twitch curve value that goes 0 → 1 → 0.
        
        Args:
            t: Progress parameter (0 to 1)
            peak_time: When the peak occurs (0 to 1)
            sharpness: S-curve steepness
            
        Returns:
            Curve value (0 to 1)
        """
        if t <= peak_time:
            # Up phase: 0 to peak_time
            if peak_time > 0:
                up_progress = t / peak_time
                return self._smoothstep(up_progress, sharpness)
            else:
                return 1.0
        else:
            # Down phase: peak_time to 1
            remaining_time = 1.0 - peak_time
            if remaining_time > 0:
                down_progress = (t - peak_time) / remaining_time
                return 1.0 - self._smoothstep(down_progress, sharpness)
            else:
                return 0.0
    
    def _smoothstep(self, t: float, power: float = 1.0) -> float:
        """
        S-curve acceleration function (same as TailSpeller).
        
        Args:
            t: Progress parameter (0 to 1)
            power: Curve steepness
            
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
            smoothed = t * t * (3 - 2 * t)
            return math.pow(smoothed, power)


def test_attract_mode():
    """Test function for attract mode."""
    from tail_speller import TailSpeller
    
    # Initialize components
    speller = TailSpeller()
    attract = AttractMode(speller)
    
    if not speller.connect():
        print("Failed to connect to controller")
        return
    
    try:
        print("Starting attract mode test...")
        print("Press Ctrl+C to stop")
        
        # Start attract mode
        attract.start()
        
        # Let it run until interrupted
        while attract.is_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\nStopping attract mode...")
    finally:
        attract.stop()
        speller.disconnect()


if __name__ == "__main__":
    test_attract_mode()
