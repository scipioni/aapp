"""Subprocess wrappers for the OpenMVG and OpenMVS C++ engines.

Command construction is kept separate from execution so the exact CLI
invocations can be unit-tested without the binaries installed.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from pathlib import Path
from typing import Sequence

from aapp.workspace import Workspace

logger = logging.getLogger(__name__)


class EngineNotFoundError(RuntimeError):
    """A required OpenMVG/OpenMVS binary is not on PATH."""


def run_command(cmd: Sequence[str | Path]) -> None:
    """Run one engine command, failing fast with a readable error."""
    cmd = [str(c) for c in cmd]
    if shutil.which(cmd[0]) is None:
        raise EngineNotFoundError(
            f"'{cmd[0]}' not found on PATH. Build/install it first — "
            "see docs/installation.md."
        )
    logger.info("Running: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


def k_matrix_arg(K) -> str:
    """Serialize a 3x3 intrinsics matrix to OpenMVG's ``-k`` format.

    OpenMVG expects "f_x;0;c_x;0;f_y;c_y;0;0;1".
    """
    return ";".join(f"{K[i][j]:g}" for i in range(3) for j in range(3))


def openmvg_commands(ws: Workspace, K=None, focal_pixels: float | None = None,
                     ratio: float = 0.8) -> list[list[str]]:
    """Build the OpenMVG sparse-SfM command sequence.

    Images are pre-undistorted with the fisheye calibration, so the scene is
    initialized with a plain pinhole camera (``-c 1``): either the exact
    calibrated K matrix or a focal-length heuristic.
    """
    listing = [
        "openMVG_main_SfMInit_ImageListing",
        "-i", str(ws.undistorted_dir),
        "-o", str(ws.matches_dir),
        "-c", "1",  # PINHOLE_CAMERA: images are already undistorted
    ]
    if K is not None:
        listing += ["-k", k_matrix_arg(K)]
    elif focal_pixels is not None:
        listing += ["-f", f"{focal_pixels:g}"]
    else:
        raise ValueError("Provide either K (calibrated intrinsics) or focal_pixels.")

    sfm_data_json = ws.matches_dir / "sfm_data.json"
    putative = ws.matches_dir / "matches.putative.bin"
    filtered = ws.matches_dir / "matches.f.bin"

    return [
        listing,
        [
            "openMVG_main_ComputeFeatures",
            "-i", str(sfm_data_json),
            "-o", str(ws.matches_dir),
            "-m", "SIFT",
            "-p", "HIGH",  # dense description for sub-millimeter targets
        ],
        [
            "openMVG_main_ComputeMatches",
            "-i", str(sfm_data_json),
            "-o", str(putative),
            "-r", f"{ratio:g}",
        ],
        [
            "openMVG_main_GeometricFilter",
            "-i", str(sfm_data_json),
            "-m", str(putative),
            "-g", "f",  # fundamental-matrix filtering
            "-o", str(filtered),
        ],
        [
            "openMVG_main_SfM",
            "--sfm_engine", "INCREMENTAL",
            "-i", str(sfm_data_json),
            "-m", str(ws.matches_dir),
            "-M", str(filtered),
            "-o", str(ws.reconstruction_dir),
        ],
        [
            "openMVG_main_openMVG2openMVS",
            "-i", str(ws.sfm_data),
            "-d", str(ws.mvs_dir),
            "-o", str(ws.mvs_scene),
        ],
    ]


def openmvs_commands(ws: Workspace, resolution_level: int = 1,
                     refine: bool = True, texture_side: int = 8192,
                     seam_leveling: bool = True,
                     export_type: str = "obj") -> list[list[str]]:
    """Build the OpenMVS densify -> mesh -> refine -> texture sequence.

    ``resolution_level=1`` keeps full 4K source detail; ``seam_leveling``
    enables Waechter-style global exposure harmonization plus local Poisson
    blending at patch borders. If black texture patches appear with masked
    datasets, re-run with ``seam_leveling=False`` (known OpenMVS issue #1251).
    """
    cmds = [
        [
            "DensifyPointCloud",
            str(ws.mvs_scene),
            "-w", str(ws.mvs_dir),
            "--resolution-level", str(resolution_level),
            "-o", str(ws.dense_scene),
        ],
        [
            "ReconstructMesh",
            str(ws.dense_scene),
            "-w", str(ws.mvs_dir),
            "-o", str(ws.mesh_scene),
        ],
    ]
    texture_input = ws.mesh_scene
    if refine:
        cmds.append([
            "RefineMesh",
            str(ws.mesh_scene),
            "-w", str(ws.mvs_dir),
            "--resolution-level", str(resolution_level),
            "-o", str(ws.refined_mesh_scene),
        ])
        texture_input = ws.refined_mesh_scene

    leveling = "1" if seam_leveling else "0"
    cmds.append([
        "TextureMesh",
        str(texture_input),
        "-w", str(ws.mvs_dir),
        "--resolution-level", str(resolution_level),
        "--global-seam-leveling", leveling,
        "--local-seam-leveling", leveling,
        "--max-texture-size", str(texture_side),
        "--export-type", export_type,
        "-o", str(ws.textured_obj),
    ])
    return cmds


def run_openmvg(ws: Workspace, **kwargs) -> None:
    ws.reconstruction_dir.mkdir(parents=True, exist_ok=True)
    ws.matches_dir.mkdir(parents=True, exist_ok=True)
    for cmd in openmvg_commands(ws, **kwargs):
        run_command(cmd)


def run_openmvs(ws: Workspace, **kwargs) -> None:
    for cmd in openmvs_commands(ws, **kwargs):
        run_command(cmd)
