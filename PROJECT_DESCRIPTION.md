# Cat Butt Oracle - Interactive Ouija Board Art Installation

## Project Overview
An interactive art installation featuring a mechanical cat tail that points to letters and symbols on a custom ouija board. The piece explores the human experience of deciphering cat behavior and body language, presenting the tail's movements as mystical communication from beyond.

## Concept & User Experience
The installation presents cat tail movements as an oracle or contacted spirit. The tail acts as a ouija board planchette, moving precisely to letters on the board to spell out messages. This mirrors how humans constantly attempt to decode cat tail language in real life - the tail becomes a messenger pointing to specific locations with feline precision.

## Technical Specifications

### Hardware
- **Controller**: MKS DLC32 board running FluidNC firmware
- **Mechanism**: Mechanical cat tail with precise 2-axis positioning
- **Surface**: Custom ouija board with letters/symbols for tail to indicate
- **Connection**: USB serial connection (CH340 chip) at 115200 baud

### Movement System
- **X-axis**: Left-right movement across ouija board letters
- **Y-axis**: Forward-back positioning for different rows of letters
- **Precision**: Sub-millimeter accuracy with configurable speed control
- **Coordinate System**: Each letter has calibrated X,Y coordinates

### Message Display
- Tail moves to precise letter positions to spell out words
- Configurable movement speed and timing
- Smooth positioning between letters with programmable delays
- Each letter position individually calibrated for board layout

## Development Status

### ✅ COMPLETED - Core Infrastructure
- **Hardware**: Prototype tail mechanism built and operational
- **Controller**: MKS DLC32 with FluidNC firmware configured and tested  
- **Software**: Complete FluidNC Python streaming library with buffer management
- **Communication**: All serial connection issues resolved (CH340 driver + line ending fixes)
- **Real-time Control**: Advanced puppeteering system for testing and validation

### ✅ COMPLETED - Precision Positioning System
- **Interactive Calibration Tool**: `calibrate_ouija_letters.py`
  - Real-time X,Y coordinate calibration for each letter
  - Keyboard controls: fine (±0.1mm) and coarse (±1mm) adjustments
  - Visual feedback via pygame interface showing current position
  - Saves calibration data in JSON format with both X and Y coordinates
  - Clean terminal interface for easy letter-by-letter setup

- **Letter Testing System**: `test_ouija_letters.py`
  - Interactive tool for testing letter positioning repeatability
  - Loads calibrated coordinates and moves tail to specific letters
  - Configurable movement speed and timing delays
  - Simple command interface: type letter, tail moves to position

### ✅ COMPLETED - Data Management
- **Coordinate Storage**: JSON-based letter position database
- **Format**: Each letter stores `{"x": float, "y": float}` coordinates
- **Precision**: Calibrated positioning accurate to 0.1mm increments
- **Flexibility**: Supports irregular ouija board layouts with unique Y positions per letter

### ✅ COMPLETED - Interactive Sensor Integration
- **Ultrasonic Distance Sensing**: `sensors/hc_sr04.py`
  - HC-SR04 ultrasonic sensor module with noise filtering
  - Thread-safe operation with rolling average filtering
  - Presence detection and stability monitoring
  - 5-10Hz update rate capability for responsive interaction
  - Built-in range validation and error handling

- **Sensor Testing System**: `test_ultrasonic.py`
  - 5Hz sensor reading validation script
  - Real-time distance output for calibration
  - Proper GPIO cleanup and error handling

### 🎯 CURRENT STATUS: Advanced Motion System Development
The core infrastructure is complete and we're now building sophisticated, lifelike motion systems. Current capabilities:
- Precisely calibrate letter positions on any ouija board layout
- Store and recall exact coordinates for each letter
- **NEW**: Advanced tail speller with organic motion profiles
- **NEW**: Ultrasonic sensor integration for presence detection
- **NEW**: Message database with mood-based response categories
- Maintain sub-millimeter positioning accuracy
- Handle complex board geometries with individual letter Y-coordinates

## Software Architecture

### FluidNC Streaming Module (`/fluidnc/`)
Complete G-code streaming library with:
- Automatic controller detection and connection
- Robust timeout handling and error recovery  
- Real-time status monitoring
- Advanced buffer management for smooth operation
- Cross-platform compatibility (macOS CH340 driver support)

### Calibration System (`calibrate_ouija_letters.py`)
Interactive tool for precise letter positioning:
- **Visual Interface**: Pygame window with real-time coordinate display
- **Keyboard Controls**: 
  - X-axis: Comma/Period (±1mm), Left/Right arrows (±0.1mm)
  - Y-axis: Quote/Slash (±1mm), Up/Down arrows (±0.1mm)
- **Data Storage**: Saves coordinates in structured JSON format
- **Progress Tracking**: Can save partial calibrations and resume later

### Testing System (`test_ouija_letters.py`)
Interactive letter positioning validator:
- **Simple Interface**: Type letter, tail moves to position
- **Movement Sequence**: Raises to 3mm, moves to X,Y position, lowers to calibrated height
- **Repeatability Testing**: Tests positioning accuracy from different starting points
- **Configurable Timing**: Adjustable delays and movement speeds

### Real-Time Puppeteering (Development Tool)
Advanced mouse-controlled positioning for mechanism testing and validation. Proven system capabilities across full coordinate ranges with responsive control and buffer optimization.

### Sensor System (`/sensors/`)
Interactive presence detection for art installation:
- **HC-SR04 Module**: `sensors/hc_sr04.py` - Ultrasonic distance sensor with raw readings
- **Test Script**: `test_ultrasonic.py` - 5Hz sensor validation and calibration
- **GPIO Integration**: Thread-safe sensor reading compatible with FluidNC control
- **Interaction Detection**: Configurable presence thresholds for triggering messages

### Advanced Motion System (`tail_speller.py`)
**🎯 CURRENT FOCUS**: Sophisticated, lifelike tail movement for spelling messages:

#### Motion Philosophy
Creating organic, cat-like movements that feel alive rather than robotic. The tail should move with the deliberate precision of a cat placing its paw, complete with natural variations and timing.

#### Movement Architecture
**Three-Phase Motion Sequence:**
1. **Lift Phase**: Tail raises 4-6mm above board surface
2. **Approach Phase**: Simultaneous X/Y movement with organic variations
3. **Tap Phase**: Final 1-2mm with slight acceleration for cat-like "pounce"

#### Lifelike Motion Features
- **Waypoint Resolution**: 0.1mm spacing for ultra-smooth curves
- **Y-Axis Randomness**: ±0.5mm variation during approach (journey varies, destination precise)
- **Speed Coordination**: X-axis completes first, then Y accelerates for final tap
- **Timing Variations**: Randomized acceleration profiles prevent robotic feel
- **Precise Targeting**: Always hits exact letter coordinates despite organic approach

#### Technical Implementation
- **Path Generation**: Linear interpolation with random Y offsets per waypoint
- **Speed Profiles**: Variable feedrates (1200 mm/min lift, 800 approach, 1500 tap)
- **Timing Control**: Configurable settle time (0.5s) and inter-letter pause (1.2s)
- **Error Handling**: Graceful skipping of undefined letters with logging

#### Future Motion Enhancements (Unexplored)
- **Sine Wave Acceleration**: Replace linear speed changes with organic curves
- **Hunting Behavior**: Slight position corrections/adjustments at target
- **Emotional Speed Mapping**: Tie movement speed to message mood categories
- **Approach Angle Variation**: Curved rather than linear approach paths
- **Micro-Movements**: Subtle tail "twitches" while settled on letters
- **Momentum Simulation**: Slight overshoot/correction for realistic physics
- **Fatigue Modeling**: Gradually slower movements during long messages
- **Attention Seeking**: Exaggerated movements when no one is detected

### Message Database (`responses.json`)
Mood-based response system with natural progression:
- **Welcoming**: Initial friendly greetings ("HELLO", "GREETINGS", "WELCOME")
- **Cryptic**: Mysterious oracle responses ("PERHAPS", "WHO KNOWS", "UNCLEAR")
- **Sleepy**: Tired, dismissive messages ("DROWSY", "LATER", "QUIET")
- **Dismissive**: Direct dismissal for overstayers ("GO AWAY", "ENOUGH", "BEGONE")

#### Planned Behavior System
- **Mood Progression**: Automatic escalation based on interaction duration
- **Response Selection**: Randomized within mood categories
- **Timing Thresholds**: Configurable delays between mood transitions
- **Presence Correlation**: Ultrasonic sensor triggers mood state changes

## Technical Achievements

### 1. Precision Positioning System
- Sub-millimeter accuracy letter positioning
- Individual X,Y calibration for each letter
- Configurable movement speeds and timing
- Support for irregular board layouts

### 2. Robust Communication Stack
- Solved FluidNC protocol compatibility issues
- Eliminated CH340 driver problems on macOS
- Implemented advanced buffer management
- Real-time status monitoring and error recovery

### 3. User-Friendly Calibration Workflow
- Interactive visual calibration interface
- Intuitive keyboard controls for fine positioning
- Progress saving and resumable calibration sessions
- Clean separation of calibration and operation phases

## Art Installation Integration

### Current Capabilities
The system is now ready for art installation deployment:
- **Message Programming**: Can spell out any pre-programmed messages
- **Precise Positioning**: Tail points exactly to intended letters
- **Smooth Operation**: Configurable movement timing for dramatic effect
- **Reliable Performance**: Robust error handling for installation environment

### Installation Requirements
- Custom ouija board with letter layout
- Message content (words/phrases to display)
- Interactive trigger system via ultrasonic sensor
- Power and mounting for tail mechanism

## Raspberry Pi Deployment

### 🔄 NEXT PHASE: Pi Integration
The project is ready for deployment on Raspberry Pi hardware. All core systems have been developed and tested, with the ultrasonic sensor integration providing interactive capabilities.

### Hardware Requirements
- **Raspberry Pi 4** (recommended) or Pi 3B+
- **MicroSD Card**: 32GB+ (Class 10 or better)
- **GPIO Connections**:
  - HC-SR04 Ultrasonic Sensor (TRIG: GPIO 18, ECHO: GPIO 24)
  - USB connection to MKS DLC32 controller
- **Power Supply**: 5V 3A for Pi + controller power requirements
- **Optional**: Voltage divider for ECHO pin (1kΩ + 2kΩ resistors)

### Pi Setup Recommendations
1. **Operating System**: Raspberry Pi OS Lite (headless operation)
2. **Python Environment**: Python 3.9+ with virtual environment
3. **Dependencies**: RPi.GPIO, pyserial, pygame (for calibration)
4. **GPIO Permissions**: Add user to gpio group for hardware access
5. **Serial Configuration**: Disable Pi's serial console for USB-serial availability

### Code Adaptations for Pi
- **GPIO Import**: HC-SR04 module uses RPi.GPIO (Pi-specific)
- **Serial Port**: FluidNC connection will use `/dev/ttyUSB0` or `/dev/ttyACM0`
- **Virtual Environment**: Use `python3 -m venv venv` for isolation
- **Systemd Service**: Consider creating service files for automatic startup

### Integration Architecture
```
Raspberry Pi
├── Ultrasonic Sensor (GPIO) → Presence Detection
├── USB Serial → MKS DLC32 Controller → Cat Tail Mechanism
└── Interactive Control Logic → Message Triggering
```

### Next Steps for Pi Deployment
1. Transfer codebase to Raspberry Pi
2. Install Python dependencies in virtual environment
3. Connect and test ultrasonic sensor with `test_ultrasonic.py`
4. Verify FluidNC controller connection and calibration
5. Develop interactive control logic combining sensor input with message output
6. Create installation startup scripts and service files

## Files & Documentation

### Core Production Files
- `calibrate_ouija_letters.py` - Interactive X,Y letter position calibration tool
- `test_ouija_letters.py` - Letter positioning test and validation system  
- `smooth_tail_puppeteer.py` - Advanced real-time control for development/testing
- `tail_speller.py` - **NEW**: Advanced lifelike message spelling system
- `fluidnc/` - Complete FluidNC streaming library
- `sensors/hc_sr04.py` - HC-SR04 ultrasonic sensor module with raw readings
- `test_ultrasonic.py` - Ultrasonic sensor validation and testing script
- `responses.json` - **NEW**: Mood-based message database
- `ouija_letter_positions.json` - Calibrated letter coordinate database (generated)

### Reference Documentation  
- `PROJECT_DESCRIPTION.md` - This document
- `FLUIDNC_SERIAL_STREAMING_ANALYSIS.md` - Technical communication analysis
- `SOLUTION_SUMMARY.md` - Development milestone summary

---

*MYSTICAL CAT TAIL CALIBRATED AND READY FOR OTHERWORLDLY DUTIES*

*PRECISION POSITIONING ACHIEVED*

*OUIJA ORACLE OPERATIONAL*