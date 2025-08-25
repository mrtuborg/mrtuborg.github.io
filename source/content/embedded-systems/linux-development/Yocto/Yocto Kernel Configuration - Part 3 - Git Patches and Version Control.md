---
{"publish":true,"title":"Yocto Kernel Configuration - Part 3: Git Patches and Version Control","description":"Learn how to create professional git patches for kernel configuration changes and manage them with proper version control in Yocto.","created":"2025-01-10","modified":"2025-08-25T23:46:26.465+02:00","tags":["yocto","git-patches","version-control","linux-variscite","git-am"],"cssclasses":""}
---


# Yocto Kernel Configuration - Part 3: Git Patches and Version Control

This is the third part of our Yocto kernel configuration series. In this article, we'll focus on creating professional git patches for kernel configuration changes and managing them with proper version control.

## Overview

In this part, you'll learn how to:
- ✅ **Create git patches** compatible with `git am`
- ✅ **Write professional commit messages** with proper attribution
- ✅ **Validate and test patches** before integration
- ✅ **Manage patch series** for complex changes
- ✅ **Integrate patches with bbappend** files

## Prerequisites

Before starting this part, make sure you've completed:
- **Part 1**: Getting Started with Devshell
- **Part 2**: Machine-Specific defconfig and bbappend
- You understand basic git operations
- You have kernel configuration changes ready to patch

## Why Use Git Patches?

### Benefits of Git-Based Patches

```bash
# Git patches provide:
# ✅ Professional attribution with Signed-off-by
# ✅ Detailed commit messages with rationale
# ✅ Compatibility with git am and standard tools
# ✅ Version control integration
# ✅ Easy review and collaboration
# ✅ Maintainable patch series
```

### Comparison with Direct defconfig

```bash
# Direct defconfig approach:
# ❌ No change history or rationale
# ❌ Difficult to review what changed
# ❌ No attribution or authorship
# ❌ Hard to maintain multiple changes

# Git patch approach:
# ✅ Clear change history with explanations
# ✅ Easy to review and understand changes
# ✅ Professional attribution
# ✅ Maintainable and scalable
```

## Creating Git Patches for Kernel Configuration

### Step 1: Set Up Working Directory

```bash
# Create a working directory for patch creation
mkdir -p ~/kernel-config-patches
cd ~/kernel-config-patches

# Copy kernel source from Yocto work directory
KERNEL_WORK_DIR=$(bitbake -e linux-variscite | grep "^S=" | cut -d'"' -f2)
cp -r "$KERNEL_WORK_DIR" ./linux-variscite-work
cd linux-variscite-work

# Initialize git if not already a git repository
if [ ! -d ".git" ]; then
    git init
    git add .
    git commit -m "Initial linux-variscite kernel source from Yocto

Source: linux-variscite based on linux-freescale
Version: $(bitbake -e linux-variscite | grep "^PV=" | cut -d'"' -f2)
Branch: $(bitbake -e linux-variscite | grep "SRCBRANCH" | cut -d'"' -f2)

Signed-off-by: $(git config user.name) <$(git config user.email)>"
fi
```

### Step 2: Configure Git Environment

```bash
# Set up environment for cross-compilation
export ARCH=arm64
export CROSS_COMPILE=aarch64-linux-gnu-

# Ensure git is properly configured
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

### Step 3: Create Configuration Changes

```bash
# Start with base configuration
make imx8mp_var_defconfig

# IMPORTANT: Always run olddefconfig first!
make olddefconfig

# Make your configuration changes
make menuconfig
# Configure your ToF camera support:
# Device Drivers --->
#   Multimedia support --->
#     Media drivers --->
#       [*] Media Controller API
#       [*] V4L2 sub-device userspace API
#       Camera sensor devices --->
#         <M> MLX75027 ToF sensor support

# Save and exit menuconfig
```

### Step 4: Generate and Commit Configuration Patch

```bash
# Generate minimal defconfig
make savedefconfig

# Update the kernel defconfig
cp defconfig arch/arm64/configs/imx8mp_var_defconfig

# Stage the changes
git add arch/arm64/configs/imx8mp_var_defconfig

# Create professional commit
git commit -m "arm64: defconfig: Enable ToF camera support

Enable Melexis MLX75027 ToF sensor and required MIPI CSI drivers:
- CONFIG_VIDEO_MLX7502X=m: MLX75027 ToF sensor driver
- CONFIG_MXC_MIPI_CSI=m: MIPI CSI receiver driver
- CONFIG_IMX8_MIPI_CSI2=m: i.MX8 MIPI CSI-2 support
- CONFIG_IMX8_ISI_CORE=m: Image Sensing Interface core
- CONFIG_IMX8_ISI_CAPTURE=m: ISI capture support

This enables ToF camera functionality for distance measurement
applications on i.MX8MP platforms. Drivers are configured as
modules to allow for easier debugging and development.

Signed-off-by: $(git config user.name) <$(git config user.email)>"
```

### Step 5: Generate Git Patch

```bash
# Generate patch file compatible with git am
mkdir -p ../patches
git format-patch -1 HEAD --output-directory=../patches/

# This creates a file like: 0001-arm64-defconfig-Enable-ToF-camera-support.patch

# Verify the patch
ls -la ../patches/
cat ../patches/0001-arm64-defconfig-Enable-ToF-camera-support.patch
```

## Professional Commit Message Guidelines

### Commit Message Format

```bash
# Good commit message structure:
# <subsystem>: <component>: <brief summary>
# 
# <detailed description>
# 
# <rationale and impact>
# 
# Signed-off-by: Your Name <your.email@example.com>

# Examples:
"arm64: defconfig: Enable ToF camera support"
"kernel: config: Add debug options for development"
"defconfig: Enable additional media drivers"
```

### Key Elements

```bash
# 1. Subsystem prefix (arm64:, kernel:, defconfig:)
# 2. Component (defconfig:, config:)
# 3. Brief summary (50 characters or less)
# 4. Blank line
# 5. Detailed description with CONFIG options
# 6. Rationale for changes
# 7. Signed-off-by line
```

## Patch Validation and Testing

### Step 1: Validate Patch Format

```bash
# Check patch format
file ../patches/0001-*.patch
# Should show: ASCII text

# Check line endings
dos2unix ../patches/0001-*.patch

# Validate patch can be applied
git apply --check ../patches/0001-*.patch
```

### Step 2: Test Patch Application

```bash
# Create test branch
git checkout -b test-patch

# Apply patch
git am ../patches/0001-*.patch

# Verify patch applied correctly
git log --oneline -1
git show HEAD --name-only

# Test configuration build
make ARCH=arm64 imx8mp_var_defconfig
make ARCH=arm64 olddefconfig
grep -E "CONFIG_VIDEO_MLX7502X|CONFIG_MXC_MIPI_CSI" .config

# Return to main branch
git checkout main
git branch -D test-patch
```

### Step 3: Integration Testing

```bash
# Test in Yocto build environment
cd ~/yocto-build-dir

# Copy patch to meta layer
cp ~/kernel-config-patches/patches/0001-*.patch \
   /path/to/meta-layer/recipes-kernel/linux/linux-variscite/

# Update bbappend to include patch
echo 'SRC_URI += "file://0001-arm64-defconfig-Enable-ToF-camera-support.patch"' \
   >> /path/to/meta-layer/recipes-kernel/linux/linux-variscite_%.bbappend

# Test build
bitbake -c cleansstate linux-variscite
bitbake linux-variscite
```

## Managing Patch Series

### Creating Multiple Related Patches

```bash
# For complex changes, create logical patch series
cd ~/kernel-config-patches/linux-variscite-work

# Patch 1: Basic media support
git checkout -b media-support
make menuconfig  # Enable basic media framework
make savedefconfig
cp defconfig arch/arm64/configs/imx8mp_var_defconfig
git add arch/arm64/configs/imx8mp_var_defconfig
git commit -m "arm64: defconfig: Enable basic media framework support

Enable core media framework components:
- CONFIG_MEDIA_SUPPORT=y: Media device support
- CONFIG_MEDIA_CONTROLLER=y: Media Controller API
- CONFIG_VIDEO_DEV=y: Video4Linux core

This provides the foundation for camera and media device support.

Signed-off-by: $(git config user.name) <$(git config user.email)>"

# Patch 2: MIPI CSI support
make menuconfig  # Enable MIPI CSI drivers
make savedefconfig
cp defconfig arch/arm64/configs/imx8mp_var_defconfig
git add arch/arm64/configs/imx8mp_var_defconfig
git commit -m "arm64: defconfig: Enable MIPI CSI drivers

Enable i.MX8MP MIPI CSI interface drivers:
- CONFIG_MXC_MIPI_CSI=m: MIPI CSI receiver driver
- CONFIG_IMX8_MIPI_CSI2=m: i.MX8 MIPI CSI-2 support
- CONFIG_IMX8_ISI_CORE=m: Image Sensing Interface core

This enables MIPI CSI camera interface support for i.MX8MP platforms.

Signed-off-by: $(git config user.name) <$(git config user.email)>"

# Patch 3: ToF sensor support
make menuconfig  # Enable ToF sensor
make savedefconfig
cp defconfig arch/arm64/configs/imx8mp_var_defconfig
git add arch/arm64/configs/imx8mp_var_defconfig
git commit -m "arm64: defconfig: Enable MLX75027 ToF sensor

Enable Melexis MLX75027 ToF sensor support:
- CONFIG_VIDEO_MLX7502X=m: MLX75027 ToF sensor driver

This enables ToF camera functionality for distance measurement
applications on i.MX8MP platforms.

Signed-off-by: $(git config user.name) <$(git config user.email)>"

# Generate patch series
git format-patch main --output-directory=../patches/
```

### Organizing Patch Series

```bash
# Patch series should be logically organized:
# 0001-arm64-defconfig-Enable-basic-media-framework-support.patch
# 0002-arm64-defconfig-Enable-MIPI-CSI-drivers.patch
# 0003-arm64-defconfig-Enable-MLX75027-ToF-sensor.patch

# Benefits:
# ✅ Easier to review individual changes
# ✅ Can apply patches incrementally
# ✅ Better bisectability if issues arise
# ✅ Clear progression of functionality
```

## bbappend Integration

### Single Patch Integration

```bash
# For single patch in your linux-variscite_%.bbappend:
FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://0001-arm64-defconfig-Enable-ToF-camera-support.patch \
"
```

### Patch Series Integration

```bash
# For patch series in your linux-variscite_%.bbappend:
FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += " \
    file://0001-arm64-defconfig-Enable-basic-media-framework-support.patch \
    file://0002-arm64-defconfig-Enable-MIPI-CSI-drivers.patch \
    file://0003-arm64-defconfig-Enable-MLX75027-ToF-sensor.patch \
"
```

### Conditional Patch Application

```bash
# Apply different patches for different machines:
SRC_URI += " \
    file://0001-arm64-defconfig-Enable-basic-media-framework-support.patch \
"

# Development-specific patches
SRC_URI:append:imx8mp-var-som-dev = " \
    file://0002-arm64-defconfig-Enable-debug-options.patch \
    file://0003-arm64-defconfig-Enable-ToF-sensor-modules.patch \
"

# Production-specific patches
SRC_URI:append:imx8mp-var-som-prod = " \
    file://0002-arm64-defconfig-Enable-ToF-sensor-builtin.patch \
"
```

## Version Control Best Practices

### Tagging Patch Versions

```bash
# Tag your patch versions for tracking
cd ~/kernel-config-patches/linux-variscite-work
git tag -a v1.0-tof-patches -m "ToF camera patches v1.0

Initial ToF camera support patches:
- Basic media framework
- MIPI CSI drivers  
- MLX75027 ToF sensor

Tested on: i.MX8MP Variscite SOM"

# List tags
git tag -l
```

### Branching Strategy

```bash
# Use branches for different features
git checkout -b feature/tof-camera
git checkout -b feature/debug-options
git checkout -b feature/performance-tuning

# Merge branches when ready
git checkout main
git merge feature/tof-camera
```

## Troubleshooting

### Common Patch Issues

```bash
# Issue 1: Patch doesn't apply
git apply --check patch.patch
# Fix: Check for whitespace issues, line endings, or context changes

# Issue 2: Wrong patch format
file patch.patch
# Should show: ASCII text, not binary

# Issue 3: Missing Signed-off-by
git commit --amend -s
# Adds Signed-off-by line to last commit
```

## Next Steps

In the final part of this series, we'll cover:
- **Part 4**: Advanced configuration management and automation

## Quick Reference

```bash
# Essential git patch workflow:
git format-patch -1 HEAD --output-directory=patches/
git apply --check patch.patch
git am patch.patch

# Professional commit message:
"subsystem: component: brief summary

Detailed description with CONFIG options
and rationale for changes.

Signed-off-by: Your Name <email@example.com>"
```

This approach ensures your kernel configuration changes are professional, maintainable, and properly attributed for long-term project success.
