# aapp — Agent Guide

Archaeological Artifact Photogrammetry Pipeline: sub-millimeter 3D digitization of small artifacts (< 20 cm) from a 4K action camera on a motorized turntable. Python orchestration around C++ engines (OpenMVG, OpenMVS) plus OpenCV and Open3D.

## Layout

- `src/aapp/` — the package (src layout, hatchling build)
  - `workspace.py` — artifact workspace directory layout; all derived paths live here
  - `calibration.py` — Kannala-Brandt fisheye calibration via `cv2.fisheye`
  - `undistort.py` — batch remap fisheye → pinhole; saves the new pinhole K for SfM
  - `engines.py` — OpenMVG/OpenMVS subprocess wrappers; command *construction* is separated from *execution* so it stays unit-testable without the binaries
  - `validation.py` — Open3D topology checks, cleaning, Poisson remeshing
  - `pipeline.py` — `ArchaeologicalPhotogrammetryPipeline` stage facade
  - `cli.py` — `aapp` entry point (`init/calibrate/undistort/sfm/dense/validate/run`)
- `tests/` — pytest suite; must run **without** opencv/open3d/numpy or the C++ binaries installed
- `docs/` — installation guide and the photogrammetry reference doc (note: its formulas are corrupted `![][imageN]` export placeholders; don't trust its embedded code samples)

## Conventions

- Heavy imports (`cv2`, `numpy`, `open3d`) are **lazy** — inside functions, never at module top level in code reachable from `aapp/__init__.py` or the CLI. The package must import and the CLI must parse on a bare Python install.
- Pipeline stages are idempotent and restartable; intermediate state (calibration npz, pinhole K, engine outputs) lives in the workspace, never in process memory only.
- Raise errors with actionable messages that name the missing step or file (e.g. "Run the undistort step first").
- Never overwrite input artifacts; write cleaned/derived outputs to new files.

## Commands

```bash
PYTHONPATH=src python3 -m pytest tests -q   # run tests
ruff check src tests                         # lint (config in pyproject.toml)
```

## Git

- Do NOT add `Co-Authored-By` (or any AI attribution trailer) to commit messages.
