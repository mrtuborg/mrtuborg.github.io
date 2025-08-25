---
{"publish":true,"title":"Configuring Melexis 75027 ToF Camera: From MIPI CSI Setup to JPEG Capture","description":"Complete guide for configuring Melexis 75027 ToF camera module with laser infra LEDs on Yocto Linux, from initial MIPI CSI setup to capturing JPEG frames","created":"2025-01-10","modified":"2025-07-25T21:41:26.535+02:00","tags":["v4l2","mipi-csi","tof","melexis-75027","laser-safety","embedded","yocto"],"cssclasses":""}
---


# Configuring Melexis 75027 ToF Camera: From MIPI CSI Setup to JPEG Capture

This guide covers the complete process of configuring a Melexis 75027 Time of Flight (ToF) camera module on an embedded Yocto Linux system, including laser infra LED initialization, MIPI CSI configuration, and capturing frames as JPEG files. The Melexis 75027 is a sophisticated ToF sensor that requires careful configuration of both the imaging pipeline and safety systems.

## Understanding the Melexis 75027 ToF System

The Melexis 75027 ToF camera system consists of several key components:

- **ToF Sensor**: Captures phase-shifted infrared light for distance measurement
- **Laser Infra LEDs**: Provide structured infrared illumination
- **MIPI CSI Interface**: High-speed data transmission to the host processor
- **Safety Systems**: Eye-safety monitoring and laser control
- **Multi-phase Capture**: 4-8 phases per frame for HDR and distance calculation

### Key Differences from Standard RGB Cameras

Unlike standard RGB cameras, ToF systems require:
- Laser illumination control and safety monitoring
- Multi-phase frame capture (4 or 8 phases per complete frame)
- Specialized processing for amplitude and distance data
- Real-time safety monitoring via GPIO
- Precise timing coordination between laser pulses and sensor capture

## Initial System Requirements

### Kernel Configuration Analysis

Based on our actual kernel configuration, here are the essential settings for ToF camera operation with detailed explanations:

#### Core Video4Linux2 and Media Framework
```bash
# Video4Linux2 Core Support - ENABLED in your config
CONFIG_VIDEO_V4L2=y                    # ✓ Core V4L2 framework
CONFIG_VIDEO_V4L2_SUBDEV_API=y         # ✓ Subdevice API for sensor control
CONFIG_MEDIA_CONTROLLER=y              # ✓ Media controller framework
CONFIG_VIDEO_DEV=y                     # ✓ Video device support
CONFIG_MEDIA_CAMERA_SUPPORT=y          # ✓ Camera support
CONFIG_MEDIA_CONTROLLER_REQUEST_API=y  # ✓ Request API for synchronized control

# Why these are needed:
# - VIDEO_V4L2: Core framework for all video operations
# - VIDEO_V4L2_SUBDEV_API: Allows direct control of camera sensors
# - MEDIA_CONTROLLER: Essential for complex camera pipelines
# - MEDIA_CONTROLLER_REQUEST_API: Enables synchronized multi-phase capture
```

#### i.MX8M Plus Specific Video Support
```bash
# Staging Media Support - ENABLED in your config
CONFIG_STAGING_MEDIA=y                 # ✓ Required for i.MX8M Plus drivers
CONFIG_VIDEO_IMX_CAPTURE=y             # ✓ i.MX capture framework
CONFIG_IMX8_MIPI_CSI2=y                # ✓ MIPI CSI-2 receiver
CONFIG_IMX8_MIPI_CSI2_SAM=y            # ✓ MIPI CSI-2 with SAM support
CONFIG_IMX8_ISI_HW=y                   # ✓ ISI hardware support
CONFIG_IMX8_ISI_CORE=y                 # ✓ ISI core driver
CONFIG_IMX8_ISI_CAPTURE=y              # ✓ ISI capture interface
CONFIG_IMX8_ISI_M2M=y                  # ✓ ISI memory-to-memory
CONFIG_IMX8_MEDIA_DEVICE=y             # ✓ i.MX8 media device framework

# Why these are critical:
# - STAGING_MEDIA: i.MX8M Plus video drivers are in staging
# - IMX8_MIPI_CSI2: Handles MIPI CSI-2 protocol for ToF sensor
# - IMX8_ISI_*: Image Sensing Interface - processes raw sensor data
# - IMX8_MEDIA_DEVICE: Coordinates complex video pipelines
```

#### Buffer Management and Memory
```bash
# Video Buffer Management - ENABLED in your config
CONFIG_VIDEOBUF2_CORE=y                # ✓ Core video buffer framework
CONFIG_VIDEOBUF2_V4L2=y                # ✓ V4L2 buffer integration
CONFIG_VIDEOBUF2_DMA_CONTIG=y          # ✓ Contiguous DMA buffers
CONFIG_VIDEOBUF2_VMALLOC=y             # ✓ Virtual memory buffers
CONFIG_VIDEOBUF2_DMA_SG=y              # ✓ Scatter-gather DMA buffers

# Memory Management - CONFIGURED in your config
CONFIG_CMA=y                           # ✓ Contiguous Memory Allocator
CONFIG_CMA_SIZE_MBYTES=32              # ⚠ Your setting (recommend 128MB for ToF)
CONFIG_DMA_CMA=y                       # ✓ DMA with CMA support

# Why buffer management matters:
# - VIDEOBUF2_DMA_CONTIG: ToF needs large contiguous buffers for multi-phase data
# - CMA: Ensures large memory blocks available for video capture
# - Your CMA size (32MB) may be insufficient for high-resolution ToF capture
# - Recommendation: Increase to 128MB for optimal ToF performance
```

#### GPIO and I2C Support
```bash
# GPIO Support - ENABLED in your config
CONFIG_GPIOLIB=y                       # ✓ GPIO library support
CONFIG_GPIO_CDEV=y                     # ✓ GPIO character device interface
CONFIG_GPIO_CDEV_V1=y                  # ✓ Legacy GPIO interface
CONFIG_GPIO_GENERIC=y                  # ✓ Generic GPIO driver
CONFIG_GPIO_MXC=y                      # ✓ i.MX GPIO controller
CONFIG_GPIO_SCU=y                      # ✓ i.MX SCU GPIO support

# I2C Support - ENABLED in your config
CONFIG_I2C=y                           # ✓ I2C bus support
CONFIG_I2C_CHARDEV=y                   # ✓ I2C character device interface
CONFIG_I2C_MUX=y                       # ✓ I2C multiplexer support
CONFIG_I2C_IMX=y                       # ✓ i.MX I2C controller
CONFIG_I2C_IMX_LPI2C=y                 # ✓ i.MX Low Power I2C

# Why these are essential:
# - GPIO_CDEV: Allows userspace control of laser enable/disable
# - I2C_CHARDEV: Enables i2c-tools for safety system communication
# - GPIO_MXC/I2C_IMX: Platform-specific drivers for i.MX8M Plus
```

#### Sensor and Camera Drivers
```bash
# Camera Sensor Support - PARTIALLY ENABLED in your config
CONFIG_VIDEO_OV5640=y                  # ✓ OV5640 sensor (example)
CONFIG_VIDEO_MLX7502X=y                # ✓ Melexis ToF sensor driver
CONFIG_MXC_CAMERA_OV5640_MIPI_V2=y     # ✓ i.MX OV5640 integration

# Missing ToF-specific configurations (ADD THESE):
# CONFIG_VIDEO_MLX75027=m              # ⚠ Melexis 75027 specific driver
# CONFIG_VIDEO_MLX_TOF=y               # ⚠ Generic Melexis ToF support

# Why sensor drivers matter:
# - VIDEO_MLX7502X: Your current ToF sensor driver
# - Missing MLX75027: May need specific driver for full functionality
# - These drivers handle sensor initialization and control
```

#### Performance and Real-Time Features
```bash
# Preemption and Real-Time - CONFIGURED in your config
CONFIG_PREEMPT=y                       # ✓ Preemptible kernel
CONFIG_PREEMPT_COUNT=y                 # ✓ Preemption counting
CONFIG_PREEMPTION=y                    # ✓ Preemption support
CONFIG_HIGH_RES_TIMERS=y               # ✓ High resolution timers
CONFIG_NO_HZ_IDLE=y                    # ✓ Tickless idle

# CPU Frequency Scaling - ENABLED in your config
CONFIG_CPU_FREQ=y                      # ✓ CPU frequency scaling
CONFIG_CPU_FREQ_DEFAULT_GOV_ONDEMAND=y # ✓ Default governor
CONFIG_CPU_FREQ_GOV_PERFORMANCE=y      # ✓ Performance governor available

# Why real-time features help ToF:
# - PREEMPT: Reduces latency for time-critical ToF operations
# - HIGH_RES_

### Required Userspace Tools

Install these tools in your Yocto image:

```bash
# Add to your image recipe
IMAGE_INSTALL += "v4l-utils media-ctl gstreamer1.0 gstreamer1.0-plugins-good"
IMAGE_INSTALL += "libjpeg-turbo libjpeg-turbo-utils"
```

## Device Tree Configuration

### MIPI CSI and ToF Sensor Configuration

Based on our actual device tree configuration:

```dts
// Device tree configuration for Melexis 75027 on i.MX8M Plus Variscite SOM
// This matches your actual imx8mp-var-som-roomboard.dts configuration

&mipi_csi_0 {
    #address-cells = <1>;
    #size-cells = <0>;
    status = "okay";

    port@0 {
        reg = <0>;
        mipi_csi0_ep: endpoint {
            remote-endpoint = <&mlx7502x_mipi0_ep>;
            data-lanes = <4>;                      // 4-lane MIPI as per your DTS
            csis-hs-settle = <13>;
            csis-clk-settle = <2>;
            csis-wclk;
        };
    };
};

&isi_0 {
    status = "okay";

    cap_device {
        status = "okay";
    };

    m2m_device {
        status = "okay";
    };
};

&i2c3 {
    clock-frequency = <400000>;
    pinctrl-names = "default", "gpio";
    pinctrl-0 = <&pinctrl_i2c3>;
    pinctrl-1 = <&pinctrl_i2c3_gpio>;
    scl-gpios = <&gpio5 18 GPIO_ACTIVE_HIGH>;
    sda-gpios = <&gpio5 19 GPIO_ACTIVE_HIGH>;
    status = "okay";

    mlx7502x_mipi1: mlx7502x_mipi@57 {
        compatible = "melexis,mlx75027";
        reg = <0x57>;                              // Actual I2C address from your DTS
        pinctrl-names = "default";
        pinctrl-0 = <&pinctrl_csi0>;
        clocks = <&mlx7502x_clk>;

        assigned-clocks = <&mlx7502x_clk>;
        assigned-clock-rates = <8000000>;          // 8MHz clock as per your DTS

        // Power supplies as defined in your DTS
        vdda-supply = <&reg_tim_2v7>;
        vddif-supply = <&reg_tim_1v8>;
        vddd-supply = <&reg_tim_1v2>;
        vdmix-supply = <&reg_tim_1v2mix>;

        csi_id = <0>;
        mipi_csi;
        status = "okay";

        port {
            mlx7502x_mipi0_ep: endpoint {
                remote-endpoint = <&mipi_csi0_ep>;
                clock-lanes = <0>;
                data-lanes = <1 2 3 4>;                // 4-lane MIPI as per your DTS
                link-frequencies = /bits/ 64 < 960000000
                                                904000000
                                                800000000
                                                704000000
                                                600000000
                                                300000000 >;
                clock-noncontinuous;
            };
        };
    };

    eye-safety@48 {
        compatible = "eyesafety";
        reg = <0x48>;                                  // BPW 34 FS-Z safety controller
        pinctrl-0 = <&pinctrl_eyesafety_gpio>;
        rst-gpios = <&gpio1 11 GPIO_ACTIVE_LOW>;
        test-gpios = <&gpio5 3 GPIO_ACTIVE_HIGH>;
        interrupt-parent = <&gpio5>;
        interrupts = <28 IRQ_TYPE_LEVEL_HIGH>;
        fw-name = "roommate/eyesafety.hex";
        status = "okay";
    };
};

// Clock configuration for ToF sensor
mlx7502x_clk: mlx7502x_clk {
    compatible = "fixed-clock";
    #clock-cells = <0>;
    clock-frequency = <8000000>;                       // 8MHz as per your DTS
};

// Power regulators for ToF sensor (as defined in your DTS)
reg_tim_1v2mix: regulator-tim_1v2mix {
    compatible = "regulator-fixed";
    pinctrl-0 = <&pinctrl_tim_enable_reg>;
    pinctrl-names = "default";
    regulator-name = "tim_1v2mix";
    regulator-min-microvolt = <1200000>;
    regulator-max-microvolt = <1200000>;
    gpio = <&gpio4 24 GPIO_ACTIVE_HIGH>;
    startup-delay-us = <20000>;
    enable-active-high;
    regulator-always-on;
};

reg_tim_1v2: regulator-tim_1v2 {
    compatible = "regulator-fixed";
    pinctrl-0 = <&pinctrl_tim_reset_reg>;
    pinctrl-names = "default";
    regulator-name = "tim_1v2";
    regulator-min-microvolt = <1200000>;
    regulator-max-microvolt = <1200000>;
    vin-supply = <&reg_tim_1v2mix>;
    gpio = <&gpio4 23 GPIO_ACTIVE_HIGH>;
    enable-active-high;
    regulator-always-on;
};

reg_tim_1v8: regulator-tim_1v8 {
    compatible = "regulator-fixed";
    regulator-name = "tim_1v8";
    regulator-min-microvolt = <1800000>;
    regulator-max-microvolt = <1800000>;
    regulator-always-on;
};

reg_tim_2v7: regulator-tim_2v7 {
    compatible = "regulator-fixed";
    regulator-name = "tim_2v7";
    regulator-min-microvolt = <2700000>;
    regulator-max-microvolt = <2700000>;
    regulator-always-on;
};
```

## Step 1: System Verification and Initial Setup

### Check Hardware Detection

First, verify that your ToF camera module is properly detected by the system:

```bash
# Check if the ToF sensor is detected on I2C
i2cdetect -y 2
# Should show device at address 0x3d

# Verify kernel modules are loaded
lsmod | grep mlx
# Should show mlx75027 and related modules

# Check device tree status
cat /proc/device-tree/soc/bus@30800000/i2c@30a30000/tof-camera@3d/status
# Should show "okay"

# Verify GPIO configuration
cat /sys/kernel/debug/gpio
# Should show laser-enable and eye-safety GPIOs
```

### Verify Video4Linux Detection

```bash
# List all video devices
v4l2-ctl --list-devices
# Expected output:
# mlx75027 2-003d (platform:soc:bus@30800000:i2c@30a30000):
#     /dev/video0
#     /dev/v4l-subdev0

# Check media controller topology
media-ctl -p
# Should show the complete ToF pipeline
```

## Step 2: Laser Infra LED Configuration and Safety Setup

### Initialize Laser Safety System

Before enabling the laser LEDs, configure the safety monitoring system with BPW 34 FS-Z photodiode:

```bash
#!/bin/bash
# /usr/local/bin/tof-safety-init.sh

# I2C bus and addresses for safety system (based on your actual DTS)
I2C_BUS=3
SAFETY_MCU_ADDR=0x48  # Safety microcontroller address
TOF_SENSOR_ADDR=0x57  # Melexis 75027 address (from your DTS)

# Export GPIO for laser control
echo 111 > /sys/class/gpio/export  # GPIO3_15 = 3*32 + 15 = 111
echo out > /sys/class/gpio/gpio111/direction
echo 0 > /sys/class/gpio/gpio111/value  # Start with laser OFF

# Check if safety microcontroller is present
if i2cdetect -y $I2C_BUS | grep -q $(printf "%02x" $SAFETY_MCU_ADDR); then
    echo "BPW 34 FS-Z safety microcontroller detected at 0x$(printf "%02x" $SAFETY_MCU_ADDR)"
    
    # Initialize safety microcontroller
    # Register 0x00: Control register
    # Bit 0: Enable photodiode monitoring
    # Bit 1: Set safety threshold mode
    i2cset -y $I2C_BUS $SAFETY_MCU_ADDR 0x00 0x03
    
    # Register 0x01: Safety threshold (adjust based on your requirements)
    # Higher values = more sensitive to ambient light
    i2cset -y $I2C_BUS $SAFETY_MCU_ADDR 0x01 0x80
    
    # Register 0x02: Sampling rate (10Hz for safety monitoring)
    i2cset -y $I2C_BUS $SAFETY_MCU_ADDR 0x02 0x0A
    
    echo "BPW 34 FS-Z photodiode safety system initialized"
else
    echo "ERROR: Safety microcontroller not found at 0x$(printf "%02x" $SAFETY_MCU_ADDR)"
    echo "Cannot proceed without safety system"
    exit 1
fi

# Check if ToF sensor is present
if i2cdetect -y $I2C_BUS | grep -q $(printf "%02x" $TOF_SENSOR_ADDR); then
    echo "Melexis 75027 ToF sensor detected at 0x$(printf "%02x" $TOF_SENSOR_ADDR)"
else
    echo "WARNING: ToF sensor not detected at 0x$(printf "%02x" $TOF_SENSOR_ADDR)"
fi

echo "ToF safety system initialization completed"
```

### Laser Control Functions

Create utility functions for safe laser operation with I2C-based BPW 34 FS-Z safety monitoring:

```bash
#!/bin/bash
# /usr/local/bin/tof-laser-control.sh

# I2C configuration (based on your actual DTS)
I2C_BUS=3
SAFETY_MCU_ADDR=0x48
LASER_GPIO="/sys/class/gpio/gpio111/value"

# Safety registers
SAFETY_STATUS_REG=0x03    # Status register
SAFETY_LIGHT_REG=0x04     # Ambient light level register
SAFETY_THRESHOLD_REG=0x01 # Threshold register

read_safety_status() {
    # Read safety status from BPW 34 FS-Z microcontroller
    # Register 0x03: Safety status
    # Bit 0: Safety OK (0) / Violation (1)
    # Bit 1: Photodiode functional (1) / Error (0)
    local status=$(i2cget -y $I2C_BUS $SAFETY_MCU_ADDR $SAFETY_STATUS_REG)
    echo $((status))
}

read_ambient_light() {
    # Read ambient light level from photodiode
    # Register 0x04: 8-bit ambient light level (0-255)
    local light_level=$(i2cget -y $I2C_BUS $SAFETY_MCU_ADDR $SAFETY_LIGHT_REG)
    echo $((light_level))
}

enable_laser() {
    echo "Checking BPW 34 FS-Z safety system before enabling laser..."
    
    # Read safety status
    local safety_status=$(read_safety_status)
    local ambient_light=$(read_ambient_light)
    
    echo "Safety status: 0x$(printf "%02x" $safety_status)"
    echo "Ambient light level: $ambient_light"
    
    # Check if photodiode is functional (bit 1)
    if [ $((safety_status & 0x02)) -eq 0 ]; then
        echo "ERROR: BPW 34 FS-Z photodiode not functional!"
        return 1
    fi
    
    # Check safety violation (bit 0)
    if [ $((safety_status & 0x01)) -ne 0 ]; then
        echo "ERROR: Eye safety violation detected by BPW 34 FS-Z!"
        echo "Ambient light level too high: $ambient_light"
        return 1
    fi
    
    # Additional check: ensure ambient light is below safe threshold
    if [ $ambient_light -gt 200 ]; then
        echo "WARNING: High ambient light detected ($ambient_light), laser may not be safe"
        echo "Consider adjusting safety threshold or environment"
        return 1
    fi
    
    echo "Safety checks passed, enabling ToF laser LEDs..."
    echo 1 > $LASER_GPIO
    
    # Verify laser is enabled
    if [ "$(cat $LASER_GPIO)" = "1" ]; then
        echo "Laser LEDs enabled successfully"
        
        # Monitor safety for 1 second after enabling
        sleep 1
        local post_enable_status=$(read_safety_status)
        if [ $((post_enable_status & 0x01)) -ne 0 ]; then
            echo "WARNING: Safety violation detected after laser enable!"
            disable_laser
            return 1
        fi
        
        return 0
    else
        echo "Failed to enable laser LEDs"
        return 1
    fi
}

disable_laser() {
    echo "Disabling ToF laser LEDs..."
    echo 0 > $LASER_GPIO
    echo "Laser LEDs disabled"
    
    # Wait for photodiode to stabilize
    sleep 0.5
    
    # Verify safety system is stable after laser disable
    local safety_status=$(read_safety_status)
    local ambient_light=$(read_ambient_light)
    echo "Post-disable safety status: 0x$(printf "%02x" $safety_status)"
    echo "Post-disable ambient light: $ambient_light"
}

check_safety() {
    local safety_status=$(read_safety_status)
    local ambient_light=$(read_ambient_light)
    
    echo "BPW 34 FS-Z Safety Check:"
    echo "  Status: 0x$(printf "%02x" $safety_status)"
    echo "  Ambient light: $ambient_light"
    
    # Check if photodiode is functional (bit 1)
    if [ $((safety_status & 0x02)) -eq 0 ]; then
        echo "ERROR: BPW 34 FS-Z photodiode not functional!"
        disable_laser
        return 1
    fi
    
    # Check safety violation (bit 0)
    if [ $((safety_status & 0x01)) -ne 0 ]; then
        echo "WARNING: Eye safety violation detected by BPW 34 FS-Z!"
        echo "Ambient light level: $ambient_light"
        disable_laser
        return 1
    fi
    
    echo "Eye safety OK"
    return 0
}

set_safety_threshold() {
    local threshold=$1
    if [ -z "$threshold" ]; then
        echo "Usage: set_safety_threshold <value>"
        echo "Value range: 0-255 (higher = more sensitive)"
        return 1
    fi
    
    echo "Setting BPW 34 FS-Z safety threshold to: $threshold"
    i2cset -y $I2C_BUS $SAFETY_MCU_ADDR $SAFETY_THRESHOLD_REG $threshold
    
    # Verify setting
    local current_threshold=$(i2cget -y $I2C_BUS $SAFETY_MCU_ADDR $SAFETY_THRESHOLD_REG)
    echo "Current threshold: $((current_threshold))"
}

case "$1" in
    on)
        enable_laser
        ;;
    off)
        disable_laser
        ;;
    check)
        check_safety
        ;;
    threshold)
        set_safety_threshold "$2"
        ;;
    status)
        echo "=== BPW 34 FS-Z Safety System Status ==="
        echo "Safety Status: 0x$(printf "%02x" $(read_safety_status))"
        echo "Ambient Light: $(read_ambient_light)"
        echo "Laser State: $(cat $LASER_GPIO)"
        ;;
    *)
        echo "Usage: $0 {on|off|check|threshold <value>|status}"
        echo ""
        echo "Commands:"
        echo "  on        - Enable laser (with safety checks)"
        echo "  off       - Disable laser"
        echo "  check     - Check safety status"
        echo "  threshold - Set safety threshold (0-255)"
        echo "  status    - Show complete system status"
        exit 1
        ;;
esac
```

## Step 3: MIPI CSI Pipeline Configuration

### Configure Media Controller Pipeline

The Melexis 75027 requires specific media controller configuration for ToF operation:

```bash
#!/bin/bash
# /usr/local/bin/configure-tof-pipeline.sh

MEDIA_DEV="/dev/media0"

configure_tof_pipeline() {
    echo "Configuring ToF camera pipeline..."
    
    # Reset media controller
    media-ctl -d $MEDIA_DEV -r
    
    # Link ToF sensor to MIPI CSI receiver (based on your actual DTS)
    media-ctl -d $MEDIA_DEV -l "'mlx7502x_mipi 3-0057':0->'mxc-mipi-csi2.0':0[1]"
    
    # Link MIPI CSI receiver to ISI
    media-ctl -d $MEDIA_DEV -l "'mxc-mipi-csi2.0':1->'mxc_isi.0':0[1]"
    
    # Link ISI to capture device
    media-ctl -d $MEDIA_DEV -l "'mxc_isi.0':1->'mxc_isi.0.capture':0[1]"
    
    # Set format for ToF data (16-bit grayscale for phase data)
    media-ctl -d $MEDIA_DEV -V "'mlx7502x_mipi 3-0057':0[fmt:Y16_1X16/320x240@1/30]"
    media-ctl -d $MEDIA_DEV -V "'mxc-mipi-csi2.0':0[fmt:Y16_1X16/320x240@1/30]"
    media-ctl -d $MEDIA_DEV -V "'mxc-mipi-csi2.0':1[fmt:Y16_1X16/320x240@1/30]"
    media-ctl -d $MEDIA_DEV -V "'mxc_isi.0':0[fmt:Y16_1X16/320x240@1/30]"
    media-ctl -d $MEDIA_DEV -V "'mxc_isi.0':1[fmt:Y16_1X16/320x240@1/30]"
    
    # Configure capture device
    v4l2-ctl --device=/dev/video0 --set-fmt-video=width=320,height=240,pixelformat=Y16
    
    echo "ToF pipeline configured successfully"
}

verify_pipeline() {
    echo "=== ToF Pipeline Status ==="
    media-ctl -p | grep -A 2 -B 2 "ENABLED"
    
    echo "=== ToF Sensor Status ==="
    v4l2-ctl --device=/dev/v4l-subdev0 --all
    
    echo "=== Capture Device Status ==="
    v4l2-ctl --device=/dev/video0 --all
}

configure_tof_pipeline
verify_pipeline
```

### ToF-Specific Camera Controls

Configure the ToF sensor parameters for optimal operation:

```bash
#!/bin/bash
# /usr/local/bin/configure-tof-sensor.sh

TOF_SUBDEV="/dev/v4l-subdev0"

configure_tof_sensor() {
    echo "Configuring ToF sensor parameters..."
    
    # Set integration time (exposure) for each phase
    # Values in microseconds - adjust based on scene and requirements
    v4l2-ctl --device=$TOF_SUBDEV --set-ctrl=integration_time_0=1000   # Phase 0
    v4l2-ctl --device=$TOF_SUBDEV --set-ctrl=integration_time_1=1000   # Phase 1
    v4l2-ctl --device=$TOF_SUBDEV --set-ctrl=integration_time_2=1000   # Phase 2
    v4l2-ctl --device=$TOF_SUBDEV --set-ctrl=integration_time_3=1000   # Phase 3
    
    # Set modulation frequency (typically 20MHz for MLX75027)
    v4l2-ctl --device=$TOF_SUBDEV --set-ctrl=modulation_frequency=20000000
    
    # Configure HDR mode (0=disabled, 1=enabled)
    v4l2-ctl --device=$TOF_SUBDEV --set-ctrl=hdr_mode=0
    
    # Set frame rate
    v4l2-ctl --device=$TOF_SUBDEV --set-ctrl=frame_rate=30
    
    # Configure laser power (0-100%)
    v4l2-ctl --device=$TOF_SUBDEV --set-ctrl=laser_power=80
    
    echo "ToF sensor configured successfully"
}

list_tof_controls() {
    echo "=== Available ToF Controls ==="
    v4l2-ctl --device=$TOF_SUBDEV --list-ctrls
}

configure_tof_sensor
list_tof_controls
```

## Step 4: Multi-Phase Frame Capture

### Understanding ToF Multi-Phase Capture

The Melexis 75027 captures multiple phases per frame to calculate distance information:

```bash
#!/bin/bash
# /usr/local/bin/capture-tof-phases.sh

VIDEO_DEV="/dev/video0"
OUTPUT_DIR="/tmp/tof_capture"

mkdir -p $OUTPUT_DIR

capture_tof_phases() {
    local num_phases=4
    local frame_count=1
    
    echo "Capturing ToF multi-phase data..."
    
    # Enable laser before capture
    /usr/local/bin/tof-laser-control.sh on
    
    # Wait for laser stabilization
    sleep 1
    
    for phase in $(seq 0 $((num_phases-1))); do
        echo "Capturing phase $phase..."
        
        # Set current phase
        v4l2-ctl --device=/dev/v4l-subdev0 --set-ctrl=current_phase=$phase
        
        # Capture phase data
        v4l2-ctl --device=$VIDEO_DEV \
                 --stream-mmap \
                 --stream-count=$frame_count \
                 --stream-to=$OUTPUT_DIR/phase_${phase}.raw
        
        # Check safety between phases
        if ! /usr/local/bin/tof-laser-control.sh check; then
            echo "Safety violation detected, aborting capture"
            /usr/local/bin/tof-laser-control.sh off
            return 1
        fi
    done
    
    # Disable laser after capture
    /usr/local/bin/tof-laser-control.sh off
    
    echo "Multi-phase capture completed"
    echo "Phase data saved to: $OUTPUT_DIR"
}

capture_tof_phases
```

## Step 5: Converting ToF Data to JPEG

### Processing Raw ToF Data

ToF sensors output 16-bit grayscale data that needs processing before JPEG conversion:

```bash
#!/bin/bash
# /usr/local/bin/tof-to-jpeg.sh

INPUT_DIR="/tmp/tof_capture"
OUTPUT_DIR="/tmp/tof_jpeg"

mkdir -p $OUTPUT_DIR

process_tof_to_jpeg() {
    echo "Converting ToF data to JPEG..."
    
    for phase_file in $INPUT_DIR/phase_*.raw; do
        if [ -f "$phase_file" ]; then
            local phase_name=$(basename "$phase_file" .raw)
            local output_file="$OUTPUT_DIR/${phase_name}.jpg"
            
            echo "Processing $phase_file -> $output_file"
            
            # Convert 16-bit raw to 8-bit grayscale and then to JPEG
            # This uses ImageMagick - ensure it's installed in your Yocto image
            convert -size 320x240 -depth 16 gray:"$phase_file" \
                    -normalize \
                    -quality 90 \
                    "$output_file"
            
            if [ $? -eq 0 ]; then
                echo "Successfully created $output_file"
            else
                echo "Failed to convert $phase_file"
            fi
        fi
    done
    
    echo "ToF to JPEG conversion completed"
    echo "JPEG files saved to: $OUTPUT_DIR"
}

# Alternative method using FFmpeg (if ImageMagick is not available)
process_tof_to_jpeg_ffmpeg() {
    echo "Converting ToF data to JPEG using FFmpeg..."
    
    for phase_file in $INPUT_DIR/phase_*.raw; do
        if [ -f "$phase_file" ]; then
            local phase_name=$(basename "$phase_file" .raw)
            local output_file="$OUTPUT_DIR/${phase_name}.jpg"
            
            echo "Processing $phase_file -> $output_file"
            
            # Convert using FFmpeg
            ffmpeg -f rawvideo -pix_fmt gray16le -s 320x240 \
                   -i "$phase_file" \
                   -pix_fmt gray \
                   -q:v 2 \
                   "$output_file" -y
            
            if [ $? -eq 0 ]; then
                echo "Successfully created $output_file"
            else
                echo "Failed to convert $phase_file"
            fi
        fi
    done
}

# Check which tool is available and use it
if command -v convert >/dev/null 2>&1; then
    process_tof_to_jpeg
elif command -v ffmpeg >/dev/null 2>&1; then
    process_tof_to_jpeg_ffmpeg
else
    echo "Error: Neither ImageMagick nor FFmpeg is available"
    echo "Please install one of these tools in your Yocto image"
    exit 1
fi
```

### Creating Amplitude and Distance Images

For more advanced ToF processing, you can create amplitude and distance images:

```bash
#!/bin/bash
# /usr/local/bin/tof-advanced-processing.sh

INPUT_DIR="/tmp/tof_capture"
OUTPUT_DIR="/tmp/tof_processed"

mkdir -p $OUTPUT_DIR

process_amplitude_distance() {
    echo "Processing ToF data for amplitude and distance..."
    
    # This is a simplified example - real ToF processing is more complex
    # and typically requires custom C/C++ code or specialized libraries
    
    if [ -f "$INPUT_DIR/phase_0.raw" ] && [ -f "$INPUT_DIR/phase_1.raw" ] && \
       [ -f "$INPUT_DIR/phase_2.raw" ] && [ -f "$INPUT_DIR/phase_3.raw" ]; then
        
        echo "All phase files found, processing..."
        
        # Create amplitude image (simplified calculation)
        # Real amplitude = sqrt((I1-I3)^2 + (I2-I4)^2)
        python3 << EOF
import numpy as np
import cv2

# Load phase data
phase0 = np.fromfile('$INPUT_DIR/phase_0.raw', dtype=np.uint16).reshape(240, 320)
phase1 = np.fromfile('$INPUT_DIR/phase_1.raw', dtype=np.uint16).reshape(240, 320)
phase2 = np.fromfile('$INPUT_DIR/phase_2.raw', dtype=np.uint16).reshape(240, 320)
phase3 = np.fromfile('$INPUT_DIR/phase_3.raw', dtype=np.uint16).reshape(240, 320)

# Calculate amplitude (simplified)
amplitude = np.sqrt((phase0.astype(np.float32) - phase2.astype(np.float32))**2 + 
                   (phase1.astype(np.float32) - phase3.astype(np.float32))**2)

# Normalize to 8-bit
amplitude_8bit = (amplitude / amplitude.max() * 255).astype(np.uint8)

# Save amplitude image
cv2.imwrite('$OUTPUT_DIR/amplitude.jpg', amplitude_8bit)

# Calculate distance (simplified - requires calibration)
# Real distance calculation needs modulation frequency and calibration
distance = np.arctan2(phase1.astype(np.float32) - phase3.astype(np.float32),
                     phase0.astype(np.float32) - phase2.astype(np.float32))

# Convert phase to distance (this is a simplified example)
# Real conversion: distance = (phase / (4 * pi)) * (c / (2 * f_mod))
# where c = speed of light, f_mod = modulation frequency
distance_normalized = ((distance + np.pi) / (2 * np.pi) * 255).astype(np.uint8)

# Save distance image
cv2.imwrite('$OUTPUT_DIR/distance.jpg', distance_normalized)

print("Amplitude and distance images created successfully")
EOF
        
        echo "Advanced ToF processing completed"
        echo "Processed images saved to: $OUTPUT_DIR"
    else
        echo "Error: Not all phase files are available"
        return 1
    fi
}

process_amplitude_distance
```

## Step 6: Complete Capture and Processing Pipeline

### Master Script for Complete ToF Operation

Create a master script that combines all the steps:

```bash
#!/bin/bash
# /usr/local/bin/tof-complete-capture.sh

set -e  # Exit on any error

OUTPUT_BASE="/tmp/tof_session_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTPUT_BASE"

echo "=== ToF Camera Complete Capture Session ==="
echo "Output directory: $OUTPUT_BASE"

# Step 1: Initialize safety system
echo "Step 1: Initializing safety system..."
/usr/local/bin/tof-safety-init.sh

# Step 2: Configure pipeline
echo "Step 2: Configuring ToF pipeline..."
/usr/local/bin/configure-tof-pipeline.sh

# Step 3: Configure sensor
echo "Step 3: Configuring ToF sensor..."
/usr/local/bin/configure-tof-sensor.sh

# Step 4: Capture phases
echo "Step 4: Capturing ToF phases..."
export OUTPUT_DIR="$OUTPUT_BASE/raw_phases"
mkdir -p "$OUTPUT_DIR"
sed -i "s|/tmp/tof_capture|$OUTPUT_DIR|g" /usr/local/bin/capture-tof-phases.sh
/usr/local/bin/capture-tof-phases.sh

# Step 5: Convert to JPEG
echo "Step 5: Converting phases to JPEG..."
export INPUT_DIR="$OUTPUT_DIR"
export OUTPUT_DIR="$OUTPUT_BASE/jpeg_phases"
mkdir -p "$OUTPUT_DIR"
sed -i "s|/tmp/tof_capture|$INPUT_DIR|g" /usr/local/bin/tof-to-jpeg.sh
sed -i "s|/tmp/tof_jpeg|$OUTPUT_DIR|g" /usr/local/bin/tof-to-jpeg.sh
/usr/local/bin/tof-to-jpeg.sh

# Step 6: Advanced processing (optional)
echo "Step 6: Creating amplitude and distance images..."
export INPUT_DIR="$OUTPUT_BASE/raw_phases"
export OUTPUT_DIR="$OUTPUT_BASE/processed"
mkdir -p "$OUTPUT_DIR"
sed -i "s|/tmp/tof_capture|$INPUT_DIR|g" /usr/local/bin/tof-advanced-processing.sh
sed -i "s|/tmp/tof_processed|$OUTPUT_DIR|g" /usr/local/bin/tof-advanced-processing.sh
/usr/local/bin/tof-advanced-processing.sh

# Step 7: Generate summary
echo "Step 7: Generating capture summary..."
cat > "$OUTPUT_BASE/capture_summary.txt" << EOF
ToF Camera Capture Session Summary
Date: $(date)
Output Directory: $OUTPUT_BASE

Files Generated:
- Raw phase data: $OUTPUT_BASE/raw_phases/
- JPEG phase images: $OUTPUT_BASE/jpeg_phases/
- Processed images: $OUTPUT_BASE/processed/

Phase Files:
$(ls -la "$OUTPUT_BASE/raw_phases/" 2>/dev/null || echo "No raw phase files found")

JPEG Files:
$(ls -la "$OUTPUT_BASE/jpeg_phases/" 2>/dev/null || echo "No JPEG files found")

Processed Files:
$(ls -la "$OUTPUT_BASE/processed/" 2>/dev/null || echo "No processed files found")

System Information:
- Kernel: $(uname -r)
- ToF Driver: $(lsmod | grep mlx || echo "MLX driver not loaded")
- V4L2 Devices: $(v4l2-ctl --list-devices | head -5)
EOF

echo "=== ToF Capture Session Completed ==="
echo "Summary saved to: $OUTPUT_BASE/capture_summary.txt"
echo "All files saved to: $OUTPUT_BASE"

# Cleanup temporary modifications
git checkout /usr/local/bin/capture-tof-phases.sh 2>/dev/null || true
git checkout /usr/local/bin/tof-to-jpeg.sh 2>/dev/null || true
git checkout /usr/local/bin/tof-advanced-processing.sh 2>/dev/null || true
```

## Troubleshooting Common Issues

### Issue 1: ToF Sensor Not Detected

**Symptoms:**
```bash
i2cdetect -y 2
# Shows no device at 0x3d
```

**Solutions:**
1. Check power supplies (3.3V and 1.8V)
2. Verify I2C bus configuration in device tree
3. Check physical connections
4. Ensure proper pull-up resistors on I2C lines

### Issue 2: MIPI CSI Synchronization Errors

**Symptoms:**
```bash
dmesg | grep mipi
# imx7-mipi-csis: MIPI CSIS error: 0x00000010
```

**Solutions:**
1. Verify MIPI lane configuration matches hardware
2. Check clock frequencies and timing
3. Ensure proper MIPI CSI receiver configuration
4. Verify sensor output format matches receiver expectations

### Issue 3: Laser Safety System Triggering

**Symptoms:**
- Laser automatically disables during operation
- Safety GPIO shows violation

**Solutions:**
1. Check safety sensor positioning and calibration
2. Verify GPIO configuration and polarity
3. Adjust safety thresholds if configurable
4. Ensure proper grounding of safety circuits

### Issue 4: Poor ToF Data Quality

**Symptoms:**
- Noisy distance measurements
- Inconsistent amplitude data
- Poor signal-to-noise ratio

**Solutions:**
1. Adjust integration times for different phases
2. Optimize laser power settings
3. Check for ambient light interference
4. Verify modulation frequency settings
5. Ensure proper lens cleanliness

## Performance Optimization

### Memory Management

```bash
# Optimize CMA allocation for ToF buffers
echo 'cma=128M' >> /boot/cmdline.txt

# Set appropriate buffer sizes
echo 'vm.min_free_kbytes = 16384' >> /etc/sysctl.conf
```

### Real-Time Performance Tuning

```bash
# Set CPU governor for consistent performance
echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor

# Disable unnecessary services during ToF capture
systemctl stop bluetooth
systemctl stop wifi

# Set process priorities
echo -1000 > /proc/sys/kernel/sched_rt_runtime_us  # Allow 100% RT usage
```

## Quick Start Commands

For immediate testing, use these commands in sequence:

```bash
# 1. Quick system check
v4l2-ctl --list-devices
media-ctl -p

# 2. Initialize safety and configure pipeline
/usr/local/bin/tof-safety-init.sh
/usr/local/bin/configure-tof-pipeline.sh
/usr/local/bin/configure-tof-sensor.sh

# 3. Capture single frame and convert to JPEG
/usr/local/bin/tof-laser-control.sh on
v4l2-ctl --device=/dev/video0 --stream-mmap --stream-count=1 --stream-to=tof_frame.raw
/usr/local/bin/tof-laser-control.sh off

# 4. Convert to JPEG (using FFmpeg)
ffmpeg -f rawvideo -pix_fmt gray16le -s 320x240 -i tof_frame.raw -pix_fmt gray -q:v 2 tof_frame.jpg

# 5. View the result
ls -la tof_frame.jpg
```

## Yocto Integration

### Adding ToF Support to Your Yocto Build

Add these lines to your `local.conf`:

```bash
# ToF camera support
IMAGE_INSTALL_append = " v4l-utils media-ctl"
IMAGE_INSTALL_append = " python3-opencv python3-numpy"
IMAGE_INSTALL_append = " imagemagick ffmpeg"

# Kernel features
KERNEL_FEATURES_append = " features/v4l2/v4l2-all.scc"

# Custom ToF scripts
IMAGE_INSTALL_append = " tof-camera-scripts"
```

### Creating a Custom Recipe for ToF Scripts

Create `meta-your-layer/recipes-multimedia/tof-camera/tof-camera-scripts_1.0.bb`:

```bash
SUMMARY = "ToF Camera Configuration Scripts"
DESCRIPTION = "Scripts for configuring and using Melexis 75027 ToF camera"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/MIT;md5=0835ade698e0bcf8506ecda2f7b4f302"

SRC_URI = "file://tof-safety-init.sh \
           file://tof-laser-control.sh \
           file://configure-tof-pipeline.sh \
           file://configure-tof-sensor.sh \
           file://capture-tof-phases.sh \
           file://tof-to-jpeg.sh \
           file://tof-advanced-processing.sh \
           file://tof-complete-capture.sh"

S = "${WORKDIR}"

do_install() {
    install -d ${D}${bindir}
    install -m 0755 ${WORKDIR}/*.sh ${D}${bindir}/
}

FILES_${PN} = "${bindir}/*"
```

## Conclusion

This comprehensive guide covers the complete process of configuring a Melexis 75027 ToF camera module on Yocto Linux, from initial hardware setup to JPEG image capture. The key aspects covered include:

### Critical Success Factors

1. **Safety First**: Always implement and test laser safety systems before enabling ToF illumination
2. **Hardware Verification**: Ensure proper MIPI CSI lane configuration and clock timing
3. **Media Pipeline**: Configure the complete Video4Linux media controller pipeline correctly
4. **Multi-phase Understanding**: ToF requires capturing and processing multiple phases per frame
5. **System Integration**: Proper Yocto integration ensures reproducible builds and deployment

### Key Takeaways

- **ToF cameras are complex**: Unlike simple RGB cameras, ToF systems require coordinated control of lasers, safety systems, and multi-phase capture
- **Safety is paramount**: Laser safety monitoring must be implemented and tested thoroughly
- **MIPI CSI timing matters**: Precise clock and lane configuration is critical for stable operation
- **Processing is essential**: Raw ToF data requires significant processing to produce usable images
- **Command-line tools are powerful**: v4l2-ctl, media-ctl, and standard Linux tools provide complete control

### Next Steps

After successfully implementing this guide, consider these advanced topics:

1. **Real-time ToF processing**: Implement optimized C/C++ code for real-time distance calculation
2. **Calibration procedures**: Develop proper calibration routines for accurate distance measurements
3. **Integration with applications**: Connect ToF data to your specific use case (robotics, industrial monitoring, etc.)
4. **Performance optimization**: Fine-tune for your specific hardware platform and requirements
5. **Advanced safety features**: Implement more sophisticated laser safety and monitoring systems

### Resources and References

- [Melexis 75027 Datasheet](https://www.melexis.com/en/product/MLX75027/Time-of-Flight-Sensor-IC)
- [Video4Linux API Documentation](https://www.kernel.org/doc/html/latest/userspace-api/media/v4l/index.html)
- [Media Controller Framework](https://www.kernel.org/doc/html/latest/userspace-api/media/mediactl/index.html)
- [MIPI CSI-2 Specification](https://www.mipi.org/specifications/csi-2)
- [Yocto Project Documentation](https://docs.yoctoproject.org/)

This guide provides a solid foundation for working with ToF cameras on embedded Linux systems. The combination of proper hardware configuration, safety systems, and processing pipelines enables reliable ToF camera operation in production environments.
