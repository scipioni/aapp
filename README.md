# aapp — Archaeological Artifact Photogrammetry Pipeline

A Python + C++ pipeline for producing sub-millimeter, photorealistic 3D models of small-scale archaeological artifacts (under 20 cm) using a 4K action camera on a motorized turntable.

## Overview

Standard photogrammetry workflows assume a standard pinhole camera. 4K action cameras break that assumption: their ultra-wide-angle lenses introduce extreme barrel distortion that standard models cannot handle, and their fixed apertures at close range demand careful distance tuning. This pipeline addresses every step from physical acquisition to a topologically-verified, textured `.obj`:

```
Fisheye calibration → Batch undistortion → OpenMVG SfM → OpenMVS dense reconstruction → Texturing → Open3D validation
```

## Key Features

- **Kannala-Brandt (equidistant) calibration** via `cv2.fisheye` — the only model numerically stable beyond 90° FOV
- **Per-mode calibration** — separate calibration for each sensor crop (still vs. video, 4:3 vs. 16:9)
- **Turntable multi-orbit capture** — three elevation passes (low / medium / high) at 10° increments = 108 images; a flipped second pass closes the base
- **Cross-polarization** — linear sheets over lights + circular filter on lens eliminates specular highlights before SfM
- **Hybrid C++ execution** — OpenMVG for sparse SfM, OpenMVS for dense MVS and texturing, called via `subprocess`
- **Waechter et al. texturing** — per-face view selection, global + local seam leveling, ABF/LSCM UV unwrapping, full 4K resolution (`--resolution-level 1`)
- **GOATex occlusion-aware texturing** — visibility-layer partitioning for concave interior surfaces (e.g. vessels)
- **Open3D post-processing** — edge/vertex manifold checks, watertight validation, degenerate triangle removal

## Hardware Requirements

| Component | Specification |
|---|---|
| Camera | 4K action camera (1/2.3" sensor, ~f/2.8 fixed, ~2.92 mm focal length) |
| Turntable | Motorized, Arduino Nano + ULN2003A stepper, 10° indexed steps |
| Lighting | Continuous ring light or diffuse overhead LED panel (~50 cm above center) |
| Polarization | Linear polarizing sheets (lights) + circular polarizing filter (lens) |
| Background | Matte black or white cloth (enables automatic masking) |
| Scale bar | Physical scale bar of known length in scene (metric ground truth) |

## Software Dependencies

```
opencv-python   # cv2.fisheye calibration and undistortion
numpy
open3d          # mesh validation and Poisson reconstruction
OpenMVG         # compiled C++ binaries on PATH
OpenMVS         # compiled C++ binaries on PATH
```

## Acquisition Protocol

1. **Calibrate** — photograph a checkerboard (9×6, 25 mm squares) from many angles in the exact capture mode you will use. Minimum 10 valid frames.
2. **Set subject distance** — place the camera ~30 cm from a 15 cm object so it fills the frame; the short focal length keeps full depth of field sharp.
3. **Cross-polarize** — rotate the circular filter until specular highlights vanish from the artifact surface.
4. **Capture three orbits** — low (15°), medium (30°), high (60°) elevation, 36 shots each via Arduino-triggered shutter.
5. **Flip and repeat** — invert the artifact and capture the base with a visible scale bar in frame.

## Usage

```python
from pipeline import ArchaeologicalPhotogrammetryPipeline

pipeline = ArchaeologicalPhotogrammetryPipeline(workspace_dir="./find_001")

pipeline.calibrate_fisheye_camera()          # Kannala-Brandt model fit
pipeline.batch_undistort_images()            # remap to standard pinhole
pipeline.execute_openmvg_sfm()               # sparse SfM (SIFT + incremental BA)
pipeline.execute_openmvs_reconstruction()    # dense cloud → mesh → texture
pipeline.validate_and_filter_mesh_open3d()   # topology check + interactive view
```

### Workspace layout

```
find_001/
├── calibration/          # checkerboard images
├── images_raw/           # raw turntable captures (.jpg)
├── images_undistorted/   # remapped images fed to OpenMVG
├── openmvg_output/       # sfm_data.bin, sparse cloud
├── openmvs_output/       # dense cloud, mesh, textured_artifact.obj
└── calibration_params.npz
```

## Texturing Configuration

The pipeline uses OpenMVS `TextureMesh` with seam leveling enabled. A known bug causes black texture patches when seam leveling is combined with active mask labels — if this occurs, verify that `--ignore-mask-label` matches your mask identifier, or disable seam leveling as a fallback.

For maximum atlas resolution target `--texture-side 8192` or `16384`; set `--resolution-level 1` to preserve full 4K source detail.

| Parameter | Recommended value | Effect |
|---|---|---|
| `--resolution-level` | `1` | Full 4K texture detail |
| `--local-seam-leveling` | `1` | Poisson blending at patch borders |
| `--global-seam-leveling` | `1` | Cross-image exposure harmonization |
| UV unwrap method | ABF (< 300k faces) / LSCM (< 600k) | Conformal parameterization |
| Padding | 2–4 px | Prevents texture bleeding |

## Post-Processing

Open3D verifies the output mesh before delivery:

- `is_edge_manifold` — every edge shared by 1 or 2 triangles
- `is_vertex_manifold` — star of each vertex is edge-connected
- `is_watertight` — no holes, no self-intersections (required for 3D printing or volumetric analysis)
- Poisson surface reconstruction available for smooth re-meshing (octree depth 9–11 for sub-millimeter artifact detail)

## Reference

Full technical derivations, calibration model comparisons, and parameter tables are in [`docs/photogrammetry-for-artifacts.md`](docs/photogrammetry-for-artifacts.md).
