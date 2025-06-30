#!/usr/bin/env python3
"""
Simple test script for the FluidNC module.
This script connects to a FluidNC controller, gets status, and sends basic commands.
"""

import time
import sys
import os

# Add the parent directory to the path so we can import the fluidnc module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fluidnc import FluidNCStreamer


def print_status(status):
    """Print status information in a formatted way."""
    print(f"Status: {status.mode}")
    print(f"Position (work): X={status.work_position['x']:.3f}, "
          f"Y={status.work_position['y']:.3f}, "
          f"Z={status.work_position['z']:.3f}")
    if status.feed_rate:
        print(f"Feed: {status.feed_rate} mm/min")
    if status.buffer_status:
        print(f"Buffer: Planner={status.buffer_status['planner']}, "
              f"RX={status.buffer_status['rx']}")
    print("-" * 40)


def status_callback(status):
    """Callback function for status updates."""
    print_status(status)


def main():
    """Main function to test FluidNC connection and basic operations."""
    print("FluidNC Simple Test")
    print("-" * 40)
    
    # Create a streamer instance with auto-detection
    streamer = FluidNCStreamer(auto_detect=True)
    
    print("Connecting to FluidNC controller...")
    if not streamer.connect():
        print("Failed to connect to FluidNC controller!")
        return
        
    print("Connected!")
    print("-" * 40)
    
    # Get initial status
    print("Getting initial status:")
    status = streamer.get_status()
    print_status(status)
    
    # Send a few basic commands
    print("Sending version command...")
    response = streamer.send_command("$I")
    print(response)
    print("-" * 40)
    
    # Enable status monitoring temporarily
    print("Enabling status monitoring for 5 seconds...")
    streamer.enable_status_monitoring(callback=None)  # No callback for cleaner output
    
    # Get a few status updates
    for _ in range(5):
        status = streamer.get_latest_status()
        if status:
            print_status(status)
        time.sleep(1)
        
    # Disable status monitoring
    print("Disabling status monitoring...")
    streamer.disable_status_monitoring()
    
    # Test jog command (only if not in alarm state)
    if status and status.mode != "Alarm":
        print("Jogging X axis by 1mm...")
        streamer.jog('X', 1, 500)
        time.sleep(1)  # Wait for movement to complete
        
        print("Getting status after jog:")
        status = streamer.get_status()
        print_status(status)
        
        # Return to previous position
        print("Jogging back...")
        streamer.jog('X', -1, 500)
        time.sleep(1)
    else:
        print("Machine is in Alarm state, skipping jog test")
    
    # Disconnect
    print("Disconnecting...")
    streamer.disconnect()
    print("Test complete!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error: {str(e)}")