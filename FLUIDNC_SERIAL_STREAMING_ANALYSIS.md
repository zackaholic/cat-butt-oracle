# FluidNC Serial Streaming Module Analysis

## Current State of Existing Python Implementations

### FluidTerm (Official FluidNC Terminal)
FluidTerm is the official serial terminal for FluidNC, built as "an extension of a simple Python serial terminal called miniterm" with FluidNC-specific features like colorized responses and automatic port detection. However, it's primarily a terminal interface, not a streaming library.

**FluidTerm Features:**
- Semi-automatic detection of suitable serial ports for FluidNC controllers
- XMODEM file transfer for uploading FluidNC config files
- Automatic triggering of FluidNC's smart line editing feature
- Highlighting (colorizing) of FluidNC informational and error messages

### Existing GRBL Python Implementations
Multiple basic Python implementations exist for GRBL streaming, but they're mostly simple examples:

1. **Basic GRBL Streamers**: Simple implementations that send single line g-code blocks to grbl and wait for an acknowledgement

2. **Advanced GRBL Streamer**: The official GRBL streaming script includes "aggressive streaming protocol that forces characters into Grbl's serial read buffer" with careful character counting to avoid buffer overflow

**Gap Analysis**: No comprehensive FluidNC-specific Python streaming library exists that combines FluidNC's extended features with robust streaming capabilities.

## FluidNC Serial Protocol Specification

### Connection Parameters
- **Baud Rate**: 115200 (standard FluidNC default)
- **Line Ending**: CRLF
- **Echo**: On by default

### Command Types

#### Immediate Commands
Immediate characters get processed as soon as they are seen even if they are in the middle of a command. Key immediate commands:
- `?` - Status query (most important for streaming)
- `!` - Feed hold
- `~` - Cycle start
- `\x18` (Ctrl-X) - Reset

#### Regular Commands
These are sent a line at a time with a line end. FluidNC will process them when it can and respond with an "ok" when ready to receive another command.

### Status Reports
FluidNC uses the standard Grbl 1.1 status report format for compatibility with gcode senders. Status response format:
```
<Idle|MPos:151.000,149.000,-1.000|Pn:XP|FS:0,0|WCO:12.000,28.000,78.000>
```

**Status Sections (separated by '|'):**
- **Mode**: Idle, Alarm, Check, Homing, Run, Jog, Hold, Door, Sleep
- **Position**: MPos (machine) or WPos (work coordinates)
- **Pin Status**: Active input pins (limits, probe, etc.)
- **Feed/Spindle**: Current feed rate and spindle speed
- **Work Coordinate Offset**: For position calculations
- **Buffer Status**: Available planner blocks and serial buffer bytes
- **Overrides**: Feed/rapid/spindle override percentages

### FluidNC-Specific Extensions
FluidNC adds automatic status reporting: "You can have the firmware automatically report status whenever something changes. This eliminates the need to poll for status".

## Recommended Module Structure

Based on the analysis, here's the structure Claude Code should implement:

### Core Classes

```python
class FluidNCStreamer:
    """Main streaming interface for FluidNC controllers"""
    
    def __init__(self, port=None, baudrate=115200, auto_detect=True)
    def connect()
    def disconnect()
    def send_command(command, wait_for_ok=True)
    def stream_gcode_file(filepath, progress_callback=None)
    def stream_gcode_lines(lines, progress_callback=None)
    def get_status()  # Send ? and parse response
    def enable_auto_status_reporting()
    def set_work_position(x=None, y=None, z=None)
    def home_axes()
    def jog(axis, distance, feed_rate)

class FluidNCStatus:
    """Parse and represent FluidNC status reports"""
    
    @classmethod
    def parse(cls, status_line)
    
    # Properties for each status section
    mode: str
    machine_position: Dict[str, float]
    work_position: Dict[str, float] 
    active_pins: List[str]
    feed_rate: float
    spindle_speed: float
    work_coordinate_offset: Dict[str, float]
    buffer_status: Dict[str, int]
    overrides: Dict[str, int]

class FluidNCConnection:
    """Low-level serial connection management"""
    
    def __init__(self, port, baudrate=115200)
    def open()
    def close()
    def write(data)
    def readline()
    def read_until_ok()
    def flush_input()
    
    @staticmethod
    def detect_fluidnc_ports()  # Auto-detection like FluidTerm
```

### Key Implementation Considerations

1. **Buffer Management**: Implement careful character counting to avoid serial buffer overflow, tracking both sent characters and received acknowledgments

2. **Status Monitoring**: Implement both polling (`?` command) and FluidNC's automatic status reporting feature

3. **Error Handling**: Parse FluidNC error messages and provide meaningful exceptions

4. **Streaming Modes**: 
   - Simple line-by-line (wait for each OK)
   - Advanced buffered streaming (manage serial buffer manually)
   - Settings mode (for configuration commands)

5. **FluidNC Compatibility**: Handle FluidNC-specific responses and features while maintaining GRBL compatibility

6. **Position Tracking**: Convert between machine and work coordinates using WCO

7. **Real-time Commands**: Handle immediate commands that don't wait for OK responses

### Dependencies
- `pyserial` - Serial communication
- `typing` - Type hints
- `dataclasses` - For status representation
- `threading` - For status monitoring
- `queue` - For thread-safe communication

This module would be significantly more comprehensive than existing GRBL streaming examples, specifically designed for FluidNC's extended capabilities while maintaining compatibility with standard GRBL workflows.
