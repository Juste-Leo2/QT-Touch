# QT-Touch 🤖🧤

> [!NOTE]
> **Project continuation:** This project has been extended with new sensors on the jacket. Check out the follow-up here: [**QT-jacket**](https://github.com/Juste-Leo2/QT-jacket)

[🇨🇵 Français](docs/README_FR.md) | [🇬🇧 English](README.md)

**Machine learning-based tactile recognition for the QT robot.**

This project equips the QT robot with a sense of touch using a vest fitted with piezo-resistive sensors. The system leverages a Deep Learning model to classify physical interactions, featuring optimized inference for the Raspberry Pi.

The ultimate goal is to seamlessly integrate this tactile feedback into the [QTRobot-Interaction](https://github.com/Juste-Leo2/QTRobot-Interaction) project to enrich user interactions.

---

## Project Overview

Although this experiment was specifically conducted on the right torso portion of the vest, the methodology and model are designed to be fully reproducible across all tactile zones of the robot.

### Signal Processing Methodology
To ensure accurate detection, we apply the following processing pipeline:
1. **Oversampling** of the raw sensor data.
2. **Digital Filtering**: Application of a moving average system to lock the signal rate at **100Hz**. This eliminates background noise and stabilizes inputs prior to feeding them into the model.

---

## 🧠 Architecture & Training

### Model Architecture
The model was purposefully designed to be lightweight and efficient for real-time execution.

<p align="center">
  <img src="docs/arch.png" alt="Model Architecture" width="400">
</p>

### Training Details
*   **Dataset**: 150 collected examples, evenly distributed across the classes.
*   **Split**: 80% for training, 20% for testing.
*   **Optimization**: Training was conducted over **300 epochs** with close monitoring of the curves to prevent overfitting.

<p align="center">
  <img src="docs/loss_curve.png" alt="Learning Curve" width="500">
</p>

---

## 📊 Results and Performance

The model achieves an **overall accuracy of 93.3%** on the test data.

### Confusion Matrix
We classify interactions into 4 distinct categories:
*   **0: None** (No contact)
*   **1: Tap** (Brief impact)
*   **2: Pinch** (Localized and sustained pressure)
*   **3: Rub** (Lateral movement)

<p align="center">
  <img src="docs/confusion_matrix.png" alt="Confusion Matrix" width="500">
</p>

---

## 🛠️ Installation and Usage

### Dependency Manager
This project uses [**uv**](https://astral.sh/uv), an extremely fast Python package manager.

**Installing `uv`:**
*   **Linux / macOS**:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source $HOME/.cargo/env
    ```
*   **Windows (PowerShell)**:
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

### Environment Setup
```bash
# Clone the repository
git clone https://github.com/Juste-Leo2/QT-Touch.git
cd QT-Touch

# Create the virtual environment and install dependencies
uv venv -p 3.11
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
```

### Execution
*   **To start training**:
    ```bash
    uv run train.py
    ```
*   **For Raspberry Pi inference**:
    See the [Specific Inference Guide](raspberry_inference/README.md).
*   **For data acquisition**:
    Use the `capture_data.py` script (see the inference documentation for hardware setup).

---

## 📜 Additional Information

*   **Inference**: The optimized code for Raspberry Pi is available in the `raspberry_inference/` directory.
*   **License**: This project is licensed under **Apache 2.0**.
