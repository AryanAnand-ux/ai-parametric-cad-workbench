import os
import sys
from pathlib import Path
from typing import Dict, Any
from pathlib import Path
import trimesh

class GeometryExporter:
    """
    Handles CAD mesh validation, bounding box extraction, and 3D file conversion.
    """

    @staticmethod
    def inspect_stl(stl_path: Path) -> Dict[str, Any]:
        """
        Inspects an STL file and calculates volume, bounding box, and surface area.
        """
        if not stl_path.exists():
            raise FileNotFoundError(f"Mesh file not found at {stl_path}")

        mesh = trimesh.load_mesh(str(stl_path))

        bounds = mesh.bounds   # [[min_x, min_y, min_z], [max_x, max_y, max_z]]
        dimensions = mesh.extents  # [length_x, length_y, length_z]

        return {
            "is_valid": getattr(mesh, 'is_watertight', True),
            "volume_mm3": round(float(mesh.volume), 2) if hasattr(mesh, 'volume') and mesh.volume is not None else 0.0,
            "surface_area_mm2": round(float(mesh.area), 2) if hasattr(mesh, 'area') and mesh.area is not None else 0.0,
            "dimensions_mm": {
                "x": round(float(dimensions[0]), 2),
                "y": round(float(dimensions[1]), 2),
                "z": round(float(dimensions[2]), 2)
            },
            "vertex_count": len(mesh.vertices),
            "face_count": len(mesh.faces)
        }

    @staticmethod
    def stl_to_obj(stl_path: Path, output_obj_path: Path) -> Path:
        """
        Converts an STL file to OBJ format for smooth web rendering.
        """
        mesh = trimesh.load_mesh(str(stl_path))
        mesh.export(str(output_obj_path))   # Fixed: was incorrectly using undefined variable
        return output_obj_path
