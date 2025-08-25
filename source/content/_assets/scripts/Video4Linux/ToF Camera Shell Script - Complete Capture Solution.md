---
{"publish":true,"title":"ToF Camera Shell Script - Complete Capture Solution","description":"Complete documentation for tof_capture.sh - automated ToF camera frame capture with TIM/LIM control","created":"2025-01-10","modified":"2025-07-25T21:41:26.536+02:00","tags":["tof-capture","bash-script","mlx75027","v4l2","gpio-control","ffmpeg"],"cssclasses":""}
---


# ToF Camera Shell Script - Complete Capture Solution

## Overview

The `tof_capture.sh` script provides a complete automated solution for capturing frames from the Melexis MLX75027 ToF camera system. It handles both hardware control (TIM/LIM subsystems) and frame capture using FFmpeg, making it easy to integrate ToF imaging into embedded applications.

## Script Architecture

### Core Components
- **Hardware Control**: TIM (camera) and LIM (laser) GPIO management
- **Frame Capture**: FFmpeg-based V4L2 video capture
- **Safety Systems**: Eye-safety monitoring and clean shutdown
- **Error Handling**: Comprehensive validation and recovery
- **User Interface**: Colored output and progress indicators

## Hardware Integration

### TIM (Time-of-Flight Camera) Control

#### Initialization Sequence:
```bash
# Primary method - uses fixed GPIO scripts
./TIM_EN_fixed.sh -t

# Fallback method - direct GPIO control
gpioset gpiochip3 24=1 23=1  # GPIO4_24 (enable), GPIO4_23 (reset)
```

#### Hardware Mapping:
- **GPIO4_24**: TIM enable signal (`reg_tim_1v2mix` in device tree)
- **GPIO4_23**: TIM reset/power signal (`reg_tim_1v2` in device tree)
- **Device**: `/dev/video0` (V4L2 MIPI CSI interface)

### LIM (Laser Illumination Module) Control

#### Initialization Sequence:
```bash
# Primary method - uses fixed GPIO scripts
./LIM_EN_fixed.sh

# Fallback method - direct GPIO control
gpioset gpiochip3 26=1      # GPIO4_26 (laser voltage)
sleep 0.1
gpioset gpiochip0 15=1      # GPIO1_15 (laser enable)
```

#### Hardware Mapping:
- **GPIO4_26**: LIM voltage enable (`lim_volt_en` in device tree)
- **GPIO1_15**: LIM laser enable (`lim_en` in device tree)
- **Safety**: Eye-safety GPIO monitoring during operation

## FFmpeg Integration

### Core Capture Command

The script uses FFmpeg with V4L2 input for frame capture:

```bash
ffmpeg -y \
    -f v4l2 \
    -input_format gray \
    -video_size 320x240 \
    -i /dev/video0 \
    -frames:v 1 \
    -q:v $((100 - JPEG_QUALITY)) \
    -pix_fmt gray \
    output.jpg \
    -loglevel error
```

### FFmpeg Parameters Explained

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `-f v4l2` | Video4Linux2 | Input format for Linux camera devices |
| `-input_format gray` | Grayscale | MLX75027 outputs 16-bit grayscale data |
| `-video_size 320x240` | Resolution | Native MLX75027 resolution |
| `-i /dev/video0` | Device | Camera device path |
| `-frames:v 1` | Single frame | Capture one frame per call |
| `-q:v` | Quality | JPEG quality (lower = better quality) |
| `-pix_fmt gray` | Pixel format | Output grayscale JPEG |
| `-loglevel error` | Logging | Suppress verbose output |

### Capture Modes

#### 1. Single Frame Capture
```bash
./tof_capture.sh -s
# Captures one frame and exits
```

#### 2. Multiple Frame Capture
```bash
./tof_capture.sh -n 20 -r 5
# Captures 20 frames at 5fps with progress indicator
```

#### 3. Continuous Capture
```bash
./tof_capture.sh -c -r 2
# Continuous capture at 2fps until Ctrl+C
```

#### 4. Test Mode
```bash
./tof_capture.sh -t
# Tests hardware without actual capture
```

## Script Usage

### Command Line Options

```bash
Usage: ./tof_capture.sh [OPTIONS]

OPTIONS:
    -d DEVICE       Camera device (default: /dev/video0)
    -o OUTPUT_DIR   Output directory (default: ./tof_captures)
    -n COUNT        Number of frames to capture (default: 10)
    -r RATE         Frame rate (default: 5)
    -q QUALITY      JPEG quality 1-100 (default: 95)
    -s              Single frame capture mode
    -c              Continuous capture mode (Ctrl+C to stop)
    -t              Test mode (no actual capture)
    -h              Show help
```

### Usage Examples

#### Basic Operations:
```bash
# Default capture (10 frames at 5fps)
./tof_capture.sh

# Single high-quality frame
./tof_capture.sh -s -q 98

# Fast continuous capture
./tof_capture.sh -c -r 10

# Custom output location
./tof_capture.sh -o /tmp/tof_data -n 50
```

#### Advanced Usage:
```bash
# Low-quality rapid capture for testing
./tof_capture.sh -n 100 -r 15 -q 70

# Single frame with custom device
./tof_capture.sh -s -d /dev/video1

# Test hardware without capture
./tof_capture.sh -t
```

## Output Format

### File Naming Convention
```
tof_frame_YYYYMMDD_HHMMSS_NNNN.jpg
```

**Example**: `tof_frame_20250110_143052_0001.jpg`

- **YYYYMMDD**: Date (Year-Month-Day)
- **HHMMSS**: Time (Hour-Minute-Second)
- **NNNN**: Frame number (zero-padded, 4 digits)

### File Properties
- **Format**: JPEG grayscale
- **Resolution**: 320x240 pixels
- **Bit Depth**: 8-bit (converted from 16-bit sensor data)
- **Typical Size**: 8-15 KB per frame (depending on quality setting)

## Script Workflow

### 1. Initialization Phase
```bash
[TOF] === ToF Camera Capture Script ===
[INFO] Camera: /dev/video0
[INFO] Output: ./tof_captures
[INFO] Frames: 10 at 5fps
[INFO] Quality: 95%
```

### 2. Hardware Check Phase
```bash
[TOF] Checking ToF Camera Hardware...
[INFO] Checking V4L2 capabilities...
[INFO] Supported formats:
[INFO] Hardware check completed
```

### 3. Hardware Initialization
```bash
[TOF] Initializing TIM (Camera)...
[INFO] Enabling TIM using ./TIM_EN_fixed.sh
[INFO] TIM initialization completed

[TOF] Initializing LIM (Laser)...
[INFO] Enabling LIM using ./LIM_EN_fixed.sh
[INFO] LIM initialization completed
```

### 4. Capture Phase
```bash
[TOF] Capturing 10 frames at 5fps...
[INFO] Capturing frame 1 to ./tof_captures/tof_frame_20250110_143052_0001.jpg
[INFO] Frame 1 captured successfully (12847 bytes)
Progress: [====                ] 20% (2/10)
```

### 5. Shutdown Phase
```bash
[TOF] Shutting down ToF hardware...
[INFO] Disabling LIM using ./LIM_EN_fixed.sh
[INFO] Disabling TIM using ./TIM_EN_fixed.sh
[INFO] Hardware shutdown completed

[TOF] === ToF Capture Completed Successfully ===
[INFO] Captured frames saved to: ./tof_captures
```

## Error Handling

### Common Issues and Solutions

#### 1. Camera Device Not Found
```bash
[ERROR] Camera device /dev/video0 not found
```
**Solution**: Check if camera driver is loaded and device exists

#### 2. Permission Denied
```bash
[ERROR] Cannot access /dev/video0 (check permissions)
```
**Solution**: Add user to `video` group or run with appropriate permissions

#### 3. GPIO Control Failed
```bash
[WARN] TIM control script not found or not executable
[INFO] Attempting manual TIM enable...
```
**Solution**: Ensure GPIO control scripts are present and executable

#### 4. FFmpeg Capture Failed
```bash
[ERROR] Failed to capture frame 1
```
**Solution**: Check camera format compatibility and V4L2 driver status

#### 5. Output Directory Issues
```bash
[ERROR] Failed to create output directory: ./tof_captures
```
**Solution**: Check filesystem permissions and available disk space

## Dependencies and Installation

### Required Packages for Yocto Linux

Add to your image recipe's `IMAGE_INSTALL`:

```bash
IMAGE_INSTALL += "ffmpeg v4l-utils libgpiod libgpiod-tools bc coreutils"
```

### Package Details

| Package | Purpose | Commands Provided |
|---------|---------|-------------------|
| `ffmpeg` | Video capture and encoding | `ffmpeg` |
| `v4l-utils` | V4L2 device management | `v4l2-ctl` |
| `libgpiod` | Modern GPIO control library | - |
| `libgpiod-tools` | GPIO command-line tools | `gpioset`, `gpioget`, `gpioinfo` |
| `bc` | Mathematical calculations | `bc` (for frame rate timing) |
| `coreutils` | Basic utilities | `stat`, `date`, `printf` |

### Optional Packages

```bash
IMAGE_INSTALL += "gstreamer1.0 gstreamer1.0-plugins-base"
```
For alternative video capture methods using GStreamer.

## Performance Considerations

### Frame Rate Limitations

| Frame Rate | Use Case | CPU Usage | Storage Rate |
|------------|----------|-----------|--------------|
| 1-5 fps | Normal operation | Low | ~50-150 KB/s |
| 5-10 fps | Fast capture | Medium | ~150-300 KB/s |
| 10-15 fps | High-speed capture | High | ~300-450 KB/s |
| 15+ fps | Maximum rate | Very High | ~450+ KB/s |

### Storage Requirements

**Per Frame**: 8-15 KB (depending on quality)
**Per Hour**: 
- 5 fps: ~650 MB
- 10 fps: ~1.3 GB
- 15 fps: ~1.9 GB

### Memory Usage

- **Script overhead**: ~2-5 MB
- **FFmpeg buffer**: ~10-20 MB
- **GPIO operations**: <1 MB

## Integration Examples

### Systemd Service Integration

Create `/etc/systemd/system/tof-capture.service`:

```ini
[Unit]
Description=ToF Camera Capture Service
After=multi-user.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/tof
ExecStart=/opt/tof/tof_capture.sh -c -r 2 -o /var/log/tof
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Cron Job for Periodic Capture

```bash
# Capture single frame every minute
* * * * * /opt/tof/tof_capture.sh -s -o /var/log/tof/$(date +\%Y\%m\%d)

# Capture 10 frames every hour
0 * * * * /opt/tof/tof_capture.sh -n 10 -o /var/log/tof/hourly
```

### Application Integration

```bash
#!/bin/bash
# Example application wrapper

# Capture frames for analysis
./tof_capture.sh -n 5 -q 90 -o /tmp/analysis

# Process captured frames
for frame in /tmp/analysis/*.jpg; do
    # Your image processing here
    echo "Processing: $frame"
done

# Cleanup
rm -rf /tmp/analysis
```

## Troubleshooting Guide

### Debug Mode

Enable verbose output by modifying the script:

```bash
# Add at the top of the script
set -x  # Enable debug mode
```

### Manual Hardware Testing

```bash
# Test TIM manually
gpioinfo | grep -E "(gpio-24|gpio-23)"
gpioset gpiochip3 24=1 23=1

# Test LIM manually  
gpioinfo | grep -E "(gpio-15|gpio-26)"
gpioset gpiochip0 15=1
gpioset gpiochip3 26=1

# Test camera device
v4l2-ctl -d /dev/video0 --info
v4l2-ctl -d /dev/video0 --list-formats-ext
```

### FFmpeg Debug

```bash
# Test FFmpeg capture manually
ffmpeg -f v4l2 -list_formats all -i /dev/video0
ffmpeg -f v4l2 -i /dev/video0 -t 5 -f null -
```

## Security Considerations

### GPIO Access Control

- Script requires root privileges for GPIO control
- Consider using `sudo` with specific permissions
- GPIO operations are hardware-level and require careful handling

### File System Permissions

```bash
# Recommended permissions
chmod 755 tof_capture.sh
chmod 755 TIM_EN_fixed.sh LIM_EN_fixed.sh
chown root:video tof_capture.sh
```

### Eye-Safety Compliance

- Script includes automatic laser shutdown on interrupt
- Eye-safety GPIO monitoring during operation
- Proper laser disable sequence on exit

## Summary

The `tof_capture.sh` script provides a comprehensive solution for ToF camera operation:

### Key Benefits
- **Complete Hardware Control**: Automated TIM/LIM GPIO management
- **Flexible Capture Modes**: Single, multiple, continuous, and test modes
- **Safety First**: Eye-safety monitoring and clean shutdown procedures
- **Error Recovery**: Comprehensive error handling and fallback mechanisms
- **Easy Integration**: Simple command-line interface with extensive options

### Use Cases
- **Development and Testing**: Quick frame capture for algorithm development
- **Production Systems**: Automated ToF data collection
- **Quality Assurance**: Hardware validation and testing
- **Research Applications**: Data collection for ToF analysis

### Related Files
- `TIM_EN_fixed.sh`: TIM (camera) GPIO control script
- `LIM_EN_fixed.sh`: LIM (laser) GPIO control script
- `tof_capture.sh`: Main capture script (this documentation)

This script bridges the gap between low-level hardware control and high-level application requirements, making ToF camera integration straightforward and reliable.
