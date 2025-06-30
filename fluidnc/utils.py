import time
from typing import Dict, Tuple, List, Optional


def calculate_checksum(line: str) -> int:
    """
    Calculate the checksum for a line (used in certain GRBL-compatible protocols).
    
    The checksum is the XOR of all characters in the line.
    
    Args:
        line: Line of G-code to calculate checksum for.
        
    Returns:
        Calculated checksum as an integer.
    """
    checksum = 0
    for c in line:
        checksum ^= ord(c)
    return checksum


def parse_error_code(error_msg: str) -> Tuple[int, str]:
    """
    Parse a FluidNC/GRBL error message into code and description.
    
    Args:
        error_msg: Error message from the controller.
        
    Returns:
        Tuple of (error_code, error_description).
    """
    error_codes = {
        1: "Expected command letter",
        2: "Bad number format",
        3: "Invalid statement",
        4: "Negative value",
        5: "Setting disabled",
        6: "Step pulse too short",
        7: "Safety door detected",
        8: "Non-numeric value",
        9: "Unsupported statement",
        10: "Unsupported command",
        11: "Coordinate system cannot be changed",
        12: "Unsupported coordinate system",
        13: "G53 not allowed in current motion mode",
        14: "Unsupported distance mode",
        15: "Unsupported feed rate mode",
        16: "Modal group violation",
        17: "Undefined feed rate",
        18: "Invalid line number",
        19: "Value out of range",
        20: "Command unavailable in alarm mode",
        21: "Homing required",
        22: "Axis must be homed",
        23: "Values not enough",
        24: "Values exceeded",
        25: "Kinematics error",
        26: "Not queuing",
        27: "End of travel",
        28: "Wait for motion mode",
        29: "Bad delimeter",
        30: "Bad axis",
        31: "G0 or G1 not allowed",
        32: "System is not ready",
        33: "Value out of limit",
        34: "PWM requires a laser",
        35: "Setting is read only",
        36: "Not running",
        37: "Probe compensation",
        38: "SD failed mount",
        39: "SD failed read",
        40: "SD failed open dir",
        41: "SD dir not found",
        42: "SD file empty",
        43: "SD file read only",
        44: "SD card changed",
        45: "Shutdown",
        46: "Test failed",
        47: "Authentication failed",
        48: "Hard limit",
        60: "File not found",
        61: "Buffer full",
    }
    
    if error_msg.startswith("error:"):
        try:
            code = int(error_msg.split(':')[1].strip())
            description = error_codes.get(code, "Unknown error")
            return code, description
        except (IndexError, ValueError):
            pass
            
    return 0, error_msg


def parse_alarm_code(alarm_msg: str) -> Tuple[int, str]:
    """
    Parse a FluidNC/GRBL alarm message into code and description.
    
    Args:
        alarm_msg: Alarm message from the controller.
        
    Returns:
        Tuple of (alarm_code, alarm_description).
    """
    alarm_codes = {
        1: "Hard limit",
        2: "Soft limit",
        3: "Reset during motion",
        4: "Probe fail",
        5: "Probe disconnect",
        6: "Homing fail",
        7: "Homing missmatch",
        8: "Deadzone homing failed",
        9: "Homing door open",
    }
    
    if alarm_msg.startswith("ALARM:"):
        try:
            code = int(alarm_msg.split(':')[1].strip())
            description = alarm_codes.get(code, "Unknown alarm")
            return code, description
        except (IndexError, ValueError):
            pass
            
    return 0, alarm_msg


def gcode_is_motion_command(gcode_line: str) -> bool:
    """
    Check if a G-code line contains a motion command.
    
    Args:
        gcode_line: Line of G-code to check.
        
    Returns:
        True if the line contains a motion command, False otherwise.
    """
    # Remove comments
    line = gcode_line.split(';')[0].strip().upper()
    
    # Check for G0, G1, G2, G3 motion commands
    return any(cmd in line for cmd in ['G0', 'G1', 'G2', 'G3', 'G28', 'G30'])


def estimate_execution_time(
    gcode_lines: List[str], 
    feed_rate: Optional[float] = None
) -> float:
    """
    Estimate the execution time for a list of G-code lines.
    This is a very rough estimate based on motion commands.
    
    Args:
        gcode_lines: List of G-code lines.
        feed_rate: Default feed rate to use if not specified in G-code.
        
    Returns:
        Estimated execution time in seconds.
    """
    total_time = 0.0
    current_feed = feed_rate or 1000.0  # Default feed rate
    
    for line in gcode_lines:
        # Skip comments and empty lines
        clean_line = line.split(';')[0].strip().upper()
        if not clean_line:
            continue
            
        # Check for feed rate changes
        if 'F' in clean_line:
            try:
                # Extract feed rate (F value)
                f_parts = clean_line.split('F')[1].strip()
                f_value = float(f_parts.split()[0].rstrip(",.;"))
                current_feed = f_value
            except (IndexError, ValueError):
                pass
                
        # Add time for motion commands
        if gcode_is_motion_command(clean_line):
            # Very rough estimate: 1 second per motion command at 1000mm/min
            # Adjust based on feed rate
            if current_feed > 0:
                total_time += 1000.0 / current_feed
            else:
                total_time += 1.0  # Default 1 second if feed rate is invalid
                
    return total_time