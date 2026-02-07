"""
# `pycubeview`

Cube-Viewing GUI for Python.

Many scientific datasets exist in the form of data "cubes". A data "cube" is
any dataset that has the following characteristics:

    1. Can be represented in three total dimensions
    2. Two dimensions representing spatial-like information
    3. The third dimension represents a repeated measurement made at each pixel

The two dimensions representing spatial information will be referred to as
the **image** axes and the third dimension with be referred to as the
**measurement** axis. All three axes together are referred to as a **cube**.

Examples of datasets that could benefit from this software include:

    - DATASET (MEASUREMENT AXIS TYPE)
    - Hyperspectral Imagery (reflectance spectrum)
    - Multispectral Imagery (radiance values)
    - Spectral maps from lab spectrometers (transmission/reflectance spectrum)
    - InSAR Time Series (elevation)
    - Cloud Cover Evolution Map (visibility through time)
    - LiDAR return counts (distance)
    - Scanning medical imagery (e.g., profile through tissue)
    - RGB Images (red, green and blue color channels)
    - General Vector Fields (vector definition)
    - And Many More!
---
"""
