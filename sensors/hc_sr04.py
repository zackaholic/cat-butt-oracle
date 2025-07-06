#!/usr/bin/env python3
"""
HC-SR04 Ultrasonic Sensor Module for Raspberry Pi

Simple, reliable distance measurements with built-in filtering.
Returns distance in inches with 10Hz update rate capability.
"""

import RPi.GPIO as GPIO
import time
import threading
from collections import deque
from typing import Optional


class UltrasonicSensor:
    """
    HC-SR04 Ultrasonic Distance Sensor Interface
    
    Features:
    - Distance measurements in inches
    - Built-in low-pass filtering to reduce noise
    - 10Hz update rate capability
    - Thread-safe operation
    - Automatic GPIO cleanup
    """
    
    def __init__(
        self, 
        trig_pin: int = 14, 
        echo_pin: int = 15,
        filter_size: int = 5,
        timeout: float = 0.1
    ):
        """
        Initialize the ultrasonic sensor.
        
        Args:
            trig_pin: GPIO pin for trigger signal (default: 14)
            echo_pin: GPIO pin for echo signal (default: 15)
            filter_size: Number of readings to average for filtering (default: 5)
            timeout: Maximum time to wait for echo response in seconds (default: 0.1)
        """
        self.trig_pin = trig_pin
        self.echo_pin = echo_pin
        self.timeout = timeout
        
        # Low-pass filter using rolling average
        self.filter_size = filter_size
        self.readings = deque(maxlen=filter_size)
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Setup GPIO
        self._setup_gpio()
        
        # Fill initial readings to avoid startup noise
        self._initialize_filter()
        
    def _setup_gpio(self):
        """Configure GPIO pins for the sensor."""
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        
        # Setup pins
        GPIO.setup(self.trig_pin, GPIO.OUT)
        GPIO.setup(self.echo_pin, GPIO.IN)
        
        # Ensure trigger starts LOW
        GPIO.output(self.trig_pin, GPIO.LOW)
        time.sleep(0.01)  # Settle time
        
    def _initialize_filter(self):
        """Take several initial readings to populate the filter."""
        for _ in range(self.filter_size):
            raw_distance = self.get_raw_reading()
            if raw_distance is not None:
                self.readings.append(raw_distance)
            time.sleep(0.05)  # Small delay between initial readings
            
    def get_raw_reading(self) -> Optional[float]:
        """
        Get a single raw distance measurement.
        
        Returns:
            Distance in inches, or None if measurement failed
        """
        try:
            # Send trigger pulse
            GPIO.output(self.trig_pin, GPIO.HIGH)
            time.sleep(0.00001)  # 10 microsecond pulse
            GPIO.output(self.trig_pin, GPIO.LOW)
            
            # Wait for echo start
            start_time = time.time()
            pulse_start = start_time
            
            while GPIO.input(self.echo_pin) == GPIO.LOW:
                pulse_start = time.time()
                if pulse_start - start_time > self.timeout:
                    return None  # Timeout waiting for echo start
                    
            # Wait for echo end
            pulse_end = pulse_start
            while GPIO.input(self.echo_pin) == GPIO.HIGH:
                pulse_end = time.time()
                if pulse_end - pulse_start > self.timeout:
                    return None  # Timeout waiting for echo end
                    
            # Calculate distance
            pulse_duration = pulse_end - pulse_start
            
            # Speed of sound: 343 m/s = 13503.94 inches/s
            # Distance = (Time × Speed) / 2 (round trip)
            distance_inches = (pulse_duration * 13503.94) / 2
            
            # Sanity check: HC-SR04 range is roughly 0.8 to 157 inches
            if 0.8 <= distance_inches <= 157:
                return distance_inches
            else:
                return None  # Out of valid range
                
        except Exception:
            return None
            
    def get_distance(self) -> Optional[float]:
        """
        Get filtered distance measurement.
        
        Returns:
            Distance in inches (filtered), or None if no valid readings
        """
        with self._lock:
            # Get new raw reading
            raw_distance = self.get_raw_reading()
            
            if raw_distance is not None:
                self.readings.append(raw_distance)
                
            # Return filtered average if we have readings
            if len(self.readings) > 0:
                return sum(self.readings) / len(self.readings)
            else:
                return None
                
    def get_distance_cm(self) -> Optional[float]:
        """
        Get distance in centimeters (for compatibility).
        
        Returns:
            Distance in centimeters, or None if no valid readings
        """
        inches = self.get_distance()
        return inches * 2.54 if inches is not None else None
        
    def is_stable(self, variance_threshold: float = 2.0) -> bool:
        """
        Check if recent readings are stable (low variance).
        Useful for detecting when someone has stopped moving.
        
        Args:
            variance_threshold: Maximum acceptable variance in inches
            
        Returns:
            True if readings are stable, False otherwise
        """
        with self._lock:
            if len(self.readings) < self.filter_size:
                return False
                
            readings_list = list(self.readings)
            mean = sum(readings_list) / len(readings_list)
            variance = sum((x - mean) ** 2 for x in readings_list) / len(readings_list)
            
            return variance < variance_threshold
            
    def clear_filter(self):
        """Clear the filter buffer. Useful for resetting after interference."""
        with self._lock:
            self.readings.clear()
            
    def cleanup(self):
        """Clean up GPIO resources."""
        try:
            GPIO.cleanup([self.trig_pin, self.echo_pin])
        except:
            pass  # Ignore cleanup errors
            
    def __del__(self):
        """Destructor - ensure GPIO cleanup."""
        self.cleanup()


# Convenience function for simple usage
def create_sensor(trig_pin: int = 14, echo_pin: int = 15) -> UltrasonicSensor:
    """
    Create a sensor with default settings.
    
    Args:
        trig_pin: GPIO pin for trigger
        echo_pin: GPIO pin for echo
        
    Returns:
        Configured UltrasonicSensor instance
    """
    return UltrasonicSensor(trig_pin=trig_pin, echo_pin=echo_pin)


# Example usage and testing
if __name__ == "__main__":
    print("HC-SR04 Ultrasonic Sensor Test")
    print("==============================")
    
    try:
        # Create sensor
        sensor = UltrasonicSensor()
        print(f"Sensor initialized on pins TRIG={sensor.trig_pin}, ECHO={sensor.echo_pin}")
        print("Taking distance readings (Ctrl+C to stop)...")
        print()
        
        # Test loop at ~10Hz
        while True:
            distance = sensor.get_distance()
            
            if distance is not None:
                stability = "STABLE" if sensor.is_stable() else "MOVING"
                print(f"Distance: {distance:6.2f} inches ({distance*2.54:6.2f} cm) - {stability}")
            else:
                print("No valid reading")
                
            time.sleep(0.1)  # 10Hz update rate
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")
        
    except Exception as e:
        print(f"Error: {e}")
        
    finally:
        # Cleanup
        try:
            sensor.cleanup()
            print("GPIO cleanup completed")
        except:
            pass


# Hardware Connection Guide:
"""
HC-SR04 to Raspberry Pi Connections:
====================================

HC-SR04 Pin    →    Raspberry Pi Pin
VCC            →    5V (Pin 2 or 4)
GND            →    Ground (Pin 6, 9, 14, 20, 25, 30, 34, or 39)
TRIG           →    GPIO 14 (Pin 8) [configurable]
ECHO           →    GPIO 15 (Pin 10) [configurable]

Note: Some HC-SR04 modules work at 3.3V, but most need 5V for VCC.
The ECHO pin outputs 5V but Raspberry Pi GPIO is 3.3V tolerant,
so direct connection is usually fine, but you can add a voltage
divider if you want to be extra safe.

Voltage Divider (optional for ECHO pin):
ECHO → 1kΩ → GPIO15
       └ 2kΩ → GND
       
This creates a 3.3V signal from the 5V ECHO output.
"""
