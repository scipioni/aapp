from pathlib import Path

from aapp.workspace import Workspace


def test_ensure_creates_layout(tmp_path):
    ws = Workspace(tmp_path / "find_001").ensure()
    assert ws.calibration_dir.is_dir()
    assert ws.raw_images_dir.is_dir()
    assert ws.undistorted_dir.is_dir()
    assert ws.mvg_dir.is_dir()
    assert ws.mvs_dir.is_dir()


def test_ensure_is_idempotent(tmp_path):
    ws = Workspace(tmp_path / "find_001")
    ws.ensure()
    ws.ensure()


def test_derived_paths_live_under_root(tmp_path):
    ws = Workspace(tmp_path / "find_001")
    for path in (ws.calibration_file, ws.pinhole_k_file, ws.sfm_data,
                 ws.mvs_scene, ws.dense_scene, ws.textured_obj):
        assert ws.root in path.parents


def test_list_images_filters_and_sorts(tmp_path):
    ws = Workspace(tmp_path / "find_001").ensure()
    (ws.raw_images_dir / "b.jpg").touch()
    (ws.raw_images_dir / "a.JPG").touch()
    (ws.raw_images_dir / "c.png").touch()
    (ws.raw_images_dir / "notes.txt").touch()
    names = [p.name for p in ws.list_images(ws.raw_images_dir)]
    assert names == ["a.JPG", "b.jpg", "c.png"]


def test_list_images_missing_dir_returns_empty(tmp_path):
    ws = Workspace(tmp_path / "find_001")
    assert ws.list_images(Path(tmp_path / "nope")) == []
