"""aapp — Archaeological Artifact Photogrammetry Pipeline.

Sub-millimeter 3D digitization of small-scale artifacts (< 20 cm) from a
4K action camera on a motorized turntable:

    fisheye calibration -> batch undistortion -> OpenMVG SfM
    -> OpenMVS dense reconstruction & texturing -> Open3D validation
"""

from aapp.pipeline import ArchaeologicalPhotogrammetryPipeline
from aapp.workspace import Workspace

__version__ = "0.1.0"

__all__ = ["ArchaeologicalPhotogrammetryPipeline", "Workspace", "__version__"]
