"""
benchmark_eval.py - Automated 20-Prompt CAD Generation Benchmark

Usage:
    python benchmark_eval.py [--url http://localhost:8000] [--timeout 180]

Output:
    - Formatted results table printed to stdout
    - benchmark_results.json saved in the same directory
"""

import argparse
import json
import time
import sys
from datetime import datetime

try:
    import requests
except ImportError:
    print("[ERROR] requests not installed. Run: pip install requests")
    sys.exit(1)

BENCHMARK_PROMPTS = [
    ("box_basic",        "A simple 50mm x 30mm x 20mm rectangular box"),
    ("cylinder_basic",   "A solid cylinder 25mm radius and 40mm tall"),
    ("hollow_cylinder",  "A hollow cylinder with 20mm outer radius, 14mm inner radius, 50mm height"),
    ("l_bracket",        "An L-shaped bracket with two 60mm arms and 5mm wall thickness"),
    ("t_bracket",        "A T-shaped bracket with a 100mm base and a 50mm vertical stem"),
    ("corner_mount",     "A corner mounting bracket with four M5 bolt holes on two perpendicular faces"),
    ("flanged_bushing",  "A flanged bushing with 10mm bore, 18mm outer diameter, 6mm flange, 25mm height"),
    ("hex_standoff",     "A hexagonal standoff 12mm across flats, 30mm tall, with M4 threaded bore"),
    ("shaft_collar",     "A shaft collar 20mm inner bore, 35mm outer diameter, 15mm wide with set-screw hole"),
    ("pulley",           "A V-groove pulley 60mm outer diameter, 10mm bore, 20mm wide groove"),
    ("electronics_box",  "A rectangular electronics enclosure 80mm x 60mm x 40mm with 2mm wall thickness and open top"),
    ("pcb_tray",         "A PCB mounting tray 70mm x 50mm with four M3 corner standoffs 5mm tall"),
    ("vented_panel",     "A flat panel 100mm x 80mm x 3mm with a 3x4 grid of 6mm circular vents"),
    ("c_channel",        "A C-channel profile 80mm wide, 40mm tall, 50mm long, 3mm wall thickness"),
    ("t_slot_bar",       "A T-slot extrusion bar 20mm x 20mm cross section, 100mm long with central T-slot"),
    ("gear_blank",       "A spur gear blank 60mm diameter, 10mm bore, 15mm wide with 12 evenly spaced teeth stubs"),
    ("pipe_flange",      "A pipe flange with 40mm pipe bore, 90mm flange diameter, 8mm flange thickness, 6 bolt holes"),
    ("heat_sink",        "A rectangular heat sink base 80mm x 60mm x 5mm with 8 fins 25mm tall and 2mm thick"),
    ("chamfered_box",    "A 60mm x 40mm x 25mm box with 3mm chamfers on all top edges"),
    ("sphere_pedestal",  "A cylindrical pedestal 30mm diameter, 20mm tall topped with a 15mm radius hemisphere"),
]


def run_benchmark(base_url, timeout):
    results = []
    total = len(BENCHMARK_PROMPTS)

    print(f"\n{'='*72}")
    print(f"  AI CAD Workbench - Benchmark Evaluation ({total} prompts)")
    print(f"  Backend: {base_url}")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*72}\n")

    for i, (slug, prompt) in enumerate(BENCHMARK_PROMPTS, 1):
        print(f"[{i:02d}/{total}] {slug:<20} {prompt[:52]:<52}", end="", flush=True)
        start = time.time()
        result = {
            "index": i, "slug": slug, "prompt": prompt,
            "success": False, "first_pass": False, "self_corrections": 0,
            "latency_ms": None, "model_used": None, "part_name": None,
            "volume_mm3": None, "error": None,
        }

        try:
            resp = requests.post(f"{base_url}/api/generate", json={"prompt": prompt}, timeout=timeout)
            elapsed_ms = int((time.time() - start) * 1000)
            result["latency_ms"] = elapsed_ms

            if resp.status_code == 200:
                data = resp.json()
                result["success"] = True
                result["self_corrections"] = data.get("self_correction_attempts", 0)
                result["first_pass"] = result["self_corrections"] == 0
                result["model_used"] = data.get("model_used", "?")
                result["part_name"] = data.get("part_name", "?")
                mesh_info = data.get("mesh_info") or {}
                result["volume_mm3"] = mesh_info.get("volume_mm3")
                icon = "OK" if result["first_pass"] else "CORR"
                print(f" [{icon}] {elapsed_ms:>6}ms | corr={result['self_corrections']} | {result['model_used']}")
            else:
                detail = resp.json().get("detail", resp.text[:80])
                result["error"] = str(detail)[:120]
                print(f" [FAIL] HTTP {resp.status_code}: {result['error'][:40]}")

        except requests.exceptions.Timeout:
            result["latency_ms"] = int((time.time() - start) * 1000)
            result["error"] = f"Timeout after {timeout}s"
            print(f" [TIMEOUT] ({timeout}s)")
        except Exception as exc:
            result["latency_ms"] = int((time.time() - start) * 1000)
            result["error"] = str(exc)[:120]
            print(f" [ERROR] {str(exc)[:50]}")

        results.append(result)

    return results


def print_summary(results):
    total = len(results)
    successes = [r for r in results if r["success"]]
    first_pass = [r for r in successes if r["first_pass"]]
    failures = [r for r in results if not r["success"]]
    latencies = [r["latency_ms"] for r in results if r["latency_ms"]]

    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0

    print(f"\n{'='*72}")
    print(f"  BENCHMARK SUMMARY")
    print(f"{'='*72}")
    print(f"  Total prompts        : {total}")
    print(f"  Successful           : {len(successes)}/{total}  ({100*len(successes)//total}%)")
    print(f"  First-pass success   : {len(first_pass)}/{total}  ({100*len(first_pass)//total}%)")
    print(f"  Self-corrections used: {sum(r['self_corrections'] for r in results)} total")
    print(f"  Avg latency          : {avg_latency} ms")

    if failures:
        print(f"\n  Failed prompts ({len(failures)}):")
        for r in failures:
            print(f"     [{r['index']:02d}] {r['slug']:<20} - {(r['error'] or '')[:60]}")

    model_counts = {}
    for r in successes:
        m = r.get("model_used") or "unknown"
        model_counts[m] = model_counts.get(m, 0) + 1
    if model_counts:
        print(f"\n  Model usage:")
        for model, count in sorted(model_counts.items(), key=lambda x: -x[1]):
            print(f"     {model:<30} {count} request(s)")
    print(f"\n{'='*72}\n")


def save_results(results, output_path):
    summary = {
        "timestamp": datetime.now().isoformat(),
        "total": len(results),
        "success_count": sum(1 for r in results if r["success"]),
        "first_pass_count": sum(1 for r in results if r["success"] and r["first_pass"]),
        "avg_latency_ms": int(sum(r["latency_ms"] for r in results if r["latency_ms"]) / max(1, sum(1 for r in results if r["latency_ms"]))),
        "results": results,
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"  Results saved to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI CAD Workbench Benchmark Evaluation")
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument("--timeout", type=int, default=180)
    parser.add_argument("--output", default="benchmark_results.json")
    args = parser.parse_args()

    try:
        health = requests.get(f"{args.url}/api/health", timeout=10)
        if health.status_code != 200:
            print(f"[ERROR] Backend returned HTTP {health.status_code}")
            sys.exit(1)
        hdata = health.json()
        print(f"[OK] Backend online - Gemini configured: {hdata.get('gemini_configured','?')}")
    except Exception as e:
        print(f"[ERROR] Cannot connect to {args.url}: {e}")
        print("       Start the backend first: uvicorn main:app --reload")
        sys.exit(1)

    results = run_benchmark(args.url, args.timeout)
    print_summary(results)
    save_results(results, args.output)
