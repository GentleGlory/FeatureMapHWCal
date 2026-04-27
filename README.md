# Feature Map Size Calculator

A PySide6 desktop application for calculating CNN feature map dimensions through stacked convolutional and pooling layers.

## Formula

```
Output = ⌊ (Input + 2 × Padding − Kernel) / Stride ⌋ + 1
```

## Features

- Set input image width and height
- Add multiple layers (Conv2D, MaxPool2D, AvgPool2D) with custom kernel size, stride, and padding
- View per-layer dimension changes in a scrollable results panel
- Final feature map size displayed at the bottom

## Requirements

- Python 3.10+
- PySide6 >= 6.5.0

On Linux, the `libxcb-cursor0` system library is also required:

```bash
sudo apt-get install libxcb-cursor0
```

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```bash
python feature_map_calculator.py
```

## License

MIT
