---
{"publish":true,"title":"Yocto Kernel Configuration - Part 1: Getting Started with Devshell","description":"Learn how to use Yocto devshell for kernel configuration with linux-variscite. Your starting point for kernel configuration management.","created":"2025-01-10","modified":"2025-08-25T23:46:26.464+02:00","tags":["yocto","kernel-config","devshell","linux-variscite","menuconfig"],"cssclasses":""}
---


# Yocto Kernel Configuration - Part 1: Getting Started with Devshell

This is the first part of a comprehensive series on managing kernel configuration in Yocto. In this article, we'll cover the basics of using `bitbake -c devshell virtual/kernel` for kernel configuration work with **linux-variscite**.

## Overview

When working with Yocto and linux-variscite kernel configuration, the devshell is your primary tool for:
- ✅ **Interactive kernel configuration** with proper environment
- ✅ **Testing configuration changes** before committing
- ✅ **Understanding the build environment** and directory structure
- ✅ **Generating defconfig files** for your Yocto layer

## Prerequisites

### Required Tools

```bash
# Ensure you have git configured
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Yocto build environment
source oe-init-build-env

# Required packages for kernel configuration
sudo apt-get install libncurses5-dev libssl-dev bc flex bison
```

### Understanding Your linux-variscite Setup

First, identify your kernel source and version:

```bash
# In your Yocto build directory
bitbake -e linux-variscite | grep "^S="
# Output: S="/path/to/tmp/work/imx8mp_var_som-poky-linux/linux-variscite/5.15.71+gitAUTOINC+hash/git"

# Check kernel version and branch
bitbake -e linux-variscite | grep "^PV="
# Output: PV="5.15.71+gitAUTOINC+hash"

bitbake -e linux-variscite | grep "SRCBRANCH"
# Output: SRCBRANCH="lf-5.15.y_var01"
```

## Working with Yocto Devshell

### Starting the Devshell

```bash
# Start kernel devshell (this is your starting point)
bitbake -c devshell virtual/kernel

# You're now in the kernel source directory with all environment variables set
```

### Understanding the Devshell Environment

```bash
# In devshell, check important variables:
echo "Current directory: $PWD"
echo "Architecture: $ARCH"
echo "Cross compiler: $CROSS_COMPILE"

# Typical output:
# Current directory: /workdir/tmp/work-shared/imx8mp-var-som-mlx75027/kernel-source  (SOURCE directory)
# Architecture: arm64
# Cross compiler: aarch64-poky-linux-

# IMPORTANT: You're in the SOURCE directory, but make commands use BUILD directory
# Build directory: /workdir/tmp/work/imx8mp_var_som_mlx75027-poky-linux/linux-variscite/5.15.60+gitAUTOINC+740e6c7a7b-r2/build
```

### Key Directory Structure

```bash
# Source directory (where you are in devshell)
/workdir/tmp/work-shared/imx8mp-var-som-mlx75027/kernel-source/

# Build directory (where .config and defconfig are created)
/workdir/tmp/work/imx8mp_var_som_mlx75027-poky-linux/linux-variscite/5.15.60+gitAUTOINC+740e6c7a7b-r2/build/
```

## Basic Kernel Configuration Workflow

### Step 1: Prepare Configuration

```bash
# In devshell, the .config file is already present
# IMPORTANT: Always run olddefconfig first!
make olddefconfig

# This step is crucial because:
# 1. It adds any new CONFIG options that weren't in your defconfig
# 2. It resolves dependencies automatically
# 3. It ensures your .config is complete and valid
# 4. It prevents menuconfig from showing unnecessary prompts
```

### Step 2: Interactive Configuration

```bash
# Now run interactive configuration
make menuconfig

# Navigate through the menu system:
# - Use arrow keys to navigate
# - Use space to toggle options
# - Use '/' to search for specific options
# - Use '?' for help on any option
# - Press 'S' to save, then 'Q' to quit
```

### Step 3: Example - Enabling ToF Camera Support

```bash
# In menuconfig, navigate to:
# Device Drivers --->
#   Multimedia support --->
#     Media drivers --->
#       [*] Media Controller API
#       [*] V4L2 sub-device userspace API
#       Camera sensor devices --->
#         <M> MLX75027 ToF sensor support

# For MIPI CSI support:
# Device Drivers --->
#   Multimedia support --->
#     Media drivers --->
#       Platform devices --->
#         <M> i.MX8 MIPI CSI-2 receiver
#         <M> i.MX8 Image Sensing Interface (ISI)

# Save and exit (S, then Q)
```

### Step 4: Generate defconfig

```bash
# Generate the minimal defconfig
make savedefconfig

# IMPORTANT: defconfig is created in BUILD directory, not source directory
# Find the build directory from the make output:
# make[1]: Entering directory '/workdir/tmp/work/imx8mp_var_som_mlx75027-poky-linux/linux-variscite/5.15.60+gitAUTOINC+740e6c7a7b-r2/build'

BUILD_DIR="/workdir/tmp/work/imx8mp_var_som_mlx75027-poky-linux/linux-variscite/5.15.60+gitAUTOINC+740e6c7a7b-r2/build"

# Check defconfig in build directory
ls -la "$BUILD_DIR/defconfig"
# Output: -rw-r--r-- 1 1000 1000 32091 Jul 10 14:04 defconfig
```

### Step 5: Verify Your Changes

```bash
# Check if your options are enabled
grep -E "CONFIG_VIDEO_MLX7502X|CONFIG_MXC_MIPI_CSI" .config

# Expected output:
# CONFIG_VIDEO_MLX7502X=m
# CONFIG_MXC_MIPI_CSI=m
# CONFIG_IMX8_MIPI_CSI2=m

# Exit devshell when done
exit
```

## Common Issues and Solutions

### Issue 1: Environment Variables Not Set

```bash
# If ARCH or CROSS_COMPILE are not set in devshell:
export ARCH=arm64
export CROSS_COMPILE=aarch64-poky-linux-
```

### Issue 2: defconfig Not Found

```bash
# Remember: defconfig is created in BUILD directory, not source directory
# Look for the build directory path in make output
# Example: make[1]: Entering directory '/path/to/build'
```

### Issue 3: Configuration Changes Not Saved

```bash
# Always run olddefconfig before menuconfig
make olddefconfig
make menuconfig

# Always save in menuconfig (press 'S' before 'Q')
```

## Next Steps

In the next part of this series, we'll cover:
- **Part 2**: Creating machine-specific defconfig files for your Yocto layer
- **Part 3**: Managing bbappend files for different machines
- **Part 4**: Git-based version control for configuration changes

## Quick Reference

```bash
# Essential devshell workflow:
bitbake -c devshell virtual/kernel
make olddefconfig
make menuconfig
make savedefconfig
# Copy defconfig from build directory to your Yocto layer
exit
```

This workflow forms the foundation for all kernel configuration management in Yocto. Master these basics before moving on to more advanced topics in the next parts of this series.
