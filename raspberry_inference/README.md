# 🍓 Raspberry Pi Inference Guide

[🇨🇵 Français](README_FR.md) | [🇬🇧 English](README.md)

This guide details the steps necessary to configure the hardware and software environment to run the model inference on the Raspberry Pi.

---

## 🛠 Hardware

**Note:** This configuration is specifically designed for a portion of the vest, more precisely the **robot's right torso**.

### 1. MCP3008 Wiring
The MCP3008 is used for analog-to-digital conversion (especially for the right torso sensor).

![MCP chip](../docs/MCP3008.jpg)

**Wiring diagram:**

Ensure the power and data pins are properly connected to the Raspberry Pi GPIOs:

| MCP3008 Pin | Raspberry Pi Pin | Function |
| :--- | :--- | :--- |
| **VDD** | Pin 1 or 17 (3.3V) | Positive Power Supply |
| **VREF** | Pin 1 or 17 (3.3V) | Reference Voltage |
| **AGND** | Pin 6, 9... (GND) | Analog Ground |
| **DGND** | Pin 6, 9... (GND) | Digital Ground |
| **CLK** | GPIO 12 | Clock |
| **DOUT** | GPIO 16 | MISO (Master In Slave Out) |
| **DIN** | GPIO 20 | MOSI (Master Out Slave In) |
| **CS/SHDN** | GPIO 21 | Chip Select |

### 2. Vest Assembly
To connect the vest sensors (piezo-resistive sensor), a **47 kΩ** resistor is required to ensure measurement stability. 
**Attention:** for the piezo-resistive sensor, you must imperatively use the clips with a "P" as the initial.

![electrical schematic](../docs/schema_elec.png)

---

## 💻 Software

### 1. Prerequisites
* A Raspberry Pi with an installed operating system (Raspberry Pi OS recommended).
* An active internet connection.

### 2. System Update
Start by updating your system and installing the necessary libraries for GPIO port management:

```bash
sudo apt update && sudo apt full-upgrade -y
sudo apt install python3-gpiozero python3-lgpio -y
```

### 3. Installing `uv` Package Manager
We use **uv**, an extremely fast Python dependency manager, to manage our virtual environment.

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# (Optional) Restart your terminal or source your profile to enable 'uv' in PATH
source $HOME/.cargo/env
```

### 4. Cloning and Project Preparation
The inference model is already included in the repository.

```bash
# Clone the repository
git clone https://github.com/Juste-Leo2/QT-Touch.git
cd QT-Touch/raspberry_inference

# Create the virtual environment with Python 3.11
uv venv -p 3.11
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements_rpi.txt
```

### 5. Running Inference
Once the environment is ready, run the inference script:

```bash
uv run inference.py
```

### 6. Inference linked with the QTRobot-Interaction project
If you are using this code within the [QTRobot-Interaction](https://github.com/Juste-Leo2/QTRobot-Interaction) project, the setup process follows the same steps (1 to 5).

The only difference lies in the `RaspberryManager` class configuration executed within the `main.py` file of the other repository (`QTRobot-Interaction`). Here you'll need to adapt it to the Raspberry Pi in question with the correct path:

```python
        # Config Raspberry Pi pour la veste
        print("\n🧤 Initialisation Raspberry Pi (veste)...")
        raspberry = RaspberryManager(
            ip="192.168.100.3",        # IP du Raspberry
            user="qt",
            password="qtrobot",
            script_path="/home/.../QT-Touch_raspberry_inference/inferenceQT0526.py",
            venv_path="/home/.../QT-Touch_raspberry_inference/.venv/bin/activate",
            port=65432
        )
```

---
*Note: Ensure the SPI interface is enabled on your Raspberry Pi via `sudo raspi-config` (Interface Options > SPI).*
