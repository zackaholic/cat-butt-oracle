import logging
import os
import time
import threading
import queue
from typing import List, Dict, Optional, Callable, Union, Tuple, Iterator

from .connection import FluidNCConnection
from .status import FluidNCStatus


class FluidNCStreamer:
    """Main streaming interface for FluidNC controllers."""
    
    # FluidNC/GRBL control characters
    RESET = '\x18'  # Ctrl-X
    FEED_HOLD = '!'
    CYCLE_START = '~'
    STATUS_REPORT = '?'
    
    # FluidNC command character limits (for buffer management)
    # GRBL_RX_BUFFER_SIZE is 127 in grbl/config.h
    SERIAL_BUFFER_SIZE = 127
    
    def __init__(
        self, 
        port: str = None, 
        baudrate: int = 115200, 
        auto_detect: bool = True,
        debug: bool = False
    ):
        """
        Initialize a FluidNC streaming interface.
        
        Args:
            port: Serial port to connect to. If None and auto_detect is True, 
                 will try to auto-detect.
            baudrate: Serial baud rate (default 115200).
            auto_detect: Whether to try to auto-detect FluidNC ports if port not specified.
            debug: Enable debug logging.
        """
        self._connection = FluidNCConnection(
            port=port if not auto_detect or port else None,
            baudrate=baudrate
        )
        self._status_monitor = None
        self._status_queue = queue.Queue()
        self._status_interval = 0.1  # Status polling interval in seconds
        self._status_monitoring = False
        self._last_status = None
        self._debug = debug
        if debug:
            logging.basicConfig(level=logging.DEBUG)
            self._logger = logging.getLogger('FluidNC')
        else:
            self._logger = logging.getLogger('FluidNC')
            self._logger.addHandler(logging.NullHandler())
        
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
        if self._status_monitoring:
            self.disable_status_monitoring()
        self._connection.close()
        
    def reset(self) -> str:
        """
        Send a soft reset command to FluidNC.
        
        Returns:
            Response from the controller.
        """
        # Send Ctrl-X reset command
        self._connection.write(self.RESET)
        
        # Wait for reset to complete
        time.sleep(1)
        
        # Clear input buffer
        self._connection.flush_input()
        
        # Send empty line to get an ok response
        self._connection.write("\r\n")
        return self._connection.read_until_ok(timeout=5)
        
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
            
        # Strip whitespace and add line ending if needed
        command = command.strip()
        
        if self._debug:
            self._logger.debug(f"Sending: {repr(command)}")
        
        # Send the command
        self._connection.write(command)
        
        # For immediate commands, don't wait for ok
        if command in [self.STATUS_REPORT, self.FEED_HOLD, self.CYCLE_START]:
            response = self._connection.readline()
            if self._debug and response:
                self._logger.debug(f"Received: {repr(response)}")
            return response
            
        # For regular commands, wait for ok if requested
        if wait_for_ok:
            response = self._connection.read_until_ok()
            if self._debug and response:
                self._logger.debug(f"Received: {repr(response)}")
            return response
        else:
            return ""
            
    def get_status(self) -> FluidNCStatus:
        """
        Request and return the current status from FluidNC.
        
        Returns:
            FluidNCStatus object with parsed status information.
        """
        response = self.send_command(self.STATUS_REPORT, wait_for_ok=False)
        return FluidNCStatus.parse(response)
        
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
            
    def get_latest_status(self) -> Optional[FluidNCStatus]:
        """
        Get the most recent status update without sending a new request.
        
        Returns:
            The most recent FluidNCStatus or None if no status has been received.
        """
        return self._last_status
        
    def stream_gcode_file(
        self, 
        filepath: str, 
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[int, int]:
        """
        Stream a G-code file to the FluidNC controller.
        
        Args:
            filepath: Path to the G-code file.
            progress_callback: Optional callback function for progress updates.
                              Receives (lines_complete, total_lines).
                              
        Returns:
            Tuple of (lines_sent, lines_total).
            
        Raises:
            FileNotFoundError: If the file does not exist.
            RuntimeError: If streaming fails.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"G-code file not found: {filepath}")
            
        # Count total lines for progress reporting
        total_lines = sum(1 for _ in open(filepath, 'r'))
        
        with open(filepath, 'r') as f:
            return self.stream_gcode_lines(f, total_lines, progress_callback)
            
    def stream_gcode_lines(
        self, 
        lines: Union[List[str], Iterator[str]], 
        total_lines: Optional[int] = None,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> Tuple[int, int]:
        """
        Stream G-code lines to the FluidNC controller.
        
        Args:
            lines: List of G-code lines or iterator producing lines.
            total_lines: Total number of lines (optional, for progress reporting).
            progress_callback: Optional callback function for progress updates.
                              Receives (lines_complete, total_lines).
                              
        Returns:
            Tuple of (lines_sent, total_lines).
            
        Raises:
            RuntimeError: If streaming fails.
        """
        if total_lines is None and hasattr(lines, '__len__'):
            total_lines = len(lines)
        elif total_lines is None:
            total_lines = 0  # Unknown
            
        lines_sent = 0
        
        # Simple line-by-line streaming (waits for 'ok' after each line)
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
                
                if progress_callback and total_lines:
                    progress_callback(lines_sent, total_lines)
                    
            except Exception as e:
                raise RuntimeError(f"Error streaming at line {lines_sent}: {str(e)}")
                
        return lines_sent, total_lines
        
    def set_work_position(
        self, 
        x: Optional[float] = None, 
        y: Optional[float] = None, 
        z: Optional[float] = None
    ) -> None:
        """
        Set the work position (zero) for specified axes.
        
        Args:
            x: X-axis position value or None to leave unchanged.
            y: Y-axis position value or None to leave unchanged.
            z: Z-axis position value or None to leave unchanged.
        """
        command = "G10 L20 P1"
        
        if x is not None:
            command += f" X{x}"
        if y is not None:
            command += f" Y{y}"
        if z is not None:
            command += f" Z{z}"
            
        self.send_command(command)
        
    def home_axes(self) -> None:
        """Home all axes that have homing enabled."""
        self.send_command("$H")
        
    def jog(self, axis: str, distance: float, feed_rate: float) -> None:
        """
        Jog a specific axis by the given distance at the specified feed rate.
        
        Args:
            axis: Axis to jog ('X', 'Y', or 'Z').
            distance: Distance to jog in mm.
            feed_rate: Feed rate in mm/min.
        """
        axis = axis.upper()
        if axis not in ['X', 'Y', 'Z']:
            raise ValueError("Axis must be X, Y, or Z")
            
        self.send_command(f"$J=G91 {axis}{distance} F{feed_rate}")
        
    def feed_hold(self) -> None:
        """Pause the current job (feed hold)."""
        self._connection.write(self.FEED_HOLD)
        
    def resume(self) -> None:
        """Resume from feed hold."""
        self._connection.write(self.CYCLE_START)
        
    def send_command_with_retry(self, command: str, max_retries: int = 2) -> str:
        """
        Send command with automatic retry on failure.
        
        Args:
            command: The command to send.
            max_retries: Maximum number of retry attempts.
            
        Returns:
            Response from the controller.
            
        Raises:
            RuntimeError: If command fails after all retries.
        """
        import serial
        
        for attempt in range(max_retries + 1):
            try:
                return self.send_command(command)
            except (TimeoutError, serial.SerialException) as e:
                if attempt == max_retries:
                    raise
                
                if self._debug:
                    self._logger.warning(f"Command failed (attempt {attempt + 1}): {e}")
                
                # Quick connection health check
                if not self._connection.test_connection_health():
                    if self._debug:
                        self._logger.warning("Connection unhealthy, attempting reconnect...")
                    self.disconnect()
                    time.sleep(0.5)
                    if not self.connect():
                        raise RuntimeError("Could not reconnect after communication failure")
                
                time.sleep(0.1 * (attempt + 1))  # Progressive backoff
        
        raise RuntimeError(f"Command failed after {max_retries + 1} attempts")
    
    def soft_reset(self) -> None:
        """Perform a soft reset of the controller."""
        self._connection.write(self.RESET)
        time.sleep(1)  # Wait for reset to complete
        self._connection.flush_input()