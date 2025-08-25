---
{"publish":true,"title":"Device Tree Configuration for ToF Cameras: i.MX8M Plus Hardware Integration","description":"Complete guide to device tree configuration for ToF camera systems, with real-world examples from i.MX8M Plus Variscite SOM","created":"2025-01-10","modified":"2025-08-25T19:36:20.462+02:00","tags":["device-tree","hardware","mipi-csi","melexis","variscite","integration"],"cssclasses":""}
---


# Device Tree Configuration for ToF Cameras: i.MX8M Plus Hardware Integration

This guide provides comprehensive coverage of device tree configuration for Time of Flight (ToF) camera systems on i.MX8M Plus processors. Using real-world examples from a Variscite SOM implementation, we'll explore how device tree entries translate to hardware functionality and how to customize them for your specific setup.

## Understanding Device Tree for ToF Systems

Device tree describes hardware to the Linux kernel without requiring code changes. For ToF cameras, this includes:

- **MIPI CSI interface configuration**: Lane count, frequencies, timing
- **I2C sensor configuration**: Addresses, power supplies, clocks
- **GPIO assignments**: Laser control, safety systems, reset lines
- **Power management**: Regulators, startup sequences, dependencies
- **Clock configuration**: Sensor clocks, frequencies, sources

## Real-World Example: Variscite i.MX8M Plus SOM

Let's analyze an actual device tree configuration from a production system:

### MIPI CSI Controller Configuration

```dts
&mipi_csi_0 {
    #address-cells = <1>;
    #size-cells = <0>;
    status = "okay";

    port@0 {
        reg = <0>;
        mipi_csi0_ep: endpoint {
            remote-endpoint = <&mlx7502x_mipi0_ep>;
            data-lanes = <4>;                      // 4-lane MIPI configuration
            csis-hs-settle = <13>;                 // High-speed settle time
            csis-clk-settle = <2>;                 // Clock settle time
            csis-wclk;                             // Enable word clock
        };
    };
};
```

**Configuration Analysis:**

- **data-lanes = <4>**: Configures 4-lane MIPI CSI
  - *Why 4 lanes*: ToF sensors generate high data rates (16-bit × multi-phase)
  - *Alternative*: 2-lane configuration (lower bandwidth, may limit frame rate)
  - *Hardware dependency*: Must match physical lane connections

- **csis-hs-settle = <13>**: High-speed settle time
  - *Purpose*: Timing for MIPI receiver to stabilize after lane transitions
  - *Value derivation*: Based on MIPI CSI-2 specification and sensor characteristics
  - *Impact*: Incorrect values cause sync errors or data corruption

- **csis-clk-settle = <2>**: Clock lane settle time
  - *Purpose*: Clock lane stabilization timing
  - *Calculation*: Derived from sensor clock frequency and MIPI timing requirements

### ISI (Image Sensing Interface) Configuration

```dts
&isi_0 {
    status = "okay";

    cap_device {
        status = "okay";
    };

    m2m_device {
        status = "okay";
    };
};
```

**ISI Components Explained:**

- **cap_device**: Capture interface for direct sensor-to-memory
  - *Function*: Handles raw ToF data capture
  - *Buffer management*: Interfaces with V4L2 buffer framework
  - *Format support*: 16-bit grayscale, various resolutions

- **m2m_device**: Memory-to-memory processing
  - *Function*: Format conversion, scaling, processing
  - *ToF usage*: Convert 16-bit raw to 8-bit for JPEG
  - *Performance*: Hardware-accelerated operations

### ToF Sensor I2C Configuration

```dts
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
        reg = <0x57>;                              // I2C address
        pinctrl-names = "default";
        pinctrl-0 = <&pinctrl_csi0>;
        clocks = <&mlx7502x_clk>;

        assigned-clocks = <&mlx7502x_clk>;
        assigned-clock-rates = <8000000>;          // 8MHz sensor clock

        // Power supplies
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
                data-lanes = <1 2 3 4>;                // 4-lane MIPI
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
```

**I2C Configuration Analysis:**

- **reg = <0x57>**: I2C address of ToF sensor
  - *Hardware dependency*: Must match sensor's configured address
  - *Common addresses*: 0x3d, 0x57 (depends on sensor configuration)
  - *Verification*: Use `i2cdetect -y 3` to confirm

- **clock-frequency = <400000>**: I2C bus speed (400kHz)
  - *Standard speeds*: 100kHz (standard), 400kHz (fast), 1MHz (fast+)
  - *ToF consideration*: 400kHz adequate for sensor control
  - *Trade-off*: Higher speeds may cause signal integrity issues

### Power Supply Configuration

```dts
// Clock configuration for ToF sensor
mlx7502x_clk: mlx7502x_clk {
    compatible = "fixed-clock";
    #clock-cells = <0>;
    clock-frequency = <8000000>;                       // 8MHz sensor clock
};

// Power regulators for ToF sensor
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
```

**Power Supply Dependencies:**

- **startup-delay-us = <20000>**: 20ms startup delay
  - *Purpose*: Ensures stable power before dependent regulators enable
  - *Critical for ToF*: Sensors require stable power sequencing
  - *Calculation*: Based on regulator specifications and sensor requirements

- **vin-supply = <&reg_tim_1v2mix>**: Supply dependency
  - *Purpose*: Defines power-up sequence (1v2mix → 1v2)
  - *Safety*: Prevents voltage conflicts during startup
  - *Hardware requirement*: Must match actual power circuit design

## Customizing Device Tree for Your Hardware

### Adapting MIPI CSI Configuration

```dts
// Example: 2-lane MIPI configuration
&mipi_csi_0 {
    port@0 {
        mipi_csi0_ep: endpoint {
            data-lanes = <2>;                      // Change to 2-lane
            csis-hs-settle = <15>;                 // Adjust timing
            csis-clk-settle = <3>;                 // Adjust timing
        };
    };
};
```

**When to Use 2-Lane Configuration
