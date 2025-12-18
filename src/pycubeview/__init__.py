"""
# `pycubeview`

A Hyperspectral Image Viewer for Python

---

## Example

```python
from pycubeview import open_cubeview
open_cubeview(wvl_fp, image_fp, cube_fp, base_dir_fp)
```
"""

from .cube_view_window import CubeViewWindow
from .helper_functions import open_cubeview

__all__ = ["open_cubeview", "CubeViewWindow"]
