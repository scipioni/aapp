"""Kannala-Brandt (equidistant) fisheye calibration via cv2.fisheye.

Action-camera lenses exceed the convergence range of the Brown-Conrady
polynomial used by ``cv2.calibrateCamera``; the equidistant model stays
numerically stable beyond 90° half-FOV. Calibrate separately for every
sensor mode you shoot in (still vs. video, 4:3 vs. 16:9) — the active
sensor area, and therefore K, changes per mode.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

from aapp.workspace import Workspace

logger = logging.getLogger(__name__)

MIN_VALID_FRAMES = 10


@dataclass
class CalibrationResult:
    K: "object"  # (3, 3) intrinsics
    D: "object"  # (4, 1) equidistant distortion coefficients k1..k4
    resolution: tuple[int, int]  # (width, height)
    rms_error: float
    used_frames: int

    def save(self, path: Path) -> None:
        import numpy as np

        np.savez(
            path, K=self.K, D=self.D, resolution=self.resolution,
            rms_error=self.rms_error, used_frames=self.used_frames,
        )
        logger.info("Calibration saved to %s", path)

    @classmethod
    def load(cls, path: Path) -> "CalibrationResult":
        import numpy as np

        if not Path(path).exists():
            raise FileNotFoundError(
                f"Calibration parameters missing at {path}. Run the calibrate step first."
            )
        data = np.load(path)
        return cls(
            K=data["K"],
            D=data["D"],
            resolution=tuple(int(v) for v in data["resolution"]),
            rms_error=float(data["rms_error"]),
            used_frames=int(data["used_frames"]),
        )


def calibrate_fisheye(
    ws: Workspace,
    checkerboard: tuple[int, int] = (9, 6),
    square_size_m: float = 0.025,
) -> CalibrationResult:
    """Detect checkerboard corners and solve the equidistant model.

    ``checkerboard`` counts inner corners (columns, rows). Requires at least
    ``MIN_VALID_FRAMES`` frames with a detected board, shot in the exact
    capture mode used for acquisition.
    """
    import cv2
    import numpy as np

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 1e-6)

    # cv2.fisheye requires object points shaped (1, N, 3), not the (N, 3)
    # accepted by standard calibration.
    cols, rows = checkerboard
    objp = np.zeros((1, cols * rows, 3), np.float32)
    objp[0, :, :2] = np.mgrid[0:cols, 0:rows].T.reshape(-1, 2)
    objp *= square_size_m

    obj_points = []
    img_points = []
    resolution: tuple[int, int] | None = None

    images = ws.list_images(ws.calibration_dir)
    if not images:
        raise FileNotFoundError(
            f"No calibration images found in {ws.calibration_dir}."
        )

    for fname in images:
        img = cv2.imread(str(fname))
        if img is None:
            logger.warning("Unreadable image skipped: %s", fname)
            continue
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        frame_res = gray.shape[::-1]  # (width, height)
        if resolution is None:
            resolution = frame_res
        elif frame_res != resolution:
            raise ValueError(
                f"Mixed resolutions in calibration set: {fname} is {frame_res}, "
                f"expected {resolution}. Calibrate one sensor mode at a time."
            )

        found, corners = cv2.findChessboardCorners(
            gray, checkerboard,
            cv2.CALIB_CB_ADAPTIVE_THRESH + cv2.CALIB_CB_FAST_CHECK + cv2.CALIB_CB_FILTER_QUADS,
        )
        if not found:
            logger.debug("No checkerboard in %s", fname)
            continue
        obj_points.append(objp)
        img_points.append(cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria))

    n_ok = len(obj_points)
    if n_ok < MIN_VALID_FRAMES:
        raise ValueError(
            f"Insufficient valid calibration frames ({n_ok}/{MIN_VALID_FRAMES}). "
            "Capture more board orientations covering the full frame, "
            "especially the corners."
        )

    K = np.zeros((3, 3))
    D = np.zeros((4, 1))
    rvecs = [np.zeros((1, 1, 3), dtype=np.float64) for _ in range(n_ok)]
    tvecs = [np.zeros((1, 1, 3), dtype=np.float64) for _ in range(n_ok)]

    # CALIB_CHECK_COND makes the solver verify projection-matrix conditioning
    # and raise instead of silently converging on a degenerate dataset.
    flags = (
        cv2.fisheye.CALIB_RECOMPUTE_EXTRINSIC
        + cv2.fisheye.CALIB_CHECK_COND
        + cv2.fisheye.CALIB_FIX_SKEW
    )

    try:
        rms, K, D, _, _ = cv2.fisheye.calibrate(
            obj_points, img_points, resolution, K, D, rvecs, tvecs, flags, criteria
        )
    except cv2.error as exc:
        raise RuntimeError(
            "Fisheye calibration failed during model estimation (ill-conditioned "
            "input). Remove blurry or near-duplicate frames and ensure the board "
            "reaches the image borders where distortion is strongest."
        ) from exc

    result = CalibrationResult(
        K=K, D=D, resolution=resolution, rms_error=float(rms), used_frames=n_ok
    )
    logger.info(
        "Calibration completed: RMS %.4f px over %d frames at %s",
        result.rms_error, n_ok, resolution,
    )
    result.save(ws.calibration_file)
    return result
