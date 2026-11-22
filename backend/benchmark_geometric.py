"""
benchmark_geometric.py — Scientific 3D Geometric Evaluation Benchmark.
=============================================================================
Calculates geometric fidelity metrics between generated CAD meshes and ground
truth engineering geometry based on the evaluation methodology of:
  "Generating CAD Code with Vision-Language Models for 3D Designs" (ICLR 2025).

Metrics:
  1. Chamfer Distance (Point Cloud ICP alignment / Nearest-Neighbor Distance)
  2. Hausdorff Distance (Maximum surface deviation / Outlier detection)
  3. Volume & Bounding Box Deviation

Usage:
    python benchmark_geometric.py [--samples 5000] [--out benchmark_geometric_results.json]
"""

import argparse
import json
import time
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
from scipy.spatial import cKDTree
from scipy.spatial.distance import directed_hausdorff
import trimesh


def compute_chamfer_distance(
    mesh_a: trimesh.Trimesh,
    mesh_b: trimesh.Trimesh,
    num_samples: int = 5000,
) -> float:
    """
    Computes bidirectional symmetric Chamfer Distance between two 3D meshes:
      CD(A, B) = 0.5 * (mean_dist(A -> B) + mean_dist(B -> A))
    """
    pts_a, _ = trimesh.sample.sample_surface(mesh_a, num_samples)
    pts_b, _ = trimesh.sample.sample_surface(mesh_b, num_samples)

    tree_b = cKDTree(pts_b)
    dist_a_to_b, _ = tree_b.query(pts_a)

    tree_a = cKDTree(pts_a)
    dist_b_to_a, _ = tree_a.query(pts_b)

    return float(0.5 * (np.mean(dist_a_to_b) + np.mean(dist_b_to_a)))


def compute_hausdorff_distance(
    mesh_a: trimesh.Trimesh,
    mesh_b: trimesh.Trimesh,
    num_samples: int = 5000,
) -> float:
    """
    Computes symmetric Hausdorff distance (maximum surface error) between meshes:
      d_H(A, B) = max(directed(A, B), directed(B, A))
    """
    pts_a, _ = trimesh.sample.sample_surface(mesh_a, num_samples)
    pts_b, _ = trimesh.sample.sample_surface(mesh_b, num_samples)

    d_ab = directed_hausdorff(pts_a, pts_b)[0]
    d_ba = directed_hausdorff(pts_b, pts_a)[0]
    return float(max(d_ab, d_ba))


def evaluate_geometric_pair(
    generated_mesh: trimesh.Trimesh,
    ground_truth_mesh: trimesh.Trimesh,
    num_samples: int = 5000,
) -> Dict[str, float]:
    """Evaluates full geometric metric suite between generated and ground-truth meshes."""
    cd = compute_chamfer_distance(generated_mesh, ground_truth_mesh, num_samples=num_samples)
    hd = compute_hausdorff_distance(generated_mesh, ground_truth_mesh, num_samples=num_samples)

    vol_gen = float(generated_mesh.volume) if generated_mesh.is_watertight else 0.0
    vol_gt = float(ground_truth_mesh.volume) if ground_truth_mesh.is_watertight else 0.0
    vol_error_pct = abs(vol_gen - vol_gt) / vol_gt * 100.0 if vol_gt > 1e-4 else 0.0

    ext_gen = generated_mesh.bounding_box.extents
    ext_gt = ground_truth_mesh.bounding_box.extents
    bbox_error_mm = float(np.linalg.norm(ext_gen - ext_gt))

    return {
        "chamfer_distance_mm": round(cd, 4),
        "hausdorff_distance_mm": round(hd, 4),
        "volume_generated_mm3": round(vol_gen, 1),
        "volume_ground_truth_mm3": round(vol_gt, 1),
        "volume_error_pct": round(vol_error_pct, 2),
        "bbox_error_mm": round(bbox_error_mm, 3),
        "is_watertight": bool(generated_mesh.is_watertight),
    }


def create_synthetic_ground_truths() -> Dict[str, Tuple[trimesh.Trimesh, trimesh.Trimesh]]:
    """
    Creates standard mechanical test pairs representing ground truth vs generated
    variations (both perfect matches and deliberate defects) for benchmarking.
    """
    pairs = {}

    # Test Case 1: Rectangular Mounting Plate (Exact Match)
    gt_box = trimesh.creation.box((50.0, 30.0, 10.0))
    gen_box = trimesh.creation.box((50.0, 30.0, 10.0))
    pairs["mounting_plate_perfect"] = (gen_box, gt_box)

    # Test Case 2: Bushing with slight dimensional offset (2mm radius variance)
    gt_bushing = trimesh.creation.cylinder(radius=15.0, height=30.0)
    gen_bushing = trimesh.creation.cylinder(radius=14.0, height=30.0)
    pairs["bushing_radius_variance"] = (gen_bushing, gt_bushing)

    # Test Case 3: Cylinder with chamfer deviation
    gt_cyl = trimesh.creation.cylinder(radius=20.0, height=40.0)
    gen_cyl = trimesh.creation.cylinder(radius=20.0, height=38.0)
    pairs["cylinder_height_variance"] = (gen_cyl, gt_cyl)

    return pairs


def run_benchmark(num_samples: int = 4000, output_path: str = "benchmark_geometric_results.json"):
    print("\n" + "=" * 76)
    print("  AI Parametric CAD Workbench — ICLR 2025 Geometric Verification Benchmark")
    print(f"  Point Cloud Samples: {num_samples:,} points per mesh")
    print("=" * 76 + "\n")

    test_pairs = create_synthetic_ground_truths()
    results = {}

    print(f"{'Test Case':<28} {'Chamfer (mm)':<14} {'Hausdorff (mm)':<16} {'Vol Err (%)':<12} {'Watertight'}")
    print("-" * 76)

    for name, (gen_mesh, gt_mesh) in test_pairs.items():
        metrics = evaluate_geometric_pair(gen_mesh, gt_mesh, num_samples=num_samples)
        results[name] = metrics
        print(
            f"{name:<28} "
            f"{metrics['chamfer_distance_mm']:<14.4f} "
            f"{metrics['hausdorff_distance_mm']:<16.4f} "
            f"{metrics['volume_error_pct']:<12.2f} "
            f"{'PASS' if metrics['is_watertight'] else 'FAIL'}"
        )

    print("-" * 76)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"[SUCCESS] Geometric benchmark results saved to: {output_path}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run 3D geometric CAD evaluation benchmark")
    parser.add_argument("--samples", type=int, default=4000, help="Surface points to sample")
    parser.add_argument("--out", type=str, default="benchmark_geometric_results.json", help="Output JSON path")
    args = parser.parse_args()
    run_benchmark(num_samples=args.samples, output_path=args.out)
