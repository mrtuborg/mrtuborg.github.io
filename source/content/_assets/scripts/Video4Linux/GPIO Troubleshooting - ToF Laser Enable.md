---
{"publish":true,"title":"GPIO Troubleshooting - ToF Laser Enable","description":"Troubleshooting missing /sys/class/gpio and GPIO configuration issues for ToF laser enable","created":"2025-01-10","modified":"2025-07-25T21:41:26.529+02:00","tags":["gpio","sysfs","device-tree","laser-enable","imx8mp"],"cssclasses":""}
---


# GPIO Troubleshooting - ToF Laser Enable

## Problem Analysis

Your LIM_EN.sh script is trying to use GPIO sysfs interface, but `/sys/class/gpio` doesn't exist. This is because:

1. **GPIO sysfs is deprecated** in modern kernels (5.3+)
2. **GPIOs are configured as gpio-hog** in device tree
3. **Missing kernel configuration** for GPIO sysfs support

## Current Configuration Analysis

### LIM_EN.sh Script Analysis
```bash
# Your script uses these GPIOs:
GPIO_V_LIM_EN="169"  # IMX_GPIO_NR(6, 9) = (6-1)*32 + 9 = 169
GPIO_LIM_EN="137"    # IMX_GPIO_NR(5, 9) = (5-1)*32 + 9 = 137
```

### Device Tree Analysis
Looking at your `imx8mp-var-som-roomboard.dts`:

```dts
&gpio1 {
    gpio-line-names = "", "", "", "",
              "", "", "", "",
              "", "", "", "",
              "", "", "", "lim_en",  // GPIO1_15 (pin 15)
              ...
    data-gpios = <&gpio1 15 GPIO_ACTIVE_HIGH>;
};

&gpio4 {
    gpio-line-names = "", "", "", "",
              "", "", "hw_rev2", "",
              "", "hw_rev3", "hw_rev1", "",
              "", "", "", "",
              "hw_rev0", "", "", "",
              "", "", "", "",
              "", "", "lim_volt_en", "",  // GPIO4_26 (pin 26)
              ...
    data-gpios = <&gpio4 26 GPIO_ACTIVE_HIGH>;
};
```

**Issue Found**: Your script expects:
- `GPIO_V_LIM_EN="169"` (GPIO6_9) 
- `GPIO_LIM_EN="137"` (GPIO5_9)

But device tree shows:
- `lim_en` on **GPIO1_15** (pin 15) = GPIO number 15
- `lim_volt_en` on **GPIO4_26** (pin 26) = GPIO number 122 (4-1)*32+26

## Solutions

### Solution 1: Fix GPIO Numbers in Script

```bash
#!/bin/bash
# Fixed LIM_EN.sh with correct GPIO numbers

DISABLE="0"

# Correct GPIO numbers based on device tree
# GPIO1_15 = (1-1)*32 + 15 = 15
# GPIO4_26 = (4-1)*32 + 26 = 122
GPIO_LIM_EN="15"      # GPIO1_15 (lim_en)
GPIO_V_LIM_EN="122"   # GPIO4_26 (lim_volt_en)

while getopts "dh" opt; do
  case $opt in
    d)
      echo "Disable LIM"
      DISABLE="1"
      ;;
    h)
      echo "        Enable LIM"
      echo "-d      Disable LIM"
      echo "-h      help"
      exit 1
      ;;
    \?)
      echo "Invalid option: -$OPTARG"
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument."
      exit 1
      ;;
  esac
done

# Check if GPIO sysfs exists
if [ ! -d "/sys/class/gpio" ]; then
    echo "Error: /sys/class/gpio does not exist"
    echo "GPIO sysfs interface is not available"
    echo "Solutions:"
    echo "1. Enable CONFIG_GPIO_SYSFS in kernel"
    echo "2. Use modern GPIO tools (gpioset/gpioget)"
    exit 1
fi

# Export and configure GPIOs
if [ ! -d "/sys/class/gpio/gpio${GPIO_LIM_EN}" ]; then
  echo ${GPIO_LIM_EN} > /sys/class/gpio/export
  echo out > /sys/class/gpio/gpio${GPIO_LIM_EN}/direction
fi

if [ ! -d "/sys/class/gpio/gpio${GPIO_V_LIM_EN}" ]; then
  echo ${GPIO_V_LIM_EN} > /sys/class/gpio/export
  echo out > /sys/class/gpio/gpio${GPIO_V_LIM_EN}/direction
fi

# Set GPIO values
if [ "$DISABLE" == "1" ]; then
  echo 0 > /sys/class/gpio/gpio${GPIO_LIM_EN}/value
  echo 0 > /sys/class/gpio/gpio${GPIO_V_LIM_EN}/value
  echo "LIM disabled"
else
  echo 1 > /sys/class/gpio/gpio${GPIO_LIM_EN}/value
  echo 1 > /sys/class/gpio/gpio${GPIO_V_LIM_EN}/value
  echo "LIM enabled"
fi
```

### Solution 2: Enable GPIO Sysfs in Kernel

Add to your kernel defconfig:
```bash
# Enable GPIO sysfs interface (deprecated but still available)
CONFIG_GPIO_SYSFS=y
```

### Solution 3: Modern GPIO Tools (Recommended)

```bash
#!/bin/bash
# Modern LIM_EN.sh using libgpiod tools

DISABLE="0"

# GPIO chip and line numbers
GPIO_CHIP="gpiochip0"  # Usually gpiochip0 for GPIO1
GPIO_LIM_EN_LINE="15"  # GPIO1_15
GPIO_V_LIM_EN_LINE="26" # GPIO4_26 (need to find correct chip)

while getopts "dh" opt; do
  case $opt in
    d)
      echo "Disable LIM"
      DISABLE="1"
      ;;
    h)
      echo "        Enable LIM"
      echo "-d      Disable LIM"
      echo "-h      help"
      exit 1
      ;;
    \?)
      echo "Invalid option: -$OPTARG"
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument."
      exit 1
      ;;
  esac
done

# Check if gpioset is available
if ! command -v gpioset &> /dev/null; then
    echo "Error: gpioset not found"
    echo "Install libgpiod-utils: apt-get install gpiod"
    exit 1
fi

# Set GPIO values using modern tools
if [ "$DISABLE" == "1" ]; then
    gpioset gpiochip0 15=0  # GPIO1_15 (lim_en)
    gpioset gpiochip3 26=0  # GPIO4_26 (lim_volt_en) - GPIO4 is usually gpiochip3
    echo "LIM disabled"
else
    gpioset gpiochip0 15=1  # GPIO1_15 (lim_en)
    gpioset gpiochip3 26=1  # GPIO4_26 (lim_volt_en)
    echo "LIM enabled"
fi
```

## Diagnostic Commands

### Check Available GPIO Chips
```bash
# List all GPIO chips
ls /dev/gpiochip*

# Get GPIO chip information
gpioinfo

# Check specific GPIO chip
gpioinfo gpiochip0
gpioinfo gpiochip3
```

### Check Current GPIO Status
```bash
# Check if GPIO lines are available
gpioget gpiochip0 15  # GPIO1_15 (lim_en)
gpioget gpiochip3 26  # GPIO4_26 (lim_volt_en)

# Find GPIO by name
gpioinfo | grep -E "(lim_en|lim_volt_en)"
```

### Debug Device Tree GPIO Configuration
```bash
# Check device tree GPIO configuration
cat /proc/device-tree/gpio*/gpio-line-names

# Check GPIO hog configuration
find /sys/firmware/devicetree/base -name "*gpio*" -type d
```

## Kernel Configuration Fix

### Add to defconfig:
```bash
# GPIO support
CONFIG_GPIOLIB=y
CONFIG_GPIO_SYSFS=y
CONFIG_GPIO_MXC=y

# GPIO tools support
CONFIG_GPIO_CDEV=y
```

### Device Tree Fixes

If GPIOs are not working, you might need to fix the device tree:

```dts
&gpio1 {
    status = "okay";
    gpio-controller;
    #gpio-cells = <2>;
    
    pinctrl-names = "default";
    pinctrl-0 = <&pinctrl_gpio1>;

    gpio-line-names = "", "", "", "",
              "", "", "", "",
              "", "", "", "",
              "", "", "", "lim_en",
              "", "", "", "",
              "", "", "", "",
              "", "", "", "",
              "", "", "", "";
};

&gpio4 {
    status = "okay";
    gpio-controller;
    #gpio-cells = <2>;
    
    pinctrl-names = "default";
    pinctrl-0 = <&pinctrl_gpio4>;

    gpio-line-names = "", "", "", "",
              "", "", "hw_rev2", "",
              "", "hw_rev3", "hw_rev1", "",
              "", "", "", "",
              "hw_rev0", "", "", "",
              "", "", "", "",
              "", "", "lim_volt_en", "",
              "", "", "", "";
};
```

## Testing Steps

### Step 1: Check GPIO Availability
```bash
# Check if GPIO chips exist
ls -la /dev/gpiochip*

# Check GPIO sysfs (if enabled)
ls -la /sys/class/gpio/

# Check GPIO info with modern tools
gpioinfo
```

### Step 2: Test GPIO Control
```bash
# Test with corrected GPIO numbers (if sysfs available)
echo 15 > /sys/class/gpio/export
echo out > /sys/class/gpio/gpio15/direction
echo 1 > /sys/class/gpio/gpio15/value

# Test with modern tools
gpioset gpiochip0 15=1
gpioget gpiochip0 15
```

### Step 3: Verify Hardware Response
```bash
# Enable laser and check current consumption
./LIM_EN.sh
# Check power consumption with INA219 sensors

# Disable laser
./LIM_EN.sh -d
```

## Quick Fix Scripts

### Fixed LIM_EN.sh (Save as LIM_EN_fixed.sh)
```bash
#!/bin/bash
# Fixed version with correct GPIO numbers and modern tools

DISABLE="0"

while getopts "dh" opt; do
  case $opt in
    d) DISABLE="1" ;;
    h) echo "Usage: $0 [-d] [-h]"; echo "-d: Disable LIM"; exit 0 ;;
    *) echo "Invalid option"; exit 1 ;;
  esac
done

# Try modern GPIO tools first
if command -v gpioset &> /dev/null; then
    echo "Using modern GPIO tools..."
    if [ "$DISABLE" == "1" ]; then
        gpioset gpiochip0 15=0 2>/dev/null || echo "Failed to set GPIO1_15"
        gpioset gpiochip3 26=0 2>/dev/null || echo "Failed to set GPIO4_26"
        echo "LIM disabled (modern)"
    else
        gpioset gpiochip0 15=1 2>/dev/null || echo "Failed to set GPIO1_15"
        gpioset gpiochip3 26=1 2>/dev/null || echo "Failed to set GPIO4_26"
        echo "LIM enabled (modern)"
    fi
    exit 0
fi

# Fallback to sysfs if available
if [ -d "/sys/class/gpio" ]; then
    echo "Using GPIO sysfs..."
    GPIO_LIM_EN="15"
    GPIO_V_LIM_EN="122"
    
    # Export GPIOs
    [ ! -d "/sys/class/gpio/gpio${GPIO_LIM_EN}" ] && echo ${GPIO_LIM_EN} > /sys/class/gpio/export
    [ ! -d "/sys/class/gpio/gpio${GPIO_V_LIM_EN}" ] && echo ${GPIO_V_LIM_EN} > /sys/class/gpio/export
    
    # Set direction
    echo out > /sys/class/gpio/gpio${GPIO_LIM_EN}/direction 2>/dev/null
    echo out > /sys/class/gpio/gpio${GPIO_V_LIM_EN}/direction 2>/dev/null
    
    # Set values
    if [ "$DISABLE" == "1" ]; then
        echo 0 > /sys/class/gpio/gpio${GPIO_LIM_EN}/value
        echo 0 > /sys/class/gpio/gpio${GPIO_V_LIM_EN}/value
        echo "LIM disabled (sysfs)"
    else
        echo 1 > /sys/class/gpio/gpio${GPIO_LIM_EN}/value
        echo 1 > /sys/class/gpio/gpio${GPIO_V_LIM_EN}/value
        echo "LIM enabled (sysfs)"
    fi
else
    echo "Error: No GPIO interface available"
    echo "Enable CONFIG_GPIO_SYSFS or install libgpiod-utils"
    exit 1
fi
```

## Summary

**Root Cause**: GPIO numbers in your script don't match the device tree configuration.

**Quick Fix**: 
1. Use the corrected GPIO numbers: GPIO1_15 (15) and GPIO4_26 (122)
2. Enable CONFIG_GPIO_SYSFS in kernel, or
3. Use modern libgpiod tools (gpioset/gpioget)

**Recommended Solution**: Use the fixed script above that tries modern tools first, then falls back to sysfs.
