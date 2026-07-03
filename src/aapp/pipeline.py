"""End-to-end pipeline facade.

Each stage is idempotent and restartable: intermediate state (calibration
parameters, pinhole intrinsics, engine outputs) lives in the workspace, so
any stage can be re-run in isolation.
"""

from __future__ import annotations

import logging
from pathlib import Path

from aapp.workspace import Workspace

logger = logging.getLogger(__name__)


class ArchaeologicalPhotogrammetryPipeline:
    """Calibrate -> undistort -> OpenMVG SfM -> OpenMVS MVS -> validate."""

    def __init__(self, workspace_dir: str | Path):
        self.workspace = Workspace(Path(workspace_dir)).ensure()

    def calibrate(self, checkerboard: tuple[int, int] = (9, 6),
                  square_size_m: float = 0.025):
        from aapp.calibration import calibrate_fisheye

        return calibrate_fisheye(self.workspace, checkerboard, square_size_m)

    def undistort(self, balance: float = 0.0):
        from aapp.undistort import batch_undistort

        return batch_undistort(self.workspace, balance=balance)

    def sfm(self, ratio: float = 0.8):
        from aapp.engines import run_openmvg
        from aapp.undistort import load_pinhole_k

        run_openmvg(self.workspace, K=load_pinhole_k(self.workspace), ratio=ratio)

    def dense_reconstruction(self, resolution_level: int = 1, refine: bool = True,
                             texture_side: int = 8192, seam_leveling: bool = True):
        from aapp.engines import run_openmvs

        run_openmvs(
            self.workspace,
            resolution_level=resolution_level,
            refine=refine,
            texture_side=texture_side,
            seam_leveling=seam_leveling,
        )

    def validate(self, clean: bool = True, visualize: bool = False):
        from aapp.validation import validate_mesh

        ws = self.workspace
        report = validate_mesh(
            ws.textured_obj,
            clean=clean,
            output_path=ws.mvs_dir / "textured_artifact_clean.obj",
            visualize=visualize,
        )
        logger.info("Mesh validation report:\n%s", report.summary())
        return report

    def run(self, visualize: bool = False):
        """Execute every stage in order."""
        self.calibrate()
        self.undistort()
        self.sfm()
        self.dense_reconstruction()
        return self.validate(visualize=visualize)
