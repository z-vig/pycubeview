# pycubeview 🔎

A Flexible and Interactive Spectral (and more!) Image Viewer for Python

[![Unit Tests](https://github.com/z-vig/pycubeview/actions/workflows/ci.yml/badge.svg)](https://github.com/z-vig/pycubeview/actions/workflows/ci.yml) [![License: MIT](https://cdn.prod.website-files.com/5e0f1144930a8bc8aace526c/65dd9eb5aaca434fac4f1c34_License-MIT-blue.svg)](/LICENSE)
---

## Motivation ✨

Whether it's an imaging spectrometer or an InSAR time-series, many remotely
sensed scientific data comes in the form of a cube, which is here defined as
any dataset that has spatial information in two dimensions and measured values
in a third dimension. Below are listed some examples of scientific data cubes:

- Hyperspectral Imagery
- Multispectral Imagery
- Spectral Maps from lab spectrometers
- InSAR Time Series
- Cloud Cover Evolution Map
- LiDAR return counts
- Scanning medical imagery
- RGB Images
- General Vector Fields
- And Many More!

## Installation ⬇️

### GUI Application 💻
To use the GUI Application, download PyCubeView **[here](https://github.com/z-vig/pycubeview/releases/latest)**!

Support is available for Linux (Ubuntu Distribution), MacOS and Windows.

For Windows Users:
1) Download the .zip file and extract all files
2) The cubeview.exe file is found at: PyCubeView-windows > main.dist > cubeview.exe

For Mac Users:
1) Downloading the .zip file will automatically give you a .app file
2) PyCubeView currently ships unsigned (because that costs money 💲), so you
   must change the permissions on the file before you run it.
3) From within the directory you downloaded the file to, run:

```bash
xattr -d com.apple.quarantine CubeView.app
```
4) You can now double-click to run the app

### Python API 🐍
`pycubeview` can be directly install from the Python Package Index using `pip`.

```bash
pip install pycubeview
```

## Usage ⚙️

### GUI Application 💻


### Python API 🐍
The basic CubeView GUI can be opened directly from the command line by ensuring you are in a python environment that has `pycubeview` installed and running

```bash
cubeview.exe
```

The CubeView GUI can also be started from a python script.

```python
from pycubeview import open_cubeview
open_cubeview(image_data, cube_data, wvl_data)
```
Where the data can optionally provided as either a Numpy-Array or a filepath to one of the supported file types.

## Supported File Types 📂
### Image and Cube Data
#### `spectralio` files

  - .geospcub
  - .spcub

#### `rasterio`-compatible files
  - .img
  - .bsq
  - .tif

### Wavelength Data
  - .wvl
  - .hdr
  - .txt
  - .csv


