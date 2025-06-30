#!/usr/bin/env python3
"""
Ouija Letter Repeatability Test Tool

Tests the repeatability of letter positioning by moving the tail to a specific
letter's coordinates and performing a double-tap sequence.

Interactive mode for testing letter positioning.

Usage: python test_ouija_letters.py
"""

import json
import sys
import time
import argparse
from smooth_tail_puppeteer import SmoothTailPuppeteer

# Configuration constants
MOVE_SPEED = 600        # mm/min for G1 commands
MOVE_DELAY = 0.50        # seconds before first Y0 move
TAP_DELAY = 0.5         # seconds between first Y0 and Y3
Y_RAISED = 7.0          # mm - raised position
Y_TOUCH = 0.0           # mm - touch position
CALIBRATION_FILE = "ouija_letter_positions.json"


class OuijaLetterTester:
    """Test tool for ouija letter positioning repeatability."""
    
    def __init__(self, port: str = None, baudrate: int = 115200):
        """Initialize the test tool."""
        self.puppeteer = SmoothTailPuppeteer(port=port, baudrate=baudrate)
        self.letter_positions = {}
        
    def load_calibration_data(self):
        """Load letter positions from calibration file."""
        try:
            with open(CALIBRATION_FILE, 'r') as f:
                data = json.load(f)
                self.letter_positions = data.get('letters', {})
                print(f"Loaded calibration data with {len(self.letter_positions)} letters")
                return True
        except FileNotFoundError:
            print(f"Error: Calibration file '{CALIBRATION_FILE}' not found.")
            print("Please run the calibration tool first to create letter positions.")
            return False
        except Exception as e:
            print(f"Error loading calibration file: {e}")
            return False
            
    def connect(self):
        """Connect to the controller."""
        if not self.puppeteer.connect():
            print("Error: Failed to connect to FluidNC controller!")
            return False
        print("Connected to controller")
        return True
        
    def disconnect(self):
        """Disconnect from the controller."""
        self.puppeteer.disconnect()
        
    def test_letter(self, letter: str):
        """Test a specific letter's positioning."""
        # Convert to uppercase for consistency
        letter = letter.upper()
        
        # Check if letter was calibrated
        if letter not in self.letter_positions:
            print(f"Error: Letter '{letter}' was not calibrated.")
            return False
            
        # Get letter coordinates
        letter_pos = self.letter_positions[letter]
        
        # Handle both old format (just X) and new format (X,Y object)
        if isinstance(letter_pos, dict):
            letter_x = letter_pos['x']
            letter_y = letter_pos['y']
        else:
            # Old format - just X coordinate
            letter_x = letter_pos
            letter_y = Y_TOUCH
            
        print(f"Moving to letter {letter} at x:{letter_x:.2f}, y:{letter_y:.2f}")
        
        try:
            # Execute the 4-move sequence
            self._execute_letter_sequence(letter_x, letter_y)
            print(f"Letter {letter} positioning completed")
            return True
            
        except Exception as e:
            print(f"Error during letter test: {e}")
            return False
            
    def _execute_letter_sequence(self, x_pos: float, y_pos: float):
        """Execute the positioning sequence for a letter."""
        # Move 1: Go to letter X position at raised height
        command1 = f"G1F{MOVE_SPEED}X{x_pos:.2f}Y{Y_RAISED:.1f}"
        self._send_command(command1)
        
        # Wait before lowering to letter position
        print(f"Waiting {MOVE_DELAY} seconds...")
        time.sleep(MOVE_DELAY)
        
        # Move 2: Lower to calibrated letter position
        command2 = f"G1F{MOVE_SPEED}X{x_pos:.2f}Y{y_pos:.2f}"
        self._send_command(command2)
        
    def _send_command(self, command: str):
        """Send a G-code command to the controller."""
        if hasattr(self.puppeteer, 'streamer') and hasattr(self.puppeteer.streamer, 'send_command'):
            try:
                self.puppeteer.streamer.send_command(command, wait_for_ok=True)
            except Exception as e:
                print(f"Error sending command '{command}': {e}")
                raise
        else:
            print("Error: Controller not available")
            raise RuntimeError("Controller not available")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Interactive ouija letter positioning test")
    parser.add_argument("-p", "--port", help="Serial port (auto-detect if not specified)")
    parser.add_argument("-b", "--baudrate", type=int, default=115200, help="Baudrate (default: 115200)")
    
    args = parser.parse_args()
        
    tester = OuijaLetterTester(port=args.port, baudrate=args.baudrate)
    
    # Load calibration data
    if not tester.load_calibration_data():
        return 1
        
    # Connect to controller
    if not tester.connect():
        return 1
        
    print("Ouija Letter Tester - Interactive Mode")
    
    try:
        # Interactive loop
        while True:
            try:
                user_input = input("Enter letter (or 'exit' to quit): ").strip()
                
                if user_input.lower() == 'exit':
                    print("Goodbye!")
                    break
                    
                if len(user_input) != 1 or not user_input.isalpha():
                    print("Please enter a single letter (A-Z)")
                    continue
                    
                tester.test_letter(user_input)
                
            except EOFError:
                print("\nGoodbye!")
                break
                
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1
    finally:
        tester.disconnect()
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
