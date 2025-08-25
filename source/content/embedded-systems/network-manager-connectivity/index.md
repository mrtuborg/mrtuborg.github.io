---
{"publish":true,"title":"Network Manager Connectivity Integration in Linux (Yocto)","description":"Real-world experiences integrating Network Manager with WiFi and cellular connectivity in embedded Linux, including the mistakes, debugging sessions, and practical solutions that actually work","created":"2025-01-07","modified":"2025-08-25T19:36:40.445+02:00","tags":["network-manager","wifi","cellular","modem","connectivity","embedded","yocto","lessons-learned"],"cssclasses":""}
---


This post chronicles my journey integrating comprehensive connectivity support - WiFi and cellular - into an embedded Linux product using Network Manager on Yocto. What started as "just add WiFi support" evolved into a full connectivity overhaul when cellular backup became a requirement mid-project. Here's what I learned, what broke, and what actually works in production.

## Project Evolution: From WiFi-Only to Dual Connectivity

**Initial Scope:** Add WiFi connectivity to an existing industrial IoT device for configuration and monitoring.

**Reality Check:** Three weeks into development, the customer requested cellular backup connectivity for remote deployments. What seemed like a simple addition turned into a complete connectivity architecture redesign.

**Final Implementation:** Dual-mode connectivity with WiFi primary, cellular fallback, and intelligent switching between interfaces.

## The Real Issues I Encountered

### Issue #1: The ModemManager vs Network Manager Dance

**The Problem:**
Initially, I configured Network Manager without considering ModemManager integration. When cellular support was added, I discovered that Network Manager and ModemManager need to cooperate, not compete, for modem control.

**What Went Wrong:**
```bash
# This seemed logical but caused conflicts
systemctl enable NetworkManager
systemctl enable ModemManager
# Both services tried to manage the same USB modem interface
```

**The Debugging Nightmare:**
- Modem would initialize correctly but never establish data connection
- `nmcli` showed the modem as "unavailable" 
- ModemManager logs showed successful AT command sequences
- Network Manager logs showed "device not managed"

**Root Cause:**
Network Manager wasn't configured to use ModemManager as the modem backend. The two services were essentially fighting over device control.

**Solution:**
```bash
# Proper ModemManager integration in NetworkManager.conf
[main]
plugins=keyfile
dhcp=internal

[device]
wifi.scan-rand-mac-address=no

[connection]
wifi.cloned-mac-address=preserve

# Critical: Let ModemManager handle modem devices
[device-modem]
managed=true
```

**Lessons Learned:**
- Read the integration documentation first, not after things break
- ModemManager and Network Manager are designed to work together, not independently
- Test cellular connectivity early, not as an afterthought

### Issue #2: The Silent Firmware Loading Failure

**The Problem:**
WiFi adapter worked perfectly on development boards but failed silently on production hardware with identical kernel configuration.

**The Investigation:**
Development vs production hardware comparison revealed different USB controller chipsets, which affected firmware loading timing.

**What Actually Happened:**
```bash
# Development board (working)
[    2.1] usb 1-1: new high-speed USB device
[    2.3] mt76x0u 1-1:1.0: ASIC revision: 76100044
[    2.8] mt76x0u 1-1:1.0: firmware loaded successfully

# Production hardware (failing)
[    1.8] usb 1-1: new high-speed USB device  
[    1.9] mt76x0u 1-1:1.0: ASIC revision: 76100044
[    2.0] mt76x0u 1-1:1.0: firmware load timeout
```

**Root Cause:**
Production hardware's USB controller enumerated devices faster, but the filesystem containing firmware wasn't ready yet. The driver gave up before `/lib/firmware` was mounted.

**Solution:**
```bash
# Add firmware loading retry mechanism
CONFIG_FW_LOADER_USER_HELPER=y
CONFIG_FW_LOADER_USER_HELPER_FALLBACK=y

# And ensure firmware is available early
echo 'SUBSYSTEM=="firmware", ACTION=="add", RUN+="/bin/sleep 1"' > /etc/udev/rules.d/50-firmware-delay.rules
```

**Lessons Learned:**
- Timing issues are the worst kind of hardware-dependent bugs
- Always test on actual production hardware, not just development boards
- Firmware loading is more fragile than it appears

### Issue #3: The Cellular Modem Power Management Trap

**The Problem:**
Cellular modem would work perfectly for hours, then suddenly become unresponsive. No amount of AT commands would revive it until a full power cycle.

**The Debugging Process:**
- Initially suspected thermal issues (it wasn't)
- Checked power supply stability (it was fine)
- Analyzed cellular network logs (no obvious problems)
- Finally discovered the issue was USB autosuspend

**What Was Happening:**
```bash
# USB autosuspend was enabled by default
echo 'auto' > /sys/bus/usb/devices/1-1/power/control

# Modem would suspend after 2 seconds of inactivity
# But wouldn't wake up properly from suspend
```

**The Real Issue:**
The Quectel EC25 modem firmware had a bug where it wouldn't properly handle USB resume after autosuspend. This is apparently a known issue with certain firmware versions, but not documented anywhere obvious.

**Solution:**
```bash
# Disable USB autosuspend for cellular modems
echo 'on' > /sys/bus/usb/devices/1-1/power/control

# Make it permanent via udev rule
echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="2c7c", ATTRS{idProduct}=="0125", ATTR{power/control}="on"' > /etc/udev/rules.d/99-modem-power.rules
```

**Lessons Learned:**
- USB power management and cellular modems don't always play nicely
- Vendor documentation often omits critical firmware quirks
- When debugging intermittent issues, always check power management first

### Issue #4: The Network Interface Priority Confusion

**The Problem:**
With both WiFi and cellular active, the system would randomly choose which interface to use for outbound connections, leading to unpredictable routing behavior.

**Expected Behavior:**
WiFi primary, cellular backup with automatic failover.

**Actual Behavior:**
```bash
# Route table chaos
default via 192.168.1.1 dev wlan0 proto dhcp metric 600
default via 10.64.64.64 dev wwan0 proto dhcp metric 700
# Sometimes wwan0 would get lower metric and become primary
```

**Root Cause:**
Network Manager's automatic metric assignment wasn't consistent across reboots, and I hadn't configured connection priorities properly.

**Solution:**
```bash
# Set explicit connection priorities
nmcli connection modify "WiFi-Connection" connection.autoconnect-priority 10
nmcli connection modify "Cellular-Connection" connection.autoconnect-priority 5

# Configure route metrics explicitly
nmcli connection modify "WiFi-Connection" ipv4.route-metric 100
nmcli connection modify "Cellular-Connection" ipv4.route-metric 200
```

**Lessons Learned:**
- Network Manager's defaults aren't always intuitive for multi-interface scenarios
- Explicit configuration beats hoping for smart defaults
- Test failover scenarios thoroughly, not just initial connectivity

## Kernel Configuration Journey: The Complete Picture

Before diving into Yocto integration, let me share the complete kernel configuration journey that made this connectivity setup work. This was one of the most time-consuming parts of the project, and getting it right was crucial for everything else to function.

### Change 1: RFKILL Configuration
```bash
CONFIG_RFKILL=y                    # Required for Network Manager to control RF device states
CONFIG_RFKILL_LEDS=y               # Enables LED indicators for RF kill switch status
CONFIG_RFKILL_INPUT=y              # Allows hardware RF kill switches to generate input events
```

**Why This Matters:**
As mentioned in Issue #1, RFKILL support is essential for Network Manager to properly manage RF devices. Even without physical kill switches, the software RFKILL interface is used internally.

**Testing Approach:**
```bash
# Verify RFKILL functionality
rfkill list
rfkill block wifi && rfkill unblock wifi
dmesg | grep rfkill
```

### Change 2: EEPROM Support
```bash
CONFIG_EEPROM_93CX6=y              # Enables support for 93CX6 EEPROMs used by WiFi adapters for calibration data
```

**The Hidden Dependency:**
Many WiFi adapters store calibration data and MAC addresses in 93CX6 EEPROMs. Without this support, adapters may initialize but perform poorly or use random MAC addresses.

### Change 3: Cellular Modem MBIM Support
```bash
CONFIG_USB_NET_CDC_MBIM=y          # Enables Mobile Broadband Interface Model protocol for 4G/5G modems
```

**Critical for Modern Modems:**
Mobile Broadband Interface Model (MBIM) is the standard protocol for 4G/5G modems. This was essential for the Quectel EC25 modem integration.

### Change 4: QMI Protocol Support
```bash
CONFIG_USB_NET_QMI_WWAN=y          # Enables Qualcomm MSM Interface protocol for cellular modems
```

**Dual Protocol Strategy:**
Some modems support both QMI and MBIM. Having both enabled provides flexibility and better compatibility across different modem firmware versions.

### Change 5: Complete MediaTek WiFi Driver Stack
```bash
CONFIG_MT7601U=m                   # Driver for MediaTek MT7601U USB WiFi adapters
CONFIG_MT76_CORE=m                 # Core library for all MediaTek MT76xx series WiFi drivers
CONFIG_MT76_LEDS=y                 # LED support for MediaTek WiFi adapters
CONFIG_MT76_USB=m                  # USB transport layer for MediaTek MT76xx drivers
CONFIG_MT76x02_LIB=m               # Common library for MT76x0 and MT76x2 series
CONFIG_MT76x02_USB=m               # USB-specific code for MT76x0 and MT76x2 series
CONFIG_MT76_CONNAC_LIB=m           # Library for newer CONNAC architecture MediaTek chips
CONFIG_MT76x0_COMMON=m             # Common code for MT76x0 series WiFi adapters
CONFIG_MT76x0U=m                   # USB driver for MT76x0 series WiFi adapters
CONFIG_MT76x2_COMMON=m             # Common code for MT76x2 series WiFi adapters
CONFIG_MT76x2U=m                   # USB driver for MT76x2 series WiFi adapters
CONFIG_MT7615_COMMON=m             # Common code for MT7615 series WiFi adapters
CONFIG_MT7663_USB_SDIO_COMMON=m    # Common code for MT7663 USB/SDIO WiFi adapters
CONFIG_MT7663U=m                   # USB driver for MT7663 WiFi adapters
```

**The Dependency Web:**
This is where I learned about the complexity of modern WiFi driver stacks. Each module has specific dependencies:

- `MT76_CORE`: Foundation for all MediaTek 76xx series
- `MT76_USB`: USB transport layer
- `MT76x02_LIB` + `MT76x02_USB`: Common code for 76x0/76x2 series
- `MT76_CONNAC_LIB`: Newer CONNAC architecture support
- `MT7615_COMMON` + `MT7663_USB_SDIO_COMMON`: Support for newer chipsets

**The Module Loading Challenge:**
Missing even one dependency resulted in silent failures. I created a module loading script to ensure proper order:

```bash
#!/bin/bash
# /usr/local/bin/load-wifi-modules.sh
modprobe mt76-core
modprobe mt76-usb
modprobe mt76x02-lib
modprobe mt76x02-usb
modprobe mt76-connac-lib
modprobe mt76x0-common
modprobe mt76x0u
# Continue for all required modules...
```

### Change 6: Additional WiFi Adapter Support
```bash
CONFIG_USB_ZD1201=m                # Driver for ZyDAS ZD1201 USB WiFi adapters
CONFIG_ZD1211RW=m                  # Driver for ZyDAS ZD1211/ZD1211B USB WiFi adapters
```

**Backup Adapter Strategy:**
These drivers support older ZyDAS-based USB WiFi adapters. Having multiple driver options proved valuable during development when primary adapters failed or weren't available.

### The Complete Kernel Configuration Testing Matrix

For each configuration change, I developed a systematic testing approach:

**RFKILL Testing:**
```bash
# Test 1: Device enumeration
rfkill list
# Expected: WiFi and other RF devices listed

# Test 2: Software blocking
rfkill block wifi
nmcli device status  # Should show WiFi as unavailable
rfkill unblock wifi
nmcli device status  # Should show WiFi as available

# Test 3: LED functionality (if hardware supports)
rfkill block wifi && sleep 1 && rfkill unblock wifi
# Expected: LED state changes
```

**MediaTek Driver Testing:**
```bash
# Test 1: Module loading
lsmod | grep mt76
# Expected: All required modules loaded

# Test 2: Hardware detection
lsusb | grep -i mediatek
dmesg | grep mt76
# Expected: Device recognized and initialized

# Test 3: Interface creation
ip link show | grep wlan
# Expected: wlan interface appears
```

**Cellular Modem Testing:**
```bash
# Test 1: USB device recognition
lsusb | grep -i quectel
# Expected: Modem appears as USB device

# Test 2: QMI/MBIM interface creation
ip link show | grep wwan
# Expected: wwan interface appears

# Test 3: ModemManager detection
mmcli -L
# Expected: Modem listed and accessible
```

## Yocto Integration Reality Check

### Custom Recipe Complexity

Adding connectivity support required more Yocto recipes than initially anticipated:

```
# WiFi drivers - Realtek USB adapters
8812au_0.0.0.bb           # Realtek RTL8812AU
8814au_0.0.0.bb           # Realtek RTL8814AU  
8821au_0.0.0.bb           # Realtek RTL8821AU
8821cu_0.0.0.bb           # Realtek RTL8821CU
8852bu_0.0.0.bb           # Realtek RTL8852BU
8852cu_0.0.0.bb           # Realtek RTL8852CU
88x2bu_0.0.0.bb           # Realtek RTL88x2BU

# WiFi drivers - MediaTek
mt76_git.bb               # MediaTek WiFi drivers

# Cellular modem support  
libqmi_1.30.8.bb          # QMI protocol library
libmbim_1.26.4.bb         # MBIM protocol library
modemmanager_1.18.12.bb   # Modem management daemon

# Network management
networkmanager_1.32.12.bb # Network Manager with cellular support
```

**The Realtek Recipe Challenge:**
Each Realtek adapter required a custom recipe because the drivers aren't mainlined. This meant:
- Managing out-of-tree driver sources
- Handling kernel version compatibility
- Dealing with GPL vs proprietary licensing issues
- Cross-compilation configuration for each chipset

**Example Recipe Structure:**
```bash
# 8812au_0.0.0.bb
SUMMARY = "Realtek RTL8812AU USB WiFi driver"
LICENSE = "GPLv2"
LIC_FILES_CHKSUM = "file://LICENSE;md5=..."

SRC_URI = "git://github.com/aircrack-ng/rtl8812au.git;branch=v5.6.4.2"
SRCREV = "..."

inherit module

EXTRA_OEMAKE = "ARCH=${TARGET_ARCH} CROSS_COMPILE=${TARGET_PREFIX} KSRC=${STAGING_KERNEL_DIR}"
```

**The Recipe Dependency Hell:**
Each recipe brought its own dependency chain, and version compatibility became a nightmare. ModemManager 1.18 required libqmi 1.30+, but our base Yocto layer had libqmi 1.28.

**Solution:**
Created a custom layer with version-locked dependencies and comprehensive testing matrix.

**Lessons Learned:**
- Plan for recipe complexity from the start
- Version compatibility testing is not optional
- Custom layers require ongoing maintenance commitment

### Kernel Configuration Gotchas

**The USB Serial Driver Surprise:**
Cellular modems need USB serial drivers, but not the ones you'd expect:

```bash
# This seemed obvious but wasn't sufficient
CONFIG_USB_SERIAL=y
CONFIG_USB_SERIAL_OPTION=y

# Actually needed for Quectel modems
CONFIG_USB_SERIAL_WWAN=y
CONFIG_USB_WDM=y           # For QMI/MBIM protocols
CONFIG_USB_NET_QMI_WWAN=y  # For data connection
```

**The Firmware Blob Challenge:**
WiFi adapters need firmware, and getting licensing right in Yocto is tricky:

```bash
# Had to create custom firmware recipe
SUMMARY = "Firmware for MediaTek WiFi adapters"
LICENSE = "Proprietary"
LIC_FILES_CHKSUM = "file://LICENSE;md5=..."

# And handle redistribution restrictions
INSANE_SKIP_${PN} = "arch"
FILES_${PN} = "/lib/firmware/mediatek/*"
```

**Lessons Learned:**
- Kernel configuration for connectivity is more complex than it appears
- Firmware licensing requires careful attention in commercial products
- Test with actual hardware early and often

## What Actually Works in Production

### Robust Connection Management

**Connection Priority Script:**
```bash
#!/bin/bash
# /usr/local/bin/connectivity-manager.sh

check_wifi() {
    nmcli -t -f ACTIVE,SSID dev wifi | grep -q "^yes:"
}

check_cellular() {
    mmcli -L | grep -q "Modem"
    return $?
}

manage_connections() {
    if check_wifi; then
        echo "WiFi active, disabling cellular"
        nmcli connection down "Cellular-Connection" 2>/dev/null
    elif check_cellular; then
        echo "WiFi unavailable, enabling cellular"
        nmcli connection up "Cellular-Connection"
    else
        echo "No connectivity available"
    fi
}

# Run every 30 seconds
while true; do
    manage_connections
    sleep 30
done
```

**Lessons Learned:**
- Simple scripts often work better than complex Network Manager dispatcher scripts
- Monitor both interfaces continuously, don't assume they'll stay stable
- Log everything for debugging production issues

### Reliable Modem Initialization

**Modem Reset Service:**
```bash
# /etc/systemd/system/modem-reset.service
[Unit]
Description=Reset cellular modem on startup
Before=ModemManager.service

[Service]
Type=oneshot
ExecStart=/usr/local/bin/modem-reset.sh
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

**Reset Script:**
```bash
#!/bin/bash
# /usr/local/bin/modem-reset.sh

# Find modem USB device
MODEM_USB=$(lsusb | grep "2c7c:0125" | cut -d' ' -f2,4 | tr -d ':')

if [ -n "$MODEM_USB" ]; then
    echo "Resetting modem at $MODEM_USB"
    echo 0 > /sys/bus/usb/devices/$MODEM_USB/authorized
    sleep 2
    echo 1 > /sys/bus/usb/devices/$MODEM_USB/authorized
    sleep 5
fi
```

**Lessons Learned:**
- Cellular modems benefit from clean initialization on boot
- USB reset is more reliable than AT command reset
- Build reset capability into your system from the start

## Recommendations for Similar Projects

### Planning Phase
1. **Assume complexity:** Connectivity integration is never as simple as it looks
2. **Plan for dual-mode:** Even if cellular isn't required initially, design for it
3. **Budget debugging time:** Plan 2-3x your initial estimate for integration testing
4. **Hardware compatibility:** Test with production hardware early

### Implementation Strategy
1. **Start with WiFi:** Get basic connectivity working first
2. **Add cellular incrementally:** Don't try to implement both simultaneously
3. **Test failover scenarios:** Automated testing for connection switching
4. **Monitor in production:** Build telemetry into your connectivity management

### Yocto-Specific Advice
1. **Create custom layer:** Don't modify existing layers for connectivity recipes
2. **Version lock dependencies:** Connectivity stacks are sensitive to version mismatches
3. **Test recipe updates:** Connectivity recipes need more testing than typical packages
4. **Document firmware requirements:** Make licensing and redistribution clear

## Conclusion

Integrating comprehensive connectivity support in embedded Linux taught me that the devil truly is in the details. What seemed like straightforward WiFi and cellular integration turned into a deep dive into USB power management, firmware loading timing, Network Manager internals, and Yocto recipe complexity.

The key insights from this project:

- **Connectivity is a system problem:** It's not just about drivers and Network Manager—it involves power management, timing, firmware, and service coordination
- **Test early with production hardware:** Development boards hide timing and power issues that only surface on production hardware
- **Plan for complexity:** Connectivity integration always takes longer than expected
- **Build monitoring from the start:** You'll need detailed logging to debug production issues

While the journey was more complex than anticipated, the result is a robust connectivity system that handles real-world deployment scenarios reliably. Sometimes the hard way is the only way to learn what actually works in production.

## Technical References

- [Network Manager Documentation](https://networkmanager.dev/) - Essential for understanding connection management
- [ModemManager Documentation](https://www.freedesktop.org/wiki/Software/ModemManager/) - Critical for cellular integration
- [Yocto Kernel Development Manual](https://docs.yoctoproject.org/kernel-dev/) - Kernel configuration in Yocto
- [Linux USB Documentation](https://www.kernel.org/doc/html/latest/driver-api/usb/index.html) - USB power management and device handling
- [QMI Protocol Documentation](https://osmocom.org/projects/quectel-modems/wiki) - For understanding cellular modem communication
