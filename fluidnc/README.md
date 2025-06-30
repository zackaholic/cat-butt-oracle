# FluidNC Streaming Module

A Python module for communicating with and streaming G-code to FluidNC controllers.

## Features

- Connect to FluidNC controllers with automatic port detection
- Stream G-code files and commands with proper buffer management
- Monitor controller status in real-time
- Support for jogging, homing, and position setting
- Error handling and exception reporting
- Compatible with FluidNC's extensions to the GRBL protocol

## Installation

```bash
# From the Cat-Butt directory
pip install -e .
```

## Usage

### Basic Connection

```python
from fluidnc import FluidNCStreamer

# Connect to a FluidNC controller (auto-detects port)
streamer = FluidNCStreamer(auto_detect=True)
streamer.connect()

# Get current status
status = streamer.get_status()
print(f"Mode: {status.mode}")
print(f"Position: X={status.work_position['x']}, Y={status.work_position['y']}")

# Disconnect when done
streamer.disconnect()
```

### Streaming G-code

```python
# Stream a G-code file
lines_sent, total_lines = streamer.stream_gcode_file('path/to/gcode_file.nc')
print(f"Sent {lines_sent} of {total_lines} lines")

# Stream G-code from a list of commands
commands = [
    "G90",  # Absolute positioning
    "G0 X10 Y10",  # Rapid move
    "G1 X20 Y20 F1000",  # Linear move
]
streamer.stream_gcode_lines(commands)
```

### Movement Commands

```python
# Home the machine
streamer.home_axes()

# Set work position (zero)
streamer.set_work_position(x=0, y=0, z=0)

# Jog an axis
streamer.jog(axis='X', distance=10, feed_rate=1000)
```

### Status Monitoring

```python
# Define a callback function
def status_update(status):
    print(f"Status: {status.mode}, X: {status.work_position['x']}")

# Enable status monitoring with callback
streamer.enable_status_monitoring(callback=status_update)

# Do other operations...

# Disable status monitoring when done
streamer.disable_status_monitoring()
```

## API Reference

### FluidNCStreamer

Main class for interacting with FluidNC controllers.

- `__init__(port=None, baudrate=115200, auto_detect=True)`: Initialize the streamer.
- `connect()`: Connect to the FluidNC controller.
- `disconnect()`: Disconnect from the controller.
- `send_command(command, wait_for_ok=True)`: Send a command to the controller.
- `stream_gcode_file(filepath, progress_callback=None)`: Stream a G-code file.
- `stream_gcode_lines(lines, total_lines=None, progress_callback=None)`: Stream G-code lines.
- `get_status()`: Get current controller status.
- `enable_status_monitoring(callback=None)`: Start automatic status monitoring.
- `disable_status_monitoring()`: Stop automatic status monitoring.
- `get_latest_status()`: Get the most recent status without sending a new request.
- `set_work_position(x=None, y=None, z=None)`: Set work position for specified axes.
- `home_axes()`: Home all axes.
- `jog(axis, distance, feed_rate)`: Jog a specific axis.
- `feed_hold()`: Pause the current job.
- `resume()`: Resume from feed hold.
- `soft_reset()`: Perform a soft reset of the controller.

### FluidNCStatus

Class for representing and parsing FluidNC status reports.

- `parse(status_line)`: Parse a status report into a FluidNCStatus object.
- Properties: `mode`, `machine_position`, `work_position`, `active_pins`, `feed_rate`, 
  `spindle_speed`, `work_coordinate_offset`, `buffer_status`, `overrides`.