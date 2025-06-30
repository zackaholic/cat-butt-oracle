import os
import re
import time
from typing import List, Optional, Tuple
import serial
import serial.tools.list_ports


class FluidNCConnection:
    """Low-level serial connection management for FluidNC controllers."""
    
    def __init__(self, port: str = None, baudrate: int = 115200):
        """
        Initialize a connection to a FluidNC controller.
        
        Args:
            port: Serial port path. If None, auto-detection will be attempted.
            baudrate: Serial connection baud rate, default 115200.
        """
        self._port = port
        self._baudrate = baudrate
        self._serial = None
        self._connected = False
        
    def open(self) -> None:
        """
        Open the serial connection to the FluidNC controller.
        
        Raises:
            serial.SerialException: If connection fails or no valid ports found.
        """
        if self._connected:
            return
            
        if not self._port:
            detected_ports = self.detect_fluidnc_ports()
            if not detected_ports:
                raise serial.SerialException("No FluidNC ports detected. Please specify port manually.")
            self._port = detected_ports[0]
            
        self._serial = serial.Serial(
            port=self._port,
            baudrate=self._baudrate,
            timeout=1,
            write_timeout=1
        )
        
        # Clear startup messages
        time.sleep(1)  # Wait for FluidNC to initialize
        self.flush_input()
        
        # Test FluidNC communication - send single \n for single ok
        if not self._test_fluidnc_communication():
            self._serial.close()
            raise serial.SerialException(f"Device on port {self._port} does not appear to be a FluidNC controller.")
            
        self._connected = True
        
    def _test_fluidnc_communication(self) -> bool:
        """
        Test FluidNC communication with proper line endings.
        
        Returns:
            True if device responds like FluidNC, False otherwise.
        """
        try:
            # Send empty line with \n only (not \r\n to avoid double commands)
            self._serial.write(b"\n")
            time.sleep(0.5)
            
            # Read all available data (handles multiple 'ok' responses)
            if self._serial.in_waiting:
                response = self._serial.read(self._serial.in_waiting)
                response_str = response.decode('utf-8', errors='ignore')
                print(f"DEBUG: Connection test response: {repr(response_str)}")
                
                # Check if we got at least one 'ok'
                if 'ok' in response_str.lower():
                    return True
            
            # Try status command as backup test
            self._serial.write(b"?\n")
            time.sleep(0.5)
            
            if self._serial.in_waiting:
                status_response = self._serial.read(self._serial.in_waiting)
                status_str = status_response.decode('utf-8', errors='ignore')
                print(f"DEBUG: Status test response: {repr(status_str)}")
                
                # Check for FluidNC status format
                if '<' in status_str and '>' in status_str:
                    return True
                    
            return False
            
        except Exception as e:
            print(f"DEBUG: Communication test failed: {e}")
            return False
        
    def close(self) -> None:
        """Close the serial connection."""
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._connected = False
        
    def write(self, data: str) -> int:
        """
        Write data to the serial connection.
        
        Args:
            data: Data to write.
            
        Returns:
            Number of bytes written.
        """
        if not self._connected:
            raise RuntimeError("Not connected to FluidNC controller")
            
        # FluidNC treats \r\n as two commands, so use just \n
        if not data.endswith('\n'):
            data = data.rstrip() + '\n'
            
        return self._serial.write(data.encode('utf-8'))
    
    def readline(self) -> str:
        """
        Read a line from the serial connection.
        
        Returns:
            A line of text from the serial connection.
        """
        if not self._connected:
            raise RuntimeError("Not connected to FluidNC controller")
            
        line = self._serial.readline().decode('utf-8').strip()
        return line
    
    def read_until_ok(self, timeout: float = 10.0) -> str:
        """
        Read from the serial connection until an 'ok' response is received.
        Now expects single 'ok' responses since we fixed the line ending issue.
        
        Args:
            timeout: Maximum time to wait for 'ok' response in seconds.
            
        Returns:
            Concatenated response lines including the 'ok'.
            
        Raises:
            TimeoutError: If 'ok' not received within timeout period.
        """
        if not self._connected:
            raise RuntimeError("Not connected to FluidNC controller")
            
        start_time = time.time()
        response = []
        
        # Use shorter timeout for individual reads
        original_timeout = self._serial.timeout
        self._serial.timeout = 0.1
        
        try:
            while (time.time() - start_time) < timeout:
                line = self.readline()
                if line:
                    response.append(line)
                    if line.startswith("ok") or line.startswith("error"):
                        break
                time.sleep(0.01)  # Prevent busy waiting
        finally:
            self._serial.timeout = original_timeout
        
        if not response or not any(line.startswith(("ok", "error")) for line in response):
            raise TimeoutError(f"No valid response within {timeout}s: {response}")
        return "\n".join(response)
    
    def flush_input(self) -> None:
        """Flush the input buffer, discarding all content."""
        if self._serial and self._serial.is_open:
            self._serial.reset_input_buffer()
    
    @staticmethod
    def detect_fluidnc_ports() -> List[str]:
        """
        Enhanced detection with CH340 fix knowledge.
        
        Returns:
            List of port paths that may be FluidNC controllers.
        """
        ports = []
        for port in serial.tools.list_ports.comports():
            # Prioritize known working configurations
            if "1A86:7523" in port.hwid.upper():  # CH340 (specific working device)
                # Prefer tty over cu on macOS (better compatibility)
                if port.device.startswith('/dev/cu.'):
                    tty_equivalent = port.device.replace('/dev/cu.', '/dev/tty.')
                    if os.path.exists(tty_equivalent):
                        ports.insert(0, tty_equivalent)  # Prioritize tty
                    ports.append(port.device)
                else:
                    ports.append(port.device)
            elif any(vid_pid in port.hwid.upper() for vid_pid in [
                "0403:6001",  # FTDI
                "10C4:EA60",  # CP210x
                "1D6B:0002",  # ESP32
            ]):
                ports.append(port.device)
                
        return ports
    
    @property
    def is_connected(self) -> bool:
        """Return whether we have an active connection."""
        return self._connected and self._serial and self._serial.is_open
    
    def test_connection_health(self) -> bool:
        """
        Quick health check without blocking.
        
        Returns:
            True if connection is healthy, False otherwise.
        """
        if not self.is_connected:
            return False
        
        try:
            # Send status command with short timeout (write() adds \n automatically)
            self._serial.write(b"?\n")
            start_time = time.time()
            
            while (time.time() - start_time) < 1.0:  # 1 second max
                if self._serial.in_waiting:
                    response = self._serial.read(self._serial.in_waiting)
                    response_str = response.decode('utf-8', errors='ignore')
                    # Check for valid FluidNC status format
                    if '<' in response_str and '>' in response_str:
                        return True
                time.sleep(0.05)
            return False
        except:
            return False
    
    @property
    def port(self) -> Optional[str]:
        """Return the current port."""
        return self._port