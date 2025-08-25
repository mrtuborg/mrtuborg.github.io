---
{"publish":true,"title":"Yocto Kernel Configuration - Part 2: Machine-Specific defconfig and bbappend","description":"Learn how to create machine-specific defconfig files and manage bbappend files for different machines in Yocto with linux-variscite.","created":"2025-01-10","modified":"2025-08-25T23:46:26.465+02:00","tags":["yocto","bbappend","defconfig","machine-specific","linux-variscite"],"cssclasses":""}
---


# Yocto Kernel Configuration - Part 2: Machine-Specific defconfig and bbappend

This is the second part of our Yocto kernel configuration series. In this article, we'll focus on creating machine-specific defconfig files and managing bbappend files for different machines with **linux-variscite**.

## Overview

In this part, you'll learn how to:
- ✅ **Create different defconfig files** for development and production
- ✅ **Manage bbappend files** with machine-specific configurations
- ✅ **Use conditional logic** in bbappend files
- ✅ **Organize your Yocto layer** for multiple machine configurations

## Prerequisites

Before starting this part, make sure you've completed:
- **Part 1**: Getting Started with Devshell
- You have a working Yocto build environment
- You understand basic devshell operations

## Understanding Your Current bbappend Setup

If you already have a bbappend file that uses custom defconfig:

```bash
# Your existing linux-variscite_%.bbappend might look like:
FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

SRC_URI += "file://defconfig"

do_configure:prepend () {
    cp "${WORKDIR}/defconfig" "${B}/.config"  
}
```

This approach works but limits you to a single configuration for all machines.

## Creating Machine-Specific defconfig Files

### Step 1: Generate Different Configurations

```bash
# Start devshell
bitbake -c devshell virtual/kernel

# Create development configuration (modules for easier debugging)
make olddefconfig
make menuconfig
# Configure for development:
# - ToF drivers as modules (=m)
# - Debug options enabled
# - Additional logging enabled

make savedefconfig
BUILD_DIR="/workdir/tmp/work/imx8mp_var_som_mlx75027-poky-linux/linux-variscite/5.15.60+gitAUTOINC+740e6c7a7b-r2/build"
cp "$BUILD_DIR/defconfig" ~/defconfig-dev

# Create production configuration (built-in for performance)
make menuconfig
# Configure for production:
# - ToF drivers built-in (=y)
# - Debug options disabled
# - Optimized for size/performance

make savedefconfig
cp "$BUILD_DIR/defconfig" ~/defconfig-prod

exit
```

### Step 2: Copy defconfig Files to Your Yocto Layer

```bash
# Copy the defconfig files to your meta layer
YOCTO_LAYER="/path/to/your/meta-layer/recipes-kernel/linux/linux-variscite"

# Copy different configurations
cp ~/defconfig-dev "$YOCTO_LAYER/defconfig-dev"
cp ~/defconfig-prod "$YOCTO_LAYER/defconfig-prod"

# Keep original as fallback
cp ~/defconfig-dev "$YOCTO_LAYER/defconfig"  # Use dev as default
```

### Step 3: Compare Configurations

```bash
# See what's different between configurations
diff -u "$YOCTO_LAYER/defconfig-dev" "$YOCTO_LAYER/defconfig-prod"

# Example output:
# -CONFIG_VIDEO_MLX7502X=m
# +CONFIG_VIDEO_MLX7502X=y
# -CONFIG_DEBUG_KERNEL=y
# +# CONFIG_DEBUG_KERNEL is not set
```

## Managing bbappend Files for Multiple Machines

### Option 1: Conditional Logic (Most Flexible)

```bash
# Your linux-variscite_%.bbappend
FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

# Add all defconfig files to SRC_URI
SRC_URI += " \
    file://defconfig \
    file://defconfig-dev \
    file://defconfig-prod \
"

# Modified configure prepend with machine detection
do_configure:prepend () {
    # Use machine-specific defconfig if available
    case "${MACHINE}" in
        "imx8mp-var-som-dev"|"imx8mp-var-som-mlx75027-dev")
            if [ -f "${WORKDIR}/defconfig-dev" ]; then
                echo "Using development defconfig for ${MACHINE}"
                cp "${WORKDIR}/defconfig-dev" "${B}/.config"
            else
                echo "Development defconfig not found, using default for ${MACHINE}"
                cp "${WORKDIR}/defconfig" "${B}/.config"
            fi
            ;;
        "imx8mp-var-som-prod"|"imx8mp-var-som-mlx75027-prod")
            if [ -f "${WORKDIR}/defconfig-prod" ]; then
                echo "Using production defconfig for ${MACHINE}"
                cp "${WORKDIR}/defconfig-prod" "${B}/.config"
            else
                echo "Production defconfig not found, using default for ${MACHINE}"
                cp "${WORKDIR}/defconfig" "${B}/.config"
            fi
            ;;
        *)
            echo "Using default defconfig for ${MACHINE}"
            cp "${WORKDIR}/defconfig" "${B}/.config"
            ;;
    esac
}
```

### Option 2: Machine Override (Cleaner)

```bash
# Your linux-variscite_%.bbappend
FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

# Base SRC_URI with default defconfig
SRC_URI += "file://defconfig"

# Machine-specific defconfig files (only added for specific machines)
SRC_URI:append:imx8mp-var-som-dev = " file://defconfig-dev"
SRC_URI:append:imx8mp-var-som-prod = " file://defconfig-prod"

# Base configure function (default behavior)
do_configure:prepend () {
    cp "${WORKDIR}/defconfig" "${B}/.config"
}

# Machine-specific overrides (these override the base function)
do_configure:prepend:imx8mp-var-som-dev () {
    if [ -f "${WORKDIR}/defconfig-dev" ]; then
        echo "Using development defconfig for ${MACHINE}"
        cp "${WORKDIR}/defconfig-dev" "${B}/.config"
    else
        echo "Development defconfig not found, using default"
        cp "${WORKDIR}/defconfig" "${B}/.config"
    fi
}

do_configure:prepend:imx8mp-var-som-prod () {
    if [ -f "${WORKDIR}/defconfig-prod" ]; then
        echo "Using production defconfig for ${MACHINE}"
        cp "${WORKDIR}/defconfig-prod" "${B}/.config"
    else
        echo "Production defconfig not found, using default"
        cp "${WORKDIR}/defconfig" "${B}/.config"
    fi
}
```

### Option 3: Simple Machine-Specific (Recommended)

```bash
# Your linux-variscite_%.bbappend
FILESEXTRAPATHS:prepend := "${THISDIR}/${PN}:"

# Default defconfig for all machines
SRC_URI += "file://defconfig"

# Machine-specific defconfig files (only fetched for specific machines)
SRC_URI:append:imx8mp-var-som-dev = " file://defconfig-dev"
SRC_URI:append:imx8mp-var-som-prod = " file://defconfig-prod"

# Simple machine-specific override
do_configure:prepend:imx8mp-var-som-dev () {
    cp "${WORKDIR}/defconfig-dev" "${B}/.config"
}

do_configure:prepend:imx8mp-var-som-prod () {
    cp "${WORKDIR}/defconfig-prod" "${B}/.config"
}

# Default behavior for other machines (uses base defconfig)
do_configure:prepend () {
    # Only run if no machine-specific override was executed
    if [ ! -f "${B}/.config" ]; then
        cp "${WORKDIR}/defconfig" "${B}/.config"
    fi
}
```

## Version Control Your Changes

### Step 1: Initialize Git in Your Meta Layer

```bash
# In your meta layer directory
cd /path/to/your/meta-layer

# Initialize git if needed
if [ ! -d ".git" ]; then
    git init
    git add .
    git commit -m "Initial meta layer commit"
fi
```

### Step 2: Add New defconfig Files

```bash
# Add the new defconfig files
git add recipes-kernel/linux/linux-variscite/defconfig-dev
git add recipes-kernel/linux/linux-variscite/defconfig-prod
git add recipes-kernel/linux/linux-variscite_%.bbappend

# Create commit
git commit -m "linux-variscite: Add machine-specific defconfig support

Add support for different kernel configurations per machine:
- defconfig-dev: Development configuration with modules and debug
- defconfig-prod: Production configuration with built-in drivers
- Updated bbappend with machine-specific logic

This enables different kernel configurations for development
and production builds of the same hardware platform.

Signed-off-by: Your Name <your.email@example.com>"
```

## Testing Your Configuration

### Step 1: Test Development Build

```bash
# Set machine to development
export MACHINE=imx8mp-var-som-dev

# Clean and rebuild
bitbake -c cleansstate linux-variscite
bitbake linux-variscite

# Verify correct defconfig was used
bitbake -c devshell linux-variscite
# In devshell:
grep -E "CONFIG_VIDEO_MLX7502X|CONFIG_DEBUG_KERNEL" .config
# Should show modules (=m) and debug enabled for dev build
exit
```

### Step 2: Test Production Build

```bash
# Set machine to production
export MACHINE=imx8mp-var-som-prod

# Clean and rebuild
bitbake -c cleansstate linux-variscite
bitbake linux-variscite

# Verify correct defconfig was used
bitbake -c devshell linux-variscite
# In devshell:
grep -E "CONFIG_VIDEO_MLX7502X|CONFIG_DEBUG_KERNEL" .config
# Should show built-in (=y) and debug disabled for prod build
exit
```

## Common Issues and Solutions

### Issue 1: Wrong defconfig Used

```bash
# Check which defconfig was actually copied
bitbake -c devshell linux-variscite
# In devshell:
echo "Current machine: ${MACHINE}"
ls -la "${WORKDIR}"/defconfig*
# Verify the correct files are present
```

### Issue 2: Machine Override Not Working

```bash
# Check machine-specific overrides
bitbake -e linux-variscite | grep "do_configure:prepend"
# Should show the machine-specific function if override is working
```

### Issue 3: SRC_URI Not Fetching Files

```bash
# Check SRC_URI expansion
bitbake -e linux-variscite | grep "^SRC_URI="
# Should show your defconfig files in the list
```

## Best Practices

### 1. Naming Conventions

```bash
# Use descriptive names for defconfig files:
defconfig-dev          # Development configuration
defconfig-prod         # Production configuration
defconfig-debug        # Debug configuration
defconfig-minimal      # Minimal configuration
```

### 2. Documentation

```bash
# Document your configurations in the meta layer
# Create a README.md in recipes-kernel/linux/linux-variscite/
echo "# Kernel Configurations

## defconfig-dev
- ToF drivers as modules for easier debugging
- Debug options enabled
- Additional logging enabled

## defconfig-prod  
- ToF drivers built-in for performance
- Debug options disabled
- Optimized for size/performance
" > "$YOCTO_LAYER/README.md"
```

### 3. Testing Matrix

```bash
# Test all machine configurations
MACHINES="imx8mp-var-som-dev imx8mp-var-som-prod"

for machine in $MACHINES; do
    echo "Testing $machine..."
    export MACHINE=$machine
    bitbake -c cleansstate linux-variscite
    bitbake linux-variscite
    echo "$machine build completed"
done
```

## Next Steps

In the next parts of this series, we'll cover:
- **Part 3**: Git-based version control and patch management
- **Part 4**: Advanced configuration management and automation

## Quick Reference

```bash
# Machine-specific bbappend template:
SRC_URI:append:machine-dev = " file://defconfig-dev"
SRC_URI:append:machine-prod = " file://defconfig-prod"

do_configure:prepend:machine-dev () {
    cp "${WORKDIR}/defconfig-dev" "${B}/.config"
}

do_configure:prepend:machine-prod () {
    cp "${WORKDIR}/defconfig-prod" "${B}/.config"
}
```

This approach gives you flexible, maintainable machine-specific kernel configurations that scale with your project needs.
