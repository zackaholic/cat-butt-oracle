#!/usr/bin/env python3
"""
FluidNC Test Script

A simple script to test the FluidNC module by sending commands from the command line.
Supports both the basic and advanced streaming modes.

Usage:
  ./test_fluidnc.py [options] [command]
  
Options:
  -h, --help            Show this help message
  -p, --port PORT       Specify serial port (default: auto-detect)
  -b, --baud RATE       Specify baud rate (default: 115200)
  -a, --advanced        Use advanced streaming mode
  -s, --status          Show status after command
  -f, --file FILE       Stream G-code from file
  
Examples:
  ./test_fluidnc.py "$H"                   # Home command
  ./test_fluidnc.py -s "G0 X10 Y10 F1000"  # Move and show status
  ./test_fluidnc.py -f path/to/gcode.nc    # Stream a G-code file
  ./test_fluidnc.py -a -f path/to/gcode.nc # Stream with advanced buffer management
"""

import sys
import argparse
import time

from fluidnc import FluidNCStreamer
from fluidnc.advanced_streamer import AdvancedFluidNCStreamer


def print_status(status):
    """Print status information in a formatted way."""
    print("\nStatus:")
    print(f"  Mode: {status.mode}")
    print(f"  Position (work): X={status.work_position['x']:.3f}, "
          f"Y={status.work_position['y']:.3f}, "
          f"Z={status.work_position['z']:.3f}")
    if status.machine_position:
        print(f"  Position (machine): X={status.machine_position['x']:.3f}, "
              f"Y={status.machine_position['y']:.3f}, "
              f"Z={status.machine_position['z']:.3f}")
    if status.feed_rate:
        print(f"  Feed: {status.feed_rate} mm/min")
    if status.buffer_status:
        print(f"  Buffer: Planner={status.buffer_status.get('planner', 'N/A')}, "
              f"RX={status.buffer_status.get('rx', 'N/A')}")


def progress_callback(lines_complete, total_lines):
    """Display streaming progress."""
    if total_lines > 0:
        percent = int(100 * lines_complete / total_lines)
        sys.stdout.write(f"\rStreaming: {lines_complete}/{total_lines} lines ({percent}%)")
        sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(description="Test FluidNC module by sending commands")
    parser.add_argument("-p", "--port", help="Serial port (default: auto-detect)")
    parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate (default: 115200)")
    parser.add_argument("-a", "--advanced", action="store_true", help="Use advanced streaming mode")
    parser.add_argument("-s", "--status", action="store_true", help="Show status after command")
    parser.add_argument("-f", "--file", help="Stream G-code from file")
    parser.add_argument("command", nargs="?", help="Command to send to FluidNC controller")
    
    args = parser.parse_args()
    
    if not args.command and not args.file:
        parser.print_help()
        return
    
    # Create the appropriate streamer
    if args.advanced:
        print("Using advanced streaming mode")
        streamer = AdvancedFluidNCStreamer(port=args.port, baudrate=args.baud)
    else:
        print("Using standard streaming mode")
        streamer = FluidNCStreamer(port=args.port, baudrate=args.baud)
    
    # Connect to the controller
    print("Connecting to FluidNC controller...")
    if not streamer.connect():
        print("Failed to connect to FluidNC controller!")
        return
    
    print(f"Connected to FluidNC controller on port {streamer._connection.port}")
    
    try:
        # Stream a file if specified
        if args.file:
            print(f"Streaming file: {args.file}")
            try:
                streamer.stream_gcode_file(args.file, progress_callback=progress_callback)
                print("\nFile streaming complete")
            except Exception as e:
                print(f"\nError streaming file: {e}")
        
        # Send a command if specified
        elif args.command:
            print(f"Sending command: {args.command}")
            response = streamer.send_command(args.command)
            print(f"Response: {response}")
        
        # Show status if requested
        if args.status:
            time.sleep(0.5)  # Brief delay to allow status to update
            status = streamer.get_status()
            print_status(status)
    
    finally:
        # Always disconnect cleanly
        print("Disconnecting...")
        streamer.disconnect()
        print("Done")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        print(f"Error: {str(e)}")