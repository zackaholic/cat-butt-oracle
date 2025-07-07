#!/usr/bin/env python3
"""
Ouija Board Letter Calibration Tool

Interactive calibration system for mapping letter positions on the ouija board.
Letters are arranged in a circle with a constant Y position and unique X positions.

Usage: python calibrate_ouija_letters.py [-p PORT] [-b BAUDRATE]
"""

import pygame
import json
import sys
import argparse
from typing import Dict, Optional
from smooth_tail_puppeteer import SmoothTailPuppeteer

# Configuration: Movement increments and speed
COARSE_INCREMENT = 1.0  # mm for comma/period keys
FINE_INCREMENT = 0.1    # mm for left/right arrow keys
Y_INCREMENT = 3.0       # mm for up/down arrow keys
MOVE_SPEED = 400        # mm/min for G1 commands
Y_POSITION = 0.0        # mm - constant Y position for all letters


class OuijaLetterCalibrator:
    """Interactive calibration tool for ouija board letter positions."""
    
    # Standard ouija board letters in typical order
    LETTERS = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L', 'M',
        'N', 'O', 'P', 'R', 'S', 'T', 'U', 'V', 'W', 'Y'
    ]
    
    def __init__(self, port: str = None, baudrate: int = 115200):
        """Initialize the calibration tool."""
        self.puppeteer = SmoothTailPuppeteer(port=port, baudrate=baudrate)
        self.current_y = Y_POSITION  # Use constant Y position
        self.current_x = 0.0  # Track X position separately
        self.letter_positions = {}
        self.current_letter_index = 0
        self.calibration_complete = False
        
    def start_calibration(self):
        """Start the interactive calibration process."""
        print("=" * 60)
        print("OUIJA BOARD LETTER CALIBRATION TOOL")
        print("=" * 60)
        print()
        print("Letters arranged in circle around tail base")
        print("Y position will be constant for all letters")
        print("X positions will be unique for each letter")
        print()
        print("Controls:")
        print("- Comma/Period: Coarse X adjustment (±1mm)")
        print("- Left/Right arrows: Fine X adjustment (±0.1mm)")
        print("- Up/Down arrows: Y adjustment (±2mm)")
        print("- SPACE: Confirm current position")
        print("- ESC: Save progress and exit")
        print("- Ctrl+C: Emergency exit")
        print(f"- Y position fixed at: {Y_POSITION}mm")
        print()
        
        # Connect to controller
        if not self.puppeteer.connect():
            print("Failed to connect to FluidNC controller!")
            return False
            
        # Initialize pygame and start command thread manually
        pygame.init()
        
        # Set up pygame screen (similar to SmoothTailPuppeteer.run())
        self.puppeteer.pygame_screen = pygame.display.set_mode((800, 600))
        pygame.display.set_caption("Ouija Letter Calibration")
        self.puppeteer.clock = pygame.time.Clock()
        
        # Initialize font for position display
        pygame.font.init()
        self.font = pygame.font.Font(None, 48)
        self.small_font = pygame.font.Font(None, 32)
        
        # Initialize threading components
        import threading
        import queue
        self.puppeteer.command_queue = queue.Queue()
        
        # Set running flag to enable command loop
        self.puppeteer.running = True
        
        # Simple setup - no complex debugging needed
        
        # Start the command thread
        self.puppeteer.command_thread = threading.Thread(
            target=self.puppeteer.command_loop,
            daemon=True
        )
        self.puppeteer.command_thread.start()
        
        # Initialize target position
        self.puppeteer.target_position = [0.0, 0.0]
        
        try:
            # Calibrate letter X positions (Y is constant)
            self._calibrate_letter_positions()
            
        except KeyboardInterrupt:
            print("\n\nCalibration interrupted by user")
            self._save_progress()
        finally:
            self.puppeteer.disconnect()
            pygame.quit()
            
        return True
        
            
    def _calibrate_letter_positions(self):
        """Calibrate X positions for each letter."""
        print("\nOUIJA LETTER CALIBRATION")
        print("Comma/Period: ±1mm X | Arrows: ±0.1mm X, ±2mm Y | SPACE: Save | ESC: Exit")
        print("-" * 60)
        
        while self.current_letter_index < len(self.LETTERS):
            letter = self.LETTERS[self.current_letter_index]
            
            print(f"\n=== Letter '{letter}' ({self.current_letter_index + 1}/{len(self.LETTERS)}) ===\nPosition tail and press SPACE to save")
            
            while True:
                # Handle pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self._save_progress()
                        return
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_SPACE:
                            # Confirm letter position
                            self.letter_positions[letter] = {
                                "x": self.current_x,
                                "y": self.current_y
                            }
                            print(f"\n'{letter}' saved at X={self.current_x:.2f}, Y={self.current_y:.2f}")
                            self.current_letter_index += 1
                            break
                        elif event.key == pygame.K_ESCAPE:
                            self._save_progress()
                            return
                        # X position keyboard controls
                        elif event.key == pygame.K_COMMA:
                            self.current_x -= COARSE_INCREMENT
                            self._send_direct_move_command()
                        elif event.key == pygame.K_PERIOD:
                            self.current_x += COARSE_INCREMENT
                            self._send_direct_move_command()
                        elif event.key == pygame.K_LEFT:
                            self.current_x -= FINE_INCREMENT
                            self._send_direct_move_command()
                        elif event.key == pygame.K_RIGHT:
                            self.current_x += FINE_INCREMENT
                            self._send_direct_move_command()
                        elif event.key == pygame.K_UP:
                            self.current_y += FINE_INCREMENT
                            self._send_direct_move_command()
                        elif event.key == pygame.K_DOWN:
                            self.current_y -= FINE_INCREMENT
                            self._send_direct_move_command()
                        elif event.key == pygame.K_QUOTE:  # ' key for Y up coarse
                            self.current_y += COARSE_INCREMENT
                            self._send_direct_move_command()
                        elif event.key == pygame.K_SLASH:  # / key for Y down coarse
                            self.current_y -= COARSE_INCREMENT
                            self._send_direct_move_command()
                            
                # Update pygame display with position info
                self._update_display()
                
                # Update pygame display with position info
                self._update_display()
                
                # Break inner loop when letter is confirmed
                if self.current_letter_index > len(self.LETTERS) - 1 or \
                   (self.current_letter_index < len(self.LETTERS) and 
                    self.LETTERS[self.current_letter_index] != letter):
                    break
        
        # Calibration complete
        print("\n\nCalibration complete!")
        self.calibration_complete = True
        self._save_progress()
        
    def _save_progress(self):
        """Save current calibration progress to file."""
        config = {
            "format_version": "2.0",  # New format with X,Y coordinates
            "letters": self.letter_positions,
            "calibration_complete": self.calibration_complete,
            "total_letters": len(self.LETTERS),
            "calibrated_letters": len(self.letter_positions)
        }
        
        filename = "ouija_letter_positions.json"
        try:
            with open(filename, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"\nProgress saved to {filename}")
            print(f"Calibrated {len(self.letter_positions)}/{len(self.LETTERS)} letters")
            
            if self.calibration_complete:
                print("Calibration is COMPLETE!")
                self._print_summary()
        except Exception as e:
            print(f"Error saving progress: {e}")
            
        
        
    def _send_direct_move_command(self):
        """Send G1 move command directly to controller with speed control."""
        if hasattr(self.puppeteer, 'streamer') and hasattr(self.puppeteer.streamer, 'send_command'):
            command = f"G1F{MOVE_SPEED}X{self.current_x:.2f}Y{self.current_y:.2f}"
            try:
                self.puppeteer.streamer.send_command(command, wait_for_ok=False)
            except Exception as e:
                pass  # Silent failure
            
    def _print_summary(self):
        """Print calibration summary."""
        print("\nCalibration Summary:")
        print(f"Landing Y position: {self.landing_y:.2f}")
        print("Letter positions:")
        for letter in self.LETTERS:
            if letter in self.letter_positions:
                pos = self.letter_positions[letter]
                print(f"  {letter}: X={pos['x']:6.2f}, Y={pos['y']:6.2f}")
        print(f"\nIncrement settings:")
        print(f"  Coarse (comma/period): ±{COARSE_INCREMENT}mm")
        print(f"  Fine (arrows): ±{FINE_INCREMENT}mm")
        
    def _update_display(self):
        """Update pygame window with current position information."""
        if hasattr(self.puppeteer, 'pygame_screen'):
            # Clear screen
            self.puppeteer.pygame_screen.fill((0, 0, 0))  # Black background
            
            # Get current letter info
            if self.current_letter_index < len(self.LETTERS):
                current_letter = self.LETTERS[self.current_letter_index]
                letter_text = f"Letter: {current_letter} ({self.current_letter_index + 1}/{len(self.LETTERS)})"
            else:
                letter_text = "Calibration Complete"
            
            # Render text
            letter_surface = self.small_font.render(letter_text, True, (255, 255, 255))
            pos_text = f"X: {self.current_x:6.2f} mm"
            pos_y_text = f"Y: {self.current_y:6.2f} mm"
            
            pos_surface = self.font.render(pos_text, True, (0, 255, 0))  # Green
            pos_y_surface = self.font.render(pos_y_text, True, (0, 255, 0))  # Green
            
            # Position text on screen
            self.puppeteer.pygame_screen.blit(letter_surface, (20, 20))
            self.puppeteer.pygame_screen.blit(pos_surface, (20, 100))
            self.puppeteer.pygame_screen.blit(pos_y_surface, (20, 150))
            
            # Add controls reminder
            controls_line1 = "X: Comma/Period ±1mm, L/R arrows ±0.1mm"
            controls_line2 = "Y: Quote/Slash ±1mm, U/D arrows ±0.1mm | SPACE: Save"
            controls1_surface = self.small_font.render(controls_line1, True, (128, 128, 128))
            controls2_surface = self.small_font.render(controls_line2, True, (128, 128, 128))
            self.puppeteer.pygame_screen.blit(controls1_surface, (20, 480))
            self.puppeteer.pygame_screen.blit(controls2_surface, (20, 510))
            
            # Update display
            pygame.display.flip()
            self.puppeteer.clock.tick(30)  # 30 FPS
        


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Calibrate ouija board letter positions")
    parser.add_argument("-p", "--port", help="Serial port (auto-detect if not specified)")
    parser.add_argument("-b", "--baudrate", type=int, default=115200, help="Baudrate (default: 115200)")
    
    args = parser.parse_args()
    
    calibrator = OuijaLetterCalibrator(port=args.port, baudrate=args.baudrate)
    
    try:
        success = calibrator.start_calibration()
        if success:
            print("\nCalibration completed successfully!")
        else:
            print("\nCalibration was not completed.")
    except Exception as e:
        print(f"Error during calibration: {e}")
        return 1
        
    return 0


if __name__ == "__main__":
    sys.exit(main())
