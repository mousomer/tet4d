"""Generate the final mesh from the same equations used to render the animation."""

import json
from pathlib import Path

import numpy as np


def corner_labels(m, name, sphere, adjacent_rp):
    tips = [[m.A, "A + B + C + D · 360°"]]
    if sphere:
        tips = [[m.A, "A · 90°"], [m.B, "B + D · 180°"], [m.C, "C · 90°"]]
    elif adjacent_rp:
        tips = [[m.A, "A · 90°"], [m.B, "B + C + D · 270°"]]
    elif name == "opposite-rp2":
        tips = [[m.A, "A + C · 180°"], [m.B, "B + D · 180°"]]
    return tips


def write_viewer(name, m, destination, filename):
    sphere = name == "sphere-revised"
    adjacent_rp = name == "direct-curl"
    if sphere:
        patches = [m.patch(m.nodes, side, 1, 1, 0) for side in (1, -1)]
    elif adjacent_rp:
        patches = [m.boy(m.nodes, side) for side in (1, -1)]
    else:
        patches = [m.final(m.nodes, side) for side in (1, -1)]
    points = np.concatenate(patches)
    count = len(m.nodes)
    faces = np.concatenate((m.tris, m.tris + count))
    seams = [[m.edge_a, m.colors["a"]], [m.edge_b, m.colors["b"]]]
    tips = corner_labels(m, name, sphere, adjacent_rp)
    model = {"seams": seams, "tips": tips}
    if name in ("adjacent-klein", "opposite-klein", "opposite-rp2"):
        if name == "opposite-rp2":

            def lift(q):
                return 2 * (q @ np.array([0.81, 0.35, 0.47])) ** 2 - 1

            heights = np.concatenate(
                [lift(m.material(m.nodes, side)) for side in (1, -1)]
            )
            radius = ((3 - np.sqrt(5)) / 2) ** (1 / 3)
            w = radius * np.exp(2j * np.pi * np.arange(3) / 3)
            triple = (
                np.column_stack((2 * w.real, 2 * w.imag, 1 - abs(w) ** 2))
                / (1 + abs(w) ** 2)[:, None]
            )
            markers = np.zeros((3, 3))
            marker_heights = lift(triple)
        else:
            markers = np.repeat(m.crossing(), 2, axis=0)
            marker_heights = [1.0, -1.0]
            if name == "adjacent-klein":
                heights = np.concatenate(
                    [np.cos(np.pi * m.coords(m.nodes, side)[1]) for side in (1, -1)]
                )
                c, s = np.cos(0.57), np.sin(0.57)
                rot = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
                points = points @ rot.T
                markers = markers @ rot.T
            else:
                heights = np.concatenate(
                    [np.cos(m.phase(*m.params(m.nodes, side))) for side in (1, -1)]
                )
        model["crossings"] = list(range(len(points), len(points) + len(markers)))
        points = np.column_stack(
            (np.vstack((points, markers)), np.concatenate((heights, marker_heights)))
        )
        model.update(points=points.round(7).tolist(), faces=faces.tolist())
    else:
        tri = points[faces]
        normals = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
        if sphere:
            normals[: len(m.tris)] *= -1
        normals /= np.maximum(np.linalg.norm(normals, axis=1)[:, None], 1e-12)
        model.update(
            points=points.round(5 if sphere else 6).tolist(),
            faces=[
                f + n
                for f, n in zip(
                    faces.tolist(),
                    normals.round(6 if name == "opposite-torus" else 5).tolist(),
                )
            ],
        )
    template = (Path(__file__).parent / "templates" / (name + ".html")).read_text()
    assert template.count("MESH_DATA") == 1
    (destination / filename).write_text(
        template.replace("MESH_DATA", json.dumps(model, separators=(",", ":")))
    )
