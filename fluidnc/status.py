import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Any


@dataclass
class FluidNCStatus:
    """Parse and represent FluidNC status reports."""
    
    # Status mode
    mode: str = "Unknown"
    
    # Position data
    machine_position: Dict[str, float] = None
    work_position: Dict[str, float] = None
    work_coordinate_offset: Dict[str, float] = None
    
    # Input pins
    active_pins: List[str] = None
    
    # Feed and speed
    feed_rate: float = 0.0
    spindle_speed: float = 0.0
    
    # Buffer information
    buffer_status: Dict[str, int] = None
    
    # Override values
    overrides: Dict[str, int] = None
    
    # Raw status line
    raw_status: str = ""
    
    def __post_init__(self):
        """Initialize default values for collection attributes."""
        if self.machine_position is None:
            self.machine_position = {'x': 0.0, 'y': 0.0, 'z': 0.0}
            
        if self.work_position is None:
            self.work_position = {'x': 0.0, 'y': 0.0, 'z': 0.0}
            
        if self.work_coordinate_offset is None:
            self.work_coordinate_offset = {'x': 0.0, 'y': 0.0, 'z': 0.0}
            
        if self.active_pins is None:
            self.active_pins = []
            
        if self.buffer_status is None:
            self.buffer_status = {'planner': 0, 'rx': 0}
            
        if self.overrides is None:
            self.overrides = {'feed': 100, 'rapid': 100, 'spindle': 100}
    
    @classmethod
    def parse(cls, status_line: str) -> 'FluidNCStatus':
        """
        Parse a FluidNC status report string into a FluidNCStatus object.
        
        Args:
            status_line: Status report string from FluidNC.
            
        Returns:
            FluidNCStatus object with parsed data.
        """
        if not status_line.startswith('<') or not status_line.endswith('>'):
            return cls(raw_status=status_line)
            
        # Remove brackets and split into sections
        content = status_line[1:-1]
        sections = content.split('|')
        
        status = cls(raw_status=status_line)
        
        # Parse mode (first section)
        status.mode = sections[0].strip()
        
        # Parse remaining sections
        for section in sections[1:]:
            if not section:
                continue
                
            # Split section into key and value
            parts = section.split(':', 1)
            if len(parts) != 2:
                continue
                
            key, value = parts[0], parts[1]
            
            # Position data
            if key == 'MPos':
                status.machine_position = cls._parse_position(value)
            elif key == 'WPos':
                status.work_position = cls._parse_position(value)
            elif key == 'WCO':
                status.work_coordinate_offset = cls._parse_position(value)
                
            # Feed and spindle
            elif key == 'FS':
                values = value.split(',')
                if len(values) >= 1:
                    try:
                        status.feed_rate = float(values[0])
                    except ValueError:
                        pass
                if len(values) >= 2:
                    try:
                        status.spindle_speed = float(values[1])
                    except ValueError:
                        pass
                        
            # Buffer status
            elif key == 'Bf':
                values = value.split(',')
                if len(values) >= 2:
                    try:
                        status.buffer_status['planner'] = int(values[0])
                        status.buffer_status['rx'] = int(values[1])
                    except ValueError:
                        pass
                        
            # Pin status
            elif key == 'Pn':
                status.active_pins = value.split(',')
                
            # Overrides
            elif key == 'Ov':
                values = value.split(',')
                if len(values) >= 3:
                    try:
                        status.overrides['feed'] = int(values[0])
                        status.overrides['rapid'] = int(values[1])
                        status.overrides['spindle'] = int(values[2])
                    except ValueError:
                        pass
                        
        return status
    
    @staticmethod
    def _parse_position(position_str: str) -> Dict[str, float]:
        """
        Parse a position string like "0.000,0.000,0.000" into a dictionary.
        
        Args:
            position_str: Comma-separated position values.
            
        Returns:
            Dictionary with x, y, z keys mapped to float values.
        """
        result = {'x': 0.0, 'y': 0.0, 'z': 0.0}
        values = position_str.split(',')
        
        axes = ['x', 'y', 'z']
        for i, value in enumerate(values):
            if i < len(axes):
                try:
                    result[axes[i]] = float(value)
                except ValueError:
                    pass
                    
        return result