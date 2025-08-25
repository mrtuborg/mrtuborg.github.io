---
{"publish":true,"title":"Melexis ToF Camera C++ Software Architecture","description":"Detailed analysis of C++ software controlling Melexis MLX75027 ToF camera with TIM and LIM subsystems","created":"2025-01-10","modified":"2025-07-25T21:41:26.534+02:00","tags":["mlx75027","tof-camera","cpp-implementation","v4l2","gpio-control"],"cssclasses":""}
---


# Melexis ToF Camera C++ Software Architecture

## Overview

The C++ software controls the Melexis MLX75027 ToF camera system with two main subsystems:
- **TIM (Time-of-Flight Camera)**: MLX75027 sensor for depth measurement
- **LIM (Laser Illumination Module)**: Infrared laser diodes for active illumination

## Software Architecture

### Main Thread Function
```cpp
void* melexisThread(void* arg)
```

## TIM (Camera) Control - C++ Implementation

### 1. Device Opening and Initialization

#### Camera Device Opening:
```cpp
// Open V4L2 camera device
int fd = open("/dev/video0", O_RDWR | O_NONBLOCK);
if (fd == -1) {
    perror("Cannot open camera device");
    return -1;
}
```

#### Camera Capability Query:
```cpp
struct v4l2_capability cap;
if (ioctl(fd, VIDIOC_QUERYCAP, &cap) == -1) {
    perror("VIDIOC_QUERYCAP");
    return -1;
}

// Verify device capabilities
if (!(cap.capabilities & V4L2_CAP_VIDEO_CAPTURE)) {
    fprintf(stderr, "Device does not support video capture\n");
    return -1;
}
```

### 2. Camera Configuration

#### Format Setting:
```cpp
struct v4l2_format fmt;
memset(&fmt, 0, sizeof(fmt));
fmt.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
fmt.fmt.pix.width = 320;        // MLX75027 resolution
fmt.fmt.pix.height = 240;
fmt.fmt.pix.pixelformat = V4L2_PIX_FMT_GREY;  // 16-bit grayscale
fmt.fmt.pix.field = V4L2_FIELD_NONE;

if (ioctl(fd, VIDIOC_S_FMT, &fmt) == -1) {
    perror("VIDIOC_S_FMT");
    return -1;
}
```

#### Extended Controls (MLX75027 Specific):
```cpp
// Set integration time and modulation frequency
struct v4l2_ext_control ext_ctrl[4];
struct v4l2_ext_controls ext_ctrls;

ext_ctrl[0].id = V4L2_CID_INTEGRATION_TIME;
ext_ctrl[0].value = 1000;  // Integration time in microseconds

ext_ctrl[1].id = V4L2_CID_MODULATION_FREQ;
ext_ctrl[1].value = 20000000;  // 20MHz modulation frequency

ext_ctrl[2].id = V4L2_CID_HDR_MODE;
ext_ctrl[2].value = 0;  // Disable HDR initially

ext_ctrl[3].id = V4L2_CID_PHASE_COUNT;
ext_ctrl[3].value = 4;  // 4 phases for standard mode

ext_ctrls.ctrl_class = V4L2_CTRL_CLASS_CAMERA;
ext_ctrls.count = 4;
ext_ctrls.controls = ext_ctrl;

if (ioctl(fd, VIDIOC_S_EXT_CTRLS, &ext_ctrls) == -1) {
    perror("VIDIOC_S_EXT_CTRLS");
}
```

### 3. Buffer Management

#### Buffer Request and Mapping:
```cpp
// Request buffers
struct v4l2_requestbuffers req;
memset(&req, 0, sizeof(req));
req.count = 4;  // Number of buffers
req.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
req.memory = V4L2_MEMORY_MMAP;

if (ioctl(fd, VIDIOC_REQBUFS, &req) == -1) {
    perror("VIDIOC_REQBUFS");
    return -1;
}

// Map buffers
struct buffer {
    void *start;
    size_t length;
} *buffers;

buffers = (struct buffer*)calloc(req.count, sizeof(*buffers));

for (int i = 0; i < req.count; ++i) {
    struct v4l2_buffer buf;
    memset(&buf, 0, sizeof(buf));
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory = V4L2_MEMORY_MMAP;
    buf.index = i;

    if (ioctl(fd, VIDIOC_QUERYBUF, &buf) == -1) {
        perror("VIDIOC_QUERYBUF");
        return -1;
    }

    buffers[i].length = buf.length;
    buffers[i].start = mmap(NULL, buf.length,
                           PROT_READ | PROT_WRITE,
                           MAP_SHARED, fd, buf.m.offset);

    if (MAP_FAILED == buffers[i].start) {
        perror("mmap");
        return -1;
    }
}
```

#### Queue Buffers:
```cpp
// Queue all buffers
for (int i = 0; i < req.count; ++i) {
    struct v4l2_buffer buf;
    memset(&buf, 0, sizeof(buf));
    buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    buf.memory = V4L2_MEMORY_MMAP;
    buf.index = i;

    if (ioctl(fd, VIDIOC_QBUF, &buf) == -1) {
        perror("VIDIOC_QBUF");
        return -1;
    }
}
```

### 4. Frame Acquisition Loop

#### Start Streaming:
```cpp
enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
if (ioctl(fd, VIDIOC_STREAMON, &type) == -1) {
    perror("VIDIOC_STREAMON");
    return -1;
}
```

#### Main Acquisition Loop:
```cpp
void mlx_frame_acquisition() {
    fd_set fds;
    struct timeval tv;
    int phase_index = 0;
    int phases_per_frame = 4;  // or 8 for HDR
    
    while (!shallTerminate) {
        // Wait for frame data
        FD_ZERO(&fds);
        FD_SET(fd, &fds);
        
        tv.tv_sec = 2;  // 2 second timeout
        tv.tv_usec = 0;
        
        int r = select(fd + 1, &fds, NULL, NULL, &tv);
        
        if (r == -1) {
            if (errno == EINTR) continue;
            perror("select");
            break;
        }
        
        if (r == 0) {
            fprintf(stderr, "select timeout\n");
            continue;
        }
        
        // Dequeue buffer
        struct v4l2_buffer buf;
        memset(&buf, 0, sizeof(buf));
        buf.type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
        buf.memory = V4L2_MEMORY_MMAP;
        
        if (ioctl(fd, VIDIOC_DQBUF, &buf) == -1) {
            perror("VIDIOC_DQBUF");
            continue;
        }
        
        // Process phase data
        uint16_t* phase_data = (uint16_t*)buffers[buf.index].start;
        process_phase_data(phase_data, phase_index);
        
        // Monitor eye-safety GPIO
        monitor_eye_safety();
        
        // Requeue buffer
        if (ioctl(fd, VIDIOC_QBUF, &buf) == -1) {
            perror("VIDIOC_QBUF");
            break;
        }
        
        phase_index++;
        
        // Complete frame processing
        if (phase_index >= phases_per_frame) {
            mlx_frame();  // Process complete frame
            phase_index = 0;
        }
    }
}
```

#### Phase Data Processing:
```cpp
void process_phase_data(uint16_t* data, int phase) {
    // Extract phase information for ToF calculation
    for (int y = 0; y < 240; y++) {
        for (int x = 0; x < 320; x++) {
            int pixel_index = y * 320 + x;
            phase_buffer[phase][pixel_index] = data[pixel_index];
        }
    }
}
```

#### Complete Frame Processing:
```cpp
void mlx_frame() {
    // Calculate amplitude and distance from phases
    for (int y = 0; y < 240; y++) {
        for (int x = 0; x < 320; x++) {
            int idx = y * 320 + x;
            
            // 4-phase ToF calculation
            float I = phase_buffer[0][idx] - phase_buffer[2][idx];
            float Q = phase_buffer[1][idx] - phase_buffer[3][idx];
            
            // Amplitude calculation
            amplitude_buffer[idx] = sqrt(I*I + Q*Q);
            
            // Phase calculation
            float phase = atan2(Q, I);
            
            // Distance calculation
            float c = 299792458.0;  // Speed of light
            float freq = 20000000.0;  // Modulation frequency
            distance_buffer[idx] = (phase * c) / (4.0 * M_PI * freq);
        }
    }
    
    // Trigger callbacks with processed data
    if (amplitude_callback) {
        amplitude_callback(amplitude_buffer);
    }
    if (distance_callback) {
        distance_callback(distance_buffer);
    }
}
```

## LIM (Laser) Control - C++ Implementation

### 1. GPIO Control for Laser Enable

#### GPIO Device Opening:
```cpp
// Open GPIO for eye-safety monitoring
int gpio_fd = open("/dev/gpiochip0", O_RDWR);
if (gpio_fd < 0) {
    perror("Cannot open GPIO device");
    return -1;
}

// Alternative: Use sysfs GPIO interface
int lim_en_fd = open("/sys/class/gpio/gpio15/value", O_WRONLY);
int lim_volt_fd = open("/sys/class/gpio/gpio122/value", O_WRONLY);
```

#### Laser Enable Control:
```cpp
void enable_laser() {
    // Enable laser voltage (GPIO4_26 = 122)
    write(lim_volt_fd, "1", 1);
    
    // Enable laser (GPIO1_15 = 15)  
    write(lim_en_fd, "1", 1);
    
    printf("Laser enabled\n");
}

void disable_laser() {
    // Disable laser first
    write(lim_en_fd, "0", 1);
    
    // Then disable voltage
    write(lim_volt_fd, "0", 1);
    
    printf("Laser disabled\n");
}
```

#### Modern GPIO Control (libgpiod):
```cpp
#include <gpiod.h>

struct gpiod_chip *chip;
struct gpiod_line *lim_en_line;
struct gpiod_line *lim_volt_line;

int init_gpio() {
    chip = gpiod_chip_open_by_name("gpiochip0");
    if (!chip) {
        perror("Open chip failed");
        return -1;
    }
    
    lim_en_line = gpiod_chip_get_line(chip, 15);    // GPIO1_15
    lim_volt_line = gpiod_chip_get_line(chip, 122); // GPIO4_26
    
    if (!lim_en_line || !lim_volt_line) {
        perror("Get line failed");
        return -1;
    }
    
    // Request lines for output
    if (gpiod_line_request_output(lim_en_line, "lim_en", 0) < 0 ||
        gpiod_line_request_output(lim_volt_line, "lim_volt", 0) < 0) {
        perror("Request line as output failed");
        return -1;
    }
    
    return 0;
}

void control_laser_modern(int enable) {
    if (enable) {
        gpiod_line_set_value(lim_volt_line, 1);  // Enable voltage
        gpiod_line_set_value(lim_en_line, 1);    // Enable laser
    } else {
        gpiod_line_set_value(lim_en_line, 0);    // Disable laser
        gpiod_line_set_value(lim_volt_line, 0);  // Disable voltage
    }
}
```

### 2. Eye-Safety Monitoring

#### GPIO Monitoring:
```cpp
void monitor_eye_safety() {
    static int eye_safety_fd = -1;
    
    if (eye_safety_fd == -1) {
        eye_safety_fd = open("/sys/class/gpio/gpio28/value", O_RDONLY);
        if (eye_safety_fd < 0) {
            perror("Cannot open eye-safety GPIO");
            return;
        }
    }
    
    char value;
    lseek(eye_safety_fd, 0, SEEK_SET);
    if (read(eye_safety_fd, &value, 1) == 1) {
        if (value == '1') {
            // Eye-safety triggered - disable laser immediately
            disable_laser();
            printf("Eye-safety triggered - laser disabled\n");
        }
    }
}
```

#### Interrupt-based Eye-Safety:
```cpp
void setup_eye_safety_interrupt() {
    struct gpiod_line *safety_line;
    struct gpiod_line_event event;
    
    safety_line = gpiod_chip_get_line(chip, 28);  // GPIO5_28
    
    if (gpiod_line_request_rising_edge_events(safety_line, "eye_safety") < 0) {
        perror("Request event notification failed");
        return;
    }
    
    while (!shallTerminate) {
        if (gpiod_line_event_wait(safety_line, NULL) == 1) {
            if (gpiod_line_event_read(safety_line, &event) == 0) {
                if (event.event_type == GPIOD_LINE_EVENT_RISING_EDGE) {
                    // Emergency laser shutdown
                    disable_laser();
                    printf("Emergency: Eye-safety interrupt triggered\n");
                }
            }
        }
    }
}
```

## System Integration

### 1. Initialization Sequence

#### Complete System Startup:
```cpp
int mlx_init() {
    // 1. Initialize GPIO control
    if (init_gpio() < 0) {
        return -1;
    }
    
    // 2. Open camera device
    camera_fd = open("/dev/video0", O_RDWR | O_NONBLOCK);
    if (camera_fd < 0) {
        perror("Cannot open camera");
        return -1;
    }
    
    // 3. Configure camera
    if (configure_camera() < 0) {
        return -1;
    }
    
    // 4. Setup buffers
    if (setup_buffers() < 0) {
        return -1;
    }
    
    // 5. Enable laser (if safe)
    enable_laser();
    
    // 6. Start streaming
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    if (ioctl(camera_fd, VIDIOC_STREAMON, &type) < 0) {
        perror("Start streaming failed");
        return -1;
    }
    
    printf("MLX75027 ToF system initialized\n");
    return 0;
}
```

### 2. Cleanup and Shutdown

#### System Shutdown:
```cpp
void mlx_exit() {
    // 1. Stop streaming
    enum v4l2_buf_type type = V4L2_BUF_TYPE_VIDEO_CAPTURE;
    ioctl(camera_fd, VIDIOC_STREAMOFF, &type);
    
    // 2. Disable laser immediately
    disable_laser();
    
    // 3. Unmap buffers
    for (int i = 0; i < buffer_count; ++i) {
        munmap(buffers[i].start, buffers[i].length);
    }
    free(buffers);
    
    // 4. Close camera device
    close(camera_fd);
    
    // 5. Release GPIO resources
    if (lim_en_line) gpiod_line_release(lim_en_line);
    if (lim_volt_line) gpiod_line_release(lim_volt_line);
    if (chip) gpiod_chip_close(chip);
    
    printf("MLX75027 ToF system shutdown complete\n");
}
```

## Hardware Integration Summary

### Device Tree Integration
Based on your `imx8mp-var-som-roomboard.dts`:

```cpp
// Hardware mappings from device tree
#define TIM_ENABLE_GPIO     24  // GPIO4_24 (reg_tim_1v2mix)
#define TIM_RESET_GPIO      23  // GPIO4_23 (reg_tim_1v2)
#define LIM_EN_GPIO         15  // GPIO1_15 (lim_en)
#define LIM_VOLT_EN_GPIO    122 // GPIO4_26 (lim_volt_en)
#define EYE_SAFETY_GPIO     28  // GPIO5_28 (eye-safety interrupt)
#define USB_HUB_RST_GPIO    157 // GPIO5_29 (USB hub reset)
```

### I2C Communication
```cpp
// MLX75027 I2C communication (address 0x57)
int i2c_fd = open("/dev/i2c-3", O_RDWR);
if (ioctl(i2c_fd, I2C_SLAVE, 0x57) < 0) {
    perror("Failed to set I2C slave address");
}

// Eye-safety MCU communication (address 0x48)
int safety_i2c_fd = open("/dev/i2c-3", O_RDWR);
if (ioctl(safety_i2c_fd, I2C_SLAVE, 0x48) < 0) {
    perror("Failed to set eye-safety I2C address");
}
```

## Key C++ Strings for ToF Control

### Critical Function Calls:
1. **Device Opening**: `open("/dev/video0", O_RDWR | O_NONBLOCK)`
2. **Camera Configuration**: `ioctl(fd, VIDIOC_S_FMT, &fmt)`
3. **Extended Controls**: `ioctl(fd, VIDIOC_S_EXT_CTRLS, &ext_ctrls)`
4. **Buffer Management**: `ioctl(fd, VIDIOC_REQBUFS, &req)`
5. **Frame Acquisition**: `ioctl(fd, VIDIOC_DQBUF, &buf)`
6. **Streaming Control**: `ioctl(fd, VIDIOC_STREAMON, &type)`
7. **GPIO Control**: `gpiod_line_set_value(line, value)`
8. **Eye-Safety**: `gpiod_line_request_rising_edge_events(line, "eye_safety")`

### Hardware Control Sequence:
1. **TIM Power**: GPIO4_24 (enable) → GPIO4_23 (reset)
2. **LIM Power**: GPIO4_26 (voltage) → GPIO1_15 (enable)
3. **Safety Monitor**: GPIO5_28 (interrupt monitoring)
4. **Camera Stream**: V4L2 MIPI CSI interface
5. **Phase Processing**: 4-phase ToF calculation for depth

This architecture provides complete control over the MLX75027 ToF camera system with proper safety mechanisms and efficient data processing.
