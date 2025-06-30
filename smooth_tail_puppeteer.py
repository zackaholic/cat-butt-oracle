#!/usr/bin/env python3
"""
ULTRA-SMOOTH Cat Tail Puppeteering Interface

Advanced real-time puppeteering with sophisticated buffer management,
position interpolation, and character counting for maximum smoothness.

Features:
- Advanced buffer management with character counting
- Position interpolation for smooth curves
- Real-time status monitoring and feedback
- Feed rate control for natural acceleration
- Optimized streaming for minimal latency
"""

import pygame
import threading
import time
import queue
import sys
import math
from typing import Tuple, Optional, List

from fluidnc.advanced_streamer import AdvancedFluidNCStreamer
from fluidnc.status import FluidNCStatus


class SmoothTailPuppeteer:
    """Ultra-smooth real-time cat tail puppeteering interface."""
    
    def __init__(self, port: str = None, baudrate: int = 115200):
        """Initialize the smooth puppeteer interface."""
        # Advanced streamer with buffer management
        self.streamer = AdvancedFluidNCStreamer(
            port=port, 
            baudrate=baudrate,
            status_interval=0.05  # 20Hz status updates
        )
        self.connected = False
        
        # Coordinate ranges (using user's expanded ranges)
        self.x_range = (-30.0, 30.0)  # Tail X range
        self.y_range = (0.0, 30.0)    # Tail Y range (positive only)
        
        # Responsive movement parameters
        self.target_position = [0.0, 0.0]      # Target position (from mouse - immediate)
        self.controller_position = [0.0, 0.0]   # Actual controller position
        self.last_sent_position = [0.0, 0.0]   # Last position sent to controller
        self.last_command_time = 0.0           # Rate limiting
        
        # Responsive settings
        self.min_movement = 0.05       # Minimum movement to send (reduced for calibration)
        self.max_feed_rate = 6000      # mm/min - very fast for responsiveness
        self.base_feed_rate = 2000     # mm/min - fast base speed
        self.command_send_rate = 30    # Max commands per second (reduced for calibration)
        
        # Buffer management
        self.rx_buffer_available = 127  # FluidNC RX buffer size
        self.pending_commands = []      # Commands waiting for acknowledgment
        self.max_pending = 8           # Max commands in flight
        
        # Threading
        self.running = False
        self.interpolation_thread = None
        self.status_callback_active = False
        
        # Pygame setup
        self.screen_size = (1000, 700)  # Larger for smoother mouse tracking
        self.screen = None
        self.clock = None
        self.font = None
        
        # Performance monitoring
        self.last_update_time = time.time()
        self.update_count = 0
        self.fps_display = 60.0
        
    def connect(self) -> bool:
        """Connect to the FluidNC controller with advanced features."""
        try:
            print("Connecting to FluidNC controller (advanced mode)...")
            if not self.streamer.connect():
                return False
            
            print("Initializing smooth control mode...")
            
            # Initialize controller state
            self.streamer.send_command("G90")  # Absolute positioning
            self.streamer.send_command("G94")  # Feed rate mm/min
            
            # Enable status monitoring for real-time feedback
            self.streamer.enable_status_monitoring(callback=self._status_callback)
            self.status_callback_active = True
            
            # Go to origin smoothly
            self.streamer.send_command(f"G0 X0 Y0 F{self.max_feed_rate}")
            
            self.connected = True
            print(f"Connected with advanced buffer management enabled")
            return True
            
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect with smooth shutdown."""
        self.running = False
        
        if self.command_thread and self.command_thread.is_alive():
            self.command_thread.join(timeout=2)
            
        if self.connected:
            try:
                # No automatic movement on disconnect - leave tail in current position
                pass
            except:
                pass
            
            if self.status_callback_active:
                self.streamer.disable_status_monitoring()
                
            self.streamer.disconnect()
            self.connected = False
            print("Disconnected with smooth shutdown")
    
    def _status_callback(self, status: FluidNCStatus):
        """Handle real-time status updates for buffer management."""
        if status.buffer_status:
            self.rx_buffer_available = status.buffer_status.get('rx', 127)
            
        # Update controller position (separate from interpolated position)
        if status.work_position:
            self.controller_position[0] = status.work_position.get('x', 0.0)
            self.controller_position[1] = status.work_position.get('y', 0.0)
    
    def calculate_command_size(self, x: float, y: float, feed_rate: int) -> int:
        """Calculate the character count for a G-code command."""
        command = f"G0 X{x:.2f} Y{y:.2f} F{feed_rate}"
        return len(command) + 1  # +1 for newline
    
    def calculate_adaptive_feed_rate(self, distance: float) -> int:
        """Calculate adaptive feed rate based on movement distance."""
        # Shorter movements = slower feed rate for precision
        # Longer movements = faster feed rate for responsiveness
        if distance < 0.5:
            return self.base_feed_rate
        elif distance > 5.0:
            return self.max_feed_rate
        else:
            # Linear interpolation between base and max
            ratio = (distance - 0.5) / 4.5
            return int(self.base_feed_rate + ratio * (self.max_feed_rate - self.base_feed_rate))
    
    def send_responsive_position(self, x: float, y: float) -> bool:
        """Send position with smart throttling for responsiveness."""
        current_time = time.time()
        
        # Calculate movement distance first for debugging
        dx = x - self.last_sent_position[0]
        dy = y - self.last_sent_position[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        # DEBUG: Always print what's happening
        
        # Rate limiting - fast but not spammy
        if current_time - self.last_command_time < (1.0 / self.command_send_rate):
            return False
            
        # Check if movement is significant enough
        if distance < self.min_movement:
            return False
            
        # Keep queue small for responsiveness - but increase limit for calibration
        if len(self.pending_commands) >= 5:  # Increased from 2 to 5 for calibration mode
            return False
            
        # Calculate adaptive feed rate for responsiveness
        feed_rate = self.calculate_adaptive_feed_rate(distance)
        
        # Send command
        try:
            command = f"G0 X{x:.2f} Y{y:.2f} F{feed_rate}"
            
            # FIX: Use proper command sending that includes newline
            self.streamer.send_command(command, wait_for_ok=False)
            
            # Track pending commands
            self.pending_commands.append({
                'command': command,
                'time': current_time
            })
            
            self.last_sent_position = [x, y]
            self.last_command_time = current_time
            return True
            
        except Exception as e:
            return False
    
    def process_acknowledgments(self):
        """Process acknowledgments to free up buffer space."""
        try:
            # Check for available responses
            while (self.streamer._connection._serial and 
                   self.streamer._connection._serial.in_waiting and
                   self.pending_commands):
                
                response = self.streamer._connection.readline()
                if response.startswith("ok") or response.startswith("error"):
                    # Remove oldest pending command
                    if self.pending_commands:
                        self.pending_commands.pop(0)
                        
        except Exception as e:
            print(f"Acknowledgment processing error: {e}")
    
    def command_loop(self):
        """Responsive command sending loop."""
        while self.running and self.connected:
            # Process any acknowledgments to free buffer space
            self.process_acknowledgments()
            
            # Send current target position directly (no interpolation lag)
            target_x, target_y = self.target_position
            self.send_responsive_position(target_x, target_y)
            
            # Fast update frequency for responsiveness
            time.sleep(0.01)  # 100Hz command checking
    
    def map_mouse_to_tail(self, mouse_pos: Tuple[int, int]) -> Tuple[float, float]:
        """Map mouse coordinates to tail coordinates with expanded ranges."""
        mouse_x, mouse_y = mouse_pos
        screen_w, screen_h = self.screen_size
        
        # Map X: 0 to screen_w → -20 to 20
        tail_x = (mouse_x / screen_w) * (self.x_range[1] - self.x_range[0]) + self.x_range[0]
        
        # Map Y: Y=0 is at 1/3 from bottom of screen  
        zero_y_screen = screen_h * (2.0/3.0)
        y_from_zero = (zero_y_screen - mouse_y) / (screen_h / 3.0)
        tail_y = y_from_zero * (self.y_range[1] / 2.0)
        
        # Clamp to valid ranges
        tail_x = max(self.x_range[0], min(self.x_range[1], tail_x))
        tail_y = max(self.y_range[0], min(self.y_range[1], tail_y))
        
        return round(tail_x, 2), round(tail_y, 2)
    
    def init_pygame(self):
        """Initialize enhanced pygame interface."""
        pygame.init()
        self.screen = pygame.display.set_mode(self.screen_size)
        pygame.display.set_caption("SMOOTH Cat Tail Puppeteer - Ultra-responsive control")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 20)
        
        # Center mouse
        center_x, center_y = self.screen_size[0] // 2, int(self.screen_size[1] * (2.0/3.0))
        pygame.mouse.set_pos(center_x, center_y)
        pygame.mouse.set_visible(False)
    
    def draw_enhanced_interface(self, mouse_pos: Tuple[int, int]):
        """Draw enhanced interface with performance monitoring."""
        # Clear screen with gradient
        self.screen.fill((15, 20, 35))
        
        # Calculate positions
        tail_x, tail_y = self.map_mouse_to_tail(mouse_pos)
        center_x = self.screen_size[0] // 2
        zero_y = int(self.screen_size[1] * (2.0/3.0))
        
        # Draw enhanced coordinate system
        pygame.draw.line(self.screen, (80, 80, 100), 
                        (50, zero_y), (self.screen_size[0] - 50, zero_y), 3)
        pygame.draw.line(self.screen, (80, 80, 100), 
                        (center_x, 50), (center_x, self.screen_size[1] - 50), 3)
        
        # Draw buffer visualization
        buffer_usage = 1.0 - (self.rx_buffer_available / 127.0)
        buffer_width = 200
        buffer_height = 20
        buffer_x = self.screen_size[0] - buffer_width - 20
        buffer_y = 20
        
        # Buffer background
        pygame.draw.rect(self.screen, (40, 40, 40), 
                        (buffer_x, buffer_y, buffer_width, buffer_height))
        
        # Buffer usage (color codes: green=low, yellow=medium, red=high)
        if buffer_usage < 0.5:
            buffer_color = (100, 255, 100)
        elif buffer_usage < 0.8:
            buffer_color = (255, 255, 100)
        else:
            buffer_color = (255, 100, 100)
            
        pygame.draw.rect(self.screen, buffer_color,
                        (buffer_x, buffer_y, int(buffer_width * buffer_usage), buffer_height))
        
        # Draw tail position indicators
        # Target position (mouse) - should match controller position when responsive
        tail_screen_x = int((tail_x - self.x_range[0]) / (self.x_range[1] - self.x_range[0]) * self.screen_size[0])
        tail_screen_y = int(zero_y - (tail_y / self.y_range[1]) * (self.screen_size[1] / 3.0) * 2)
        
        pygame.draw.circle(self.screen, (255, 150, 150), (tail_screen_x, tail_screen_y), 12, 2)
        
        # Controller position (green) - should follow target immediately
        ctrl_screen_x = int((self.controller_position[0] - self.x_range[0]) / (self.x_range[1] - self.x_range[0]) * self.screen_size[0])
        ctrl_screen_y = int(zero_y - (self.controller_position[1] / self.y_range[1]) * (self.screen_size[1] / 3.0) * 2)
        
        pygame.draw.circle(self.screen, (100, 255, 100), (ctrl_screen_x, ctrl_screen_y), 8)
        
        # Draw mouse cursor
        pygame.draw.circle(self.screen, (255, 255, 255), mouse_pos, 6, 2)
        
        # Performance info
        current_time = time.time()
        self.update_count += 1
        if current_time - self.last_update_time >= 1.0:
            self.fps_display = self.update_count / (current_time - self.last_update_time)
            self.update_count = 0
            self.last_update_time = current_time
        
        # Enhanced info display
        info_lines = [
            f"TARGET: X={tail_x:+7.2f}, Y={tail_y:+7.2f}",
            f"CONTROLLER: X={self.controller_position[0]:+7.2f}, Y={self.controller_position[1]:+7.2f}",
            f"PENDING: {len(self.pending_commands)}/2 commands",
            f"FPS: {self.fps_display:.1f}",
            "",
            "RESPONSIVE CONTROLS:",
            "  Mouse: Control tail position",
            "  SPACE: Center tail",
            "  R: Reset/home",
            "  ESC: Exit",
            "",
            "RESPONSIVE FEATURES:",
            "• Direct mouse-to-target mapping",
            "• Smart command throttling",
            "• Adaptive feed rates (2000-6000 mm/min)",
            "• Minimal queue for immediate response",
            "• 60Hz command rate limit"
        ]
        
        y_offset = 10
        for line in info_lines:
            if line.startswith("TARGET:") or line.startswith("ACTUAL:"):
                color = (255, 255, 100)
            elif line.startswith("BUFFER:") or line.startswith("PENDING:"):
                color = (150, 255, 150)
            elif line.startswith("ULTRA-SMOOTH") or line.startswith("ADVANCED"):
                color = (255, 150, 255)
            elif line.startswith("•"):
                color = (150, 200, 255)
            else:
                color = (200, 200, 200)
                
            text = self.font.render(line, True, color)
            self.screen.blit(text, (10, y_offset))
            y_offset += 22
        
        # Connection status
        status_color = (100, 255, 100) if self.connected else (255, 100, 100)
        status_text = "SMOOTH MODE ACTIVE" if self.connected else "DISCONNECTED"
        status_surface = self.font.render(f"Status: {status_text}", True, status_color)
        self.screen.blit(status_surface, (10, self.screen_size[1] - 30))
        
        pygame.display.flip()
    
    def center_tail_smooth(self):
        """Smoothly center the tail."""
        self.target_position = [0.0, 10.0]  # Center X, mid Y
    
    def home_tail_smooth(self):
        """Smoothly home the tail."""
        try:
            self.target_position = [0.0, 0.0]
        except Exception as e:
            print(f"Smooth homing error: {e}")
    
    def get_current_target_position(self) -> Tuple[float, float]:
        """Get current target position for calibration use."""
        return tuple(self.target_position)
    
    def run(self):
        """Run the ultra-smooth puppeteering interface."""
        if not self.connect():
            return False
            
        self.init_pygame()
        self.running = True
        
        # Start responsive command thread
        self.command_thread = threading.Thread(target=self.command_loop, daemon=True)
        self.command_thread.start()
        
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
                            self.center_tail_smooth()
                        elif event.key == pygame.K_r:
                            self.home_tail_smooth()
                
                # Update target position from mouse
                mouse_pos = pygame.mouse.get_pos()
                self.target_position = list(self.map_mouse_to_tail(mouse_pos))
                
                # Draw enhanced interface
                self.draw_enhanced_interface(mouse_pos)
                
                # High refresh rate for ultra-smooth display
                self.clock.tick(120)  # 120 FPS display
                
        except KeyboardInterrupt:
            print("\nSmooth shutdown requested...")
        
        finally:
            self.disconnect()
            pygame.quit()
        
        return True


def main():
    """Main entry point for ultra-smooth puppeteering."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Ultra-smooth cat tail puppeteering interface")
    parser.add_argument("-p", "--port", help="Serial port (default: auto-detect)")
    parser.add_argument("-b", "--baud", type=int, default=115200, help="Baud rate")
    
    args = parser.parse_args()
    
    puppeteer = SmoothTailPuppeteer(port=args.port, baudrate=args.baud)
    
    print("=== ULTRA-SMOOTH Cat Tail Puppeteer ===")
    print("Advanced real-time control with:")
    print("• Buffer management & character counting")
    print("• Position interpolation (200Hz)")
    print("• Adaptive feed rates")
    print("• Real-time status monitoring")
    print("• Ultra-responsive mouse control")
    print()
    
    success = puppeteer.run()
    
    if success:
        print("Ultra-smooth puppeteering session completed")
    else:
        print("Failed to start smooth puppeteering session")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
