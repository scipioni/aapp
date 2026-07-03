"""Command-line interface: ``aapp <stage> <workspace> [options]``."""

from __future__ import annotations

import argparse
import logging
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aapp",
        description="Archaeological Artifact Photogrammetry Pipeline",
    )
    parser.add_argument("-v", "--verbose", action="store_true",
                        help="enable debug logging")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_stage(name: str, help_text: str) -> argparse.ArgumentParser:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("workspace", help="artifact workspace directory")
        return p

    p = add_stage("init", "create the workspace directory layout")

    p = add_stage("calibrate", "solve fisheye calibration from checkerboard images")
    p.add_argument("--checkerboard", default="9x6", metavar="CxR",
                   help="inner corners as COLSxROWS (default: 9x6)")
    p.add_argument("--square-size", type=float, default=0.025, metavar="M",
                   help="checkerboard square edge in meters (default: 0.025)")

    p = add_stage("undistort", "remap raw captures to pinhole geometry")
    p.add_argument("--balance", type=float, default=0.0,
                   help="0=crop clean borders, 1=keep full FOV (default: 0)")

    p = add_stage("sfm", "run OpenMVG sparse reconstruction")
    p.add_argument("--ratio", type=float, default=0.8,
                   help="feature match ratio-test threshold (default: 0.8)")

    p = add_stage("dense", "run OpenMVS densify/mesh/refine/texture")
    p.add_argument("--resolution-level", type=int, default=1,
                   help="image downscale level, 1 = full 4K detail (default: 1)")
    p.add_argument("--texture-side", type=int, default=8192,
                   help="max texture atlas dimension (default: 8192)")
    p.add_argument("--no-refine", action="store_true",
                   help="skip the RefineMesh pass")
    p.add_argument("--no-seam-leveling", action="store_true",
                   help="disable seam leveling (workaround for black patches "
                        "with masked datasets)")

    p = add_stage("validate", "check mesh topology with Open3D and clean it")
    p.add_argument("--no-clean", action="store_true",
                   help="report only, do not clean the mesh")
    p.add_argument("--show", action="store_true",
                   help="open an interactive render window")

    p = add_stage("run", "execute all stages in order")
    p.add_argument("--show", action="store_true",
                   help="open an interactive render window at the end")

    return parser


def _parse_checkerboard(value: str) -> tuple[int, int]:
    try:
        cols, rows = (int(v) for v in value.lower().split("x"))
        return cols, rows
    except ValueError:
        raise SystemExit(f"Invalid --checkerboard '{value}': expected COLSxROWS, e.g. 9x6")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )

    from aapp.pipeline import ArchaeologicalPhotogrammetryPipeline

    pipeline = ArchaeologicalPhotogrammetryPipeline(args.workspace)

    try:
        if args.command == "init":
            print(f"Workspace initialized at {pipeline.workspace.root}")
        elif args.command == "calibrate":
            result = pipeline.calibrate(
                checkerboard=_parse_checkerboard(args.checkerboard),
                square_size_m=args.square_size,
            )
            print(f"Calibration RMS error: {result.rms_error:.4f} px "
                  f"({result.used_frames} frames)")
        elif args.command == "undistort":
            written, _ = pipeline.undistort(balance=args.balance)
            print(f"Undistorted {len(written)} frames.")
        elif args.command == "sfm":
            pipeline.sfm(ratio=args.ratio)
        elif args.command == "dense":
            pipeline.dense_reconstruction(
                resolution_level=args.resolution_level,
                refine=not args.no_refine,
                texture_side=args.texture_side,
                seam_leveling=not args.no_seam_leveling,
            )
            print(f"Textured mesh: {pipeline.workspace.textured_obj}")
        elif args.command == "validate":
            report = pipeline.validate(clean=not args.no_clean, visualize=args.show)
            print(report.summary())
        elif args.command == "run":
            report = pipeline.run(visualize=args.show)
            print(report.summary())
    except Exception as exc:  # surface stage failures as clean CLI errors
        logging.getLogger("aapp").debug("Traceback:", exc_info=True)
        print(f"aapp: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
