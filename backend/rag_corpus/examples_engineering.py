"""
RAG Corpus — Production-Grade build123d CAD Snippet Pairs
Covers Mechanical, Aerospace, Robotics, Enclosures, Thermal, and Fluid components.
"""

EXAMPLES = [
    # ── 1. DRONES & AEROSPACE ───────────────────────────────────────────────
    {
        "id": "drone_quad_x_frame",
        "description": "Parametric X-frame quadcopter base plate with motor mounts, central bay, arm mounting holes, battery strap slots, and cable-routing cutouts",
        "tags": ["quadcopter", "drone", "uav", "x-frame", "motor mount", "chassis", "carbon fiber", "frame"],
        "code": """\
PARAMS = {
    "frame_size": 220.0,
    "arm_width": 16.0,
    "plate_thickness": 3.0,
    "center_bay_size": 70.0,
    "motor_mount_dia": 28.0,
    "motor_bolt_pcd": 16.0,
    "motor_bolt_dia": 3.2,
    "motor_bore_dia": 8.0,
    "arm_hole_dia": 4.0,
    "strap_slot_width": 4.0,
    "strap_slot_length": 24.0,
    "outer_fillet_r": 2.5
}
import math
from build123d import *

FS = PARAMS["frame_size"]
AW = PARAMS["arm_width"]
T = PARAMS["plate_thickness"]
CBS = PARAMS["center_bay_size"]
MD = PARAMS["motor_mount_dia"]
PCD = PARAMS["motor_bolt_pcd"]
MBD = PARAMS["motor_bolt_dia"]
MBD_CTR = PARAMS["motor_bore_dia"]
AHD = PARAMS["arm_hole_dia"]
SW = PARAMS["strap_slot_width"]
SL = PARAMS["strap_slot_length"]
FILLET_R = PARAMS["outer_fillet_r"]

pad_r = MD / 2.0
# Exactly position motor pads so the outer tip touches the frame_size envelope
arm_hx = (FS / 2.0) - pad_r
arm_hy = (FS / 2.0) - pad_r
root_x = CBS * 0.40
root_y = CBS * 0.40

with BuildPart() as part:
    # 1. Central fuselage bay plate
    with BuildSketch(Plane.XY):
        Rectangle(CBS, CBS)
    extrude(amount=T)

    # 2. Four diagonal structural arms with circular motor landing pads
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            mx, my = sx * arm_hx, sy * arm_hy
            rx, ry = sx * root_x, sy * root_y
            dx, dy = mx - rx, my - ry
            beam_len = math.hypot(dx, dy)
            beam_ang = math.degrees(math.atan2(dy, dx))
            # Beam connects fuselage root to motor center with controlled overlap
            with Locations(Location(((rx + mx)/2.0, (ry + my)/2.0, T/2.0), (0, 0, beam_ang))):
                Box(beam_len + min(8.0, pad_r), AW, T)
            with Locations((mx, my, T/2.0)):
                Cylinder(radius=pad_r, height=T)

    # 3. Motor center shaft bores and PCD bolt pattern
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            mx, my = sx * arm_hx, sy * arm_hy
            with Locations((mx, my, T/2.0)):
                Cylinder(radius=MBD_CTR/2.0, height=T * 2.0, mode=Mode.SUBTRACT)
                with PolarLocations(PCD/2.0, 4, 45):
                    Cylinder(radius=MBD/2.0, height=T * 2.0, mode=Mode.SUBTRACT)

    # 4. Arm structural mounting holes (90° conical countersunk, aligned along arm vector)
    ah_r = AHD / 2.0
    cs_head_r = ah_r + 2.0  # standard 90° countersink head radius
    cs_depth = cs_head_r - ah_r  # 90° included angle depth
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            rx, ry = sx * root_x, sy * root_y
            mx, my = sx * arm_hx, sy * arm_hy
            dx, dy = mx - rx, my - ry
            beam_ang = math.degrees(math.atan2(dy, dx))
            # 2 countersunk mounting holes spaced along the arm root centerline
            for arm_dist in [-10.0, 10.0]:
                with Locations(Location((rx, ry, 0), (0, 0, beam_ang))):
                    with Locations((arm_dist, 0, T - cs_depth / 2.0)):
                        Cone(bottom_radius=ah_r, top_radius=cs_head_r, height=cs_depth, mode=Mode.SUBTRACT)
                    with Locations((arm_dist, 0, T / 2.0)):
                        Cylinder(radius=ah_r, height=T * 2.0, mode=Mode.SUBTRACT)

    # 5. Battery strap slots with rounded ends (explicitly positioned along Y)
    for slot_y in [CBS * 0.25, -CBS * 0.25]:
        straight_len = max(2.0, SL - SW)
        with Locations((0, slot_y, T/2.0)):
            Box(straight_len, SW, T * 2.0, mode=Mode.SUBTRACT)
            with Locations((straight_len/2.0, 0, 0), (-straight_len/2.0, 0, 0)):
                Cylinder(radius=SW/2.0, height=T * 2.0, mode=Mode.SUBTRACT)

    # 6. Cable-routing pass-through cutouts along axes
    for cx in [CBS * 0.28, -CBS * 0.28]:
        with Locations((cx, 0, T/2.0)):
            Cylinder(radius=5.0, height=T * 2.0, mode=Mode.SUBTRACT)

# Validation: ensure monolithic single solid and exact envelope match
assert part.part is not None, "Part build failed"
assert len(part.part.solids()) == 1, f"Expected 1 solid, found {len(part.part.solids())}"
bb = part.part.bounding_box()
assert abs(bb.size.X - FS) < 0.5, f"X envelope mismatch: {bb.size.X:.2f} != {FS}"
assert abs(bb.size.Y - FS) < 0.5, f"Y envelope mismatch: {bb.size.Y:.2f} != {FS}"
assert abs(bb.size.Z - T) < 0.2, f"Z thickness mismatch: {bb.size.Z:.2f} != {T}"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": "drone_deadcat_frame",
        "description": "Deadcat asymmetric quadcopter frame plate with wider front arm angle for obstacle clearance",
        "tags": ["deadcat", "drone", "fpv", "frame", "camera clear", "asymmetric"],
        "code": """\
PARAMS = {
    "wheelbase_x": 210.0,
    "front_span_y": 190.0,
    "rear_span_y": 160.0,
    "thickness": 3.5,
    "arm_width": 18.0,
    "motor_pad_dia": 30.0
}
import math
from build123d import *

LX = PARAMS["wheelbase_x"]
FY = PARAMS["front_span_y"]
RY = PARAMS["rear_span_y"]
T = PARAMS["thickness"]
AW = PARAMS["arm_width"]
MPD = PARAMS["motor_pad_dia"]

with BuildPart() as part:
    # Central fuselage
    Box(LX * 0.65, 55.0, T)
    
    # Front arms (wider Y spread)
    for sy in [-1, 1]:
        mx, my = LX * 0.45, sy * FY * 0.45
        dx, dy = mx - 20.0, my - (sy * 20.0)
        ang = math.degrees(math.atan2(dy, dx))
        with Locations(Location(((20.0 + mx)/2, (sy*20.0 + my)/2, T/2), (0, 0, ang))):
            Box(math.hypot(dx, dy) + 10.0, AW, T)
        with Locations((mx, my, T/2)):
            Cylinder(radius=MPD/2, height=T)
            Cylinder(radius=4.0, height=T*2, mode=Mode.SUBTRACT)

    # Rear arms (narrower Y spread)
    for sy in [-1, 1]:
        mx, my = -LX * 0.45, sy * RY * 0.45
        dx, dy = mx - (-20.0), my - (sy * 20.0)
        ang = math.degrees(math.atan2(dy, dx))
        with Locations(Location(((-20.0 + mx)/2, (sy*20.0 + my)/2, T/2), (0, 0, ang))):
            Box(math.hypot(dx, dy) + 10.0, AW, T)
        with Locations((mx, my, T/2)):
            Cylinder(radius=MPD/2, height=T)
            Cylinder(radius=4.0, height=T*2, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1, "Arm disconnected from fuselage"
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": "drone_hexacopter_spider_hub",
        "description": "Hexacopter circular center plate hub with 6 radial arm sockets and electronics mounting holes",
        "tags": ["hexacopter", "drone", "6 arm", "spider", "radial hub", "uav"],
        "code": """\
PARAMS = {
    "hub_diameter": 140.0,
    "center_bore": 30.0,
    "thickness": 4.0,
    "arm_socket_width": 22.0,
    "mount_hole_pcd": 115.0,
    "mount_hole_dia": 4.5
}
import math
from build123d import *

HD = PARAMS["hub_diameter"]
CB = PARAMS["center_bore"]
T = PARAMS["thickness"]
PCD = PARAMS["mount_hole_pcd"]
HDIA = PARAMS["mount_hole_dia"]

with BuildPart() as part:
    Cylinder(radius=HD/2, height=T)
    # Center weight reduction hole
    Cylinder(radius=CB/2, height=T*2, mode=Mode.SUBTRACT)
    # 6 radial arm mounting hole pairs
    with PolarLocations(PCD/2, 6):
        Cylinder(radius=HDIA/2, height=T*2, mode=Mode.SUBTRACT)
    with PolarLocations((PCD/2) - 15.0, 6, 30):
        Cylinder(radius=HDIA/2, height=T*2, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": "drone_motor_mount_bracket",
        "description": "Tubular carbon fiber arm motor mount clamp bracket for 20mm round tube",
        "tags": ["motor mount", "tube clamp", "carbon arm", "drone bracket", "clamp"],
        "code": """\
PARAMS = {
    "tube_dia": 20.0,
    "bracket_length": 50.0,
    "bracket_width": 38.0,
    "bracket_height": 28.0,
    "wall_thickness": 3.5,
    "clamp_bolt_dia": 3.4
}
from build123d import *

TD = PARAMS["tube_dia"]
L = PARAMS["bracket_length"]
W = PARAMS["bracket_width"]
H = PARAMS["bracket_height"]
CBD = PARAMS["clamp_bolt_dia"]

with BuildPart() as part:
    Box(L, W, H)
    # Tube bore along X
    with Locations(Location((0, 0, 0), (0, 90, 0))):
        Cylinder(radius=TD/2, height=L*2, mode=Mode.SUBTRACT)
    # Top motor plate landing
    with Locations((0, 0, H/2 - 2.0)):
        Box(L * 0.7, W, 4.0, mode=Mode.SUBTRACT)
    # Clamp split slot along X
    with Locations((0, 0, -H/4)):
        Box(L * 2, 2.0, H/2, mode=Mode.SUBTRACT)
    # Clamping bolt cross-holes along Y
    with Locations((L*0.25, 0, -H/4), (-L*0.25, 0, -H/4)):
        with Locations(Location((0, 0, 0), (90, 0, 0))):
            Cylinder(radius=CBD/2, height=W*2, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },

    # ── 2. MECHANICAL FASTENERS, BRACKETS & MOUNTS ──────────────────────────
    {
        "id": "heavy_duty_l_bracket",
        "description": "Reinforced heavy-duty 90-degree angle L-bracket with triangular gusset web and M6 mounting holes",
        "tags": ["l-bracket", "angle bracket", "gusset", "stiffener", "90 deg", "reinforcement"],
        "code": """\
PARAMS = {
    "arm_length_x": 80.0,
    "arm_length_z": 80.0,
    "width": 45.0,
    "flange_thickness": 6.0,
    "gusset_thickness": 5.0,
    "bolt_hole_dia": 6.5
}
from build123d import *

LX = PARAMS["arm_length_x"]
LZ = PARAMS["arm_length_z"]
W = PARAMS["width"]
T = PARAMS["flange_thickness"]
GT = PARAMS["gusset_thickness"]
BHD = PARAMS["bolt_hole_dia"]

with BuildPart() as part:
    # Horizontal arm
    with Locations((LX/2, 0, T/2)):
        Box(LX, W, T)
    # Vertical arm
    with Locations((T/2, 0, LZ/2)):
        Box(T, W, LZ)
    # Triangular center gusset web
    with BuildSketch(Plane.XZ):
        with Locations((T, T)):
            Polygon([(0, 0), (LX - T - 10.0, 0), (0, LZ - T - 10.0)])
    extrude(amount=GT, both=True)

    # Mounting holes on horizontal flange
    with Locations((LX * 0.65, -W/4, T/2), (LX * 0.65, W/4, T/2)):
        Cylinder(radius=BHD/2, height=T*2, mode=Mode.SUBTRACT)
    # Mounting holes on vertical flange
    with Locations((T/2, -W/4, LZ * 0.65), (T/2, W/4, LZ * 0.65)):
        with Locations(Location((0, 0, 0), (0, 90, 0))):
            Cylinder(radius=BHD/2, height=T*2, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": "pillow_block_bearing_mount",
        "description": "Two-bolt pillow block split bearing housing for 608/ball bearings with lubricating groove",
        "tags": ["pillow block", "bearing mount", "bearing housing", "shaft support", "ball bearing"],
        "code": """\
PARAMS = {
    "bearing_od": 22.0,
    "bearing_width": 7.0,
    "housing_length": 75.0,
    "housing_width": 20.0,
    "shaft_height": 25.0,
    "bolt_spacing": 55.0,
    "bolt_dia": 5.5
}
from build123d import *

BOD = PARAMS["bearing_od"]
BW = PARAMS["bearing_width"]
HL = PARAMS["housing_length"]
HW = PARAMS["housing_width"]
SH = PARAMS["shaft_height"]
BS = PARAMS["bolt_spacing"]
BD = PARAMS["bolt_dia"]

with BuildPart() as part:
    # Base block
    with Locations((0, 0, SH * 0.5)):
        Box(HL, HW, SH * 1.0)
    # Top arch cap
    with Locations(Location((0, 0, SH), (90, 0, 0))):
        Cylinder(radius=BOD/2 + 6.0, height=HW)
    # Bearing bore along Y axis
    with Locations(Location((0, 0, SH), (90, 0, 0))):
        Cylinder(radius=BOD/2, height=HW*2, mode=Mode.SUBTRACT)
    # Shaft clearance through-hole
    with Locations(Location((0, 0, SH), (90, 0, 0))):
        Cylinder(radius=(BOD/2) - 3.0, height=HW*4, mode=Mode.SUBTRACT)
    # Base mounting bolt holes along Z
    with Locations((-BS/2, 0, 0), (BS/2, 0, 0)):
        Cylinder(radius=BD/2, height=SH*3, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": "nema17_stepper_motor_bracket",
        "description": "NEMA 17 stepper motor mounting bracket with 31mm bolt pattern and 22mm pilot bore",
        "tags": ["nema 17", "stepper motor", "motor bracket", "cnc", "3d printer", "actuator mount"],
        "code": """\
PARAMS = {
    "face_size": 42.3,
    "flange_thickness": 4.0,
    "pilot_bore_dia": 23.0,
    "bolt_hole_dia": 3.4,
    "base_mount_len": 40.0
}
from build123d import *

FS = PARAMS["face_size"]
T = PARAMS["flange_thickness"]
PBD = PARAMS["pilot_bore_dia"]
BHD = PARAMS["bolt_hole_dia"]
BL = PARAMS["base_mount_len"]

with BuildPart() as part:
    # Front vertical motor plate
    with Locations((0, T/2, FS/2)):
        Box(FS, T, FS)
    # Base horizontal mounting flange
    with Locations((0, BL/2, T/2)):
        Box(FS, BL, T)
    # Triangular side gussets
    with BuildSketch(Plane.YZ):
        with Locations((T, T)):
            Polygon([(0, 0), (BL - T - 4.0, 0), (0, FS - T - 4.0)])
    with Locations((-FS/2 + T/2, 0, 0), (FS/2 - T/2, 0, 0)):
        extrude(amount=T)

    # Motor pilot bore along Y
    with Locations(Location((0, T/2, FS/2), (90, 0, 0))):
        Cylinder(radius=PBD/2, height=T*2, mode=Mode.SUBTRACT)
        # 4x 31mm square motor bolt pattern
        with GridLocations(31.0, 31.0, 2, 2):
            Cylinder(radius=BHD/2, height=T*2, mode=Mode.SUBTRACT)

    # Base mounting slots
    with Locations((-14.0, BL*0.65, T/2), (14.0, BL*0.65, T/2)):
        Cylinder(radius=4.5/2, height=T*2, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": "pipe_flange_ansi_class150",
        "description": "ANSI Class 150 4-bolt raised-face weld neck pipe flange with hub and bolt circle",
        "tags": ["pipe flange", "ansi 150", "weld neck", "flange", "piping", "valve flange"],
        "code": """\
PARAMS = {
    "flange_od": 108.0,
    "flange_thickness": 14.0,
    "raised_face_dia": 63.5,
    "raised_face_height": 2.0,
    "pipe_bore_id": 35.0,
    "hub_od": 50.0,
    "hub_height": 18.0,
    "bolt_circle_dia": 79.4,
    "bolt_hole_dia": 16.0,
    "bolt_count": 4
}
from build123d import *

OD = PARAMS["flange_od"]
FT = PARAMS["flange_thickness"]
RFD = PARAMS["raised_face_dia"]
RFH = PARAMS["raised_face_height"]
ID = PARAMS["pipe_bore_id"]
HOD = PARAMS["hub_od"]
HH = PARAMS["hub_height"]
BCD = PARAMS["bolt_circle_dia"]
BHD = PARAMS["bolt_hole_dia"]
BCNT = int(PARAMS["bolt_count"])

with BuildPart() as part:
    # Main flange disc
    Cylinder(radius=OD/2, height=FT)
    # Raised gasket face
    with Locations((0, 0, FT/2 + RFH/2)):
        Cylinder(radius=RFD/2, height=RFH)
    # Weld neck hub on rear
    with Locations((0, 0, -FT/2 - HH/2)):
        Cone(bottom_radius=HOD/2, top_radius=(HOD/2)+4.0, height=HH)
    # Through-pipe bore
    Cylinder(radius=ID/2, height=(FT + RFH + HH)*2, mode=Mode.SUBTRACT)
    # Bolt holes on PCD
    with PolarLocations(BCD/2, BCNT):
        Cylinder(radius=BHD/2, height=(FT + RFH)*2, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },

    # ── 3. ELECTRONICS ENCLOSURES & CASES ────────────────────────────────────
    {
        "id": "electronics_enclosure_pcb_bosses",
        "description": "Electronics enclosure lower tub case with PCB mounting screw bosses, cable gland ports, and lid rim lip",
        "tags": ["enclosure", "box", "case", "pcb box", "bosses", "electronics tub", "cable gland"],
        "code": """\
PARAMS = {
    "box_length": 120.0,
    "box_width": 80.0,
    "box_height": 40.0,
    "wall_thickness": 3.0,
    "pcb_spacing_x": 90.0,
    "pcb_spacing_y": 55.0,
    "boss_dia": 7.0,
    "boss_hole_dia": 2.8,
    "gland_hole_dia": 16.0
}
from build123d import *

L = PARAMS["box_length"]
W = PARAMS["box_width"]
H = PARAMS["box_height"]
T = PARAMS["wall_thickness"]
PX = PARAMS["pcb_spacing_x"]
PY = PARAMS["pcb_spacing_y"]
BD = PARAMS["boss_dia"]
BHD = PARAMS["boss_hole_dia"]
GD = PARAMS["gland_hole_dia"]

with BuildPart() as part:
    # Outer solid box
    Box(L, W, H)
    # Inner cavity hollowed from top
    with Locations((0, 0, T)):
        Box(L - 2*T, W - 2*T, H, mode=Mode.SUBTRACT)

    # 4x Internal PCB Standoff Bosses
    with GridLocations(PX, PY, 2, 2):
        with Locations((0, 0, -H/2 + T + 5.0)):
            Cylinder(radius=BD/2, height=10.0)
            Cylinder(radius=BHD/2, height=12.0, mode=Mode.SUBTRACT)

    # Side cable gland entry hole on -X face
    with Locations(Location((-L/2, 0, 0), (0, 90, 0))):
        Cylinder(radius=GD/2, height=T*3, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": "raspberry_pi_style_case_lid",
        "description": "Snap-fit enclosure lid plate with ventilation air grille slots and recessed perimeter mating rim",
        "tags": ["lid", "case lid", "snap fit", "vent grille", "raspberry pi", "enclosure top"],
        "code": """\
PARAMS = {
    "lid_length": 100.0,
    "lid_width": 70.0,
    "top_thickness": 2.5,
    "lip_depth": 3.0,
    "lip_wall": 1.5,
    "vent_count": 8,
    "vent_slot_len": 35.0,
    "vent_slot_width": 2.5
}
from build123d import *

L = PARAMS["lid_length"]
W = PARAMS["lid_width"]
TT = PARAMS["top_thickness"]
LD = PARAMS["lip_depth"]
LW = PARAMS["lip_wall"]
VC = int(PARAMS["vent_count"])
VL = PARAMS["vent_slot_len"]
VW = PARAMS["vent_slot_width"]

with BuildPart() as part:
    # Main flat lid top plate
    Box(L, W, TT)
    # Inset mating rim lip
    with Locations((0, 0, -TT/2 - LD/2)):
        Box(L - 2*LW, W - 2*LW, LD)
        Box(L - 4*LW, W - 4*LW, LD*2, mode=Mode.SUBTRACT)

    # Ventilation grill linear array of slots
    spacing = VL * 0.8 / VC
    with GridLocations(spacing, 0, VC, 1):
        with Locations((0, 0, 0)):
            Box(VW, VL, TT*3, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },

    # ── 4. ROBOTICS & MECHANISMS ─────────────────────────────────────────────
    {
        "id": "robotic_gripper_finger",
        "description": "Articulated robotic gripper finger jaw with silicone grip tread teeth and pivot bearing bore",
        "tags": ["gripper", "robot finger", "jaw", "end effector", "tread teeth", "robotics"],
        "code": """\
PARAMS = {
    "finger_length": 90.0,
    "finger_width": 18.0,
    "base_height": 25.0,
    "tip_height": 12.0,
    "pivot_hole_dia": 5.0,
    "tooth_pitch": 8.0,
    "tooth_depth": 2.0
}
from build123d import *

FL = PARAMS["finger_length"]
FW = PARAMS["finger_width"]
BH = PARAMS["base_height"]
TH = PARAMS["tip_height"]
PD = PARAMS["pivot_hole_dia"]
TP = PARAMS["tooth_pitch"]
TD = PARAMS["tooth_depth"]

with BuildPart() as part:
    # Tapered finger body extruded along Y
    with BuildSketch(Plane.XZ):
        Polygon([
            (0, 0),
            (FL, 0),
            (FL, TH),
            (20.0, BH),
            (0, BH)
        ])
    extrude(amount=FW)

    # Pivot bushing hole at root
    with Locations(Location((10.0, FW/2, BH/2), (90, 0, 0))):
        Cylinder(radius=PD/2, height=FW*2, mode=Mode.SUBTRACT)

    # Serrated grip tread teeth on gripping surface (Z=0 face)
    num_teeth = int((FL - 30.0) / TP)
    for i in range(num_teeth):
        tx = 25.0 + i * TP
        with Locations((tx, FW/2, TD/2)):
            Box(TP/2, FW*1.2, TD*2, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": "timing_pulley_gt2_20t",
        "description": "GT2 20-tooth synchronous timing pulley with dual flanges, 5mm motor bore, and grub screw hub",
        "tags": ["gt2 pulley", "timing pulley", "pulley", "gears", "belt drive", "stepper pulley"],
        "code": """\
PARAMS = {
    "pitch_dia": 12.73,
    "outer_dia": 12.22,
    "flange_dia": 16.0,
    "belt_width": 7.0,
    "flange_thick": 1.2,
    "hub_dia": 15.0,
    "hub_length": 6.0,
    "bore_dia": 5.0,
    "set_screw_dia": 3.0
}
import math
from build123d import *

OD = PARAMS["outer_dia"]
FD = PARAMS["flange_dia"]
BW = PARAMS["belt_width"]
FT = PARAMS["flange_thick"]
HD = PARAMS["hub_dia"]
HL = PARAMS["hub_length"]
BD = PARAMS["bore_dia"]
SSD = PARAMS["set_screw_dia"]

total_h = BW + 2*FT + HL

with BuildPart() as part:
    # 1. Lower Hub
    Cylinder(radius=HD/2, height=HL)
    # 2. Lower Flange
    with Locations((0, 0, HL/2 + FT/2)):
        Cylinder(radius=FD/2, height=FT)
    # 3. Main Belt Tooth Drum
    with Locations((0, 0, HL/2 + FT + BW/2)):
        Cylinder(radius=OD/2, height=BW)
    # 4. Upper Flange
    with Locations((0, 0, HL/2 + FT + BW + FT/2)):
        Cylinder(radius=FD/2, height=FT)

    # Central motor shaft bore
    Cylinder(radius=BD/2, height=total_h*2, mode=Mode.SUBTRACT)
    # M3 grub screw set hole in hub along X
    with Locations(Location((0, 0, HL/2), (0, 90, 0))):
        Cylinder(radius=SSD/2, height=HD*2, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },

    # ── 5. THERMAL, HEAT SINKS & DUCTS ───────────────────────────────────────
    {
        "id": "extruded_aluminum_heatsink",
        "description": "High-efficiency linear extruded aluminum heat sink with base plate and 10 parallel cooling fins",
        "tags": ["heatsink", "thermal", "cooling", "fins", "cpu cooling", "led heatsink"],
        "code": """\
PARAMS = {
    "length": 80.0,
    "width": 60.0,
    "base_thickness": 5.0,
    "fin_height": 25.0,
    "fin_thickness": 1.5,
    "fin_count": 10
}
from build123d import *

L = PARAMS["length"]
W = PARAMS["width"]
BT = PARAMS["base_thickness"]
FH = PARAMS["fin_height"]
FT = PARAMS["fin_thickness"]
FC = int(PARAMS["fin_count"])

with BuildPart() as part:
    # Base thermal conduction plate
    with Locations((0, 0, BT/2)):
        Box(L, W, BT)
    # Parallel cooling fins array along width Y
    pitch = (W - FT) / (FC - 1)
    for i in range(FC):
        fy = -W/2 + FT/2 + i * pitch
        with Locations((0, fy, BT + FH/2)):
            Box(L, FT, FH)

    # 4x Corner mounting screw holes through base plate
    with GridLocations(L - 12.0, W - 12.0, 2, 2):
        with Locations((0, 0, BT/2)):
            Cylinder(radius=3.2/2, height=BT*3, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": "radial_fan_blower_nozzle",
        "description": "5015 radial cooling blower fan air duct nozzle directing focused airflow toward 3D printer hotend",
        "tags": ["fan duct", "blower nozzle", "airflow", "5015 fan", "air duct", "3d printer duct"],
        "code": """\
PARAMS = {
    "inlet_width": 20.0,
    "inlet_height": 15.0,
    "outlet_width": 35.0,
    "outlet_height": 3.5,
    "duct_length": 45.0,
    "wall_thickness": 1.6
}
from build123d import *

IW = PARAMS["inlet_width"]
IH = PARAMS["inlet_height"]
OW = PARAMS["outlet_width"]
OH = PARAMS["outlet_height"]
DL = PARAMS["duct_length"]
T = PARAMS["wall_thickness"]

with BuildPart() as part:
    # Outer loft transition from rectangular inlet to slim wide nozzle
    with BuildSketch(Plane.XY) as s1:
        Rectangle(IW + 2*T, IH + 2*T)
    with BuildSketch(Plane.XY.offset(DL)) as s2:
        Rectangle(OW + 2*T, OH + 2*T)
    loft()

    # Inner hollow air passage loft
    with BuildSketch(Plane.XY.offset(-1.0)) as s_in1:
        Rectangle(IW, IH)
    with BuildSketch(Plane.XY.offset(DL + 1.0)) as s_in2:
        Rectangle(OW, OH)
    loft(mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },

    # ── 6. PIPES, VALVES & FLUIDICS ──────────────────────────────────────────
    {
        "id": "pipe_tee_fitting_threaded",
        "description": "Tee junction pipe manifold fitting with three flanged cylindrical ports and intersecting internal fluid bores",
        "tags": ["pipe tee", "tee fitting", "plumbing", "manifold", "fluid junction", "three way"],
        "code": """\
PARAMS = {
    "run_length": 80.0,
    "branch_height": 45.0,
    "outer_dia": 32.0,
    "inner_dia": 24.0,
    "flange_dia": 42.0,
    "flange_thick": 5.0
}
from build123d import *

RL = PARAMS["run_length"]
BH = PARAMS["branch_height"]
OD = PARAMS["outer_dia"]
ID = PARAMS["inner_dia"]
FD = PARAMS["flange_dia"]
FT = PARAMS["flange_thick"]

with BuildPart() as part:
    # Horizontal run pipe along X
    with Locations(Location((0, 0, 0), (0, 90, 0))):
        Cylinder(radius=OD/2, height=RL)
        # End Flanges on run
        with Locations((0, 0, RL/2 - FT/2), (0, 0, -RL/2 + FT/2)):
            Cylinder(radius=FD/2, height=FT)

    # Vertical branch pipe along Z
    with Locations((0, 0, BH/2)):
        Cylinder(radius=OD/2, height=BH)
        with Locations((0, 0, BH/2 - FT/2)):
            Cylinder(radius=FD/2, height=FT)

    # Internal fluid flow through-bores
    with Locations(Location((0, 0, 0), (0, 90, 0))):
        Cylinder(radius=ID/2, height=RL*2, mode=Mode.SUBTRACT)
    with Locations((0, 0, BH/2)):
        Cylinder(radius=ID/2, height=BH*2, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": "hydraulic_manifold_block",
        "description": "Compact aluminum hydraulic manifold valve block with 4 O-ring ported channels and cross-drilled gallery",
        "tags": ["hydraulic", "manifold", "valve block", "o-ring port", "pneumatic", "fluid block"],
        "code": """\
PARAMS = {
    "block_length": 90.0,
    "block_width": 60.0,
    "block_height": 35.0,
    "port_thread_dia": 18.0,
    "port_depth": 12.0,
    "o_ring_groove_dia": 24.0,
    "gallery_bore_dia": 10.0
}
from build123d import *

L = PARAMS["block_length"]
W = PARAMS["block_width"]
H = PARAMS["block_height"]
PD = PARAMS["port_thread_dia"]
PDEP = PARAMS["port_depth"]
ODIA = PARAMS["o_ring_groove_dia"]
GD = PARAMS["gallery_bore_dia"]

with BuildPart() as part:
    Box(L, W, H)
    # Internal horizontal oil gallery bore along X
    with Locations(Location((0, 0, 0), (0, 90, 0))):
        Cylinder(radius=GD/2, height=L*2, mode=Mode.SUBTRACT)

    # 3 Top port counterbores with O-ring sealing recess
    with Locations((-25.0, 0, H/2), (0, 0, H/2), (25.0, 0, H/2)):
        Cylinder(radius=PD/2, height=PDEP*2, mode=Mode.SUBTRACT)
        Cylinder(radius=ODIA/2, height=3.0*2, mode=Mode.SUBTRACT)

    # 4 Corner mounting thru-holes
    with GridLocations(L - 14.0, W - 14.0, 2, 2):
        Cylinder(radius=6.5/2, height=H*2, mode=Mode.SUBTRACT)

assert len(part.part.solids()) == 1
export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    }
]
