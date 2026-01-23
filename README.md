# Ehrenfest Model Simulation

A desktop GUI application demonstrating the **Ehrenfest model of diffusion** using **CustomTkinter** and **Matplotlib**.

## Features

- **Left panel:** Ball distribution (Box A / Box B)  
- **Top-right panel:** Simplified state diagram with transition probabilities  
- **Bottom-right panel:** Real-time plot of X (balls in A) vs time  
- **Controls:** Start, Pause, Reset, Timelapse, Animate, Change number of balls (N) and Adjust simulation speed

Pictured below is the simulation window:

<img width="610" height="370" alt="Ehrenfest GUI" src="https://github.com/user-attachments/assets/8ae4d277-2c84-480b-b2cf-443966aafd8f" />

## Download (Windows)

If you just want to run the app on Windows, check out the latest release on the [releases](../../releases) page.

Then:

1. Download the `.exe` file from the latest release.
2. Double‑click it to launch the simulation (no Python installation required).

## Running from Source

### Requirements

- Python 3.8+
- matplotlib
- numpy
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)

### Installation

Install dependencies using `pip`:

```bash
pip install -r requirements.txt
```

### Run

Launch the simulation:

```bash
python main.py
```

## Wiki

Full guide, concepts, and module docs live in the [GitHub Wiki](../../wiki).
