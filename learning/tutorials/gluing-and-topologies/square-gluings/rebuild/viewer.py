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


def square_coordinates(m):
    _, b, c = (m.nodes**2).T
    return np.vstack(
        (
            np.column_stack((b + c - 0.5, 0.5 - c)),
            np.column_stack((c - 0.5, 0.5 - b - c)),
        )
    )


def playback_mesh(m, adjacent, faces, points):
    if adjacent:
        points = points * 0.86
    else:
        axis = np.array([0.81, 0.35, 0.47])
        heights = np.concatenate(
            [2 * (m.material(m.nodes, side) @ axis) ** 2 - 1 for side in (1, -1)]
        )
        points = np.column_stack((points, heights))
    return {
        "square": square_coordinates(m).round(8).tolist(),
        "adjacent": adjacent,
        "points": points.round(7).tolist(),
        "faces": faces.tolist(),
    }


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
    if adjacent_rp or name == "opposite-rp2":
        model.update(playback_mesh(m, adjacent_rp, faces, points))
    elif name in ("adjacent-klein", "opposite-klein"):
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
    write_page(name, m, model, destination / filename)


def write_page(name, m, model, output):
    templates = Path(__file__).parent / "templates"
    template = (templates / (name + ".html")).read_text()
    if "RP2_PLAYBACK" in template:
        template = template.replace(
            "RP2_PLAYBACK", (templates / "rp2-playback.js").read_text()
        )
    else:
        model["square"] = (2 * square_coordinates(m)).round(9).tolist()
        equations = templates.parents[1] / "viewers" / "src" / "surfaces.js"
        template = template.replace("GLUING_EQUATIONS", equations.read_text())
        template = template.replace(
            "GLUING_PLAYBACK", (templates / "gluing-playback.js").read_text()
        )
    template = template.replace(
        "PLAYBACK_TRANSPORT", (templates / "transport.js").read_text()
    )
    model["kind"] = name
    template = template.replace(
        "GLUING_GUIDES", (templates / "gluing-guides.js").read_text()
    )
    assert template.count("MESH_DATA") == 1
    output.write_text(
        template.replace("MESH_DATA", json.dumps(model, separators=(",", ":")))
    )
