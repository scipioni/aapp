"""Workspace layout for a single artifact reconstruction."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tif", ".tiff")


@dataclass
class Workspace:
    """Directory layout for one artifact (one ``find``).

    find_001/
    ├── calibration/          # checkerboard images
    ├── images_raw/           # raw turntable captures
    ├── images_undistorted/   # remapped images fed to OpenMVG
    ├── openmvg_output/       # sfm_data.bin, sparse cloud, matches
    ├── openmvs_output/       # dense cloud, mesh, textured_artifact.obj
    └── calibration_params.npz
    """

    root: Path

    calibration_dir: Path = field(init=False)
    raw_images_dir: Path = field(init=False)
    undistorted_dir: Path = field(init=False)
    mvg_dir: Path = field(init=False)
    mvs_dir: Path = field(init=False)

    def __post_init__(self) -> None:
        self.root = Path(self.root).resolve()
        self.calibration_dir = self.root / "calibration"
        self.raw_images_dir = self.root / "images_raw"
        self.undistorted_dir = self.root / "images_undistorted"
        self.mvg_dir = self.root / "openmvg_output"
        self.mvs_dir = self.root / "openmvs_output"

    def ensure(self) -> "Workspace":
        """Create all workspace directories (idempotent)."""
        for path in (
            self.calibration_dir,
            self.raw_images_dir,
            self.undistorted_dir,
            self.mvg_dir,
            self.mvs_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
        return self

    @property
    def calibration_file(self) -> Path:
        return self.root / "calibration_params.npz"

    @property
    def pinhole_k_file(self) -> Path:
        return self.root / "pinhole_K.npz"

    @property
    def matches_dir(self) -> Path:
        return self.mvg_dir / "matches"

    @property
    def reconstruction_dir(self) -> Path:
        return self.mvg_dir / "reconstruction"

    @property
    def sfm_data(self) -> Path:
        return self.reconstruction_dir / "sfm_data.bin"

    @property
    def mvs_scene(self) -> Path:
        return self.mvs_dir / "scene.mvs"

    @property
    def dense_scene(self) -> Path:
        return self.mvs_dir / "scene_dense.mvs"

    @property
    def mesh_scene(self) -> Path:
        return self.mvs_dir / "scene_dense_mesh.mvs"

    @property
    def refined_mesh_scene(self) -> Path:
        return self.mvs_dir / "scene_dense_mesh_refine.mvs"

    @property
    def textured_obj(self) -> Path:
        return self.mvs_dir / "textured_artifact.obj"

    def list_images(self, directory: Path) -> list[Path]:
        """Return image files in ``directory``, sorted for deterministic ordering."""
        return sorted(
            p for p in directory.iterdir()
            if p.suffix.lower() in IMAGE_EXTENSIONS
        ) if directory.is_dir() else []
