# Cat Butt - Interactive Ouija Board Art Installation

## Project Overview
An interactive art installation featuring a mechanical cat tail that spells out cryptic messages on a custom ouija board. The piece explores the human experience of deciphering cat behavior and body language, presenting it as a mystical communication from beyond.

## Concept & User Experience
The installation presents cat tail movements as an oracle or contacted spirit, offering vague knowledge that visitors must interpret. This mirrors how humans constantly attempt to decode cat tail language in real life - usually to avoid getting scratched. The tail acts as a ouija board planchette, moving across letters to spell out short, cryptic responses in classic ouija style.

## Technical Specifications

### Hardware
- **Controller**: MKS DLC32 board running FluidNC firmware
- **Mechanism**: Mechanical cat tail built with tentacle-like articulation
- **Surface**: Custom ouija board with letters/symbols for tail to indicate
- **Connection**: USB serial connection (CH340 chip) at 115200 baud

### Movement System
- **X-axis**: Left-right movement (positive to negative range)
- **Y-axis**: Vertical curl from laying flat to upward curl (positive range only)
- **Configuration**: Effectively 1.5-axis system due to Y-axis constraint
- **Starting Position**: Tail laying flat on ground

### Interaction Design
- Tail spells out words by moving to letters on the ouija board
- Responses are short (typically 1-3 words), cryptic, and sometimes seemingly unrelated
- Mimics classic ouija board communication style - ambiguous and requiring interpretation
- Cat personality: aloof, detached, occasionally sharing mystical knowledge

## Character Persona
The "spirit" contacted through this ouija board is a cat with typical feline personality traits:
- Detached and aloof demeanor
- Reluctant to share knowledge directly
- Responses often seem to address different questions than asked
- Occasionally provides clear answers (especially for names)
- Names tend to be embarrassingly cute (like "Dr. Mittens")
- Classic cat behaviors: doesn't want pets, admits to scratching/biting

## Development Status

### ✅ COMPLETED
- **Hardware**: Prototype tail mechanism built and operational
- **Controller**: MKS DLC32 with FluidNC firmware configured and tested
- **Software**: Complete FluidNC Python streaming library implemented and debugged
- **Communication**: All serial connection issues resolved (CH340 driver + line ending fixes)
- **Testing**: Full integration testing completed successfully
- **Debugging**: Comprehensive diagnostic and troubleshooting framework developed
- **Puppeteering Interface**: Real-time mouse-controlled testing applications built and optimized
- **Motion Validation**: Tail mechanism tested extensively with expanded coordinate ranges (-30 to 30, 0 to 30)
- **Responsiveness Optimization**: Advanced buffer management and command throttling implemented

### 🔧 CURRENT PHASE
- **Ouija Board Implementation**: Transitioning from puppeteering to ouija board letter positioning
- **Coordinate Mapping**: Defining letter positions and movement patterns for mystical communication
- **Cat Personality System**: Implementing AI-driven responses with feline characteristics

### 📋 NEXT STEPS
- Ouija board letter coordinate mapping and calibration
- Response database with cat-appropriate mystical messages
- Message spelling algorithms and smooth letter-to-letter movement
- Installation integration and final performance tuning

## Software Architecture

### FluidNC Streaming Module
**Location**: `/fluidnc/` directory

**Core Components**:
- `streamer.py` - Main streaming interface with basic line-by-line G-code sending
- `advanced_streamer.py` - Advanced buffered streaming with throughput optimization
- `connection.py` - Low-level serial communication with timeout protection and macOS compatibility
- `status.py` - FluidNC status report parsing and representation
- `exceptions.py` - Custom exception handling for streaming errors
- `utils.py` - Utility functions for G-code processing

**Key Features**:
- Automatic FluidNC port detection with CH340 chip support
- Robust timeout handling prevents system freezing
- Real-time status monitoring with background threads
- Both simple and advanced streaming modes
- Comprehensive error handling and recovery
- Debug logging for development and troubleshooting
- **Compatibility Fix**: Handles FluidNC's unique line ending requirements (`\n` vs `\r\n`)

### Testing & Development Tools
**Location**: `/archive/` directory

Complete suite of debugging and diagnostic tools developed during troubleshooting:
- Serial communication diagnostics
- CH340 driver compatibility tools
- Command tracing and protocol analysis
- Connection failure diagnosis tools
- Port testing utilities

## Technical Challenges Solved

### 1. CH340 USB-Serial Driver Issues (macOS)
**Problem**: Hard system freezing when attempting serial connections
**Solution**: Implemented macOS built-in driver activation sequence
**Impact**: Eliminated system hangs, enabled reliable connections

### 2. FluidNC Protocol Compatibility
**Problem**: FluidNC interprets `\r\n` as two separate commands, causing multiple 'ok' responses
**Solution**: Modified all line endings from `\r\n` to `\n` throughout the module
**Impact**: Proper single-response communication, standard GRBL-like behavior restored

### 3. Connection Timeout Management
**Problem**: Potential for indefinite hangs during communication
**Solution**: Comprehensive timeout handling with graceful degradation
**Impact**: Robust, production-ready communication stack

## Ready for Production

The technical foundation is now complete and thoroughly tested. The system reliably:
- Connects to FluidNC controllers automatically
- Handles communication errors gracefully
- Provides both simple and advanced streaming modes
- Supports real-time status monitoring
- Maintains stable connections during operation

## Real-Time Puppeteering System

### Overview
Advanced real-time control applications for testing and exploring the tail mechanism's capabilities through direct mouse control. Essential for understanding movement limits and calibrating positioning before implementing ouija board functionality.

### Puppeteering Applications

#### `tail_puppeteer.py` - Basic Real-Time Control
**Purpose**: Simple, reliable mouse-controlled tail positioning for basic testing and calibration.

**Features**:
- Direct mouse-to-tail coordinate mapping
- Real-time G-code streaming via FluidNCConnection
- Visual feedback with position indicators
- Basic rate limiting and movement thresholds
- Intuitive Y-axis mapping (zero at 1/3 from bottom of screen)

**Usage**: `./tail_puppeteer.py [-p PORT] [-b BAUDRATE]`

#### `smooth_tail_puppeteer.py` - Advanced Responsive Control
**Purpose**: High-performance real-time control with sophisticated buffer management and responsiveness optimization.

**Features**:
- **Advanced Buffer Management**: Character counting and RX buffer tracking to prevent command overflow
- **Responsive Control**: Direct mouse-to-target mapping with minimal latency (no interpolation lag)
- **Smart Command Throttling**: 60Hz command rate with intelligent movement filtering
- **Adaptive Feed Rates**: 2000-6000 mm/min based on movement distance for optimal responsiveness
- **Real-Time Status Monitoring**: Live controller position feedback and buffer visualization
- **Enhanced Visual Interface**: Multi-indicator display showing target vs actual positions

**Technical Achievements**:
- Eliminated command queue buildup that caused lag
- Solved the "smoothness vs responsiveness" challenge by focusing on immediate response
- Advanced acknowledgment processing for optimal buffer utilization
- Expanded coordinate range testing (-30 to 30, 0 to 30) validating mechanism capabilities

**Usage**: `./smooth_tail_puppeteer.py [-p PORT] [-b BAUDRATE]`

### Key Learnings from Puppeteering Phase
1. **Mechanism Validation**: Tail performs reliably across expanded coordinate ranges
2. **Responsiveness Requirements**: Direct mapping preferred over interpolated smoothness for control feel
3. **Buffer Management**: Critical for preventing command buildup and maintaining real-time performance
4. **Coordinate System**: Y-axis zero positioning at 1/3 screen height provides intuitive control
5. **Performance Optimization**: Command throttling and adaptive feed rates enable smooth, responsive control

Next phase focuses on transitioning from exploratory puppeteering to structured ouija board letter positioning and mystical cat personality implementation.

---

*TECHNICAL SPIRITS SUCCESSFULLY BANISHED*

*COMMUNICATION CHANNELS PURIFIED*

*PUPPETEERING MASTERY ACHIEVED*

*MYSTICAL CAT TAIL READY FOR OTHERWORLDLY DUTIES*

## Files & Documentation

### Core Project Files
- `PROJECT_DESCRIPTION.md` - This document
- `test_fluidnc.py` - Main testing script for the FluidNC module
- `tail_puppeteer.py` - Basic real-time mouse-controlled tail positioning
- `smooth_tail_puppeteer.py` - Advanced responsive puppeteering with buffer management
- `setup.py` - Python package configuration
- `fluidnc/` - Complete FluidNC streaming library

### Reference Documentation
- `FLUIDNC_SERIAL_STREAMING_ANALYSIS.md` - Original technical analysis
- `RECOMMENDED_FLUIDNC_IMPROVEMENTS.md` - Suggested enhancements
- `archive/` - All debugging tools and diagnostic scripts (preserved for reference)