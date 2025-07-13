#!/usr/bin/env python3
"""
Main Controller for Cat Butt Oracle

Orchestrates the complete interactive experience:
sensor monitoring → attract mode → message spelling → repeat cycle
"""

import json
import logging
import random
import time
import threading
from collections import deque
from typing import Optional, List, Dict

from tail_speller import TailSpeller
from attract_mode import AttractMode
from sensors.hc_sr04 import UltrasonicSensor


class CatButtOracle:
    """
    Main controller for the Cat Butt Oracle interactive art installation.
    
    Manages the complete interaction flow from presence detection through
    attract mode to message spelling with proper error handling and reconnection.
    """
    
    # Configurable parameters
    PRESENCE_CONFIRMATION_TIME = 8.0  # seconds of continuous presence required
    POST_MESSAGE_PAUSE = 3.0          # seconds to pause after spelling message
    DISTANCE_THRESHOLD = 36.0         # inches - presence detection threshold
    DEBUG_MODE = True                 # Enable debug prints (set False for production)
    ATTRACT_MOVEMENT_BUFFER = 1.0     # seconds to wait after attract movement before state changes
    DRAMATIC_PAUSE_TIME = 2.5         # seconds to wait before spelling message

    # Anti-repetition settings
    ANTI_REPETITION_COUNT = 5         # avoid repeating last N messages
    
    # Connection retry settings
    RECONNECT_DELAY = 2.0             # seconds between reconnection attempts
    MAX_RECONNECT_ATTEMPTS = 10       # max attempts before giving up temporarily
    RECONNECT_PAUSE = 30.0            # seconds to wait before retrying after max attempts
    
    # Sensor settings
    SENSOR_UPDATE_RATE = 5.0          # Hz - sensor reading frequency
    SENSOR_TRIG_PIN = 14              # GPIO pin for ultrasonic trigger (same as test script)
    SENSOR_ECHO_PIN = 15              # GPIO pin for ultrasonic echo (same as test script)
    
    def __init__(self, responses_file: str = "responses.json"):
        """
        Initialize the Cat Butt Oracle controller.
        
        Args:
            responses_file: Path to JSON file with message responses
        """
        self.responses_file = responses_file
        self.messages = []
        self.recent_messages = deque(maxlen=self.ANTI_REPETITION_COUNT)
        
        # Component instances
        self.tail_speller = None
        self.attract_mode = None
        self.sensor = None
        
        # State tracking
        self.is_running = False
        self.presence_start_time = None
        self.is_in_attract_mode = False
        self.fluidnc_connected = False
        self.last_attract_movement_time = None
        
        # Threading
        self.main_thread = None
        self.should_stop = threading.Event()
        
        # Setup logging
        self._setup_logging()
        
        # Load messages
        self._load_messages()
        
        # Initialize components
        self._initialize_components()
    
    def _debug_print(self, message: str):
        """Print debug message if debug mode is enabled."""
        if self.DEBUG_MODE:
            print(f"[DEBUG] {message}")
    
    def _setup_logging(self):
        """Setup error-only logging."""
        logging.basicConfig(
            level=logging.ERROR,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('cat_butt_oracle.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def _load_messages(self):
        """Load message responses from JSON file."""
        try:
            with open(self.responses_file, 'r') as f:
                data = json.load(f)
            
            # Extract all messages from all moods
            self.messages = []
            if 'moods' in data:
                for mood_name, mood_data in data['moods'].items():
                    if 'responses' in mood_data:
                        self.messages.extend(mood_data['responses'])
            
            print(f"Loaded {len(self.messages)} messages from {self.responses_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to load messages from {self.responses_file}: {e}")
            # Fallback messages
            self.messages = ["HELLO", "GREETINGS", "WELCOME"]
    
    def _initialize_components(self):
        """Initialize hardware components."""
        # Initialize ultrasonic sensor FIRST to avoid GPIO conflicts
        try:
            self.sensor = UltrasonicSensor(
                trig_pin=self.SENSOR_TRIG_PIN,
                echo_pin=self.SENSOR_ECHO_PIN
            )
            print(f"✅ Initialized ultrasonic sensor on pins TRIG={self.SENSOR_TRIG_PIN}, ECHO={self.SENSOR_ECHO_PIN}")
            self._debug_print(f"Sensor threshold set to {self.DISTANCE_THRESHOLD} inches")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize ultrasonic sensor: {e}")
            print(f"❌ Failed to initialize sensor: {e}")
            self.sensor = None
        
        # Initialize tail speller (after sensor to avoid any GPIO issues)
        self.tail_speller = TailSpeller()
        
        # Initialize attract mode (requires tail speller)
        self.attract_mode = AttractMode(self.tail_speller)
    
    
    def start(self):
        """Start the main control loop."""
        if self.is_running:
            print("Oracle is already running")
            return False
        
        print("Starting Cat Butt Oracle...")
        
        # Connect to FluidNC
        if not self._connect_fluidnc():
            print("Failed to establish initial FluidNC connection")
            return False
        
        # Start main loop
        self.should_stop.clear()
        self.is_running = True
        self.main_thread = threading.Thread(target=self._main_loop, daemon=True)
        self.main_thread.start()
        
        print("Cat Butt Oracle is now active")
        return True
    
    def stop(self):
        """Stop the main control loop and cleanup."""
        if not self.is_running:
            return
        
        print("Stopping Cat Butt Oracle...")
        
        # Signal stop
        self.should_stop.set()
        
        # Stop attract mode if running
        if self.is_in_attract_mode:
            self.attract_mode.stop()
            self.is_in_attract_mode = False
        
        # Wait for main thread to finish
        if self.main_thread and self.main_thread.is_alive():
            self.main_thread.join(timeout=10.0)
        
        # Cleanup components
        self._cleanup()
        
        self.is_running = False
        print("Cat Butt Oracle stopped")
    
    def _main_loop(self):
        """Main control loop - runs in separate thread."""
        print("🔄 Main control loop started")
        self._debug_print(f"Sensor update rate: {self.SENSOR_UPDATE_RATE} Hz")
        
        try:
            while not self.should_stop.is_set():
                # Check sensor connectivity
                if not self._check_sensor():
                    self._debug_print("Sensor check failed, waiting 1s")
                    time.sleep(1.0)
                    continue
                
                # Check FluidNC connectivity
                if not self._check_fluidnc_connection():
                    self._debug_print(f"FluidNC check failed, waiting {self.RECONNECT_DELAY}s")
                    time.sleep(self.RECONNECT_DELAY)
                    continue
                
                # Get distance reading using raw method (more reliable)
                distance = self.sensor.get_raw_reading()
                
                if distance is not None:
                    self._debug_print(f"Sensor reading: {distance:.1f} inches (threshold: {self.DISTANCE_THRESHOLD})")
                else:
                    self._debug_print("Sensor reading: None (no object in range)")
                
                if distance is not None and distance <= self.DISTANCE_THRESHOLD:
                    # Presence detected
                    self._handle_presence_detected()
                else:
                    # No presence (either None reading or distance > threshold)
                    self._handle_no_presence()
                
                # Update attract movement tracking
                if self.is_in_attract_mode:
                    self._update_attract_movement_time()
                
                # Sleep based on sensor update rate
                time.sleep(1.0 / self.SENSOR_UPDATE_RATE)
                
        except Exception as e:
            self.logger.error(f"Error in main loop: {e}")
        finally:
            # Ensure attract mode is stopped
            if self.is_in_attract_mode:
                self.attract_mode.stop()
                self.is_in_attract_mode = False
    
    def _check_sensor(self) -> bool:
        """Check if sensor is working properly."""
        if self.sensor is None:
            self._debug_print("Sensor is None - not initialized")
            return False
        
        try:
            # Try to get a reading - None is valid when no object in range
            distance = self.sensor.get_raw_reading()
            # Sensor is working if it returns a number OR None (no object detected)
            return True
        except Exception as e:
            self.logger.error(f"Sensor error: {e}")
            self._debug_print(f"Sensor exception: {e}")
            return False
    
    def _check_fluidnc_connection(self) -> bool:
        """Check FluidNC connection and reconnect if needed."""
        if self.tail_speller.streamer is None:
            self._debug_print("Streamer is None, connecting...")
            return self._connect_fluidnc()
        
        # Check if the underlying connection is still active
        try:
            if (hasattr(self.tail_speller.streamer, '_connection') and 
                self.tail_speller.streamer._connection and
                hasattr(self.tail_speller.streamer._connection, '_connected') and
                self.tail_speller.streamer._connection._connected):
                # Connection looks good
                self._debug_print("FluidNC connection verified")
                return True
            else:
                self._debug_print("FluidNC connection lost, reconnecting...")
                self.fluidnc_connected = False
                return self._connect_fluidnc(go_home=False)  # Don't go home on reconnection checks
        except Exception as e:
            self.logger.error(f"FluidNC connection check failed: {e}")
            self._debug_print(f"FluidNC connection check exception: {e}")
            self.fluidnc_connected = False
            return self._connect_fluidnc(go_home=False)  # Don't go home on reconnection checks
    
    def _connect_fluidnc(self, go_home: bool = True) -> bool:
        """Attempt to connect to FluidNC with retry logic."""
        for attempt in range(self.MAX_RECONNECT_ATTEMPTS):
            try:
                print(f"Attempting FluidNC connection (attempt {attempt + 1}/{self.MAX_RECONNECT_ATTEMPTS})...")
                
                if self.tail_speller.connect():
                    self.fluidnc_connected = True
                    print("FluidNC connection established")
                    
                    # Return to home position only on initial connection or when requested
                    if go_home:
                        print("Moving to home position...")
                        self.tail_speller.go_home()
                    return True
                else:
                    time.sleep(self.RECONNECT_DELAY)
                    
            except Exception as e:
                self.logger.error(f"FluidNC connection attempt {attempt + 1} failed: {e}")
                time.sleep(self.RECONNECT_DELAY)
        
        # Max attempts reached
        self.logger.error(f"Failed to connect to FluidNC after {self.MAX_RECONNECT_ATTEMPTS} attempts")
        print(f"FluidNC connection failed - waiting {self.RECONNECT_PAUSE}s before retrying...")
        time.sleep(self.RECONNECT_PAUSE)
        return False
    
    def _handle_presence_detected(self):
        """Handle when presence is detected."""
        current_time = time.time()
        
        if self.presence_start_time is None:
            # First detection
            self.presence_start_time = current_time
            print(f"✨ PRESENCE DETECTED - person within {self.DISTANCE_THRESHOLD} inches")
            self._debug_print(f"Presence timer started at {current_time}")
        
        # Check if we should start attract mode
        if not self.is_in_attract_mode:
            print("🎯 STARTING ATTRACT MODE")
            if self.attract_mode.start():
                self.is_in_attract_mode = True
                self._debug_print("Attract mode thread started successfully")
            else:
                self._debug_print("Failed to start attract mode")
        
        # Check if presence has been continuous long enough
        presence_duration = current_time - self.presence_start_time
        self._debug_print(f"Presence duration: {presence_duration:.1f}s / {self.PRESENCE_CONFIRMATION_TIME}s required")
        
        if presence_duration >= self.PRESENCE_CONFIRMATION_TIME:
            # Check if we're within the buffer time after an attract movement
            if self._within_attract_movement_buffer():
                self._debug_print(f"Presence confirmed ({presence_duration:.1f}s) but within attract movement buffer - waiting")
                return
            
            # Confirmed presence - trigger message
            print(f"✅ PRESENCE CONFIRMED ({presence_duration:.1f}s) - TRIGGERING MESSAGE")
            self._trigger_message()
            
            # Reset presence timer
            self.presence_start_time = None
            self._debug_print("Presence timer reset")
    
    def _handle_no_presence(self):
        """Handle when no presence is detected."""
        # Reset presence timer
        if self.presence_start_time is not None:
            self._debug_print("Presence lost - resetting timer")
            self.presence_start_time = None
        
        # Stop attract mode if running, but only if not currently moving
        if self.is_in_attract_mode:
            if self.attract_mode.is_moving:
                self._debug_print("No presence detected but attract mode movement in progress - waiting for completion")
                return
            
            # Check if we're within the buffer time after a movement
            if self._within_attract_movement_buffer():
                self._debug_print("No presence detected but within movement buffer time - waiting")
                return
            
            print("❌ NO PRESENCE - STOPPING ATTRACT MODE")
            self.attract_mode.stop()
            self.is_in_attract_mode = False
            self.last_attract_movement_time = None  # Clear buffer
            self._debug_print("Attract mode stopped")
    
    def _within_attract_movement_buffer(self) -> bool:
        """Check if we're within the buffer time after an attract movement."""
        if self.last_attract_movement_time is None:
            return False
        
        time_since_movement = time.time() - self.last_attract_movement_time
        return time_since_movement < self.ATTRACT_MOVEMENT_BUFFER
    
    def _update_attract_movement_time(self):
        """Update the timestamp of the last attract movement completion."""
        if self.is_in_attract_mode and not self.attract_mode.is_moving:
            # Movement just completed
            current_time = time.time()
            if (self.last_attract_movement_time is None or 
                current_time - self.last_attract_movement_time > 0.5):  # Avoid rapid updates
                self.last_attract_movement_time = current_time
                self._debug_print(f"Attract movement completed, buffer active for {self.ATTRACT_MOVEMENT_BUFFER}s")
    
    def _trigger_message(self):
        """Trigger message spelling sequence."""
        try:
            print("🔮 TRIGGERING MESSAGE SEQUENCE")
            
            # Stop attract mode gracefully
            if self.is_in_attract_mode:
                print("⏹️  STOPPING ATTRACT MODE FOR MESSAGE")
                
                # Wait for current movement to complete naturally
                if self.attract_mode.is_moving:
                    self._debug_print("Waiting for current attract movement to complete...")
                    while self.attract_mode.is_moving and self.attract_mode.is_running:
                        time.sleep(0.1)  # Check every 100ms
                    self._debug_print("Current attract movement completed")
                
                # Now stop attract mode
                self.attract_mode.stop()
                self.is_in_attract_mode = False
                self.last_attract_movement_time = None  # Clear buffer
                self._debug_print("Attract mode stopped for message sequence")
                
                # Add dramatic pause after attract mode ends (creates anticipation before spelling)
                print("⏸️  PAUSING AFTER ATTRACT MODE")
                dramatic_pause_time = self.DRAMATIC_PAUSE_TIME  # Long pause for dramatic effect
                self._debug_print(f"Pausing {dramatic_pause_time}s for dramatic effect and hardware settling")
                time.sleep(dramatic_pause_time)
            
            # Select message
            message = self._select_message()
            if not message:
                self.logger.error("No message available to spell")
                return
            
            print(f"📝 SPELLING MESSAGE: '{message}'")
            self._debug_print(f"Selected from {len(self.messages)} total messages, {len(self.recent_messages)} recent")
            
            # Attract mode already ends at home - no need for additional movement
            print("🏠 TAIL AT HOME POSITION")
            self._debug_print("Ready to spell - attract mode ended at (0,0)")
            
            print("✍️  BEGINNING MESSAGE SPELLING")
            self.tail_speller.spell_message(message)
            
            # Add to recent messages for anti-repetition
            self.recent_messages.append(message)
            self._debug_print(f"Added '{message}' to recent messages ({len(self.recent_messages)}/{self.ANTI_REPETITION_COUNT})")
            
            # Post-message pause
            print(f"⏱️  MESSAGE COMPLETE - pausing {self.POST_MESSAGE_PAUSE}s")
            time.sleep(self.POST_MESSAGE_PAUSE)
            print("🔄 RESUMING SENSOR MONITORING")
            
        except Exception as e:
            self.logger.error(f"Error during message spelling: {e}")
            # Try to return home on error
            try:
                self.tail_speller.go_home()
            except:
                pass
    
    def _select_message(self) -> Optional[str]:
        """
        Select a random message avoiding recent repetitions.
        
        Returns:
            Selected message string, or None if no messages available
        """
        if not self.messages:
            return None
        
        # Filter out recently used messages
        available_messages = [
            msg for msg in self.messages 
            if msg not in self.recent_messages
        ]
        
        # If all messages were recent, use full list (reset anti-repetition)
        if not available_messages:
            available_messages = self.messages
            self.recent_messages.clear()
            print("Anti-repetition reset - all messages available again")
        
        # Select random message
        return random.choice(available_messages)
    
    def _cleanup(self):
        """Cleanup all components."""
        # Disconnect FluidNC
        if self.tail_speller:
            try:
                self.tail_speller.disconnect()
            except Exception as e:
                self.logger.error(f"Error disconnecting FluidNC: {e}")
        
        # Cleanup sensor
        if self.sensor:
            try:
                self.sensor.cleanup()
            except Exception as e:
                self.logger.error(f"Error cleaning up sensor: {e}")
    
    def __del__(self):
        """Destructor - ensure cleanup."""
        self._cleanup()


def main():
    """Main function for running the Cat Butt Oracle."""
    oracle = CatButtOracle()
    
    try:
        if oracle.start():
            print("\nCat Butt Oracle is running...")
            print("Press Ctrl+C to stop")
            
            # Keep main thread alive
            while oracle.is_running:
                time.sleep(1)
        else:
            print("Failed to start Cat Butt Oracle")
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        oracle.logger.error(f"Unexpected error: {e}")
        print(f"Error: {e}")
    finally:
        oracle.stop()


if __name__ == "__main__":
    main()
