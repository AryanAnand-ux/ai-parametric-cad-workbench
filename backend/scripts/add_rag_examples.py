"""
One-shot script: stores validated gold-standard examples into the RAG database.
Run with: python scripts/add_rag_examples.py (from the backend/ directory)
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent.resolve()))

from services.rag_service import RAGService

rag = RAGService()

# =============================================================================
# Example 1: Validated Hybrid RC Flying Car Chassis
# Test results: 1 solid, watertight, 380×278×4 mm, 192.54 cm³
# Architecture: Solid-First CSG, Location rotation, vector midpoint beams
# =============================================================================
CHASSIS_CODE = (
    "# Units: millimeters (mm)\n"
    "# X=length (front/rear), Y=width (left/right), Z=height, Origin=chassis center at Z=0\n"
    "# VALIDATED: 1 monolithic solid, watertight, 380x278x4mm, 192.54cm3\n"
    "\n"
    "PARAMS = {\n"
    "    'chassis_length': 380.0,\n"
    "    'chassis_width': 100.0,\n"
    "    'plate_thickness': 4.0,\n"
    "    'nose_radius': 45.0,\n"
    "    'arm_span_x': 280.0,\n"
    "    'arm_span_y': 240.0,\n"
    "    'arm_beam_width': 22.0,\n"
    "    'motor_mount_dia': 38.0,\n"
    "    'motor_center_bore_dia': 9.0,\n"
    "    'motor_bolt_pcd': 19.0,\n"
    "    'motor_bolt_dia': 3.4,\n"
    "    'motor_bolt_count': 4,\n"
    "    'wheelbase_x': 260.0,\n"
    "    'wheel_track_y': 220.0,\n"
    "    'wheel_mount_length': 36.0,\n"
    "    'wheel_mount_width': 20.0,\n"
    "    'axle_hole_dia': 5.2,\n"
    "    'wheel_clamp_bolt_dia': 3.4,\n"
    "    'wheel_clamp_spacing': 18.0,\n"
    "    'fc_stack_spacing': 30.5,\n"
    "    'stack_bolt_dia': 3.4,\n"
    "    'battery_slot_length': 22.0,\n"
    "    'battery_slot_width': 3.5,\n"
    "    'battery_slot_spacing_x': 45.0,\n"
    "    'corner_fillet_radius': 3.0,\n"
    "}\n"
    "\n"
    "import math\n"
    "from build123d import *\n"
    "\n"
    "assert PARAMS['chassis_length'] > 100, 'chassis_length too small'\n"
    "assert PARAMS['arm_beam_width'] < PARAMS['motor_mount_dia'], 'arm wider than motor pad'\n"
    "assert PARAMS['motor_bolt_pcd'] < PARAMS['motor_mount_dia'] - 4, 'bolt circle exceeds pad'\n"
    "\n"

    "L = PARAMS['chassis_length']; W = PARAMS['chassis_width']; T = PARAMS['plate_thickness']\n"
    "arm_hx = PARAMS['arm_span_x'] / 2.0; arm_hy = PARAMS['arm_span_y'] / 2.0\n"
    "pad_r = PARAMS['motor_mount_dia'] / 2.0; beam_w = PARAMS['arm_beam_width']\n"
    "wh_hx = PARAMS['wheelbase_x'] / 2.0; wh_hy = PARAMS['wheel_track_y'] / 2.0\n"
    "body_root_x = L * 0.22; body_root_y = W * 0.35\n"
    "\n"
    "with BuildPart() as part:\n"
    "    # ==== SECTION 1: Main Fuselage Body ====\n"
    "    with BuildSketch(Plane.XY):\n"
    "        Rectangle(L - 2 * PARAMS['nose_radius'], W)\n"
    "        with Locations(((L / 2.0) - PARAMS['nose_radius'], 0)): Circle(PARAMS['nose_radius'])\n"
    "        with Locations((-(L / 2.0) + PARAMS['nose_radius'], 0)): Circle(PARAMS['nose_radius'])\n"
    "    extrude(amount=T)\n"
    "\n"
    "    # ==== SECTION 2: Motor Arms (Solid-First CSG, vector midpoint beam) ====\n"
    "    for sx in [-1, 1]:\n"
    "        for sy in [-1, 1]:\n"
    "            mx = sx * arm_hx; my = sy * arm_hy\n"
    "            rx = sx * body_root_x; ry = sy * body_root_y\n"
    "            dx = mx - rx; dy = my - ry\n"
    "            beam_len = math.hypot(dx, dy)\n"
    "            beam_ang = math.degrees(math.atan2(dy, dx))\n"
    "            mid_x = (rx + mx) / 2.0; mid_y = (ry + my) / 2.0\n"
    "            # Correct rotation: use Location((pos), (rot)) -- NOT with Rotation():\n"
    "            with Locations(Location((mid_x, mid_y, T / 2.0), (0, 0, beam_ang))):\n"
    "                Box(beam_len + 10.0, beam_w, T)  # +10mm overlap prevents islands\n"
    "            with Locations((mx, my, T / 2.0)): Cylinder(radius=pad_r, height=T)\n"
    "\n"
    "    # ==== SECTION 3: Wheel Mount Bracket Stations ====\n"
    "    for sx in [-1, 1]:\n"
    "        for sy in [-1, 1]:\n"
    "            wx = sx * wh_hx; wy = sy * wh_hy\n"
    "            bridge_mid_y = (sy * (W / 2.0) + wy) / 2.0\n"
    "            bridge_len = abs(wy - sy * W / 2.0)\n"
    "            with Locations((wx, bridge_mid_y, T / 2.0)): Box(PARAMS['wheel_mount_length'], bridge_len + 10.0, T)\n"
    "            with Locations((wx, wy, T / 2.0)): Box(PARAMS['wheel_mount_length'], PARAMS['wheel_mount_width'], T)\n"
    "\n"
    "    # ==== SECTION 4: Motor Mount Bores & Fastener Patterns ====\n"
    "    for sx in [-1, 1]:\n"
    "        for sy in [-1, 1]:\n"
    "            mx = sx * arm_hx; my = sy * arm_hy\n"
    "            with Locations((mx, my, T / 2.0)):\n"
    "                Cylinder(radius=PARAMS['motor_center_bore_dia'] / 2.0, height=T*2, mode=Mode.SUBTRACT)\n"
    "            pcd_r = PARAMS['motor_bolt_pcd'] / 2.0; hole_r = PARAMS['motor_bolt_dia'] / 2.0\n"
    "            for i in range(PARAMS['motor_bolt_count']):\n"
    "                ang = math.radians(i * 90.0 + 45.0)\n"
    "                bx = mx + pcd_r * math.cos(ang); by = my + pcd_r * math.sin(ang)\n"
    "                with Locations((bx, by, T / 2.0)): Cylinder(radius=hole_r, height=T*2, mode=Mode.SUBTRACT)\n"
    "\n"
    "    # ==== SECTION 5: Wheel Axle & Clamping Holes ====\n"
    "    for sx in [-1, 1]:\n"
    "        for sy in [-1, 1]:\n"
    "            wx = sx * wh_hx; wy = sy * wh_hy\n"
    "            with Locations((wx, wy, T / 2.0)): Cylinder(radius=PARAMS['axle_hole_dia']/2, height=T*2, mode=Mode.SUBTRACT)\n"
    "            c_off = PARAMS['wheel_clamp_spacing'] / 2.0\n"
    "            with Locations((wx-c_off, wy, T/2.0), (wx+c_off, wy, T/2.0)):\n"
    "                Cylinder(radius=PARAMS['wheel_clamp_bolt_dia']/2, height=T*2, mode=Mode.SUBTRACT)\n"
    "\n"
    "    # ==== SECTION 6: Flight Controller & Battery Strap Slots ====\n"
    "    with GridLocations(PARAMS['fc_stack_spacing'], PARAMS['fc_stack_spacing'], 2, 2):\n"
    "        Cylinder(radius=PARAMS['stack_bolt_dia']/2, height=T*2, mode=Mode.SUBTRACT)\n"
    "    for x_pos in [-PARAMS['battery_slot_spacing_x'], PARAMS['battery_slot_spacing_x']]:\n"
    "        for y_pos in [-W*0.28, W*0.28]:\n"
    "            with Locations((x_pos, y_pos, T/2.0)): Box(PARAMS['battery_slot_length'], PARAMS['battery_slot_width'], T*2, mode=Mode.SUBTRACT)\n"
    "\n"
    "# ==== SECTION 7: Edge Finishing ====\n"
    "if PARAMS['corner_fillet_radius'] > 0:\n"
    "    try:\n"
    "        part.part = fillet(part.edges().filter_by(Axis.Z), radius=PARAMS['corner_fillet_radius'])\n"
    "    except Exception as fe:\n"
    "        print(f'[WARNING] Fillet skipped: {fe}')\n"
    "\n"
    "# ==== SECTION 8: Geometry Validation ====\n"
    "assert part.part is not None, 'Build failed: solid is None'\n"
    "solids = part.part.solids()\n"
    "assert len(solids) == 1, f'Disconnected bodies! Found {len(solids)} solids'\n"
    "bb = part.part.bounding_box()\n"
    "assert bb.size.X > 0 and bb.size.Y > 0 and bb.size.Z > 0\n"
    "\n"
    "# ==== SECTION 9: Export ====\n"
    "export_stl(part.part, OUTPUT_STL)\n"
    "export_step(part.part, OUTPUT_STEP)\n"
)

rag.add_example(
    prompt="hybrid RC flying car chassis quadcopter drone ground vehicle motor arm wheel mount avionics plate",
    python_code=CHASSIS_CODE,
    part_name="Hybrid RC Flying Car Chassis",
    description=(
        "Validated monolithic plate chassis (380×278×4mm) for a hybrid "
        "RC flying car: fuselage + 4 diagonal motor arms + 4 wheel mounts + "
        "flight controller stack + battery strap slots. Solid-First CSG pattern."
    ),
    parameters=[
        {"name": "chassis_length",   "label": "Chassis Length (mm)",       "type": "number", "default": 380.0, "min": 200.0, "max": 600.0, "step": 10.0},
        {"name": "arm_span_x",       "label": "Motor Arm Span X (mm)",     "type": "number", "default": 280.0, "min": 120.0, "max": 500.0, "step": 10.0},
        {"name": "arm_span_y",       "label": "Motor Arm Span Y (mm)",     "type": "number", "default": 240.0, "min": 100.0, "max": 450.0, "step": 10.0},
        {"name": "plate_thickness",  "label": "Plate Thickness (mm)",      "type": "number", "default": 4.0,   "min": 2.0,   "max": 10.0,  "step": 0.5},
        {"name": "motor_mount_dia",  "label": "Motor Mount Pad Dia (mm)", "type": "number", "default": 38.0,  "min": 20.0,  "max": 60.0,  "step": 1.0},
    ],
)
print("RAG: Gold-standard hybrid chassis stored.")

# =============================================================================
# Example 2: Location rotation pattern reference (teaches correct API usage)
# =============================================================================
ROTATION_REF_CODE = (
    "import math\n"
    "from build123d import *\n"
    "\n"
    "PARAMS = {'angle_deg': 45.0, 'beam_length': 80.0, 'beam_width': 10.0, 'beam_height': 4.0}\n"
    "\n"

    "a = PARAMS['angle_deg']; L = PARAMS['beam_length']\n"
    "W = PARAMS['beam_width']; H = PARAMS['beam_height']\n"
    "\n"
    "with BuildPart() as part:\n"
    "    # CORRECT: Location((translation_xyz), (rotation_euler_xyz))\n"
    "    # Rotation() is NOT a context manager -- using 'with Rotation():' causes TypeError\n"
    "    with Locations(Location((0, 0, H / 2.0), (0, 0, a))):\n"
    "        Box(L, W, H)\n"
    "\n"
    "assert len(part.part.solids()) == 1\n"
    "export_stl(part.part, OUTPUT_STL)\n"
    "export_step(part.part, OUTPUT_STEP)\n"
)

rag.add_example(
    prompt="rotate box diagonal arm beam angle Location rotation build123d context manager euler",
    python_code=ROTATION_REF_CODE,
    part_name="Rotated Beam Reference",
    description=(
        "Reference: use Location((x,y,z),(rx,ry,rz)) to rotate primitives. "
        "Rotation() is not a context manager and will raise TypeError if used with 'with'."
    ),
    parameters=[
        {"name": "angle_deg",    "label": "Rotation Angle (deg)", "type": "number", "default": 45.0, "min": 0.0,  "max": 360.0, "step": 5.0},
        {"name": "beam_length",  "label": "Beam Length (mm)",     "type": "number", "default": 80.0, "min": 10.0, "max": 300.0, "step": 5.0},
    ],
)
print("RAG: Location rotation reference stored.")

print("\nAll RAG examples inserted successfully.")
