"""Topological validation and cleaning of the textured mesh via Open3D."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class MeshReport:
    vertices: int
    triangles: int
    edge_manifold: bool
    vertex_manifold: bool
    self_intersecting: bool
    watertight: bool
    cleaned: bool = False
    notes: list[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [
            f"Vertices:          {self.vertices}",
            f"Triangles:         {self.triangles}",
            f"Edge manifold:     {self.edge_manifold}",
            f"Vertex manifold:   {self.vertex_manifold}",
            f"Self-intersecting: {self.self_intersecting}",
            f"Watertight:        {self.watertight}",
        ]
        lines += self.notes
        return "\n".join(lines)


def validate_mesh(
    mesh_path: Path,
    clean: bool = True,
    min_component_triangles: int = 100,
    output_path: Path | None = None,
    visualize: bool = False,
) -> MeshReport:
    """Verify manifoldness/watertightness and optionally clean the mesh.

    Cleaning removes degenerate triangles, duplicated geometry, unreferenced
    vertices and small floating components (turntable debris, masking noise).
    If ``output_path`` is given the cleaned mesh is written there; the input
    file is never overwritten.
    """
    import open3d as o3d

    mesh_path = Path(mesh_path)
    if not mesh_path.exists():
        raise FileNotFoundError(
            f"Mesh not found at {mesh_path}. Run the reconstruction stages first."
        )

    mesh = o3d.io.read_triangle_mesh(str(mesh_path), enable_post_processing=True)
    if not mesh.has_vertex_normals():
        mesh.compute_vertex_normals()

    report = _inspect(mesh)

    if clean and not (report.edge_manifold and report.vertex_manifold):
        logger.info("Non-manifold geometry detected; cleaning mesh.")
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_triangles()
        mesh.remove_duplicated_vertices()
        mesh.remove_unreferenced_vertices()
        if min_component_triangles > 0:
            _remove_small_components(mesh, min_component_triangles)
        cleaned_report = _inspect(mesh)
        cleaned_report.cleaned = True
        cleaned_report.notes.append(
            f"Cleaned: {report.triangles - cleaned_report.triangles} triangles removed."
        )
        report = cleaned_report
        if output_path is not None:
            o3d.io.write_triangle_mesh(str(output_path), mesh)
            report.notes.append(f"Cleaned mesh written to {output_path}.")

    if not report.watertight:
        report.notes.append(
            "Mesh is not watertight: unsuitable for 3D printing or volumetric "
            "analysis without hole filling (consider Poisson remeshing)."
        )

    if visualize:
        o3d.visualization.draw_geometries(
            [mesh], mesh_show_wireframe=False,
        )
    return report


def poisson_remesh(
    point_cloud_path: Path,
    output_path: Path,
    depth: int = 10,
    density_quantile: float = 0.01,
) -> None:
    """Fit a smooth watertight surface to a dense point cloud.

    Octree ``depth`` 9-11 recovers sub-millimeter detail on a < 20 cm
    artifact; higher depths amplify alignment noise. Vertices in the lowest
    ``density_quantile`` of Poisson support density are trimmed — these are
    extrapolated triangles in sparsely covered regions.
    """
    import numpy as np
    import open3d as o3d

    pcd = o3d.io.read_point_cloud(str(point_cloud_path))
    if not pcd.has_normals():
        pcd.estimate_normals()
        pcd.orient_normals_consistent_tangent_plane(30)

    mesh, densities = o3d.geometry.TriangleMesh.create_from_point_cloud_poisson(
        pcd, depth=depth
    )
    densities = np.asarray(densities)
    mesh.remove_vertices_by_mask(
        densities < np.quantile(densities, density_quantile)
    )
    o3d.io.write_triangle_mesh(str(output_path), mesh)
    logger.info("Poisson mesh (depth %d) written to %s", depth, output_path)


def _inspect(mesh) -> MeshReport:
    import numpy as np

    return MeshReport(
        vertices=len(np.asarray(mesh.vertices)),
        triangles=len(np.asarray(mesh.triangles)),
        edge_manifold=mesh.is_edge_manifold(allow_boundary_edges=True),
        vertex_manifold=mesh.is_vertex_manifold(),
        self_intersecting=mesh.is_self_intersecting(),
        watertight=mesh.is_watertight(),
    )


def _remove_small_components(mesh, min_triangles: int) -> None:
    import numpy as np

    cluster_ids, cluster_sizes, _ = mesh.cluster_connected_triangles()
    cluster_ids = np.asarray(cluster_ids)
    cluster_sizes = np.asarray(cluster_sizes)
    mesh.remove_triangles_by_mask(cluster_sizes[cluster_ids] < min_triangles)
    mesh.remove_unreferenced_vertices()
