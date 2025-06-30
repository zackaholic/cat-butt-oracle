import os
import threading
import time
import queue
from typing import List, Dict, Optional, Callable, Union, Tuple, Iterator

from .connection import FluidNCConnection
from .status import FluidNCStatus
from .exceptions import FluidNCStreamingError


class AdvancedFluidNCStreamer:
    """
    Advanced streaming interface with buffer management for FluidNC controllers.
    
    This class implements a more sophisticated streaming algorithm that tracks
    both the serial RX buffer and the planner buffer to maximize streaming
    efficiency. It's based on GRBL's "aggressive buffering" approach.
    """
    
    # FluidNC/GRBL control characters
    RESET = '\x18'  # Ctrl-X
    FEED_HOLD = '!'
    CYCLE_START = '~'
    STATUS_REPORT = '?'
    
    # FluidNC buffer sizes from FluidNC source code
    # Values from grbl/config.h
    RX_BUFFER_SIZE = 127      # Serial receive buffer size
    PLANNER_BUFFER_SIZE = 32  # Planner buffer size (number of blocks/lines)
    
    def __init__(
        self, 
        port: str = None, 
        baudrate: int = 115200, 
        auto_detect: bool = True,
        status_interval: float = 0.1
    ):
        """
        Initialize an advanced FluidNC streaming interface.
        
        Args:
            port: Serial port path. If None and auto_detect is True, 
                  port detection will be attempted.
            baudrate: Serial baud rate.
            auto_detect: Whether to try auto-detection if port not specified.
            status_interval: Status polling interval in seconds.
        """
        self._connection = FluidNCConnection(
            port=port if not auto_detect or port else None,
            baudrate=baudrate
        )
        
        self._status_interval = status_interval
        self._status_monitor = None
        self._status_queue = queue.Queue()
        self._status_monitoring = False
        self._last_status = None
        
        # Buffer tracking for advanced streaming
        self._rx_buffer_available = self.RX_BUFFER_SIZE
        self._planner_buffer_available = self.PLANNER_BUFFER_SIZE
        self._buffer_monitor = None
        self._buffer_monitoring = False
        
        # Stream control
        self._streaming = False
        self._stream_paused = False
        self._streamer_thread = None
        
    def connect(self) -> bool:
        """
        Connect to the FluidNC controller.
        
        Returns:
            True if connection successful, False otherwise.
        """
        try:
            self._connection.open()
            return True
        except Exception as e:
            print(f"Connection error: {str(e)}")
            return False
            
    def disconnect(self) -> None:
        """Disconnect from the FluidNC controller."""
        self.stop_streaming()
        
        if self._status_monitoring:
            self.disable_status_monitoring()
            
        if self._buffer_monitoring:
            self._buffer_monitoring = False
            if self._buffer_monitor and self._buffer_monitor.is_alive():
                self._buffer_monitor.join(timeout=2)
                
        self._connection.close()
        
    def enable_status_monitoring(self, callback: Optional[Callable[[FluidNCStatus], None]] = None) -> None:
        """
        Enable automatic status monitoring in a background thread.
        
        Args:
            callback: Optional callback function that receives status updates.
        """
        if self._status_monitoring:
            return
            
        self._status_monitoring = True
        
        def monitor_status():
            while self._status_monitoring:
                try:
                    status = self.get_status()
                    self._last_status = status
                    
                    # Track buffer state if available
                    if status.buffer_status:
                        self._rx_buffer_available = status.buffer_status.get('rx', self.RX_BUFFER_SIZE)
                        self._planner_buffer_available = status.buffer_status.get('planner', self.PLANNER_BUFFER_SIZE)
                    
                    if callback:
                        callback(status)
                        
                    # Add to queue for consumers
                    try:
                        self._status_queue.put(status, block=False)
                    except queue.Full:
                        pass
                        
                except Exception as e:
                    print(f"Status monitoring error: {str(e)}")
                    
                time.sleep(self._status_interval)
                
        self._status_monitor = threading.Thread(target=monitor_status, daemon=True)
        self._status_monitor.start()
        
        # Enable automatic status reporting in FluidNC if possible
        try:
            self.send_command("$10=1")  # Enable status reports
        except:
            pass  # Some versions may not support this
            
    def disable_status_monitoring(self) -> None:
        """Disable automatic status monitoring."""
        self._status_monitoring = False
        if self._status_monitor and self._status_monitor.is_alive():
            self._status_monitor.join(timeout=2)
            
        # Disable automatic status reporting
        try:
            self.send_command("$10=0")
        except:
            pass
            
    def get_status(self) -> FluidNCStatus:
        """
        Request and return the current status from FluidNC.
        
        Returns:
            FluidNCStatus object with parsed status information.
        """
        response = self.send_immediate_command(self.STATUS_REPORT)
        return FluidNCStatus.parse(response)
        
    def get_latest_status(self) -> Optional[FluidNCStatus]:
        """
        Get the most recent status update without sending a new request.
        
        Returns:
            The most recent FluidNCStatus or None if no status has been received.
        """
        return self._last_status
        
    def send_immediate_command(self, command: str) -> str:
        """
        Send an immediate command (?, !, ~, etc.) to the FluidNC controller.
        
        Args:
            command: The immediate command character.
            
        Returns:
            Response from the controller (if any).
        """
        self._connection.write(command)
        return self._connection.readline()
        
    def send_command(self, command: str, wait_for_ok: bool = True) -> str:
        """
        Send a command to the FluidNC controller.
        
        Args:
            command: The command to send.
            wait_for_ok: Whether to wait for an "ok" response.
            
        Returns:
            Response from the controller.
        """
        if not command:
            return ""
            
        # Strip whitespace
        command = command.strip()
        
        # For immediate commands, use the dedicated method
        if command in [self.STATUS_REPORT, self.FEED_HOLD, self.CYCLE_START]:
            return self.send_immediate_command(command)
            
        # Send the command
        self._connection.write(command)
        
        # For regular commands, wait for ok if requested
        if wait_for_ok:
            return self._connection.read_until_ok()
        else:
            return ""
            
    def stream_gcode_file(
        self, 
        filepath: str, 
        progress_callback: Optional[Callable[[int, int], None]] = None,
        buffer_mode: bool = True
    ) -> Tuple[int, int]:
        """
        Stream a G-code file to the FluidNC controller.
        
        Args:
            filepath: Path to the G-code file.
            progress_callback: Optional callback function for progress updates.
                              Receives (lines_complete, total_lines).
            buffer_mode: Whether to use advanced buffer management (True) or
                        simple line-by-line streaming (False).
                        
        Returns:
            Tuple of (lines_sent, lines_total).
            
        Raises:
            FileNotFoundError: If the file does not exist.
            RuntimeError: If streaming fails.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"G-code file not found: {filepath}")
            
        # Count total lines for progress reporting
        total_lines = sum(1 for line in open(filepath, 'r') 
                          if line.strip() and not line.strip().startswith(';'))
        
        with open(filepath, 'r') as f:
            if buffer_mode:
                return self._stream_buffered(f, total_lines, progress_callback)
            else:
                return self._stream_line_by_line(f, total_lines, progress_callback)
    
    def stream_gcode_lines(
        self,
        lines: Union[List[str], Iterator[str]],
        total_lines: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None,
        buffer_mode: bool = True
    ) -> Tuple[int, int]:
        """
        Stream G-code lines to the FluidNC controller.
        
        Args:
            lines: List of G-code lines or iterator producing lines.
            total_lines: Total number of lines (optional, for progress reporting).
            progress_callback: Optional callback function for progress updates.
                              Receives (lines_complete, total_lines).
            buffer_mode: Whether to use advanced buffer management (True) or
                        simple line-by-line streaming (False).
                        
        Returns:
            Tuple of (lines_sent, total_lines).
            
        Raises:
            RuntimeError: If streaming fails.
        """
        if total_lines is None and hasattr(lines, '__len__'):
            total_lines = len(lines)
        elif total_lines is None:
            total_lines = 0  # Unknown
            
        if buffer_mode:
            return self._stream_buffered(lines, total_lines, progress_callback)
        else:
            return self._stream_line_by_line(lines, total_lines, progress_callback)
            
    def _stream_line_by_line(
        self,
        lines: Union[List[str], Iterator[str]],
        total_lines: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[int, int]:
        """
        Stream G-code lines one by one, waiting for 'ok' after each line.
        
        Args:
            lines: G-code lines to stream.
            total_lines: Total number of lines for progress reporting.
            progress_callback: Optional progress callback function.
            
        Returns:
            Tuple of (lines_sent, total_lines).
        """
        lines_sent = 0
        
        for line in lines:
            # Skip blank lines and comments
            line = line.strip()
            if not line or line.startswith(';'):
                continue
                
            # Remove inline comments
            line = line.split(';')[0].strip()
            if not line:
                continue
                
            # Send the command and wait for ok
            try:
                self.send_command(line)
                lines_sent += 1
                
                if progress_callback:
                    progress_callback(lines_sent, total_lines)
                    
            except Exception as e:
                raise FluidNCStreamingError(f"Error streaming: {str(e)}", lines_sent)
                
        return lines_sent, total_lines
        
    def _stream_buffered(
        self,
        lines: Union[List[str], Iterator[str]],
        total_lines: int,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[int, int]:
        """
        Stream G-code using buffer management for maximum throughput.
        
        This method aggressively fills the controller's buffers and
        manages acknowledgments to maintain maximum streaming efficiency.
        
        Args:
            lines: G-code lines to stream.
            total_lines: Total number of lines for progress reporting.
            progress_callback: Optional progress callback function.
            
        Returns:
            Tuple of (lines_sent, total_lines).
        """
        if self._streaming:
            raise RuntimeError("Streaming already in progress")
            
        self._streaming = True
        self._stream_paused = False
        
        # Initialize counters and buffers
        lines_sent = 0
        lines_confirmed = 0
        line_queue = []  # Lines waiting to be sent
        
        # Preprocess lines to clean and filter them
        filtered_lines = []
        for line in lines:
            # Skip blank lines and comments
            line = line.strip()
            if not line or line.startswith(';'):
                continue
                
            # Remove inline comments
            line = line.split(';')[0].strip()
            if not line:
                continue
                
            filtered_lines.append(line)
            
        # Enable status monitoring if not already running
        was_monitoring = self._status_monitoring
        if not was_monitoring:
            self.enable_status_monitoring()
            
        # Track command size
        def command_size(cmd):
            # Count the length of the command plus CRLF
            return len(cmd) + 2
            
        try:
            # Start with a clean state - get initial buffer sizes
            status = self.get_status()
            self._rx_buffer_available = self.RX_BUFFER_SIZE
            self._planner_buffer_available = self.PLANNER_BUFFER_SIZE
            
            i = 0
            while (i < len(filtered_lines) or line_queue) and self._streaming:
                # Fill the line queue with as many commands as possible
                while i < len(filtered_lines) and len(line_queue) < self.PLANNER_BUFFER_SIZE:
                    line_queue.append(filtered_lines[i])
                    i += 1
                    
                if not line_queue:
                    break
                    
                # Get current status and buffer availability
                status = self.get_status()
                if status.buffer_status:
                    self._rx_buffer_available = status.buffer_status.get('rx', self.RX_BUFFER_SIZE)
                    self._planner_buffer_available = status.buffer_status.get('planner', self.PLANNER_BUFFER_SIZE)
                    
                # Send as many commands as the buffer allows
                cmd_idx = 0
                while cmd_idx < len(line_queue):
                    cmd = line_queue[cmd_idx]
                    cmd_size = command_size(cmd)
                    
                    if cmd_size <= self._rx_buffer_available and self._planner_buffer_available > 0:
                        # Send without waiting for ok
                        self._connection.write(cmd)
                        
                        # Update buffer tracking
                        self._rx_buffer_available -= cmd_size
                        self._planner_buffer_available -= 1
                        
                        # Remove from queue and update counters
                        line_queue.pop(cmd_idx)
                        lines_sent += 1
                        
                        if progress_callback:
                            progress_callback(lines_sent, total_lines)
                    else:
                        # Buffer full, need to wait for acknowledgment
                        break
                        
                # Read any available responses to free up buffer space
                while self._connection._serial and self._connection._serial.in_waiting:
                    response = self._connection.readline()
                    if response.startswith("ok"):
                        lines_confirmed += 1
                        # Each ok frees up a planning buffer slot
                        self._planner_buffer_available += 1
                        
                # If we couldn't send any commands, wait for buffer space
                if cmd_idx == 0 and line_queue:
                    time.sleep(0.01)
                    
            # Wait for all commands to be confirmed
            while lines_confirmed < lines_sent and self._streaming:
                response = self._connection.readline()
                if response.startswith("ok"):
                    lines_confirmed += 1
                    
                time.sleep(0.01)
                
        except Exception as e:
            raise FluidNCStreamingError(f"Error in buffered streaming: {str(e)}", lines_sent)
            
        finally:
            self._streaming = False
            
            # Disable status monitoring if we enabled it
            if not was_monitoring:
                self.disable_status_monitoring()
                
        return lines_sent, total_lines
        
    def stop_streaming(self) -> None:
        """Stop any active streaming operation."""
        self._streaming = False
        if self._streamer_thread and self._streamer_thread.is_alive():
            self._streamer_thread.join(timeout=2)
            
    def pause_streaming(self) -> None:
        """Pause streaming (feed hold)."""
        self._stream_paused = True
        self.send_immediate_command(self.FEED_HOLD)
        
    def resume_streaming(self) -> None:
        """Resume streaming from pause."""
        self._stream_paused = False
        self.send_immediate_command(self.CYCLE_START)
        
    def reset(self) -> None:
        """
        Perform a soft reset of the controller.
        This will stop any running job.
        """
        self.stop_streaming()
        self._connection.write(self.RESET)
        time.sleep(1)  # Wait for reset to complete
        self._connection.flush_input()
        
        # Reset buffer tracking
        self._rx_buffer_available = self.RX_BUFFER_SIZE
        self._planner_buffer_available = self.PLANNER_BUFFER_SIZE