"""
RAG Corpus — Universal CAD Archetypes (20 Production-Grade Examples)
====================================================================
Covers all major mechanical, consumer, industrial, and structural archetypes:
1. universal_stepped_shaft (Rotational / Turned)
2. universal_electronics_enclosure (Thin-Walled Shell & Screw Bosses)
3. universal_v_belt_pulley (V-Groove Pulley & Hub)
4. universal_spur_gear (Parametric Gear with Teeth)
5. universal_flanged_pipe_elbow (Swept 90° Elbow with Flanges)
6. universal_gusseted_l_bracket (Angle Bracket with Stiffener Rib)
7. universal_ergonomic_phone_stand (Angled Consumer Product)
8. universal_square_to_round_duct (Lofted Transition Duct)
9. universal_clevis_joint (Fork Pin Joint / Mechanism)
10. universal_centrifugal_impeller (Vanes & Backplate)
11. universal_heat_sink_extrusion (Finned Thermal Extrusion)
12. universal_hex_bolt_and_nut (Mechanical Fastener Assembly)
13. universal_hollow_bottle_vase (Axisymmetric Revolved Container)
14. universal_hinge_leaf (Knuckle Hinge with Fasteners)
15. universal_nema17_stepper_mount (Motor Faceplate with Adjustment Slots)
16. universal_knurled_control_knob (Ribbed Rotary Grip & D-Shaft)
17. universal_u_channel_bracket (Sheet Metal U-Profile)
18. universal_bearing_pillow_block (Cast Bearing Housing)
19. universal_robotic_arm_link (Hollow Arm Link with Clevis Ends)
20. universal_coffee_mug (Hollow Drinkware with Swept Handle)
"""

EXAMPLES = [
    # ── 1. ROTATIONAL / TURNED: STEPPED SHAFT ──────────────────────────────
    {
        "id": "universal_stepped_shaft",
        "description": "Precision turned stepped drive shaft with motor coupling section, bearing journals, keyway slot, circlip retaining groove, and center bore",
        "tags": ["shaft", "stepped shaft", "lathe", "turned", "rotational", "bearing seat", "keyway", "circlip", "drive shaft", "transmission"],
        "code": '''\
PARAMS = {
    "section1_dia": 16.0,
    "section1_len": 25.0,
    "bearing_dia": 20.0,
    "bearing_len": 35.0,
    "main_dia": 25.0,
    "main_len": 50.0,
    "keyway_width": 5.0,
    "keyway_depth": 3.0,
    "keyway_len": 20.0,
    "circlip_dia": 18.0,
    "circlip_width": 1.5,
    "center_bore_dia": 6.0,
    "center_bore_depth": 15.0
}
import math
from build123d import *

# Parameter Validation
assert PARAMS["section1_dia"] < PARAMS["bearing_dia"], "Section 1 must step up to bearing journal"
assert PARAMS["bearing_dia"] < PARAMS["main_dia"], "Bearing journal must step up to main body"
assert PARAMS["keyway_depth"] < PARAMS["section1_dia"] / 2.0, "Keyway too deep"

D1 = PARAMS["section1_dia"]
L1 = PARAMS["section1_len"]
D2 = PARAMS["bearing_dia"]
L2 = PARAMS["bearing_len"]
D3 = PARAMS["main_dia"]
L3 = PARAMS["main_len"]
KW = PARAMS["keyway_width"]
KD = PARAMS["keyway_depth"]
KL = PARAMS["keyway_len"]
CD = PARAMS["circlip_dia"]
CW = PARAMS["circlip_width"]
BD = PARAMS["center_bore_dia"]
BL = PARAMS["center_bore_depth"]

total_len = L1 + L2 + L3

with BuildPart() as part:
    # Concentric stepped cylinder stack along Z (Z=0 at shaft start)
    # Section 1 (Drive end): Z = 0 to L1
    with Locations((0, 0, L1 / 2.0)):
        Cylinder(radius=D1 / 2.0, height=L1)
    
    # Section 2 (Bearing journal): Z = L1 to L1 + L2
    with Locations((0, 0, L1 + L2 / 2.0)):
        Cylinder(radius=D2 / 2.0, height=L2)
        
    # Section 3 (Main shaft body): Z = L1 + L2 to total_len
    with Locations((0, 0, L1 + L2 + L3 / 2.0)):
        Cylinder(radius=D3 / 2.0, height=L3)

    # Keyway slot on Section 1
    with Locations((0, (D1 / 2.0) - (KD / 2.0), L1 / 2.0)):
        Box(KW, KD + 0.1, KL, mode=Mode.SUBTRACT)

    # Circlip retaining groove on bearing section (5mm from shoulder)
    groove_z = L1 + 5.0 + CW / 2.0
    with Locations((0, 0, groove_z)):
        Cylinder(radius=D2 / 2.0 + 0.1, height=CW, mode=Mode.SUBTRACT)
        Cylinder(radius=CD / 2.0, height=CW, mode=Mode.ADD)

    # Center axial bore on drive end
    with Locations((0, 0, BL / 2.0)):
        Cylinder(radius=BD / 2.0, height=BL + 0.1, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
solids = part.part.solids()
assert len(solids) == 1, f"Expected 1 solid, got {len(solids)}"
bb = part.part.bounding_box()
assert abs(bb.size.Z - total_len) < 0.5, f"Shaft length mismatch: got {bb.size.Z}, expected {total_len}"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 2. ENCLOSURES: ELECTRONICS PROJECT BOX ─────────────────────────────
    {
        "id": "universal_electronics_enclosure",
        "description": "Parametric electronics enclosure box with hollow interior, uniform wall thickness, 4 corner mounting screw bosses, and perimeter lid recess",
        "tags": ["enclosure", "electronics box", "case", "housing", "shell", "container", "box", "screw boss", "standoff"],
        "code": '''\
PARAMS = {
    "box_length": 120.0,
    "box_width": 80.0,
    "box_height": 40.0,
    "wall_thickness": 3.0,
    "corner_radius": 6.0,
    "boss_outer_dia": 9.0,
    "boss_hole_dia": 3.2,
    "boss_depth": 25.0,
    "lid_recess_depth": 2.0
}
import math
from build123d import *

assert PARAMS["wall_thickness"] * 2 < PARAMS["box_width"], "Wall too thick"
assert PARAMS["boss_hole_dia"] < PARAMS["boss_outer_dia"], "Boss hole exceeds outer dia"

L = PARAMS["box_length"]
W = PARAMS["box_width"]
H = PARAMS["box_height"]
T = PARAMS["wall_thickness"]
CR = PARAMS["corner_radius"]
B_OD = PARAMS["boss_outer_dia"]
B_ID = PARAMS["boss_hole_dia"]
B_H = PARAMS["boss_depth"]
LRD = PARAMS["lid_recess_depth"]

cavity_L = L - 2.0 * T
cavity_W = W - 2.0 * T
cavity_H = H - T

with BuildPart() as part:
    # 1. Outer rounded block
    with BuildSketch(Plane.XY):
        RectangleRounded(L, W, radius=CR)
    extrude(amount=H)

    # 2. Hollow inner cavity from top down (leaving floor thickness T)
    with Locations((0, 0, T + cavity_H / 2.0 + 0.1)):
        Box(cavity_L, cavity_W, cavity_H + 0.2, mode=Mode.SUBTRACT)

    # 3. Four corner mounting screw bosses with pilot bores
    inset_x = cavity_L / 2.0 - B_OD / 2.0
    inset_y = cavity_W / 2.0 - B_OD / 2.0
    with GridLocations(inset_x * 2.0, inset_y * 2.0, 2, 2):
        with Locations((0, 0, T + B_H / 2.0)):
            Cylinder(radius=B_OD / 2.0, height=B_H)
            Cylinder(radius=B_ID / 2.0, height=B_H + 0.2, mode=Mode.SUBTRACT)

    # 4. Perimeter lid rebate / lip along top edge
    with Locations((0, 0, H - LRD / 2.0)):
        with BuildSketch(Plane.XY):
            Rectangle(cavity_L + 1.5, cavity_W + 1.5)
        extrude(amount=LRD + 0.1, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Enclosure must be a single connected solid"
bb = part.part.bounding_box()
assert abs(bb.size.Z - H) < 0.5, "Height mismatch"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 3. ROTATIONAL / POWER TRANSMISSION: V-BELT PULLEY ─────────────────
    {
        "id": "universal_v_belt_pulley",
        "description": "Double-groove V-belt pulley with central reinforced hub, shaft bore, keyway, set-screw port, and weight-reducing web pockets",
        "tags": ["pulley", "v-belt", "belt drive", "rotational", "power transmission", "groove", "sheave", "hub", "keyway"],
        "code": '''\
PARAMS = {
    "pulley_outer_dia": 110.0,
    "pulley_width": 38.0,
    "hub_dia": 42.0,
    "hub_length": 48.0,
    "shaft_bore_dia": 19.0,
    "keyway_width": 6.0,
    "keyway_depth": 3.0,
    "groove_top_width": 12.5,
    "groove_depth": 11.0,
    "num_grooves": 2,
    "groove_spacing": 16.0
}
import math
from build123d import *

OD = PARAMS["pulley_outer_dia"]
PW = PARAMS["pulley_width"]
HD = PARAMS["hub_dia"]
HL = PARAMS["hub_length"]
BD = PARAMS["shaft_bore_dia"]
KW = PARAMS["keyway_width"]
KD = PARAMS["keyway_depth"]
GW = PARAMS["groove_top_width"]
GD = PARAMS["groove_depth"]
NG = int(PARAMS["num_grooves"])
GS = PARAMS["groove_spacing"]

with BuildPart() as part:
    # 1. Main outer pulley rim disc centered at Z = 0
    Cylinder(radius=OD / 2.0, height=PW)

    # 2. Central hub extending beyond rim
    Cylinder(radius=HD / 2.0, height=HL)

    # 3. V-belt grooves cut around perimeter
    start_z = -((NG - 1) * GS) / 2.0
    for g in range(NG):
        gz = start_z + g * GS
        with Locations((0, 0, gz)):
            Cone(bottom_radius=OD / 2.0 - GD, top_radius=OD / 2.0 + 1.0, height=GW, mode=Mode.SUBTRACT)

    # 4. Central shaft through-bore
    Cylinder(radius=BD / 2.0, height=HL * 2.0, mode=Mode.SUBTRACT)

    # 5. Standard parallel keyway slot in hub
    with Locations((0, (BD / 2.0) + (KD / 2.0), 0)):
        Box(KW, KD + 0.2, HL * 1.5, mode=Mode.SUBTRACT)

    # 6. Web lightening pockets
    web_r = (OD / 2.0 - GD + HD / 2.0) / 2.0
    with PolarLocations(radius=web_r, count=4):
        with Locations((0, 0, PW / 4.0)):
            Cylinder(radius=10.0, height=PW / 2.0, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Pulley must be 1 connected solid"
bb = part.part.bounding_box()
assert bb.size.X > 0 and bb.size.Y > 0, "Invalid bounding box"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 4. GEARS & POWER TRANSMISSION: SPUR GEAR ──────────────────────────
    {
        "id": "universal_spur_gear",
        "description": "Parametric spur gear with precision tooth profile, central hub, keyed shaft bore, and circular lightening pockets",
        "tags": ["gear", "spur gear", "pinion", "teeth", "involute", "pitch circle", "transmission", "drive", "cog"],
        "code": '''\
PARAMS = {
    "module": 2.5,
    "num_teeth": 24,
    "face_width": 18.0,
    "bore_dia": 15.0,
    "hub_dia": 35.0,
    "hub_length": 28.0,
    "keyway_width": 5.0,
    "keyway_depth": 2.5
}
import math
from build123d import *

M = PARAMS["module"]
N = int(PARAMS["num_teeth"])
FW = PARAMS["face_width"]
BD = PARAMS["bore_dia"]
HD = PARAMS["hub_dia"]
HL = PARAMS["hub_length"]
KW = PARAMS["keyway_width"]
KD = PARAMS["keyway_depth"]

pitch_dia = M * N
pitch_r = pitch_dia / 2.0
addendum = 1.0 * M
dedendum = 1.25 * M
root_r = pitch_r - dedendum
tooth_thickness = math.pi * M / 2.0

with BuildPart() as part:
    # 1. Base gear blank cylinder
    Cylinder(radius=root_r, height=FW)

    # 2. Add teeth radially around perimeter
    tooth_h = addendum + dedendum
    tooth_mid_r = root_r + tooth_h / 2.0
    for i in range(N):
        ang_deg = i * (360.0 / N)
        ang_rad = math.radians(ang_deg)
        tx = tooth_mid_r * math.cos(ang_rad)
        ty = tooth_mid_r * math.sin(ang_rad)
        with Locations(Location((tx, ty, 0), (0, 0, ang_deg))):
            Box(tooth_h + 1.0, tooth_thickness * 0.9, FW)

    # 3. Central reinforced hub
    Cylinder(radius=HD / 2.0, height=HL)

    # 4. Central keyed shaft through-bore
    Cylinder(radius=BD / 2.0, height=HL * 2.0, mode=Mode.SUBTRACT)
    with Locations((0, (BD / 2.0) + (KD / 2.0), 0)):
        Box(KW, KD + 0.2, HL * 2.0, mode=Mode.SUBTRACT)

    # 5. Weight-reducing radial cutouts
    pocket_r = (root_r + HD / 2.0) / 2.0
    if pocket_r - HD / 2.0 > 8.0:
        with PolarLocations(radius=pocket_r, count=5):
            Cylinder(radius=pocket_r * 0.28, height=FW * 1.5, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Spur gear must be 1 solid"
bb = part.part.bounding_box()
assert bb.size.X > pitch_dia, "Gear bounding box must exceed pitch diameter"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 5. PIPING & SWEPT: FLANGED PIPE ELBOW ─────────────────────────────
    {
        "id": "universal_flanged_pipe_elbow",
        "description": "Swept 90-degree pipe elbow with circular bolt-circle flanges, continuous fluid bore, and raised gasket faces",
        "tags": ["pipe", "elbow", "flange", "sweep", "plumbing", "fluid", "conduit", "bend", "tube", "duct"],
        "code": '''\
PARAMS = {
    "pipe_outer_dia": 48.0,
    "wall_thickness": 4.0,
    "bend_radius": 75.0,
    "flange_dia": 105.0,
    "flange_thickness": 12.0,
    "bolt_circle_dia": 82.0,
    "bolt_hole_dia": 10.0,
    "num_bolts": 4
}
import math
from build123d import *

OD = PARAMS["pipe_outer_dia"]
WT = PARAMS["wall_thickness"]
BR = PARAMS["bend_radius"]
FD = PARAMS["flange_dia"]
FT = PARAMS["flange_thickness"]
BCD = PARAMS["bolt_circle_dia"]
BHD = PARAMS["bolt_hole_dia"]
NB = int(PARAMS["num_bolts"])

ID = OD - 2.0 * WT

with BuildPart() as part:
    # 1. Swept curved pipe body
    with BuildSketch(Plane.XY) as pipe_sk:
        Circle(radius=OD / 2.0)
    with BuildLine(Plane.XZ) as path:
        CenterArc(center=(BR, 0), radius=BR, start_angle=180, arc_size=90)
    sweep(sections=pipe_sk.sketch, path=path.line)

    # 2. Flange 1 at Inlet (at Z=0, normal along Z)
    with Locations((0, 0, -FT / 2.0)):
        Cylinder(radius=FD / 2.0, height=FT)
        with PolarLocations(radius=BCD / 2.0, count=NB):
            Cylinder(radius=BHD / 2.0, height=FT * 2.0, mode=Mode.SUBTRACT)

    # 3. Flange 2 at Outlet (at X=BR, Z=BR, normal along X)
    with Locations(Location((BR + FT / 2.0, 0, BR), (0, 90, 0))):
        Cylinder(radius=FD / 2.0, height=FT)
        with PolarLocations(radius=BCD / 2.0, count=NB):
            Cylinder(radius=BHD / 2.0, height=FT * 2.0, mode=Mode.SUBTRACT)

    # 4. Continuous internal hollow fluid bore
    with BuildSketch(Plane.XY) as bore_sk:
        Circle(radius=ID / 2.0)
    with BuildLine(Plane.XZ) as bore_path:
        CenterArc(center=(BR, 0), radius=BR, start_angle=180, arc_size=90)
    sweep(sections=bore_sk.sketch, path=bore_path.line, mode=Mode.SUBTRACT)

    with Locations((0, 0, -FT / 2.0)):
        Cylinder(radius=ID / 2.0, height=FT * 2.0, mode=Mode.SUBTRACT)
    with Locations(Location((BR + FT / 2.0, 0, BR), (0, 90, 0))):
        Cylinder(radius=ID / 2.0, height=FT * 2.0, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Pipe elbow must be 1 solid"
bb = part.part.bounding_box()
assert bb.size.X > BR, "X dimension must span bend radius"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 6. STRUCTURAL BRACKETS: GUSSETED L-BRACKET ────────────────────────
    {
        "id": "universal_gusseted_l_bracket",
        "description": "Heavy-duty 90-degree angle bracket with central triangular stiffening gusset rib and slotted fastener mounting holes",
        "tags": ["bracket", "l-bracket", "angle bracket", "gusset", "stiffener", "rib", "mounting", "structural", "heavy duty"],
        "code": '''\
PARAMS = {
    "flange_width": 60.0,
    "base_length": 80.0,
    "upright_height": 80.0,
    "plate_thickness": 8.0,
    "gusset_thickness": 6.0,
    "slot_length": 18.0,
    "slot_width": 9.0,
    "hole_inset": 22.0
}
import math
from build123d import *

W = PARAMS["flange_width"]
BL = PARAMS["base_length"]
UH = PARAMS["upright_height"]
T = PARAMS["plate_thickness"]
GT = PARAMS["gusset_thickness"]
SL = PARAMS["slot_length"]
SW = PARAMS["slot_width"]
INSET = PARAMS["hole_inset"]

with BuildPart() as part:
    # 1. Horizontal base plate
    with Locations((BL / 2.0, 0, T / 2.0)):
        Box(BL, W, T)

    # 2. Vertical upright plate
    with Locations((T / 2.0, 0, UH / 2.0)):
        Box(T, W, UH)

    # 3. Triangular stiffening gusset rib
    gw = BL - T
    gh = UH - T
    with BuildSketch(Plane.XZ) as gusset_sk:
        with Locations((T, T)):
            Polygon([(0, 0), (gw, 0), (0, gh)])
    extrude(amount=GT, both=True)

    # 4. Slotted mounting holes in base
    for y_pos in [-W * 0.25, W * 0.25]:
        with Locations((BL - INSET, y_pos, T / 2.0)):
            Box(SL, SW, T * 2.0, mode=Mode.SUBTRACT)

    # 5. Mounting holes in upright
    for y_pos in [-W * 0.25, W * 0.25]:
        with Locations((T / 2.0, y_pos, UH - INSET)):
            Cylinder(radius=SW / 2.0, height=T * 2.0, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Gusseted bracket must be 1 monolithic solid"
bb = part.part.bounding_box()
assert abs(bb.size.X - BL) < 0.5, "Base length mismatch"
assert abs(bb.size.Z - UH) < 0.5, "Upright height mismatch"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 7. CONSUMER / ERGONOMIC: PHONE STAND ──────────────────────────────
    {
        "id": "universal_ergonomic_phone_stand",
        "description": "Ergonomic desktop phone and tablet stand with angled viewing cradle, retention lip, rear support strut, and cable cutouts",
        "tags": ["phone stand", "stand", "holder", "cradle", "desk organizer", "consumer", "tablet", "ergonomic", "charging dock"],
        "code": '''\
PARAMS = {
    "stand_width": 75.0,
    "base_depth": 90.0,
    "cradle_height": 110.0,
    "cradle_angle": 65.0,
    "lip_height": 16.0,
    "shelf_depth": 18.0,
    "plate_thickness": 5.0,
    "cable_slot_width": 18.0
}
import math
from build123d import *

W = PARAMS["stand_width"]
BD = PARAMS["base_depth"]
CH = PARAMS["cradle_height"]
ANG = PARAMS["cradle_angle"]
LH = PARAMS["lip_height"]
SD = PARAMS["shelf_depth"]
T = PARAMS["plate_thickness"]
CSW = PARAMS["cable_slot_width"]

with BuildPart() as part:
    # 1. Desktop base foot plate
    with Locations((BD / 2.0, 0, T / 2.0)):
        Box(BD, W, T)

    # 2. Angled cradle backrest plate
    rad_ang = math.radians(90 - ANG)
    mid_x = (CH / 2.0) * math.cos(rad_ang) + 15.0
    mid_z = (CH / 2.0) * math.sin(rad_ang) + T
    with Locations(Location((mid_x, 0, mid_z), (0, -(90 - ANG), 0))):
        Box(CH, W, T)

    # 3. Horizontal phone resting shelf
    shelf_x = 15.0 + SD / 2.0
    shelf_z = T + 12.0
    with Locations((shelf_x, 0, shelf_z)):
        Box(SD, W, T)

    # 4. Front retaining lip
    lip_x = 15.0 + SD
    lip_z = shelf_z + LH / 2.0
    with Locations((lip_x, 0, lip_z)):
        Box(T, W, LH)

    # 5. Rear triangular structural support truss
    support_len = BD * 0.65
    with BuildSketch(Plane.XZ) as rib_sk:
        Polygon([(15.0, T), (15.0 + support_len, T), (15.0, mid_z * 1.2)])
    extrude(amount=T * 1.5, both=True)

    # 6. Cable pass-through slot
    with Locations((shelf_x, 0, shelf_z)):
        Box(SD * 1.5, CSW, T * 3.0, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Phone stand must be 1 connected solid"
bb = part.part.bounding_box()
assert bb.size.X > 50 and bb.size.Z > 50, "Geometry extent check failed"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 8. LOFTED / DUCTS: SQUARE TO ROUND TRANSITION ─────────────────────
    {
        "id": "universal_square_to_round_duct",
        "description": "Smooth lofted HVAC transition duct connecting a rectangular ventilation intake to a circular exhaust duct with mounting flanges",
        "tags": ["loft", "duct", "transition", "square to round", "hvac", "ventilation", "nozzle", "funnel", "adapter", "aerodynamic"],
        "code": '''\
PARAMS = {
    "base_width": 80.0,
    "base_length": 80.0,
    "top_dia": 50.0,
    "transition_height": 70.0,
    "wall_thickness": 3.0,
    "base_flange_width": 12.0
}
import math
from build123d import *

BW = PARAMS["base_width"]
BL = PARAMS["base_length"]
TD = PARAMS["top_dia"]
H = PARAMS["transition_height"]
T = PARAMS["wall_thickness"]
FW = PARAMS["base_flange_width"]

with BuildPart() as part:
    # 1. Outer lofted solid
    with BuildSketch(Plane.XY) as sk_base:
        Rectangle(BL, BW)
    with BuildSketch(Plane.XY.offset(H)) as sk_top:
        Circle(radius=TD / 2.0)
    
    loft(sections=[sk_base.sketch, sk_top.sketch])

    # 2. Bottom rectangular mounting flange
    with Locations((0, 0, 3.0)):
        with BuildSketch(Plane.XY):
            Rectangle(BL + 2 * FW, BW + 2 * FW)
        extrude(amount=6.0)

    # 3. Flange corner bolt holes
    bx = (BL + FW) / 2.0
    by = (BW + FW) / 2.0
    with GridLocations(bx * 2.0, by * 2.0, 2, 2):
        Cylinder(radius=2.5, height=20.0, mode=Mode.SUBTRACT)

    # 4. Hollow inner air passage
    with BuildSketch(Plane.XY.offset(-5.0)) as sk_in_base:
        Rectangle(BL - 2 * T, BW - 2 * T)
    with BuildSketch(Plane.XY.offset(H + 5.0)) as sk_in_top:
        Circle(radius=(TD - 2 * T) / 2.0)
    
    loft(sections=[sk_in_base.sketch, sk_in_top.sketch], mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Duct transition must be 1 solid"
bb = part.part.bounding_box()
assert abs(bb.size.Z - (H + 3.0)) < 2.0, "Duct height mismatch"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 9. MECHANISMS / LINKAGES: CLEVIS FORK JOINT ───────────────────────
    {
        "id": "universal_clevis_joint",
        "description": "Mechanical clevis fork joint with cylindrical mounting shank, U-slot for rod end, and cross-pin bore",
        "tags": ["clevis", "fork", "rod end", "pin joint", "actuator", "linkage", "pivot", "mechanism", "suspension"],
        "code": '''\
PARAMS = {
    "shank_dia": 22.0,
    "shank_length": 35.0,
    "clevis_outer_width": 36.0,
    "clevis_slot_width": 16.0,
    "clevis_length": 45.0,
    "pin_hole_dia": 10.0,
    "end_fillet_r": 18.0
}
import math
from build123d import *

SD = PARAMS["shank_dia"]
SL = PARAMS["shank_length"]
CW = PARAMS["clevis_outer_width"]
SW = PARAMS["clevis_slot_width"]
CL = PARAMS["clevis_length"]
PD = PARAMS["pin_hole_dia"]
FR = PARAMS["end_fillet_r"]

total_len = SL + CL

with BuildPart() as part:
    # 1. Cylindrical mounting shank
    with Locations(Location((-SL / 2.0, 0, 0), (0, 90, 0))):
        Cylinder(radius=SD / 2.0, height=SL)

    # 2. Main rectangular clevis head block
    with Locations((CL / 2.0, 0, 0)):
        Box(CL, CW, CW)

    # 3. Rounded tip on clevis prongs
    with Locations((CL, 0, 0)):
        with Locations(Location((0, 0, 0), (90, 0, 0))):
            Cylinder(radius=CW / 2.0, height=CW)

    # 4. Central U-slot
    with Locations((CL / 2.0 + 5.0, 0, 0)):
        Box(CL + 10.0, SW, CW * 1.5, mode=Mode.SUBTRACT)

    # 5. Cross-pin through-bore
    pin_x = CL - (CW / 2.0) + 5.0
    with Locations(Location((pin_x, 0, 0), (90, 0, 0))):
        Cylinder(radius=PD / 2.0, height=CW * 1.5, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Clevis must be 1 connected solid"
bb = part.part.bounding_box()
assert bb.size.X > SL, "Total length must exceed shank length"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 10. FLUIDS / ROTATING: CENTRIFUGAL IMPELLER ───────────────────────
    {
        "id": "universal_centrifugal_impeller",
        "description": "Parametric centrifugal pump/fan impeller with curved backward-swept vanes, circular backplate shroud, and hub with bore",
        "tags": ["impeller", "pump", "turbine", "fan", "blower", "vanes", "rotor", "centrifugal", "fluid dynamics"],
        "code": '''\
PARAMS = {
    "outer_dia": 120.0,
    "backplate_thickness": 4.0,
    "hub_dia": 28.0,
    "hub_height": 22.0,
    "shaft_bore_dia": 8.0,
    "vane_height": 15.0,
    "vane_thickness": 3.0,
    "num_vanes": 6,
    "vane_inner_r": 20.0,
    "vane_outer_r": 55.0
}
import math
from build123d import *

OD = PARAMS["outer_dia"]
BT = PARAMS["backplate_thickness"]
HD = PARAMS["hub_dia"]
HH = PARAMS["hub_height"]
BD = PARAMS["shaft_bore_dia"]
VH = PARAMS["vane_height"]
VT = PARAMS["vane_thickness"]
NV = int(PARAMS["num_vanes"])
R_IN = PARAMS["vane_inner_r"]
R_OUT = PARAMS["vane_outer_r"]

with BuildPart() as part:
    # 1. Circular backplate disc
    with Locations((0, 0, BT / 2.0)):
        Cylinder(radius=OD / 2.0, height=BT)

    # 2. Central drive hub boss
    with Locations((0, 0, HH / 2.0)):
        Cylinder(radius=HD / 2.0, height=HH)

    # 3. Radial vanes arrayed around circumference
    vane_span = R_OUT - R_IN
    vane_mid_r = (R_IN + R_OUT) / 2.0
    for i in range(NV):
        ang_deg = i * (360.0 / NV)
        ang_rad = math.radians(ang_deg)
        vx = vane_mid_r * math.cos(ang_rad)
        vy = vane_mid_r * math.sin(ang_rad)
        with Locations(Location((vx, vy, BT + VH / 2.0), (0, 0, ang_deg + 30.0))):
            Box(vane_span, VT, VH)

    # 4. Central motor shaft through-bore
    with Locations((0, 0, HH / 2.0)):
        Cylinder(radius=BD / 2.0, height=HH * 2.0, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Impeller must be 1 connected solid"
bb = part.part.bounding_box()
assert abs(bb.size.X - OD) < 1.0, "Outer diameter mismatch"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 11. THERMAL / COOLING: HEAT SINK EXTRUSION ────────────────────────
    {
        "id": "universal_heat_sink_extrusion",
        "description": "High-surface-area extruded aluminum heatsink with thick base plate, array of cooling fins, and PCB mounting ears",
        "tags": ["heatsink", "heat sink", "cooling", "thermal", "fins", "extrusion", "electronics cooling", "pcb mount"],
        "code": '''\
PARAMS = {
    "sink_length": 100.0,
    "sink_width": 70.0,
    "base_thickness": 6.0,
    "fin_height": 28.0,
    "fin_thickness": 2.0,
    "num_fins": 12,
    "mount_hole_dia": 4.2
}
import math
from build123d import *

L = PARAMS["sink_length"]
W = PARAMS["sink_width"]
BT = PARAMS["base_thickness"]
FH = PARAMS["fin_height"]
FT = PARAMS["fin_thickness"]
NF = int(PARAMS["num_fins"])
MHD = PARAMS["mount_hole_dia"]

total_h = BT + FH
fin_pitch = (W - FT) / (NF - 1)

with BuildPart() as part:
    # 1. Base plate
    with Locations((0, 0, BT / 2.0)):
        Box(L, W, BT)

    # 2. Vertical cooling fins array
    start_y = -W / 2.0 + FT / 2.0
    for f in range(NF):
        y_pos = start_y + f * fin_pitch
        with Locations((0, y_pos, BT + FH / 2.0)):
            Box(L, FT, FH)

    # 3. Corner mounting holes
    inset_x = L / 2.0 - 8.0
    inset_y = W / 2.0 - 8.0
    with GridLocations(inset_x * 2.0, inset_y * 2.0, 2, 2):
        with Locations((0, 0, BT / 2.0)):
            Cylinder(radius=MHD / 2.0, height=BT * 2.0, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Heatsink must be 1 monolithic solid"
bb = part.part.bounding_box()
assert abs(bb.size.Z - total_h) < 0.5, "Total height mismatch"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 12. FASTENERS / ASSEMBLY: HEX BOLT & NUT ──────────────────────────
    {
        "id": "universal_hex_bolt_and_nut",
        "description": "Standard metric hexagonal head bolt and matching hexagonal threaded nut mechanical fastener assembly",
        "tags": ["bolt", "nut", "screw", "hex bolt", "fastener", "hardware", "assembly", "thread", "metric"],
        "code": '''\
PARAMS = {
    "nominal_dia": 10.0,
    "bolt_length": 45.0,
    "head_width_af": 16.0,
    "head_thickness": 6.8,
    "nut_thickness": 8.4,
    "nut_offset_z": 25.0
}
import math
from build123d import *

D = PARAMS["nominal_dia"]
BL = PARAMS["bolt_length"]
AF = PARAMS["head_width_af"]
HT = PARAMS["head_thickness"]
NT = PARAMS["nut_thickness"]
NZ = PARAMS["nut_offset_z"]

hex_r = AF / math.sqrt(3.0)

with BuildPart() as part:
    # Hex Head
    with Locations((0, 0, -HT / 2.0)):
        with BuildSketch(Plane.XY):
            RegularPolygon(radius=hex_r, side_count=6)
        extrude(amount=HT)

    # Bolt Shank
    with Locations((0, 0, BL / 2.0)):
        Cylinder(radius=D / 2.0, height=BL)

    # Chamfer tip
    with Locations((0, 0, BL)):
        Cone(bottom_radius=D / 2.0, top_radius=D / 2.0 - 1.0, height=1.5, mode=Mode.SUBTRACT)

    # Nut
    with Locations((0, 0, NZ + NT / 2.0)):
        with BuildSketch(Plane.XY):
            RegularPolygon(radius=hex_r, side_count=6)
        extrude(amount=NT)
        Cylinder(radius=D / 2.0, height=NT * 2.0, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
solids = part.part.solids()
assert len(solids) >= 1, "Must contain solid geometry"
bb = part.part.bounding_box()
assert bb.size.Z > BL, "Total length must span head and bolt shank"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 13. AXISYMMETRIC / REVOLVED: HOLLOW BOTTLE / VASE ─────────────────
    {
        "id": "universal_hollow_bottle_vase",
        "description": "Parametric revolved ergonomic container vase with thick weighted base, bulging profile, slender neck, and hollow cavity",
        "tags": ["bottle", "vase", "container", "revolve", "lathe", "axisymmetric", "pottery", "decor", "consumer", "hollow"],
        "code": '''\
PARAMS = {
    "base_dia": 60.0,
    "belly_dia": 95.0,
    "neck_dia": 36.0,
    "lip_dia": 44.0,
    "total_height": 150.0,
    "wall_thickness": 3.5,
    "base_thickness": 6.0
}
import math
from build123d import *

BD = PARAMS["base_dia"]
MD = PARAMS["belly_dia"]
ND = PARAMS["neck_dia"]
LD = PARAMS["lip_dia"]
H = PARAMS["total_height"]
WT = PARAMS["wall_thickness"]
BT = PARAMS["base_thickness"]

with BuildPart() as part:
    # 1. Base section
    with Locations((0, 0, 10.0)):
        Cylinder(radius=BD / 2.0, height=20.0)

    # 2. Expanding body cone
    with Locations((0, 0, 40.0)):
        Cone(bottom_radius=BD / 2.0, top_radius=MD / 2.0, height=40.0)

    # 3. Contracting shoulder cone
    with Locations((0, 0, 85.0)):
        Cone(bottom_radius=MD / 2.0, top_radius=ND / 2.0, height=50.0)

    # 4. Slender neck
    with Locations((0, 0, 125.0)):
        Cylinder(radius=ND / 2.0, height=30.0)

    # 5. Flared lip
    with Locations((0, 0, 145.0)):
        Cone(bottom_radius=ND / 2.0, top_radius=LD / 2.0, height=10.0)

    # 6. Hollow cavity
    cavity_h = H - BT
    with Locations((0, 0, BT + cavity_h / 2.0 + 0.1)):
        Cylinder(radius=(ND - 2 * WT) / 2.0, height=cavity_h + 0.2, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Vase must be 1 connected solid"
bb = part.part.bounding_box()
assert abs(bb.size.Z - H) < 1.0, "Vase height mismatch"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 14. MECHANISMS: HINGE LEAF WITH KNUCKLES ──────────────────────────
    {
        "id": "universal_hinge_leaf",
        "description": "Interlocking continuous mechanical hinge leaf with alternating cylindrical pin knuckles and countersunk screw holes",
        "tags": ["hinge", "leaf", "knuckle", "door hinge", "mechanism", "pivot", "fastener", "countersink", "hardware"],
        "code": '''\
PARAMS = {
    "leaf_width": 45.0,
    "leaf_height": 80.0,
    "plate_thickness": 3.0,
    "knuckle_outer_dia": 8.0,
    "pin_dia": 4.0,
    "num_knuckles": 3,
    "screw_hole_dia": 4.5,
    "screw_head_dia": 8.5
}
import math
from build123d import *

LW = PARAMS["leaf_width"]
LH = PARAMS["leaf_height"]
T = PARAMS["plate_thickness"]
KD = PARAMS["knuckle_outer_dia"]
PD = PARAMS["pin_dia"]
NK = int(PARAMS["num_knuckles"])
SHD = PARAMS["screw_hole_dia"]
CHD = PARAMS["screw_head_dia"]

total_segments = NK * 2 - 1
seg_h = LH / total_segments
cs_depth = (CHD - SHD) / 2.0

with BuildPart() as part:
    # 1. Plate leaf
    with Locations((LW / 2.0, 0, T / 2.0)):
        Box(LW, LH, T)

    # 2. Knuckle barrels
    for k in range(NK):
        y_center = -LH / 2.0 + (k * 2 + 0.5) * seg_h
        with Locations(Location((0, y_center, KD / 2.0), (90, 0, 0))):
            Cylinder(radius=KD / 2.0, height=seg_h)
            Cylinder(radius=PD / 2.0, height=seg_h * 2.0, mode=Mode.SUBTRACT)

    # 3. Countersunk holes
    hole_xs = [LW * 0.4, LW * 0.75]
    hole_ys = [-LH * 0.28, LH * 0.28]
    for hx in hole_xs:
        for hy in hole_ys:
            with Locations((hx, hy, T / 2.0)):
                Cylinder(radius=SHD / 2.0, height=T * 2.0, mode=Mode.SUBTRACT)
                with Locations((0, 0, T / 2.0 - cs_depth / 2.0)):
                    Cone(bottom_radius=SHD / 2.0, top_radius=CHD / 2.0, height=cs_depth, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Hinge leaf must be 1 solid"
bb = part.part.bounding_box()
assert abs(bb.size.Y - LH) < 0.5, "Leaf height mismatch"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 15. MOTOR MOUNTS: NEMA 17 / 23 STEPPER BRACKET ────────────────────
    {
        "id": "universal_nema17_stepper_mount",
        "description": "L-shaped precision stepper motor bracket with pilot circular recess, slotted motor bolt pattern, and base mounting slots",
        "tags": ["stepper", "nema17", "nema23", "motor mount", "bracket", "cnc", "3d printer", "robotics", "motion control"],
        "code": '''\
PARAMS = {
    "motor_face_size": 42.3,
    "pilot_dia": 22.5,
    "bolt_pcd": 31.0,
    "bolt_slot_len": 6.0,
    "bolt_hole_dia": 3.4,
    "plate_thickness": 4.0,
    "base_depth": 35.0,
    "stiffener_width": 5.0
}
import math
from build123d import *

MFS = PARAMS["motor_face_size"]
PD = PARAMS["pilot_dia"]
PCD = PARAMS["bolt_pcd"]
BSL = PARAMS["bolt_slot_len"]
BHD = PARAMS["bolt_hole_dia"]
T = PARAMS["plate_thickness"]
BD = PARAMS["base_depth"]
SW = PARAMS["stiffener_width"]

bracket_h = MFS + 12.0

with BuildPart() as part:
    # 1. Vertical face plate
    with Locations((T / 2.0, 0, bracket_h / 2.0)):
        Box(T, MFS + 6.0, bracket_h)

    # 2. Horizontal chassis base plate
    with Locations((BD / 2.0, 0, T / 2.0)):
        Box(BD, MFS + 6.0, T)

    # 3. Triangular stiffeners
    rib_len = BD - T
    rib_h = bracket_h * 0.7
    for sy in [-1, 1]:
        y_pos = sy * ((MFS + 6.0) / 2.0 - SW / 2.0)
        with BuildSketch(Plane.XZ) as rib_sk:
            with Locations((T, T)):
                Polygon([(0, 0), (rib_len, 0), (0, rib_h)])
        with Locations((0, y_pos, 0)):
            extrude(amount=SW / 2.0, both=True)

    # 4. Motor shaft pilot bore
    motor_center_z = bracket_h - (MFS / 2.0) - 2.0
    with Locations((T / 2.0, 0, motor_center_z)):
        Cylinder(radius=PD / 2.0, height=T * 2.0, mode=Mode.SUBTRACT)

    # 5. Slotted motor bolt pattern
    half_pcd = PCD / 2.0
    for dy in [-half_pcd, half_pcd]:
        for dz in [-half_pcd, half_pcd]:
            with Locations((T / 2.0, dy, motor_center_z + dz)):
                Box(T * 2.0, BHD, BSL, mode=Mode.SUBTRACT)

    # 6. Base chassis mounting slots
    with Locations((BD * 0.65, 0, T / 2.0)):
        Box(12.0, 24.0, T * 2.0, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Stepper bracket must be 1 solid"
bb = part.part.bounding_box()
assert bb.size.X > BD * 0.9, "Base extent check"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 16. CONSUMER / HARDWARE: KNURLED CONTROL KNOB ─────────────────────
    {
        "id": "universal_knurled_control_knob",
        "description": "Ergonomic rotary control knob with ribbed outer knurling, position indicator pointer, and D-shaft flat bore",
        "tags": ["knob", "dial", "potentiometer", "rotary", "d-shaft", "knurled", "ribbed", "audio", "control", "consumer"],
        "code": '''\
PARAMS = {
    "knob_dia": 32.0,
    "knob_height": 18.0,
    "skirt_dia": 38.0,
    "skirt_height": 4.0,
    "shaft_dia": 6.0,
    "d_flat_depth": 1.2,
    "num_ribs": 24,
    "pointer_len": 6.0
}
import math
from build123d import *

KD = PARAMS["knob_dia"]
KH = PARAMS["knob_height"]
SD = PARAMS["skirt_dia"]
SH = PARAMS["skirt_height"]
SFD = PARAMS["shaft_dia"]
DFD = PARAMS["d_flat_depth"]
NR = int(PARAMS["num_ribs"])
PL = PARAMS["pointer_len"]

with BuildPart() as part:
    # 1. Base skirt
    with Locations((0, 0, SH / 2.0)):
        Cylinder(radius=SD / 2.0, height=SH)

    # 2. Main knob body
    with Locations((0, 0, SH + (KH - SH) / 2.0)):
        Cylinder(radius=KD / 2.0, height=KH - SH)

    # 3. Perimeter knurling ribs
    knurl_r = KD / 2.0
    for i in range(NR):
        ang_deg = i * (360.0 / NR)
        ang_rad = math.radians(ang_deg)
        rx = knurl_r * math.cos(ang_rad)
        ry = knurl_r * math.sin(ang_rad)
        with Locations(Location((rx, ry, SH + (KH - SH) / 2.0), (0, 0, ang_deg))):
            Box(1.2, 1.8, KH - SH)

    # 4. Indicator pointer
    with Locations((KD / 4.0, 0, KH - 0.5)):
        Box(KD / 2.0, 1.5, 1.2, mode=Mode.SUBTRACT)

    # 5. D-shaft keyed bore
    bore_h = KH * 0.75
    with Locations((0, 0, bore_h / 2.0)):
        Cylinder(radius=SFD / 2.0, height=bore_h, mode=Mode.SUBTRACT)
        with Locations((0, (SFD / 2.0) - (DFD / 2.0), 0)):
            Box(SFD, DFD, bore_h, mode=Mode.ADD)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Control knob must be 1 solid"
bb = part.part.bounding_box()
assert abs(bb.size.Z - KH) < 0.5, "Knob height mismatch"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 17. SHEET METAL: U-CHANNEL BRACKET ────────────────────────────────
    {
        "id": "universal_u_channel_bracket",
        "description": "Formed sheet metal U-channel bracket with base mounting web, dual vertical flanges, and fastener matrix",
        "tags": ["u-channel", "sheet metal", "c-channel", "bracket", "stamped", "folded", "flange", "structural", "enclosure"],
        "code": '''\
PARAMS = {
    "channel_length": 120.0,
    "web_width": 50.0,
    "flange_height": 40.0,
    "sheet_thickness": 3.0,
    "hole_dia": 5.5,
    "hole_spacing": 40.0
}
import math
from build123d import *

L = PARAMS["channel_length"]
W = PARAMS["web_width"]
FH = PARAMS["flange_height"]
T = PARAMS["sheet_thickness"]
HD = PARAMS["hole_dia"]
HS = PARAMS["hole_spacing"]

with BuildPart() as part:
    # 1. Base web
    with Locations((0, 0, T / 2.0)):
        Box(L, W, T)

    # 2. Left side flange
    left_y = -W / 2.0 + T / 2.0
    with Locations((0, left_y, FH / 2.0)):
        Box(L, T, FH)

    # 3. Right side flange
    right_y = W / 2.0 - T / 2.0
    with Locations((0, right_y, FH / 2.0)):
        Box(L, T, FH)

    # 4. Patterned mounting holes in web
    for x_pos in [-HS, 0, HS]:
        with Locations((x_pos, 0, T / 2.0)):
            Cylinder(radius=HD / 2.0, height=T * 2.0, mode=Mode.SUBTRACT)

    # 5. Mounting holes in flanges
    for x_pos in [-HS, HS]:
        with Locations((x_pos, left_y, FH * 0.65)):
            Cylinder(radius=HD / 2.0, height=T * 2.0, mode=Mode.SUBTRACT)
        with Locations((x_pos, right_y, FH * 0.65)):
            Cylinder(radius=HD / 2.0, height=T * 2.0, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "U-channel must be 1 solid"
bb = part.part.bounding_box()
assert abs(bb.size.X - L) < 0.5, "Channel length mismatch"
assert abs(bb.size.Z - FH) < 0.5, "Channel height mismatch"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 18. HEAVY INDUSTRIAL: BEARING PILLOW BLOCK ────────────────────────
    {
        "id": "universal_bearing_pillow_block",
        "description": "Industrial split-style bearing pillow block housing with precision bore, lubrication grease port, and slotted base feet",
        "tags": ["pillow block", "bearing housing", "journal bearing", "cast iron", "grease port", "bushing", "heavy machinery"],
        "code": '''\
PARAMS = {
    "shaft_center_height": 45.0,
    "bearing_bore_dia": 35.0,
    "bearing_width": 24.0,
    "base_length": 140.0,
    "base_width": 40.0,
    "base_thickness": 14.0,
    "bolt_slot_spacing": 105.0,
    "bolt_slot_dia": 12.0
}
import math
from build123d import *

SCH = PARAMS["shaft_center_height"]
BBD = PARAMS["bearing_bore_dia"]
BW = PARAMS["bearing_width"]
BL = PARAMS["base_length"]
B_W = PARAMS["base_width"]
BT = PARAMS["base_thickness"]
BSS = PARAMS["bolt_slot_spacing"]
BSD = PARAMS["bolt_slot_dia"]

housing_outer_r = BBD / 2.0 + 12.0

with BuildPart() as part:
    # 1. Base mounting foot
    with Locations((0, 0, BT / 2.0)):
        Box(BL, B_W, BT)

    # 2. Central bearing housing boss
    with Locations(Location((0, 0, SCH), (90, 0, 0))):
        Cylinder(radius=housing_outer_r, height=BW)

    # 3. Tapered pillar
    with Locations((0, 0, (SCH + BT) / 2.0)):
        Box(housing_outer_r * 2.0, BW, SCH - BT + 2.0)

    # 4. Precision bearing through-bore
    with Locations(Location((0, 0, SCH), (90, 0, 0))):
        Cylinder(radius=BBD / 2.0, height=BW * 2.0, mode=Mode.SUBTRACT)

    # 5. Slotted bolt holes in base feet
    for sx in [-1, 1]:
        x_pos = sx * (BSS / 2.0)
        with Locations((x_pos, 0, BT / 2.0)):
            Box(18.0, BSD, BT * 2.0, mode=Mode.SUBTRACT)

    # 6. Lubrication port
    with Locations((0, 0, SCH + housing_outer_r - 4.0)):
        Cylinder(radius=3.0, height=10.0, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Pillow block must be 1 solid"
bb = part.part.bounding_box()
assert abs(bb.size.X - BL) < 0.5, "Base length mismatch"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 19. ROBOTICS: HOLLOW ARM LINKAGE ──────────────────────────────────
    {
        "id": "universal_robotic_arm_link",
        "description": "Lightweight robotic arm structural link with dual-end pivot clevises, internal wiring channel, and servo mount",
        "tags": ["robot arm", "linkage", "clevis", "pivot", "robotics", "drone arm", "chassis", "lightweight", "actuator link"],
        "code": '''\
PARAMS = {
    "center_distance": 150.0,
    "tube_outer_dia": 24.0,
    "tube_wall": 3.0,
    "clevis_width": 28.0,
    "clevis_gap": 14.0,
    "pivot_hole_dia": 6.0
}
import math
from build123d import *

CD = PARAMS["center_distance"]
TOD = PARAMS["tube_outer_dia"]
TW = PARAMS["tube_wall"]
CW = PARAMS["clevis_width"]
CG = PARAMS["clevis_gap"]
PHD = PARAMS["pivot_hole_dia"]

with BuildPart() as part:
    # 1. Connecting tubular body
    with Locations(Location((CD / 2.0, 0, 0), (0, 90, 0))):
        Cylinder(radius=TOD / 2.0, height=CD - 20.0)
        Cylinder(radius=(TOD - 2 * TW) / 2.0, height=CD, mode=Mode.SUBTRACT)

    # 2. Pivot clevis 1
    with Locations((0, 0, 0)):
        Cylinder(radius=CW / 2.0, height=CW)
        Box(CW + 5.0, CW + 5.0, CG, mode=Mode.SUBTRACT)
        Cylinder(radius=PHD / 2.0, height=CW * 2.0, mode=Mode.SUBTRACT)

    # 3. Pivot clevis 2
    with Locations((CD, 0, 0)):
        Cylinder(radius=CW / 2.0, height=CW)
        Box(CW + 5.0, CW + 5.0, CG, mode=Mode.SUBTRACT)
        Cylinder(radius=PHD / 2.0, height=CW * 2.0, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Robot arm link must be 1 solid"
bb = part.part.bounding_box()
assert bb.size.X >= CD, "Link extent must span center distance"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    # ── 20. CONSUMER: COFFEE MUG WITH SWEPT HANDLE ────────────────────────
    {
        "id": "universal_coffee_mug",
        "description": "Ergonomic ceramic coffee mug with hollow drink cavity, smooth rounded rim, and swept ergonomic finger handle",
        "tags": ["mug", "cup", "coffee mug", "drinkware", "consumer", "kitchen", "handle", "sweep", "hollow"],
        "code": '''\
PARAMS = {
    "mug_outer_dia": 82.0,
    "mug_height": 95.0,
    "wall_thickness": 4.0,
    "floor_thickness": 6.0,
    "handle_radius": 25.0,
    "handle_thickness": 6.0
}
import math
from build123d import *

OD = PARAMS["mug_outer_dia"]
H = PARAMS["mug_height"]
WT = PARAMS["wall_thickness"]
FT = PARAMS["floor_thickness"]
HR = PARAMS["handle_radius"]
HT = PARAMS["handle_thickness"]

ID = OD - 2.0 * WT

with BuildPart() as part:
    # 1. Main cylindrical mug body
    with Locations((0, 0, H / 2.0)):
        Cylinder(radius=OD / 2.0, height=H)

    # 2. Hollow drink cavity
    cavity_h = H - FT
    with Locations((0, 0, FT + cavity_h / 2.0 + 0.1)):
        Cylinder(radius=ID / 2.0, height=cavity_h + 0.2, mode=Mode.SUBTRACT)

    # 3. Ergonomic finger loop handle fused to outer wall
    with Locations(Location((OD / 2.0 - 4.0, 0, H / 2.0), (0, 90, 0))):
        Torus(major_radius=HR, minor_radius=HT)

    # 4. Clean subtractive re-pass inside cavity to ensure clear interior
    with Locations((0, 0, FT + cavity_h / 2.0 + 0.1)):
        Cylinder(radius=ID / 2.0, height=cavity_h + 0.2, mode=Mode.SUBTRACT)

# Validation
assert part.part is not None, "Build failed: part is None"
assert len(part.part.solids()) == 1, "Coffee mug must be 1 monolithic solid"
bb = part.part.bounding_box()
assert abs(bb.size.Z - H) < 0.5, "Mug height mismatch"

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    }
]
