import pytest

from aapp import engines
from aapp.engines import (
    EngineNotFoundError,
    k_matrix_arg,
    openmvg_commands,
    openmvs_commands,
    run_command,
)
from aapp.workspace import Workspace

K = [[2400.0, 0.0, 1920.0], [0.0, 2400.0, 1080.0], [0.0, 0.0, 1.0]]


@pytest.fixture
def ws(tmp_path):
    return Workspace(tmp_path / "find_001").ensure()


def test_k_matrix_arg_row_major_semicolons():
    assert k_matrix_arg(K) == "2400;0;1920;0;2400;1080;0;0;1"


def test_openmvg_sequence_with_calibrated_k(ws):
    cmds = openmvg_commands(ws, K=K)
    binaries = [c[0] for c in cmds]
    assert binaries == [
        "openMVG_main_SfMInit_ImageListing",
        "openMVG_main_ComputeFeatures",
        "openMVG_main_ComputeMatches",
        "openMVG_main_GeometricFilter",
        "openMVG_main_SfM",
        "openMVG_main_openMVG2openMVS",
    ]
    listing = cmds[0]
    assert listing[listing.index("-k") + 1] == k_matrix_arg(K)
    # pinhole model: images are pre-undistorted
    assert listing[listing.index("-c") + 1] == "1"


def test_openmvg_focal_heuristic_fallback(ws):
    cmds = openmvg_commands(ws, focal_pixels=4600.8)
    listing = cmds[0]
    assert listing[listing.index("-f") + 1] == "4600.8"
    assert "-k" not in listing


def test_openmvg_requires_intrinsics(ws):
    with pytest.raises(ValueError):
        openmvg_commands(ws)


def test_openmvs_full_detail_defaults(ws):
    cmds = openmvs_commands(ws)
    by_binary = {c[0]: c for c in cmds}
    assert list(by_binary) == [
        "DensifyPointCloud", "ReconstructMesh", "RefineMesh", "TextureMesh",
    ]
    densify = by_binary["DensifyPointCloud"]
    assert densify[densify.index("--resolution-level") + 1] == "1"
    texture = by_binary["TextureMesh"]
    assert texture[texture.index("--global-seam-leveling") + 1] == "1"
    assert texture[texture.index("--local-seam-leveling") + 1] == "1"
    assert texture[texture.index("--max-texture-size") + 1] == "8192"
    # texturing consumes the refined mesh
    assert texture[1] == str(ws.refined_mesh_scene)


def test_openmvs_no_refine_and_no_seam_leveling(ws):
    cmds = openmvs_commands(ws, refine=False, seam_leveling=False)
    binaries = [c[0] for c in cmds]
    assert "RefineMesh" not in binaries
    texture = cmds[-1]
    assert texture[1] == str(ws.mesh_scene)
    assert texture[texture.index("--global-seam-leveling") + 1] == "0"
    assert texture[texture.index("--local-seam-leveling") + 1] == "0"


def test_run_command_missing_binary_raises(monkeypatch):
    monkeypatch.setattr(engines.shutil, "which", lambda _: None)
    with pytest.raises(EngineNotFoundError, match="not found on PATH"):
        run_command(["DensifyPointCloud", "scene.mvs"])


def test_run_command_executes_when_available(monkeypatch):
    calls = []
    monkeypatch.setattr(engines.shutil, "which", lambda _: "/usr/bin/fake")
    monkeypatch.setattr(
        engines.subprocess, "run",
        lambda cmd, check: calls.append((cmd, check)),
    )
    run_command(["DensifyPointCloud", "scene.mvs"])
    assert calls == [(["DensifyPointCloud", "scene.mvs"], True)]
