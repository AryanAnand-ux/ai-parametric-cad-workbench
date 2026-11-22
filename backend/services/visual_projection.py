"""
visual_projection.py — Headless Multi-View 3D Mesh Projection & Renderer.
=============================================================================
Renders canonical multi-view projections (Top, Front, Right Side, Isometric)
directly from 3D STL meshes or Trimesh instances without requiring an active
display server, X11, pyglet, or GPU context.

Implements the multi-view visual rendering stage for the ICLR 2025 CADCodeVerify
framework:
  - Generates 4 canonical views: Top (Z-normal), Front (Y-normal), Side (X-normal),
    and Isometric (35.26° elevation, 45° azimuth).
  - Uses depth-sorted polygon shading (Painter's algorithm) with directional
    diffuse lighting.
  - Assembles views into a labeled 2x2 grid image suitable for Gemini Vision inspection.
"""

import io
from pathlib import Path
from typing import Dict, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont
import trimesh


# View configurations: (azimuth_deg, elevation_deg, label)
CANONICAL_VIEWS = {
    "top": (0.0, 90.0, "Top View (XY Plane)"),
    "front": (0.0, 0.0, "Front View (XZ Plane)"),
    "side": (90.0, 0.0, "Right Side View (YZ Plane)"),
    "isometric": (45.0, 35.26, "Isometric View (3D)"),
}


def _create_rotation_matrix(azimuth_deg: float, elevation_deg: float) -> np.ndarray:
    """Computes a 3x3 rotation matrix for given azimuth and elevation angles."""
    az = np.radians(azimuth_deg)
    el = np.radians(elevation_deg)
    
    # Rotation about Z-axis (azimuth)
    Rz = np.array([
        [np.cos(az), -np.sin(az), 0.0],
        [np.sin(az),  np.cos(az), 0.0],
        [0.0,         0.0,        1.0]
    ], dtype=np.float64)
    
    # Rotation about X-axis (elevation tilt)
    Rx = np.array([
        [1.0, 0.0,         0.0],
        [0.0, np.cos(el), -np.sin(el)],
        [0.0, np.sin(el),  np.cos(el)]
    ], dtype=np.float64)
    
    return Rx @ Rz


def render_single_view(
    mesh: trimesh.Trimesh,
    azimuth_deg: float,
    elevation_deg: float,
    size: Tuple[int, int] = (400, 400),
    label: str = "",
) -> Image.Image:
    """
    Renders an orthographic projection of a 3D mesh with directional lighting
    and returns a PIL Image.
    """
    width, height = size
    img = Image.new("RGB", (width, height), (248, 250, 252))
    draw = ImageDraw.Draw(img)

    if mesh.is_empty or len(mesh.faces) == 0:
        draw.text((20, height // 2), "Empty Geometry", fill=(150, 150, 150))
        return img

    # Rotate centered vertices
    R = _create_rotation_matrix(azimuth_deg, elevation_deg)
    verts = (mesh.vertices - mesh.centroid) @ R.T

    # Calculate orthographic scaling
    ptp = np.ptp(verts, axis=0)
    span = float(np.max(ptp[:2]))
    scale = (width * 0.72) / (span if span > 1e-4 else 1.0)
    
    # Screen coordinates (Y-inverted)
    xy = verts[:, :2] * scale + np.array([width / 2.0, height / 2.0])

    # Depth sorting for Painter's Algorithm
    face_z = verts[mesh.faces].mean(axis=1)[:, 2]
    face_order = np.argsort(face_z)

    # Lighting setup (key light from upper right front)
    light_dir = np.array([0.4, 0.5, 0.77], dtype=np.float64)
    light_dir /= np.linalg.norm(light_dir)
    
    transformed_normals = mesh.face_normals @ R.T

    for f_idx in face_order:
        normal = transformed_normals[f_idx]
        dot = float(np.dot(normal, light_dir))
        intensity = max(0.22, min(1.0, 0.35 + 0.65 * max(0.0, dot)))
        
        # Base tone: engineering slate blue-grey
        r = int(140 * intensity + 20)
        g = int(160 * intensity + 30)
        b = int(185 * intensity + 45)
        
        poly = [(xy[v, 0], height - xy[v, 1]) for v in mesh.faces[f_idx]]
        draw.polygon(poly, fill=(r, g, b), outline=(55, 65, 81))

    # Add view title label
    if label:
        draw.rectangle([(8, 8), (len(label) * 8 + 20, 28)], fill=(30, 41, 59, 200))
        draw.text((14, 11), label, fill=(241, 245, 249))

    return img


def render_canonical_views(
    mesh_source: Union[str, Path, trimesh.Trimesh],
    size: Tuple[int, int] = (400, 400),
) -> Dict[str, bytes]:
    """
    Renders 4 canonical views (top, front, side, isometric) and returns
    a dictionary of PNG bytes.
    """
    if isinstance(mesh_source, (str, Path)):
        mesh = trimesh.load(mesh_source, force="mesh")
    else:
        mesh = mesh_source

    result = {}
    for key, (az, el, label) in CANONICAL_VIEWS.items():
        img = render_single_view(mesh, az, el, size=size, label=label)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        result[key] = buf.getvalue()

    return result


def render_multiview_composite(
    mesh_source: Union[str, Path, trimesh.Trimesh],
    sub_size: Tuple[int, int] = (380, 380),
) -> bytes:
    """
    Renders all 4 canonical views and composites them into a single 2x2 grid image.
    Ideal for single-pass Vision-Language Model visual verification.
    """
    if isinstance(mesh_source, (str, Path)):
        mesh = trimesh.load(mesh_source, force="mesh")
    else:
        mesh = mesh_source

    grid_w = sub_size[0] * 2 + 30
    grid_h = sub_size[1] * 2 + 30
    composite = Image.new("RGB", (grid_w, grid_h), (226, 232, 240))

    layout = [
        ("top", 10, 10),
        ("front", sub_size[0] + 20, 10),
        ("side", 10, sub_size[1] + 20),
        ("isometric", sub_size[0] + 20, sub_size[1] + 20),
    ]

    for key, x, y in layout:
        az, el, label = CANONICAL_VIEWS[key]
        sub_img = render_single_view(mesh, az, el, size=sub_size, label=label)
        composite.paste(sub_img, (x, y))

    buf = io.BytesIO()
    composite.save(buf, format="PNG", quality=90)
    return buf.getvalue()
