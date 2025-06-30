class FluidNCError(Exception):
    """Base exception class for FluidNC-related errors."""
    pass


class FluidNCConnectionError(FluidNCError):
    """Exception raised for connection-related errors."""
    pass


class FluidNCTimeoutError(FluidNCError):
    """Exception raised when a command times out."""
    pass


class FluidNCCommandError(FluidNCError):
    """Exception raised when a command fails or returns an error."""
    
    def __init__(self, command: str, error_message: str):
        self.command = command
        self.error_message = error_message
        super().__init__(f"Command '{command}' failed: {error_message}")


class FluidNCStreamingError(FluidNCError):
    """Exception raised when G-code streaming fails."""
    
    def __init__(self, message: str, line_number: int = None):
        self.line_number = line_number
        if line_number is not None:
            message = f"{message} at line {line_number}"
        super().__init__(message)


class FluidNCAlarmError(FluidNCError):
    """Exception raised when the controller enters ALARM state."""
    
    def __init__(self, alarm_code: str, description: str = None):
        self.alarm_code = alarm_code
        self.description = description
        message = f"Controller ALARM: {alarm_code}"
        if description:
            message += f" - {description}"
        super().__init__(message)