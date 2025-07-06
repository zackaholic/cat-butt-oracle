#!/usr/bin/env python3
"""
Test script for HC-SR04 ultrasonic sensor
Reads sensor 5x per second and outputs filtered distance readings
"""

import time
import sys
from sensors.hc_sr04 import UltrasonicSensor

def main():
    print("Testing HC-SR04 Ultrasonic Sensor")
    print("Reading at 5Hz (Ctrl+C to stop)")
    print("-" * 35)
    
    try:
        # Initialize sensor
        sensor = UltrasonicSensor()
        print(f"Sensor initialized on TRIG={sensor.trig_pin}, ECHO={sensor.echo_pin}")
        print()
        
        # Test loop at 5Hz
        while True:
            distance = sensor.get_raw_reading()
            
            if distance is not None:
                print(f"{distance:6.2f} inches")
            else:
                print("No reading")
                
            time.sleep(0.2)  # 5Hz update rate
            
    except KeyboardInterrupt:
        print("\nTest stopped by user")
        
    except Exception as e:
        print(f"Sensor initialization failed: {e}")
        sys.exit(1)
        
    finally:
        # Cleanup
        try:
            sensor.cleanup()
        except:
            pass

if __name__ == "__main__":
    main()
