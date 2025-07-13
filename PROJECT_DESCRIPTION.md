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

### ✅ COMPLETED: Coordinated Motion System 
The core infrastructure is complete and we now have working coordinated motion! Current capabilities:
- Precisely calibrate letter positions on any ouija board layout
- Store and recall exact coordinates for each letter
- **COMPLETED**: Coordinated X/Y motion system with proper timing
- **COMPLETED**: Time-based interpolation at 30Hz for smooth movement
- **COMPLETED**: Special tap motion for repeated letters
- **COMPLETED**: Ultrasonic sensor integration for presence detection
- **COMPLETED**: Message database with mood-based response categories
- **COMPLETED**: Raspberry Pi deployment and testing
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

### ✅ COMPLETED: Advanced Motion System (`tail_speller.py`)
Successfully implemented sophisticated parametric motion system with natural S-curve acceleration:

#### Motion Philosophy
Parametric coordinated X/Y movement with independent timing control. Y movement speed determines overall timing to ensure consistent visual effect regardless of distance.

#### Movement Architecture
**Parametric Motion Sequence:**
1. **Y-Speed Controlled Timing**: Total movement time determined by Y travel distance and speed limit
2. **X Delayed Start**: X begins movement at configurable fraction of total time (default 5%)
3. **X Early Completion**: X reaches target and holds at configurable fraction (default 80%)
4. **Y Continuous Arc**: Y completes full lift/drop sequence with smooth curves
5. **Drop Effect**: Tail drops down onto target after X movement completes

#### Technical Implementation Details
- **Parametric Curves**: Single parameter `t` (0 to 1) drives both axes with perfect synchronization
- **S-Curve Acceleration**: Configurable smoothstep function with power control for acceleration steepness
- **Dynamic Lift Height**: Height scales with X distance (min 3mm, max 8mm, configurable scale factor)
- **High-Frequency Updates**: 50-80Hz position updates for ultra-smooth motion
- **Asymmetric Timing**: Configurable lift peak timing for varied movement character
- **Unified Acceleration**: Both X and Y use identical S-curve profiles for natural feel

#### Motion Parameters
- **Y Speed Control**: 5-8 mm/s maximum Y speed (determines overall timing)
- **X Timing**: Start at 5%, finish at 80% of total movement time
- **S-Curve Power**: 1.5 (configurable steepness: 1.0 = standard, >1 = sharper)
- **Lift Asymmetry**: 0.6 (peak timing: 0.5 = center, >0.5 = late peak)
- **Dynamic Heights**: 3-8mm based on X distance with 0.5mm/mm scale factor
- **Update Rate**: 50-80Hz for smooth interpolation
- **Safety Constraints**: Y movement limited to positive values only

#### Advanced Features
- **Distance-Based Scaling**: Longer moves automatically get higher lift for visual drama
- **Tap Motion Enhancement**: Repeated letters use same S-curve system for consistency
- **Physical Safety**: Y axis constrained to prevent collision with physical obstructions
- **Timing Flexibility**: Independent control of start/finish timing for varied movement personalities

### ✅ COMPLETED: Attract Mode System (`attract_mode.py`)
Sophisticated twitch-based movement system for attracting visitor attention:

#### Attract Mode Philosophy
Creates natural cat-like micro-movements that start and end at home position. Each twitch is a single parametric curve with randomized characteristics for organic behavior.

#### Twitch Movement Architecture
**Single Parametric Twitches:**
1. **Home-Based Movement**: Every twitch starts and ends at (0,0) home position
2. **Random Peak Selection**: Each twitch targets a random peak position within safe boundaries
3. **Variable Timing**: Peak occurs at randomized time (30-70% of movement duration)
4. **Dynamic Acceleration**: Each twitch uses different S-curve steepness for varied character
5. **Safe Threading**: Clean start/stop with guaranteed return to home position

#### Technical Implementation
- **Parametric Curves**: Same system as message spelling but with 0→peak→0 profile
- **Randomized Parameters**: Peak position, timing, speed, and acceleration vary per twitch
- **Safety Constraints**: X range ±6mm, Y range 2-5mm (positive only for physical safety)
- **Thread-Safe Control**: Non-blocking start/stop with clean exit at movement completion
- **High Update Rate**: 80Hz for smooth micro-movements

#### Attract Mode Parameters
- **X Movement**: ±6mm from home position
- **Y Movement**: 2-5mm positive only (physical obstruction prevention)
- **Speed Range**: 3-8 mm/s variable per twitch
- **Timing Asymmetry**: 30-70% peak timing for varied movement character
- **S-Curve Range**: 0.8-2.0 steepness for acceleration variety
- **Inter-Twitch Pause**: 0.5-3.0 seconds random intervals

### Message Database (`responses.json`)
Response system with categorized messages for varied interactions:
- **Welcoming**: Initial friendly greetings ("HELLO", "GREETINGS", "WELCOME")
- **Cryptic**: Mysterious oracle responses ("PERHAPS", "WHO KNOWS", "UNCLEAR")
- **Sleepy**: Tired, dismissive messages ("DROWSY", "LATER", "QUIET")
- **Dismissive**: Direct dismissal for overstayers ("GO AWAY", "ENOUGH", "BEGONE")

#### Message Selection Strategy
- **Random Selection**: Messages chosen randomly from database with anti-repetition tracking
- **Simplified Approach**: No complex mood progression - focuses on core interactive experience
- **Extensible Design**: Database structure supports future mood system if desired

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

### ✅ COMPLETED: Main Controller Integration
**The complete interactive experience is now fully operational!**

#### System Architecture
**Main Control Loop (`main_controller.py`):**
```
Monitor Sensor → Detect Presence → Start Attract Mode → Confirm Presence → 
Stop Attract Mode → Dramatic Pause → Select Message → Spell Message → 
Exhausted Return → Post-Message Pause → Return to Monitor
```

#### Completed Features
1. **✅ Complete Integration** 
   - Main controller with 5Hz sensor monitoring loop
   - Presence detection with configurable threshold (36 inches)
   - Seamless attract mode → message spelling pipeline
   - Tested complete sensor → attract → spell → repeat cycle

2. **✅ Advanced Message Management** 
   - Random message selection from response database
   - Anti-repetition tracking (last 5 messages avoided)
   - Configurable timing parameters for all interactions
   - Mood-based message categories (neutral, irritated)

3. **✅ Production-Ready Robustness** 
   - Comprehensive error handling and FluidNC reconnection logic
   - Error-only logging system for debugging
   - Auto-start systemd service for autonomous operation
   - Graceful shutdown and GPIO cleanup

#### Refined Control Flow
- **Presence Detection**: 8-second confirmation before triggering message
- **Attract Mode**: Natural cat-like twitching with smooth completion
- **Dramatic Pause**: 2.5-second anticipation period after attract mode
- **Message Spelling**: Precise letter-by-letter spelling with dynamic lift heights
- **Exhausted Return**: Special deceleration motion showing spirit fatigue
- **Anti-Repetition**: Tracks last 5 messages to ensure variety
- **Movement Buffer**: 1-second buffer prevents jerky state transitions

## Raspberry Pi Deployment

### ✅ READY FOR DEPLOYMENT
The project is now ready for deployment on Raspberry Pi hardware. All core systems have been developed and tested, with only the main controller integration remaining.

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
- `main_controller.py` - **COMPLETED**: Central orchestration system with full interactive control
- `tail_speller.py` - **COMPLETED**: Advanced parametric motion system with exhausted return home
- `attract_mode.py` - **COMPLETED**: Sophisticated twitch-based attract mode with smooth transitions
- `calibrate_ouija_letters.py` - Interactive X,Y letter position calibration tool
- `test_ouija_letters.py` - Letter positioning test and validation system  
- `smooth_tail_puppeteer.py` - Advanced real-time control for development/testing
- `fluidnc/` - Complete FluidNC streaming library with robust error handling
- `sensors/hc_sr04.py` - HC-SR04 ultrasonic sensor module with thread-safe operation
- `test_ultrasonic.py` - Ultrasonic sensor validation and testing script
- `responses.json` - Categorized message database with anti-repetition support
- `ouija_letter_positions.json` - Calibrated letter coordinate database

### Auto-Start Configuration
- `cat-butt-oracle.service` - **COMPLETED**: Systemd service for autonomous operation
- `setup_autostart.sh` - **COMPLETED**: Installation script for auto-start on boot

### Reference Documentation  
- `PROJECT_DESCRIPTION.md` - This document
- `FLUIDNC_SERIAL_STREAMING_ANALYSIS.md` - Technical communication analysis
- `SOLUTION_SUMMARY.md` - Development milestone summary

---

## 🎭 **MYSTICAL CAT BUTT ORACLE - FULLY OPERATIONAL** 🎭

**✨ INTERACTIVE ART INSTALLATION COMPLETE ✨**

The mystical feline spirit is now ready to commune with visitors through precise tail movements, offering cryptic messages and otherworldly wisdom. The oracle awakens automatically on boot, ready to detect approaching souls and share its ancient knowledge through the sacred ouija board.

*PRECISION POSITIONING ACHIEVED*  
*AUTONOMOUS OPERATION ENABLED*  
*MYSTICAL COMMUNICATION ACTIVATED*

**🔮 THE ORACLE AWAITS... 🔮**