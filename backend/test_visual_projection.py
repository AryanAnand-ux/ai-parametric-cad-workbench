"""
Unit tests for visual_projection.py — Headless Multi-View 3D Mesh Renderer.
"""

import io
from PIL import Image
import trimesh

from services.visual_projection import (
    CANONICAL_VIEWS,
    render_canonical_views,
    render_multiview_composite,
    render_single_view,
)


def test_render_single_view():
    box = trimesh.creation.box((20.0, 30.0, 10.0))
    img = render_single_view(box, azimuth_deg=45.0, elevation_deg=35.0, size=(200, 200), label="Test")
    assert isinstance(img, Image.Image)
    assert img.size == (200, 200)
    # Check that image is not uniform background
    extrema = img.getextrema()
    assert any(low != high for low, high in extrema)


def test_render_canonical_views():
    cylinder = trimesh.creation.cylinder(radius=10.0, height=25.0)
    views = render_canonical_views(cylinder, size=(150, 150))
    
    assert set(views.keys()) == set(CANONICAL_VIEWS.keys())
    for key, data in views.items():
        assert isinstance(data, bytes)
        assert len(data) > 500  # valid PNG header + body
        img = Image.open(io.BytesIO(data))
        assert img.size == (150, 150)
        assert img.format == "PNG"


def test_render_multiview_composite():
    box = trimesh.creation.box((15.0, 15.0, 15.0))
    composite_bytes = render_multiview_composite(box, sub_size=(100, 100))
    
    assert isinstance(composite_bytes, bytes)
    assert len(composite_bytes) > 1000
    img = Image.open(io.BytesIO(composite_bytes))
    # 2 * 100 + 30 = 230
    assert img.size == (230, 230)
    assert img.format == "PNG"
