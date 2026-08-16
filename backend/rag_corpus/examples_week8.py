"""
RAG Corpus — Advanced Mechanical & CSG Examples (Week 8)
========================================================
Includes Solid-First CSG assemblies:
- Hybrid RC Flying Car Chassis
- Quadcopter Drone Frame
- Robot Rover Chassis
- Precision Bearing Mount Block
- Rotated Beam Location Reference
"""

EXAMPLES = [
    {
        "id": "hybrid_flying_car_chassis",
        "description": "A parametric hybrid RC flying car chassis plate with central fuselage, 4 swept motor arms, 4 wheel mount stations, flight controller stack, and battery slots",
        "tags": ["chassis", "flying car", "drone", "quadcopter", "rc car", "hybrid", "motor arms", "wheel mount", "avionics", "plate"],
        "code": '''\
# Units: millimeters (mm)
# X=length, Y=width, Z=height, Origin=chassis center at Z=0
# Architecture: Solid-First CSG with vector-midpoint beam positioning

PARAMS = {
    "chassis_length": 380.0,
    "chassis_width": 100.0,
    "plate_thickness": 4.0,
    "nose_radius": 45.0,
    "arm_span_x": 280.0,
    "arm_span_y": 240.0,
    "arm_beam_width": 22.0,
    "motor_mount_dia": 38.0,
    "motor_center_bore_dia": 9.0,
    "motor_bolt_pcd": 19.0,
    "motor_bolt_dia": 3.4,
    "motor_bolt_count": 4,
    "wheelbase_x": 260.0,
    "wheel_track_y": 220.0,
    "wheel_mount_length": 36.0,
    "wheel_mount_width": 20.0,
    "axle_hole_dia": 5.2,
    "wheel_clamp_bolt_dia": 3.4,
    "wheel_clamp_spacing": 18.0,
    "fc_stack_spacing": 30.5,
    "stack_bolt_dia": 3.4,
    "battery_slot_length": 22.0,
    "battery_slot_width": 3.5,
    "battery_slot_spacing_x": 45.0,
    "corner_fillet_radius": 3.0,
}

import math
from build123d import *

# --- Parameter Sanity Checks ---
assert PARAMS["chassis_length"] > 100, "chassis_length must be positive"
assert PARAMS["arm_beam_width"] < PARAMS["motor_mount_dia"], "arm beam width cannot exceed motor pad"
assert PARAMS["motor_bolt_pcd"] < PARAMS["motor_mount_dia"] - 4, "bolt circle exceeds motor pad"

L = PARAMS["chassis_length"]; W = PARAMS["chassis_width"]; T = PARAMS["plate_thickness"]
arm_hx = PARAMS["arm_span_x"] / 2.0; arm_hy = PARAMS["arm_span_y"] / 2.0
pad_r = PARAMS["motor_mount_dia"] / 2.0; beam_w = PARAMS["arm_beam_width"]
wh_hx = PARAMS["wheelbase_x"] / 2.0; wh_hy = PARAMS["wheel_track_y"] / 2.0
body_root_x = L * 0.22; body_root_y = W * 0.35

with BuildPart() as part:
    # ==== 1. BASE FUSELAGE PROFILE ====
    with BuildSketch(Plane.XY):
        Rectangle(L - 2 * PARAMS["nose_radius"], W)
        with Locations(((L / 2.0) - PARAMS["nose_radius"], 0)): Circle(PARAMS["nose_radius"])
        with Locations((-(L / 2.0) + PARAMS["nose_radius"], 0)): Circle(PARAMS["nose_radius"])
    extrude(amount=T)

    # ==== 2. SOLID MOTOR ARMS & LANDING PADS (4x SYMMETRIC) ====
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            mx = sx * arm_hx; my = sy * arm_hy
            rx = sx * body_root_x; ry = sy * body_root_y
            dx = mx - rx; dy = my - ry
            beam_len = math.hypot(dx, dy); beam_ang = math.degrees(math.atan2(dy, dx))
            mid_x = (rx + mx) / 2.0; mid_y = (ry + my) / 2.0
            # Solid rectangular beam placed with Location rotation
            with Locations(Location((mid_x, mid_y, T / 2.0), (0, 0, beam_ang))):
                Box(beam_len + 10.0, beam_w, T)
            # Motor Mount Landing Pad Solid Disc
            with Locations((mx, my, T / 2.0)): Cylinder(radius=pad_r, height=T)

    # ==== 3. SOLID WHEEL MOUNT BRACKET STATIONS (4x) ====
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            wx = sx * wh_hx; wy = sy * wh_hy
            bridge_mid_y = (sy * (W / 2.0) + wy) / 2.0; bridge_len = abs(wy - sy * W / 2.0)
            with Locations((wx, bridge_mid_y, T / 2.0)): Box(PARAMS["wheel_mount_length"], bridge_len + 10.0, T)
            with Locations((wx, wy, T / 2.0)): Box(PARAMS["wheel_mount_length"], PARAMS["wheel_mount_width"], T)

    # ==== 4. MOTOR MOUNT BORES & FASTENER PATTERNS ====
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            mx = sx * arm_hx; my = sy * arm_hy
            with Locations((mx, my, T / 2.0)):
                Cylinder(radius=PARAMS["motor_center_bore_dia"] / 2.0, height=T*2, mode=Mode.SUBTRACT)
            pcd_r = PARAMS["motor_bolt_pcd"] / 2.0; hole_r = PARAMS["motor_bolt_dia"] / 2.0
            for i in range(int(PARAMS["motor_bolt_count"])):
                ang = math.radians(i * (360.0 / PARAMS["motor_bolt_count"]) + 45.0)
                bx = mx + pcd_r * math.cos(ang); by = my + pcd_r * math.sin(ang)
                with Locations((bx, by, T / 2.0)): Cylinder(radius=hole_r, height=T*2, mode=Mode.SUBTRACT)

    # ==== 5. WHEEL AXLE & CLAMPING PINCH BOLT HOLES ====
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            wx = sx * wh_hx; wy = sy * wh_hy
            with Locations((wx, wy, T / 2.0)): Cylinder(radius=PARAMS["axle_hole_dia"]/2, height=T*2, mode=Mode.SUBTRACT)
            c_off = PARAMS["wheel_clamp_spacing"] / 2.0
            with Locations((wx-c_off, wy, T/2.0), (wx+c_off, wy, T/2.0)):
                Cylinder(radius=PARAMS["wheel_clamp_bolt_dia"]/2, height=T*2, mode=Mode.SUBTRACT)

    # ==== 6. AVIONICS FLIGHT CONTROLLER & BATTERY STRAP SLOTS ====
    with GridLocations(PARAMS["fc_stack_spacing"], PARAMS["fc_stack_spacing"], 2, 2):
        with Locations((0, 0, T/2.0)): Cylinder(radius=PARAMS["stack_bolt_dia"]/2, height=T*2, mode=Mode.SUBTRACT)
    for x_pos in [-PARAMS["battery_slot_spacing_x"], PARAMS["battery_slot_spacing_x"]]:
        for y_pos in [-W*0.28, W*0.28]:
            with Locations((x_pos, y_pos, T/2.0)): Box(PARAMS["battery_slot_length"], PARAMS["battery_slot_width"], T*2, mode=Mode.SUBTRACT)

# ==== 7. POST-BUILD GEOMETRY VALIDATION ====
assert part.part is not None, "Build failed: solid is None"
solids = part.part.solids()
assert len(solids) == 1, f"Disconnected bodies! Found {len(solids)} solids (expected 1 monolithic chassis)."
bb = part.part.bounding_box()
assert bb.size.X > 0 and bb.size.Y > 0 and bb.size.Z > 0, "Zero extent bounding box"

# ==== 8. EXPORT ====
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "quadcopter_x_frame",
        "description": "An X-configuration quadcopter drone bottom frame plate with diagonal arms, motor mount pads, flight controller stack mounting, and battery slots",
        "tags": ["quadcopter", "drone", "fpv", "frame", "motor arm", "x-frame", "flight controller", "carbon fiber plate"],
        "code": '''\
# Units: millimeters (mm)
# X=length, Y=width, Z=height, Origin=frame center at Z=0

PARAMS = {
    "center_plate_dia": 70.0,
    "arm_length": 110.0,
    "arm_width": 16.0,
    "plate_thickness": 3.0,
    "motor_pad_dia": 28.0,
    "motor_bore_dia": 6.0,
    "motor_pcd": 16.0,
    "motor_bolt_dia": 3.4,
    "fc_stack_spacing": 30.5,
    "fc_bolt_dia": 3.4,
}

import math
from build123d import *




D = PARAMS["center_plate_dia"]; T = PARAMS["plate_thickness"]
arm_l = PARAMS["arm_length"]; arm_w = PARAMS["arm_width"]
pad_r = PARAMS["motor_pad_dia"] / 2.0; pcd_r = PARAMS["motor_pcd"] / 2.0
bore_r = PARAMS["motor_bore_dia"] / 2.0; hole_r = PARAMS["motor_bolt_dia"] / 2.0

with BuildPart() as part:
    # 1. Central Hub Solid
    with BuildSketch(Plane.XY):
        Circle(radius=D / 2.0)
    extrude(amount=T)

    # 2. Four Diagonal Arms (45, 135, 225, 315 deg)
    for i in range(4):
        ang_deg = 45.0 + i * 90.0
        ang_rad = math.radians(ang_deg)
        tip_x = (arm_l + D * 0.3) * math.cos(ang_rad)
        tip_y = (arm_l + D * 0.3) * math.sin(ang_rad)
        mid_x = tip_x / 2.0; mid_y = tip_y / 2.0

        # Structural beam with rotation
        with Locations(Location((mid_x, mid_y, T / 2.0), (0, 0, ang_deg))):
            Box(arm_l + 10.0, arm_w, T)
        # Motor landing pad at tip
        with Locations((tip_x, tip_y, T / 2.0)):
            Cylinder(radius=pad_r, height=T)

    # 3. Motor Mount Bores
    for i in range(4):
        ang_deg = 45.0 + i * 90.0
        ang_rad = math.radians(ang_deg)
        tip_x = (arm_l + D * 0.3) * math.cos(ang_rad)
        tip_y = (arm_l + D * 0.3) * math.sin(ang_rad)

        with Locations((tip_x, tip_y, T / 2.0)):
            Cylinder(radius=bore_r, height=T * 2.0, mode=Mode.SUBTRACT)

        for b in range(4):
            b_ang = math.radians(b * 90.0 + ang_deg)
            bx = tip_x + pcd_r * math.cos(b_ang)
            by = tip_y + pcd_r * math.sin(b_ang)
            with Locations((bx, by, T / 2.0)):
                Cylinder(radius=hole_r, height=T * 2.0, mode=Mode.SUBTRACT)

    # 4. Flight Controller Stack Holes
    with GridLocations(PARAMS["fc_stack_spacing"], PARAMS["fc_stack_spacing"], 2, 2):
        with Locations((0, 0, T / 2.0)):
            Cylinder(radius=PARAMS["fc_bolt_dia"] / 2.0, height=T * 2.0, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1, "Expected 1 solid monolithic frame"
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "rotated_primitive_location_rule",
        "description": "Correct build123d syntax for positioning and rotating 3D solid primitives using Location((x,y,z), (rx,ry,rz))",
        "tags": ["rotation", "location", "angle", "euler", "rotated beam", "diagonal", "context manager"],
        "code": '''\
import math
from build123d import *

PARAMS = {
    "beam_length": 100.0,
    "beam_width": 15.0,
    "beam_thickness": 4.0,
    "angle_deg": 35.0
}




L = PARAMS["beam_length"]
W = PARAMS["beam_width"]
T = PARAMS["beam_thickness"]
ang = PARAMS["angle_deg"]

with BuildPart() as part:
    # Base block
    Box(40.0, 40.0, T)
    # CORRECT: Location takes position tuple and euler rotation tuple (rx, ry, rz)
    # Rotation() is not a context manager -- do NOT write 'with Rotation(...):'
    with Locations(Location((30.0, 20.0, T / 2.0), (0, 0, ang))):
        Box(L, W, T)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    }
]
