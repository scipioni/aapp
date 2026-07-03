import pytest

from aapp.cli import _parse_checkerboard, build_parser, main


def test_parser_requires_command():
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_parse_checkerboard():
    assert _parse_checkerboard("9x6") == (9, 6)
    assert _parse_checkerboard("11X8") == (11, 8)
    with pytest.raises(SystemExit):
        _parse_checkerboard("nine-by-six")


def test_dense_flags(tmp_path):
    args = build_parser().parse_args([
        "dense", str(tmp_path), "--no-refine", "--no-seam-leveling",
        "--texture-side", "16384",
    ])
    assert args.no_refine and args.no_seam_leveling
    assert args.texture_side == 16384


def test_init_creates_workspace(tmp_path, capsys):
    workspace = tmp_path / "find_001"
    assert main(["init", str(workspace)]) == 0
    assert (workspace / "images_raw").is_dir()
    assert "Workspace initialized" in capsys.readouterr().out


def test_stage_error_becomes_clean_exit_code(tmp_path, capsys):
    # sfm without a prior undistort step must fail with a readable message
    assert main(["sfm", str(tmp_path / "find_001")]) == 1
    assert "aapp: error:" in capsys.readouterr().err
