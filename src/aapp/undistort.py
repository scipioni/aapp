"""Batch undistortion: equidistant fisheye -> central pinhole projection."""

from __future__ import annotations

import logging
from pathlib import Path

from aapp.calibration import CalibrationResult
from aapp.workspace import Workspace

logger = logging.getLogger(__name__)


def batch_undistort(
    ws: Workspace,
    calibration: CalibrationResult | None = None,
    balance: float = 0.0,
    jpeg_quality: int = 98,
) -> tuple[list[Path], "object"]:
    """Remap every raw capture to the pinhole geometry OpenMVG expects.

    ``balance`` in [0, 1] trades cropped-but-clean borders (0) against
    retaining the full distorted FOV with black corners (1). Keep 0 for
    turntable captures where the artifact is centered.

    Returns ``(written_paths, pinhole_K)`` — the undistorted images obey a
    plain pinhole model with intrinsics ``pinhole_K``, which is also saved
    next to the calibration file for the SfM stage.
    """
    import cv2
    import numpy as np

    if calibration is None:
        calibration = CalibrationResult.load(ws.calibration_file)

    raw_images = ws.list_images(ws.raw_images_dir)
    if not raw_images:
        raise FileNotFoundError(f"No raw images found in {ws.raw_images_dir}.")

    new_K = cv2.fisheye.estimateNewCameraMatrixForUndistortRectify(
        calibration.K, calibration.D, calibration.resolution, np.eye(3),
        balance=balance,
    )
    map1, map2 = cv2.fisheye.initUndistortRectifyMap(
        calibration.K, calibration.D, np.eye(3), new_K,
        calibration.resolution, cv2.CV_16SC2,
    )

    written: list[Path] = []
    for img_path in raw_images:
        img = cv2.imread(str(img_path))
        if img is None:
            logger.warning("Unreadable image skipped: %s", img_path)
            continue
        if (img.shape[1], img.shape[0]) != calibration.resolution:
            raise ValueError(
                f"{img_path} is {img.shape[1]}x{img.shape[0]} but calibration "
                f"is for {calibration.resolution}. Recalibrate in the capture "
                "mode used for these images."
            )
        undistorted = cv2.remap(
            img, map1, map2,
            interpolation=cv2.INTER_LANCZOS4,
            borderMode=cv2.BORDER_CONSTANT,
        )
        out_path = ws.undistorted_dir / img_path.name
        cv2.imwrite(str(out_path), undistorted,
                    [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
        written.append(out_path)

    np.savez(ws.pinhole_k_file, K=new_K)
    logger.info("Undistorted %d frames into %s", len(written), ws.undistorted_dir)
    return written, new_K


def load_pinhole_k(ws: Workspace):
    """Load the pinhole intrinsics produced by :func:`batch_undistort`."""
    if not ws.pinhole_k_file.exists():
        raise FileNotFoundError(
            f"{ws.pinhole_k_file} missing. Run the undistort step first."
        )
    import numpy as np

    return np.load(ws.pinhole_k_file)["K"]
