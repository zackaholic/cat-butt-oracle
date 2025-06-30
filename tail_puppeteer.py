#!/usr/bin/env python3
"""
Real-Time Cat Tail Puppeteering Interface

Ultra-responsive mouse-controlled puppeteering for the mechanical cat tail.
Maps mouse position to tail coordinates with real-time G-code streaming.

Controls:
- Mouse movement: Control tail position
- ESC: Exit
- SPACE: Center tail position
- R: Reset/home axes

Coordinate Mapping:
- Mouse X (screen width) → Tail X (-10 to 10)
- Mouse Y (screen height) → Tail Y (0 to 10, inverted)
"""

import pygame
import threading
import time
import queue
import sys
from typing import Tuple, Optional

from fluidnc.connection import FluidNCConnection


class TailPuppeteer:
    """Real-time cat tail puppeteering interface."""
    
    def __init__(self, port: str = None, baudrate: int = 115200):
        """Initialize the puppeteer interface."""
        # Connection setup
        self.connection = FluidNCConnection(port=port, baudrate=baudrate)
        self.connected = False
        
        # Coordinate ranges
        self.x_range = (-20.0, 20.0)  # Tail X range
        self.y_range = (0.0, 20.0)    # Tail Y range (positive only)
        
        # Threading and communication
        self.running = False
        self.command_queue = queue.Queue(maxsize=10)  # Small queue for latest commands
        self.comm_thread = None
        
        # Position tracking
        self.current_position = [0.0, 0.0]  # [X, Y]
        self.target_position = [0.0, 0.0]   # [X, Y]
        self.last_sent_position = [None, None]
        
        # Rate limiting
        self.update_rate = 60  # Hz
        self.min_movement = 0.05  # Minimum movement to send command
        
        # Pygame setup
        self.screen_size = (800, 600)
        self.screen = None
        self.clock = None
        self.font = None
        
    def connect(self) -> bool:
        """Connect to the FluidNC controller."""
        try:
            print("Connecting to FluidNC controller...")
            self.connection.open()
            
            # Initialize controller state
            print("Initializing controller...")
            self.connection.write("G90")  # Absolute positioning
            time.sleep(0.1)
            self.connection.write("G0 X0 Y0")  # Go to origin
            time.sleep(0.1)
            
            self.connected = True
            print(f"Connected to FluidNC controller on port {self.connection.port}")
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from the controller."""
        self.running = False
        
        if self.comm_thread and self.comm_thread.is_alive():
            self.comm_thread.join(timeout=2)
            
        if self.connected:
            try:
                # Return to origin on exit
                self.connection.write("G0 X0 Y0")
                time.sleep(0.5)
            except:
                pass
            
            self.connection.close()
            self.connected = False
            print("Disconnected from controller")
    
    def map_mouse_to_tail(self, mouse_pos: Tuple[int, int]) -> Tuple[float, float]:
        """
        Map mouse coordinates to tail coordinates.
        
        Args:
            mouse_pos: (x, y) mouse position in screen coordinates
            
        Returns:
            (x, y) tail position in mechanical coordinates
        """
        mouse_x, mouse_y = mouse_pos
        screen_w, screen_h = self.screen_size
        
        # Map X: 0 to screen_w → -5 to 5
        tail_x = (mouse_x / screen_w) * (self.x_range[1] - self.x_range[0]) + self.x_range[0]
        
        # Map Y: Y=0 is at 1/3 from bottom of screen
        # Bottom 1/3 of screen → negative Y values (below zero)
        # Top 2/3 of screen → positive Y values (above zero)
        zero_y_screen = screen_h * (2.0/3.0)  # Y=0 position on screen
        
        # Convert mouse Y to relative position from zero line
        y_from_zero = (zero_y_screen - mouse_y) / (screen_h / 3.0)  # Normalize to thirds
        
        # Scale to tail Y range
        tail_y = y_from_zero * (self.y_range[1] / 2.0)  # Use half range as scale factor
        
        # Clamp to valid ranges
        tail_x = max(self.x_range[0], min(self.x_range[1], tail_x))
        tail_y = max(self.y_range[0], min(self.y_range[1], tail_y))
        
        return round(tail_x, 2), round(tail_y, 2)
    
    def should_send_command(self, new_pos: Tuple[float, float]) -> bool:
        """Check if we should send a new position command."""
        if self.last_sent_position[0] is None:
            return True
            
        # Check if movement is significant enough
        dx = abs(new_pos[0] - self.last_sent_position[0])
        dy = abs(new_pos[1] - self.last_sent_position[1])
        
        return dx >= self.min_movement or dy >= self.min_movement
    
    def communication_loop(self):
        """Background thread for handling FluidNC communication."""
        last_update = time.time()
        update_interval = 1.0 / self.update_rate
        
        while self.running and self.connected:
            try:
                current_time = time.time()
                
                # Rate limiting
                if current_time - last_update < update_interval:
                    time.sleep(0.001)
                    continue
                
                # Get latest position from queue (non-blocking)
                try:
                    while True:
                        new_position = self.command_queue.get_nowait()
                        self.target_position = new_position
                except queue.Empty:
                    pass
                
                # Send command if position changed significantly
                if self.should_send_command(self.target_position):
                    command = f"G0 X{self.target_position[0]} Y{self.target_position[1]}"
                    
                    try:
                        # Send without waiting for ok (for real-time feel)
                        self.connection.write(command)
                        self.last_sent_position = list(self.target_position)
                        self.current_position = list(self.target_position)
                        
                    except Exception as e:
                        print(f"Communication error: {e}")
                        break
                
                last_update = current_time
                
            except Exception as e:
                print(f"Communication loop error: {e}")
                break
    
    def init_pygame(self):
        """Initialize pygame interface."""
        pygame.init()
        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("Cat Tail Puppeteer - Move mouse to control tail")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        
        # Hide mouse cursor and center it
        pygame.mouse.set_visible(False)
        center_x, center_y = self.screen_size[0] // 2, self.screen_size[1] // 2
        pygame.mouse.set_pos(center_x, center_y)
    
    def draw_interface(self, mouse_pos: Tuple[int, int]):
        """Draw the puppeteer interface."""
        # Clear screen
        self.screen.fill((20, 20, 40))
        
        # Calculate tail coordinates
        tail_x, tail_y = self.map_mouse_to_tail(mouse_pos)
        
        # Draw coordinate system
        center_x = self.screen_size[0] // 2
        zero_y = int(self.screen_size[1] * (2.0/3.0))  # Y=0 line at 2/3 down from top
        
        # Draw axes - horizontal line at Y=0, vertical line at center
        pygame.draw.line(self.screen, (60, 60, 60), 
                        (50, zero_y), (self.screen_size[0] - 50, zero_y), 2)
        pygame.draw.line(self.screen, (60, 60, 60), 
                        (center_x, 50), (center_x, self.screen_size[1] - 50), 2)
        
        # Draw tail position indicator
        tail_screen_x = int((tail_x - self.x_range[0]) / (self.x_range[1] - self.x_range[0]) * self.screen_size[0])
        # Map tail Y to screen coordinates relative to zero line
        tail_screen_y = int(zero_y - (tail_y / self.y_range[1]) * (self.screen_size[1] / 3.0) * 2)
        
        pygame.draw.circle(self.screen, (255, 100, 100), 
                          (tail_screen_x, tail_screen_y), 8)
        
        # Draw mouse cursor
        pygame.draw.circle(self.screen, (100, 255, 100), mouse_pos, 5)
        pygame.draw.circle(self.screen, (255, 255, 255), mouse_pos, 5, 2)
        
        # Draw text info
        info_lines = [
            f"Tail Position: X={tail_x:+6.2f}, Y={tail_y:+6.2f}",
            f"Mouse: {mouse_pos[0]:3d}, {mouse_pos[1]:3d}",
            f"Range: X({self.x_range[0]:+.0f} to {self.x_range[1]:+.0f}), Y({self.y_range[0]:.0f} to {self.y_range[1]:.0f})",
            "",
            "Controls:",
            "  Move mouse: Control tail",
            "  SPACE: Center tail",
            "  R: Reset/home",
            "  ESC: Exit"
        ]
        
        y_offset = 10
        for line in info_lines:
            color = (255, 255, 255) if line else (150, 150, 150)
            text = self.font.render(line, True, color)
            self.screen.blit(text, (10, y_offset))
            y_offset += 25
        
        # Connection status
        status_color = (100, 255, 100) if self.connected else (255, 100, 100)
        status_text = "CONNECTED" if self.connected else "DISCONNECTED"
        status_surface = self.font.render(f"Status: {status_text}", True, status_color)
        self.screen.blit(status_surface, (10, self.screen_size[1] - 30))
        
        pygame.display.flip()
    
    def center_tail(self):
        """Move tail to center position."""
        center_pos = (0.0, 5.0)  # Center X, mid Y
        try:
            self.command_queue.put_nowait(center_pos)
        except queue.Full:
            pass
    
    def home_tail(self):
        """Reset/home the tail."""
        try:
            # Send home command directly
            self.connection.write("$H")
            time.sleep(1)
            # Return to origin
            origin_pos = (0.0, 0.0)
            self.command_queue.put_nowait(origin_pos)
        except Exception as e:
            print(f"Homing error: {e}")
    
    def run(self):
        """Run the puppeteering interface."""
        if not self.connect():
            return False
            
        self.init_pygame()
        self.running = True
        
        # Start communication thread
        self.comm_thread = threading.Thread(target=self.communication_loop, daemon=True)
        self.comm_thread.start()
        
        try:
            while self.running:
                # Handle pygame events
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        self.running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            self.running = False
                        elif event.key == pygame.K_SPACE:
                            self.center_tail()
                        elif event.key == pygame.K_r:
                            self.home_tail()
                
                # Get mouse position and update tail
                mouse_pos = pygame.mouse.get_pos()
                tail_pos = self.map_mouse_to_tail(mouse_pos)
                
                # Queue the new position (replace old ones)
                try:
                    # Clear queue and add latest position
                    while not self.command_queue.empty():
                        try:
                            self.command_queue.get_nowait()
                        except queue.Empty:
                            break
                    
                    self.command_queue.put_nowait(tail_pos)
                except queue.Full:
                    pass  # Queue full, skip this update
                
                # Draw interface
                self.draw_interface(mouse_pos)
                
                # Maintain frame rate
                self.clock.tick(60)
                
        except KeyboardInterrupt:
            print("\nShutdown requested...")
        
        finally:
            self.disconnect()
            pygame.quit()
        
        return True


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Real-time cat tail puppeteering interface")
    parser.add_argument("-p", "--port", help="Serial port (default: auto-detect)")
    parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate")
    
    args = parser.parse_args()
    
    puppeteer = TailPuppeteer(port=args.port, baudrate=args.baud)
    
    print("=== Cat Tail Puppeteer ===")
    print("Starting real-time puppeteering interface...")
    print("Controls:")
    print("  Move mouse: Control tail position") 
    print("  SPACE: Center tail")
    print("  R: Reset/home axes")
    print("  ESC: Exit")
    print()
    
    success = puppeteer.run()
    
    if success:
        print("Puppeteering session completed successfully")
    else:
        print("Failed to start puppeteering session")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())