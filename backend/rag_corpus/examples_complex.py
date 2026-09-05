"""
RAG Corpus — 30 High-Difficulty Engineering & Mechanical CAD Examples
Covers heatsinks, cylindrical motor housings, gear blanks, pulleys,
weld flanges, turbine discs, enclosures, manifolds, camshafts, and actuators.
"""

EXAMPLES = [
    {
        "id": 'cpu_heatsink_fin_array',
        "description": 'High-performance linear extruded aluminum CPU heatsink with rectangular fin array, thick heat spreader base plate, and 4 corner mounting screw holes',
        "tags": ['heatsink', 'heat sink', 'cpu', 'thermal', 'cooling', 'fins', 'extruded', 'heat spreader', 'electronics cooling'],
        "code": """\
PARAMS = {
    "base_length": 80.0,
    "base_width": 60.0,
    "base_thickness": 6.0,
    "fin_height": 28.0,
    "fin_thickness": 2.0,
    "fin_count": 8,
    "mount_hole_dia": 3.5,
    "mount_hole_inset": 6.0
}
import math
from build123d import *

L = PARAMS["base_length"]
W = PARAMS["base_width"]
T = PARAMS["base_thickness"]
FH = PARAMS["fin_height"]
FT = PARAMS["fin_thickness"]
N = int(PARAMS["fin_count"])
HD = PARAMS["mount_hole_dia"]
INS = PARAMS["mount_hole_inset"]

gap = (W - (N * FT)) / max(1, N - 1)

with BuildPart() as part:
    # 1. Base plate
    with Locations((0, 0, T / 2.0)):
        Box(L, W, T)
    # 2. Cooling fins
    for i in range(N):
        y_pos = -W / 2.0 + FT / 2.0 + i * (FT + gap)
        with Locations((0, y_pos, T + FH / 2.0)):
            Box(L, FT, FH)
    # 3. 4 Corner mounting holes
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            hx = sx * (L / 2.0 - INS)
            hy = sy * (W / 2.0 - INS)
            with Locations((hx, hy, T / 2.0)):
                Cylinder(radius=HD / 2.0, height=T * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'cylindrical_motor_stator_housing',
        "description": 'Brushless electric motor cylindrical stator housing with central bore, front mounting flange with 4-bolt pattern, and longitudinal external cooling ribs',
        "tags": ['motor housing', 'stator', 'brushless', 'electric motor', 'casing', 'cooling ribs', 'flange', 'powertrain'],
        "code": """\
PARAMS = {
    "outer_radius": 30.0,
    "inner_radius": 24.0,
    "length": 70.0,
    "flange_radius": 42.0,
    "flange_thickness": 6.0,
    "bolt_pcd": 68.0,
    "bolt_hole_dia": 4.5,
    "rib_count": 6,
    "rib_height": 4.0,
    "rib_thickness": 3.0
}
import math
from build123d import *

OR = PARAMS["outer_radius"]
IR = PARAMS["inner_radius"]
L = PARAMS["length"]
FR = PARAMS["flange_radius"]
FT = PARAMS["flange_thickness"]
PCD = PARAMS["bolt_pcd"]
BHD = PARAMS["bolt_hole_dia"]
NR = int(PARAMS["rib_count"])
RH = PARAMS["rib_height"]
RT = PARAMS["rib_thickness"]

with BuildPart() as part:
    # 1. Main outer cylinder body
    with Locations((0, 0, L / 2.0)):
        Cylinder(radius=OR, height=L)
    # 2. Front mounting flange
    with Locations((0, 0, FT / 2.0)):
        Cylinder(radius=FR, height=FT)
    # 3. External longitudinal cooling ribs
    for i in range(NR):
        angle = i * (360.0 / NR)
        rad = math.radians(angle)
        rib_center_r = OR + RH / 2.0
        rx = rib_center_r * math.cos(rad)
        ry = rib_center_r * math.sin(rad)
        rib_len = L - FT
        with Locations(Location((rx, ry, FT + rib_len / 2.0), (0, 0, angle))):
            Box(RH, RT, rib_len)
    # 4. Central stator through bore
    with Locations((0, 0, (L + FT) / 2.0)):
        Cylinder(radius=IR, height=(L + FT) * 2.0, mode=Mode.SUBTRACT)
    # 5. Flange bolt pattern
    with Locations((0, 0, FT / 2.0)):
        with PolarLocations(radius=PCD / 2.0, count=4):
            Cylinder(radius=BHD / 2.0, height=FT * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'spur_gear_blank',
        "description": 'Machined industrial spur gear blank with central hub, shaft bore, standard keyway, recessed web, and outer rim with circular lightening holes',
        "tags": ['spur gear', 'gear blank', 'hub', 'keyway', 'lightening holes', 'transmission', 'powertrain', 'machined'],
        "code": """\
PARAMS = {
    "rim_outer_radius": 60.0,
    "rim_inner_radius": 48.0,
    "rim_width": 20.0,
    "web_thickness": 8.0,
    "hub_outer_radius": 24.0,
    "hub_width": 30.0,
    "bore_radius": 12.0,
    "keyway_width": 6.0,
    "keyway_depth": 3.0,
    "hole_pcd": 72.0,
    "hole_diameter": 12.0
}
import math
from build123d import *

ROR = PARAMS["rim_outer_radius"]
RIR = PARAMS["rim_inner_radius"]
RW = PARAMS["rim_width"]
WT = PARAMS["web_thickness"]
HOR = PARAMS["hub_outer_radius"]
HW = PARAMS["hub_width"]
BR = PARAMS["bore_radius"]
KW = PARAMS["keyway_width"]
KD = PARAMS["keyway_depth"]
HPCD = PARAMS["hole_pcd"]
HD = PARAMS["hole_diameter"]

with BuildPart() as part:
    # 1. Outer rim
    with Locations((0, 0, 0)):
        Cylinder(radius=ROR, height=RW)
    # 2. Recessed central web
    with Locations((0, 0, 0)):
        Cylinder(radius=ROR, height=WT)
    # Remove hollow between hub and rim to leave web
    with Locations((0, 0, RW / 2.0)):
        # Top recess
        recess_depth = (RW - WT) / 2.0
        with Locations((0, 0, -recess_depth / 2.0)):
            Cylinder(radius=RIR, height=recess_depth, mode=Mode.SUBTRACT)
    with Locations((0, 0, -RW / 2.0)):
        # Bottom recess
        recess_depth = (RW - WT) / 2.0
        with Locations((0, 0, recess_depth / 2.0)):
            Cylinder(radius=RIR, height=recess_depth, mode=Mode.SUBTRACT)
    # 3. Central hub
    with Locations((0, 0, 0)):
        Cylinder(radius=HOR, height=HW)
    # 4. Central bore
    with Locations((0, 0, 0)):
        Cylinder(radius=BR, height=HW * 2.0, mode=Mode.SUBTRACT)
    # 5. Keyway
    with Locations((0, BR + KD / 2.0, 0)):
        Box(KW, KD + 1.0, HW * 2.0, mode=Mode.SUBTRACT)
    # 6. Lightening holes in web
    with Locations((0, 0, 0)):
        with PolarLocations(radius=HPCD / 2.0, count=4):
            Cylinder(radius=HD / 2.0, height=RW * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'v_groove_pulley',
        "description": 'Single-groove industrial V-belt drive pulley with central hub, shaft bore, keyway slot, web plate, and 38-degree trapezoidal V-groove rim',
        "tags": ['pulley', 'v-belt', 'v-groove', 'belt drive', 'hub', 'keyway', 'sheave', 'mechanical drive'],
        "code": """\
PARAMS = {
    "outer_dia": 100.0,
    "groove_depth": 14.0,
    "groove_top_width": 16.0,
    "groove_bottom_width": 8.0,
    "rim_width": 24.0,
    "hub_dia": 40.0,
    "hub_width": 32.0,
    "bore_dia": 20.0,
    "key_width": 6.0,
    "key_depth": 3.0
}
import math
from build123d import *

OD = PARAMS["outer_dia"]
GD = PARAMS["groove_depth"]
GTW = PARAMS["groove_top_width"]
GBW = PARAMS["groove_bottom_width"]
RW = PARAMS["rim_width"]
HD = PARAMS["hub_dia"]
HW = PARAMS["hub_width"]
BD = PARAMS["bore_dia"]
KW = PARAMS["key_width"]
KD = PARAMS["key_depth"]

OR = OD / 2.0
HR = HD / 2.0
BR = BD / 2.0

with BuildPart() as part:
    # 1. Main outer rim cylinder
    with Locations((0, 0, 0)):
        Cylinder(radius=OR, height=RW)
    # 2. Central hub
    with Locations((0, 0, 0)):
        Cylinder(radius=HR, height=HW)
    # 3. Center through bore
    with Locations((0, 0, 0)):
        Cylinder(radius=BR, height=max(HW, RW) * 2.0, mode=Mode.SUBTRACT)
    # 4. Keyway slot
    with Locations((0, BR + KD / 2.0, 0)):
        Box(KW, KD + 1.0, max(HW, RW) * 2.0, mode=Mode.SUBTRACT)
    # 5. V-groove revolve subtraction
    with BuildSketch(Plane.XZ) as sk:
        with Locations((OR, 0)):
            # Trapezoidal groove cross section centered at outer radius
            pts = [
                (0, GTW / 2.0),
                (-GD, GBW / 2.0),
                (-GD, -GBW / 2.0),
                (0, -GTW / 2.0)
            ]
            Polygon(pts)
    revolve(axis=Axis.Z, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'weld_neck_pipe_flange',
        "description": 'Class 150 weld neck pipe flange with raised face, through bore, tapered welding neck hub, and 8-bolt circle pattern',
        "tags": ['pipe flange', 'flange', 'weld neck', 'piping', 'valve', 'raised face', 'pressure vessel', 'bolt circle'],
        "code": """\
PARAMS = {
    "flange_od": 150.0,
    "flange_thickness": 18.0,
    "raised_face_dia": 90.0,
    "raised_face_height": 2.0,
    "neck_base_dia": 85.0,
    "neck_tip_dia": 60.0,
    "neck_height": 35.0,
    "bore_dia": 50.0,
    "bolt_pcd": 120.0,
    "bolt_hole_dia": 18.0,
    "num_bolts": 8
}
import math
from build123d import *

FOD = PARAMS["flange_od"]
FT = PARAMS["flange_thickness"]
RFD = PARAMS["raised_face_dia"]
RFH = PARAMS["raised_face_height"]
NBD = PARAMS["neck_base_dia"]
NTD = PARAMS["neck_tip_dia"]
NH = PARAMS["neck_height"]
BD = PARAMS["bore_dia"]
PCD = PARAMS["bolt_pcd"]
BHD = PARAMS["bolt_hole_dia"]
NB = int(PARAMS["num_bolts"])

with BuildPart() as part:
    # 1. Main flange ring
    with Locations((0, 0, FT / 2.0)):
        Cylinder(radius=FOD / 2.0, height=FT)
    # 2. Raised face on bottom
    with Locations((0, 0, -RFH / 2.0)):
        Cylinder(radius=RFD / 2.0, height=RFH)
    # 3. Tapered weld neck
    with Locations((0, 0, FT + NH / 2.0)):
        Cone(bottom_radius=NBD / 2.0, top_radius=NTD / 2.0, height=NH)
    # 4. Central through bore
    total_h = FT + RFH + NH + 10.0
    with Locations((0, 0, total_h / 2.0 - RFH)):
        Cylinder(radius=BD / 2.0, height=total_h * 2.0, mode=Mode.SUBTRACT)
    # 5. Bolt holes
    with Locations((0, 0, FT / 2.0)):
        with PolarLocations(radius=PCD / 2.0, count=NB):
            Cylinder(radius=BHD / 2.0, height=FT * 2.5, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'turbine_compressor_disc_blank',
        "description": 'Gas turbine or turbocharger centrifugal compressor rotor disc blank with central shaft bore, curved hub, rim, and circular balancing holes',
        "tags": ['turbine disc', 'compressor disc', 'rotor', 'turbocharger', 'aerospace', 'impeller blank', 'blisk', 'turbomachinery'],
        "code": """\
PARAMS = {
    "disc_outer_radius": 65.0,
    "disc_rim_thickness": 12.0,
    "hub_outer_radius": 26.0,
    "hub_height": 40.0,
    "bore_radius": 10.0,
    "web_thickness": 7.0,
    "balance_hole_pcd": 80.0,
    "balance_hole_dia": 8.0
}
import math
from build123d import *

R_OUT = PARAMS["disc_outer_radius"]
T_RIM = PARAMS["disc_rim_thickness"]
R_HUB = PARAMS["hub_outer_radius"]
H_HUB = PARAMS["hub_height"]
R_BORE = PARAMS["bore_radius"]
T_WEB = PARAMS["web_thickness"]
PCD = PARAMS["balance_hole_pcd"]
BHD = PARAMS["balance_hole_dia"]

with BuildPart() as part:
    # 1. Central cylindrical hub
    with Locations((0, 0, H_HUB / 2.0)):
        Cylinder(radius=R_HUB, height=H_HUB)
    # 2. Disc body from bottom
    with Locations((0, 0, T_RIM / 2.0)):
        Cylinder(radius=R_OUT, height=T_RIM)
    # 3. Transition cone from hub to disc web
    with Locations((0, 0, T_RIM + (H_HUB - T_RIM) / 2.0)):
        Cone(bottom_radius=R_HUB * 1.3, top_radius=R_HUB, height=H_HUB - T_RIM)
    # 4. Central shaft bore
    with Locations((0, 0, H_HUB / 2.0)):
        Cylinder(radius=R_BORE, height=H_HUB * 2.0, mode=Mode.SUBTRACT)
    # 5. Perimeter dynamic balancing holes
    with Locations((0, 0, T_RIM / 2.0)):
        with PolarLocations(radius=PCD / 2.0, count=6):
            Cylinder(radius=BHD / 2.0, height=T_RIM * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'electronics_enclosure_standoffs',
        "description": 'Rectangular electronics project box bottom enclosure with rounded corners, hollow interior, 4 corner PCB screw standoff bosses, and side cable gland cutout',
        "tags": ['enclosure', 'electronics box', 'chassis', 'pcb standoff', 'boss', 'cable gland', 'housing', 'sheet metal box'],
        "code": """\
PARAMS = {
    "box_length": 110.0,
    "box_width": 75.0,
    "box_height": 35.0,
    "wall_thickness": 3.0,
    "corner_radius": 6.0,
    "boss_dia": 8.0,
    "boss_hole_dia": 2.8,
    "boss_height": 12.0,
    "cable_cutout_dia": 14.0
}
import math
from build123d import *

L = PARAMS["box_length"]
W = PARAMS["box_width"]
H = PARAMS["box_height"]
T = PARAMS["wall_thickness"]
CR = PARAMS["corner_radius"]
BD = PARAMS["boss_dia"]
BHD = PARAMS["boss_hole_dia"]
BH = PARAMS["boss_height"]
CD = PARAMS["cable_cutout_dia"]

with BuildPart() as part:
    # 1. Solid rounded outer box
    with BuildSketch(Plane.XY):
        RectangleRounded(L, W, CR)
    extrude(amount=H)
    # 2. Hollow out inside cavity (leaving floor of thickness T)
    inner_l = L - 2.0 * T
    inner_w = W - 2.0 * T
    inner_cr = max(1.0, CR - T)
    with BuildSketch(Plane.XY.offset(T)):
        RectangleRounded(inner_l, inner_w, inner_cr)
    extrude(amount=H, mode=Mode.SUBTRACT)
    # 3. 4 Corner PCB standoff bosses
    boss_inset_x = L / 2.0 - T - BD / 2.0 - 2.0
    boss_inset_y = W / 2.0 - T - BD / 2.0 - 2.0
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            bx = sx * boss_inset_x
            by = sy * boss_inset_y
            with Locations((bx, by, T + BH / 2.0)):
                Cylinder(radius=BD / 2.0, height=BH)
                Cylinder(radius=BHD / 2.0, height=BH * 2.0, mode=Mode.SUBTRACT)
    # 4. Side cable pass-through hole
    with Locations((L / 2.0, 0, T + CD / 2.0 + 4.0)):
        with Locations(Location((0, 0, 0), (0, 90, 0))):
            Cylinder(radius=CD / 2.0, height=T * 4.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'heat_exchanger_tube_sheet',
        "description": 'Shell-and-tube heat exchanger circular tube sheet plate with peripheral flange bolt holes and perforated hexagonal/triangular pitch tube hole array',
        "tags": ['tube sheet', 'heat exchanger', 'perforated', 'boiler', 'condenser', 'baffle', 'thermal engineering', 'tube bundle'],
        "code": """\
PARAMS = {
    "plate_diameter": 160.0,
    "plate_thickness": 14.0,
    "tube_hole_dia": 10.0,
    "tube_pitch": 18.0,
    "bolt_pcd": 140.0,
    "bolt_hole_dia": 12.0,
    "num_bolts": 8
}
import math
from build123d import *

PD = PARAMS["plate_diameter"]
PT = PARAMS["plate_thickness"]
TD = PARAMS["tube_hole_dia"]
PITCH = PARAMS["tube_pitch"]
BPCD = PARAMS["bolt_pcd"]
BHD = PARAMS["bolt_hole_dia"]
NB = int(PARAMS["num_bolts"])

max_tube_radius = BPCD / 2.0 - 20.0

with BuildPart() as part:
    # 1. Main circular plate
    with Locations((0, 0, PT / 2.0)):
        Cylinder(radius=PD / 2.0, height=PT)
    # 2. Outer flange bolt pattern
    with Locations((0, 0, PT / 2.0)):
        with PolarLocations(radius=BPCD / 2.0, count=NB):
            Cylinder(radius=BHD / 2.0, height=PT * 2.0, mode=Mode.SUBTRACT)
    # 3. Grid of tube holes within tube bundle zone
    coords = []
    n_steps = int(max_tube_radius // PITCH) + 1
    for ix in range(-n_steps, n_steps + 1):
        for iy in range(-n_steps, n_steps + 1):
            x = ix * PITCH + (PITCH / 2.0 if (iy % 2 != 0) else 0.0)
            y = iy * (PITCH * math.sqrt(3) / 2.0)
            if math.hypot(x, y) <= max_tube_radius:
                coords.append((x, y))
    for (cx, cy) in coords:
        with Locations((cx, cy, PT / 2.0)):
            Cylinder(radius=TD / 2.0, height=PT * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'jaw_coupling_hub',
        "description": 'Three-jaw flexible spider shaft coupling hub with central bore, keyway, clamping slit, and interlocking curved drive jaws',
        "tags": ['jaw coupling', 'coupling', 'spider coupling', 'shaft coupling', 'drive jaw', 'flexible coupling', 'powertrain'],
        "code": """\
PARAMS = {
    "outer_radius": 35.0,
    "hub_height": 25.0,
    "jaw_height": 18.0,
    "jaw_span_deg": 50.0,
    "bore_radius": 12.0,
    "key_width": 5.0,
    "key_depth": 2.5
}
import math
from build123d import *

OR = PARAMS["outer_radius"]
HH = PARAMS["hub_height"]
JH = PARAMS["jaw_height"]
SPAN = PARAMS["jaw_span_deg"]
BR = PARAMS["bore_radius"]
KW = PARAMS["key_width"]
KD = PARAMS["key_depth"]

with BuildPart() as part:
    # 1. Base hub solid cylinder
    with Locations((0, 0, HH / 2.0)):
        Cylinder(radius=OR, height=HH)
    # 2. 3 interlocking drive jaws protruding upward
    for i in range(3):
        angle = i * 120.0
        with BuildSketch(Plane.XY.offset(HH)) as sk:
            with Locations((0, 0)):
                start_a = angle - SPAN / 2.0
                end_a = angle + SPAN / 2.0
                # Sector annulus
                n_segs = 12
                pts = []
                # Outer arc
                for s in range(n_segs + 1):
                    a = math.radians(start_a + s * (end_a - start_a) / n_segs)
                    pts.append((OR * math.cos(a), OR * math.sin(a)))
                # Inner arc
                for s in range(n_segs, -1, -1):
                    a = math.radians(start_a + s * (end_a - start_a) / n_segs)
                    pts.append(((BR + 5.0) * math.cos(a), (BR + 5.0) * math.sin(a)))
                Polygon(pts)
        extrude(amount=JH)
    # 3. Center shaft bore through entire assembly
    total_h = HH + JH + 10.0
    with Locations((0, 0, total_h / 2.0)):
        Cylinder(radius=BR, height=total_h * 2.0, mode=Mode.SUBTRACT)
    # 4. Keyway slot
    with Locations((0, BR + KD / 2.0, total_h / 2.0)):
        Box(KW, KD + 1.0, total_h * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'stepped_drive_shaft',
        "description": 'Three-step mechanical transmission drive shaft with precision bearing journals, central gear seating shoulder, keyway, and retaining circlip groove',
        "tags": ['stepped shaft', 'drive shaft', 'transmission shaft', 'shaft', 'bearing journal', 'keyway', 'circlip groove', 'axle'],
        "code": """\
PARAMS = {
    "d_small": 20.0,
    "len_small": 35.0,
    "d_middle": 28.0,
    "len_middle": 60.0,
    "d_large": 36.0,
    "len_large": 45.0,
    "key_width": 8.0,
    "key_length": 30.0,
    "key_depth": 4.0,
    "groove_width": 2.0,
    "groove_depth": 1.5
}
import math
from build123d import *

D1 = PARAMS["d_small"]
L1 = PARAMS["len_small"]
D2 = PARAMS["d_large"]
L2 = PARAMS["len_large"]
D3 = PARAMS["d_middle"]
L3 = PARAMS["len_middle"]
KW = PARAMS["key_width"]
KL = PARAMS["key_length"]
KD = PARAMS["key_depth"]
GW = PARAMS["groove_width"]
GD = PARAMS["groove_depth"]

with BuildPart() as part:
    # 1. Section 1 (Left small journal)
    with Locations((0, 0, L1 / 2.0)):
        Cylinder(radius=D1 / 2.0, height=L1)
    # 2. Section 2 (Center large seating shoulder)
    with Locations((0, 0, L1 + L2 / 2.0)):
        Cylinder(radius=D2 / 2.0, height=L2)
    # 3. Section 3 (Right middle journal)
    with Locations((0, 0, L1 + L2 + L3 / 2.0)):
        Cylinder(radius=D3 / 2.0, height=L3)
    # 4. Keyway milled into center large section
    center_z = L1 + L2 / 2.0
    r_large = D2 / 2.0
    with Locations((0, r_large - KD / 2.0, center_z)):
        Box(KW, KD * 2.0, KL, mode=Mode.SUBTRACT)
    # 5. Circlip groove on small journal near end
    groove_z = 10.0
    with Locations((0, 0, groove_z)):
        # Subtract outer annular ring leaving inner core
        ring_ir = D1 / 2.0 - GD
        with BuildSketch(Plane.XY) as sk:
            Circle(D1 / 2.0 + 1.0)
            Circle(ring_ir, mode=Mode.SUBTRACT)
        extrude(amount=GW, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'hydraulic_subplate_valves_manifold',
        "description": 'High-pressure hydraulic valve subplate manifold block with standard P, T, A, B port counterbores, internal galleries, and mounting holes',
        "tags": ['hydraulic manifold', 'valve block', 'fluid power', 'subplate', 'hydraulic ports', 'o-ring counterbore', 'manifold'],
        "code": """\
PARAMS = {
    "block_length": 90.0,
    "block_width": 60.0,
    "block_height": 50.0,
    "port_dia": 10.0,
    "counterbore_dia": 18.0,
    "counterbore_depth": 3.0,
    "port_spacing_x": 30.0,
    "port_spacing_y": 24.0,
    "mount_hole_dia": 6.5,
    "mount_hole_inset": 8.0
}
import math
from build123d import *

L = PARAMS["block_length"]
W = PARAMS["block_width"]
H = PARAMS["block_height"]
PD = PARAMS["port_dia"]
CBD = PARAMS["counterbore_dia"]
CBD_H = PARAMS["counterbore_depth"]
SX = PARAMS["port_spacing_x"]
SY = PARAMS["port_spacing_y"]
MHD = PARAMS["mount_hole_dia"]
INS = PARAMS["mount_hole_inset"]

with BuildPart() as part:
    # 1. Main rectangular solid block
    with Locations((0, 0, H / 2.0)):
        Box(L, W, H)
    # 2. 4 Hydraulic ports (P, T, A, B) on top surface with O-ring counterbores
    for px in [-SX / 2.0, SX / 2.0]:
        for py in [-SY / 2.0, SY / 2.0]:
            # Main port blind bore
            with Locations((px, py, H - 20.0)):
                Cylinder(radius=PD / 2.0, height=45.0, mode=Mode.SUBTRACT)
            # O-ring cavity counterbore
            with Locations((px, py, H - CBD_H / 2.0)):
                Cylinder(radius=CBD / 2.0, height=CBD_H + 0.1, mode=Mode.SUBTRACT)
    # 3. 4 Corner mounting through holes
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            mx = sx * (L / 2.0 - INS)
            my = sy * (W / 2.0 - INS)
            with Locations((mx, my, H / 2.0)):
                Cylinder(radius=MHD / 2.0, height=H * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'engine_rocker_arm',
        "description": 'Engine valvetrain rocker arm with central fulcrum pivot boss bore, pushrod socket end, and roller valve stem actuating pad',
        "tags": ['rocker arm', 'valvetrain', 'engine', 'fulcrum', 'pushrod', 'valve', 'clevis', 'automotive mechanical'],
        "code": """\
PARAMS = {
    "center_boss_dia": 28.0,
    "center_bore_dia": 14.0,
    "boss_width": 24.0,
    "arm_length_left": 40.0,
    "arm_length_right": 35.0,
    "arm_thickness": 12.0,
    "arm_height": 18.0,
    "pushrod_cup_dia": 8.0,
    "pushrod_cup_depth": 6.0,
    "valve_pad_width": 16.0
}
import math
from build123d import *

CBD = PARAMS["center_boss_dia"]
CRD = PARAMS["center_bore_dia"]
BW = PARAMS["boss_width"]
L_LEFT = PARAMS["arm_length_left"]
L_RIGHT = PARAMS["arm_length_right"]
AT = PARAMS["arm_thickness"]
AH = PARAMS["arm_height"]
PCD = PARAMS["pushrod_cup_dia"]
PCH = PARAMS["pushrod_cup_depth"]
VPW = PARAMS["valve_pad_width"]

with BuildPart() as part:
    # 1. Central cylindrical fulcrum pivot boss (oriented along Y)
    with Locations(Location((0, 0, 0), (90, 0, 0))):
        Cylinder(radius=CBD / 2.0, height=BW)
        Cylinder(radius=CRD / 2.0, height=BW * 2.0, mode=Mode.SUBTRACT)
    # 2. Left pushrod arm
    with Locations((-L_LEFT / 2.0, 0, 0)):
        Box(L_LEFT, AT, AH)
    # Pushrod spherical cup pocket on left tip
    with Locations((-L_LEFT + 4.0, 0, AH / 2.0 - PCH / 2.0)):
        Cylinder(radius=PCD / 2.0, height=PCH + 0.1, mode=Mode.SUBTRACT)
    # 3. Right valve actuator arm
    with Locations((L_RIGHT / 2.0, 0, 0)):
        Box(L_RIGHT, AT, AH)
    # Rounded valve pad contact cylinder on right tip
    with Locations((L_RIGHT, 0, 0)):
        with Locations(Location((0, 0, 0), (90, 0, 0))):
            Cylinder(radius=AH / 2.0, height=VPW)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'rocket_conical_nozzle',
        "description": 'Convergent-divergent supersonic de Laval conical rocket nozzle with combustion chamber injector flange, throat, and conical expansion bell',
        "tags": ['rocket nozzle', 'de laval', 'convergent divergent', 'supersonic nozzle', 'propulsion', 'thrust chamber', 'aerospace'],
        "code": """\
PARAMS = {
    "chamber_radius": 32.0,
    "throat_radius": 12.0,
    "exit_radius": 45.0,
    "convergent_length": 25.0,
    "divergent_length": 65.0,
    "wall_thickness": 4.0,
    "flange_radius": 44.0,
    "flange_thickness": 8.0,
    "flange_hole_dia": 5.0,
    "flange_hole_pcd": 74.0
}
import math
from build123d import *

RC = PARAMS["chamber_radius"]
RT = PARAMS["throat_radius"]
RE = PARAMS["exit_radius"]
LC = PARAMS["convergent_length"]
LD = PARAMS["divergent_length"]
WT = PARAMS["wall_thickness"]
FR = PARAMS["flange_radius"]
FT = PARAMS["flange_thickness"]
FHD = PARAMS["flange_hole_dia"]
PCD = PARAMS["flange_hole_pcd"]

with BuildPart() as part:
    # 1. Revolved nozzle shell
    with BuildSketch(Plane.XZ) as sk:
        # Define inner nozzle contour
        # Origin Z=0 at throat
        inner_pts = [
            (RC, -LC),
            (RT, 0),
            (RE, LD)
        ]
        outer_pts = [
            (RE + WT, LD),
            (RT + WT, 0),
            (RC + WT, -LC)
        ]
        Polygon(inner_pts + outer_pts)
    revolve(axis=Axis.Z)
    # 2. Chamber inlet mounting flange
    with Locations((0, 0, -LC + FT / 2.0)):
        Cylinder(radius=FR, height=FT)
        Cylinder(radius=RC, height=FT * 2.0, mode=Mode.SUBTRACT)
        with PolarLocations(radius=PCD / 2.0, count=6):
            Cylinder(radius=FHD / 2.0, height=FT * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'pillow_block_bearing_housing',
        "description": 'Split journal pillow block bearing housing pedestal base with semicircular bearing seat, twin slotted foot mounting holes, and cap bolt bosses',
        "tags": ['pillow block', 'bearing housing', 'pedestal', 'split bearing', 'journal bearing', 'bearing mount', 'machine base'],
        "code": """\
PARAMS = {
    "base_length": 140.0,
    "base_width": 45.0,
    "base_thickness": 14.0,
    "bearing_seat_dia": 50.0,
    "bearing_seat_width": 35.0,
    "center_height": 40.0,
    "foot_slot_len": 20.0,
    "foot_slot_width": 12.0,
    "foot_slot_spacing": 100.0,
    "cap_bolt_pcd": 74.0,
    "cap_bolt_dia": 8.5
}
import math
from build123d import *

BL = PARAMS["base_length"]
BW = PARAMS["base_width"]
BT = PARAMS["base_thickness"]
BSD = PARAMS["bearing_seat_dia"]
BSW = PARAMS["bearing_seat_width"]
CH = PARAMS["center_height"]
FSL = PARAMS["foot_slot_len"]
FSW = PARAMS["foot_slot_width"]
FSS = PARAMS["foot_slot_spacing"]
CPCD = PARAMS["cap_bolt_pcd"]
CBD = PARAMS["cap_bolt_dia"]

with BuildPart() as part:
    # 1. Rectangular foot mounting base plate
    with Locations((0, 0, BT / 2.0)):
        Box(BL, BW, BT)
    # 2. Central upright bearing support saddle
    with Locations((0, 0, CH / 2.0)):
        Box(BSW * 1.5, BSW, CH)
    # 3. Semicircular bearing seat bore (horizontal along Y)
    with Locations(Location((0, 0, CH), (90, 0, 0))):
        Cylinder(radius=BSD / 2.0, height=BW * 2.0, mode=Mode.SUBTRACT)
    # 4. Twin slotted mounting holes on base wings
    for sx in [-1, 1]:
        slot_x = sx * (FSS / 2.0)
        with Locations((slot_x, 0, BT / 2.0)):
            Box(FSL, FSW, BT * 2.0, mode=Mode.SUBTRACT)
    # 5. Vertical cap retaining screw holes
    for sx in [-1, 1]:
        cx = sx * (CPCD / 2.0)
        with Locations((cx, 0, CH / 2.0)):
            Cylinder(radius=CBD / 2.0, height=CH * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'structural_c_channel_beam',
        "description": 'Standard structural steel C-channel profile section with upper and lower flanges, central web plate, and web mounting slots',
        "tags": ['c-channel', 'structural beam', 'channel iron', 'beam profile', 'structural steel', 'chassis rail', 'framing'],
        "code": """\
PARAMS = {
    "channel_height": 80.0,
    "flange_width": 40.0,
    "web_thickness": 5.0,
    "flange_thickness": 6.0,
    "length": 150.0,
    "slot_length": 25.0,
    "slot_width": 9.0,
    "slot_pitch": 45.0
}
import math
from build123d import *

H = PARAMS["channel_height"]
W = PARAMS["flange_width"]
TW = PARAMS["web_thickness"]
TF = PARAMS["flange_thickness"]
L = PARAMS["length"]
SL = PARAMS["slot_length"]
SW = PARAMS["slot_width"]
SP = PARAMS["slot_pitch"]

with BuildPart() as part:
    # 1. Extrude C-profile sketch along Z
    with BuildSketch(Plane.XY) as sk:
        with Locations((0, 0)):
            pts = [
                (0, 0),
                (W, 0),
                (W, TF),
                (TW, TF),
                (TW, H - TF),
                (W, H - TF),
                (W, H),
                (0, H)
            ]
            Polygon(pts)
    extrude(amount=L)
    # 2. Mounting slots punched through central web
    num_slots = int(L // SP)
    start_z = (L - (num_slots - 1) * SP) / 2.0
    for i in range(num_slots):
        sz = start_z + i * SP
        with Locations((TW / 2.0, H / 2.0, sz)):
            Box(TW * 2.0, SW, SL, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'worm_gear_wheel_blank',
        "description": 'Machined bronze worm wheel gear blank with concave throated outer rim, central drive hub, shaft bore, and keyway',
        "tags": ['worm gear', 'worm wheel', 'gear blank', 'throated rim', 'worm drive', 'speed reducer', 'bronze gear'],
        "code": """\
PARAMS = {
    "pitch_radius": 50.0,
    "throat_radius": 46.0,
    "rim_width": 20.0,
    "worm_mating_radius": 18.0,
    "hub_dia": 36.0,
    "hub_width": 28.0,
    "bore_dia": 18.0,
    "key_width": 6.0,
    "key_depth": 3.0
}
import math
from build123d import *

PR = PARAMS["pitch_radius"]
TR = PARAMS["throat_radius"]
RW = PARAMS["rim_width"]
WR = PARAMS["worm_mating_radius"]
HD = PARAMS["hub_dia"]
HW = PARAMS["hub_width"]
BD = PARAMS["bore_dia"]
KW = PARAMS["key_width"]
KD = PARAMS["key_depth"]

HR = HD / 2.0
BR = BD / 2.0

with BuildPart() as part:
    # 1. Main outer blank disc
    with Locations((0, 0, 0)):
        Cylinder(radius=PR + 4.0, height=RW)
    # 2. Central hub
    with Locations((0, 0, 0)):
        Cylinder(radius=HR, height=HW)
    # 3. Concave throat grooving along outer circumference
    # The throat radius matches the mating worm pitch radius
    throat_center_r = TR + WR
    with BuildSketch(Plane.XZ) as sk:
        with Locations((throat_center_r, 0)):
            Circle(WR)
    revolve(axis=Axis.Z, mode=Mode.SUBTRACT)
    # 4. Center bore
    with Locations((0, 0, 0)):
        Cylinder(radius=BR, height=HW * 2.0, mode=Mode.SUBTRACT)
    # 5. Keyway
    with Locations((0, BR + KD / 2.0, 0)):
        Box(KW, KD + 1.0, HW * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'vented_louvered_panel',
        "description": 'Rectangular equipment ventilation cover panel with angled cooling louver slats and perimeter mounting holes',
        "tags": ['louver', 'vented panel', 'ventilation', 'grille', 'cooling slats', 'sheet metal cover', 'cabinet panel'],
        "code": """\
PARAMS = {
    "panel_length": 120.0,
    "panel_width": 80.0,
    "panel_thickness": 3.0,
    "louver_width": 45.0,
    "louver_gap": 4.0,
    "louver_angle": 30.0,
    "num_louvers": 6,
    "mount_hole_dia": 4.5,
    "mount_hole_inset": 6.0
}
import math
from build123d import *

PL = PARAMS["panel_length"]
PW = PARAMS["panel_width"]
PT = PARAMS["panel_thickness"]
LW = PARAMS["louver_width"]
LG = PARAMS["louver_gap"]
LA = PARAMS["louver_angle"]
NL = int(PARAMS["num_louvers"])
MHD = PARAMS["mount_hole_dia"]
INS = PARAMS["mount_hole_inset"]

with BuildPart() as part:
    # 1. Base solid rectangular sheet
    with Locations((0, 0, PT / 2.0)):
        Box(PL, PW, PT)
    # 2. Angled louver pass-through slots
    pitch = (PL - 2.0 * INS - 20.0) / max(1, NL - 1)
    start_x = -((NL - 1) * pitch) / 2.0
    for i in range(NL):
        lx = start_x + i * pitch
        with Locations(Location((lx, 0, PT / 2.0), (0, LA, 0))):
            Box(LG, LW, PT * 3.0, mode=Mode.SUBTRACT)
    # 3. Perimeter mounting screw holes
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            hx = sx * (PL / 2.0 - INS)
            hy = sy * (PW / 2.0 - INS)
            with Locations((hx, hy, PT / 2.0)):
                Cylinder(radius=MHD / 2.0, height=PT * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'camshaft_eccentric_lobe',
        "description": 'Automotive internal combustion camshaft segment with circular base journal shaft and asymmetric teardrop cam lobe',
        "tags": ['camshaft', 'cam lobe', 'eccentric cam', 'valvetrain', 'engine cam', 'follower', 'timing shaft'],
        "code": """\
PARAMS = {
    "shaft_dia": 24.0,
    "shaft_length": 80.0,
    "base_circle_dia": 32.0,
    "lobe_lift": 9.0,
    "nose_dia": 14.0,
    "lobe_width": 16.0
}
import math
from build123d import *

SD = PARAMS["shaft_dia"]
SL = PARAMS["shaft_length"]
BCD = PARAMS["base_circle_dia"]
LIFT = PARAMS["lobe_lift"]
ND = PARAMS["nose_dia"]
LW = PARAMS["lobe_width"]

R_BASE = BCD / 2.0
R_NOSE = ND / 2.0
D_CENTERS = R_BASE + LIFT - R_NOSE

with BuildPart() as part:
    # 1. Main circular drive shaft
    with Locations((0, 0, SL / 2.0)):
        Cylinder(radius=SD / 2.0, height=SL)
    # 2. Cam lobe profile extruded at center
    with BuildSketch(Plane.XY.offset((SL - LW) / 2.0)) as sk:
        # Base circle
        Circle(R_BASE)
        # Nose circle offset along X
        with Locations((D_CENTERS, 0)):
            Circle(R_NOSE)
        # Tangent hull connecting base circle and nose
        angle = math.degrees(math.asin(max(-1.0, min(1.0, (R_BASE - R_NOSE) / D_CENTERS))))
        rad = math.radians(angle)
        p1 = (R_BASE * math.sin(rad), R_BASE * math.cos(rad))
        p2 = (D_CENTERS + R_NOSE * math.sin(rad), R_NOSE * math.cos(rad))
        p3 = (D_CENTERS + R_NOSE * math.sin(rad), -R_NOSE * math.cos(rad))
        p4 = (R_BASE * math.sin(rad), -R_BASE * math.cos(rad))
        Polygon([p1, p2, p3, p4])
    extrude(amount=LW)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'exhaust_manifold_flange_3port',
        "description": 'Three-port automotive inline engine exhaust manifold interface flange plate with circular exhaust ports and cylinder head mounting stud holes',
        "tags": ['exhaust flange', 'manifold flange', 'engine exhaust', 'cylinder head', 'exhaust header', 'gasket plate', 'automotive'],
        "code": """\
PARAMS = {
    "port_pitch": 75.0,
    "port_dia": 36.0,
    "flange_width": 65.0,
    "flange_thickness": 10.0,
    "stud_hole_dia": 9.0,
    "stud_offset_y": 24.0,
    "end_margin": 25.0
}
import math
from build123d import *

PITCH = PARAMS["port_pitch"]
PD = PARAMS["port_dia"]
FW = PARAMS["flange_width"]
FT = PARAMS["flange_thickness"]
SHD = PARAMS["stud_hole_dia"]
SOY = PARAMS["stud_offset_y"]
EM = PARAMS["end_margin"]

total_len = 2.0 * PITCH + 2.0 * EM

with BuildPart() as part:
    # 1. Main flat flange plate
    with Locations((0, 0, FT / 2.0)):
        Box(total_len, FW, FT)
    # 2. 3 Circular exhaust gas ports
    for i in [-1, 0, 1]:
        px = i * PITCH
        with Locations((px, 0, FT / 2.0)):
            Cylinder(radius=PD / 2.0, height=FT * 2.0, mode=Mode.SUBTRACT)
    # 3. Stud mounting holes (pair above and below each port)
    for i in [-1, 0, 1]:
        px = i * PITCH
        for sy in [-1, 1]:
            with Locations((px, sy * SOY, FT / 2.0)):
                Cylinder(radius=SHD / 2.0, height=FT * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'robotics_wrist_clevis',
        "description": 'Dual-fork 2-axis robotic arm wrist clevis bracket with base actuator mounting plate, twin fork arms, and cross pivot pin bores',
        "tags": ['robotics clevis', 'wrist bracket', 'clevis fork', 'robot arm', 'actuator mount', 'servo clevis', 'end effector'],
        "code": """\
PARAMS = {
    "base_dia": 50.0,
    "base_thickness": 8.0,
    "clevis_height": 45.0,
    "fork_gap": 26.0,
    "fork_thickness": 8.0,
    "pin_hole_dia": 10.0,
    "pin_center_z": 38.0,
    "base_mount_pcd": 38.0,
    "base_mount_dia": 4.5
}
import math
from build123d import *

BD = PARAMS["base_dia"]
BT = PARAMS["base_thickness"]
CH = PARAMS["clevis_height"]
FG = PARAMS["fork_gap"]
FT = PARAMS["fork_thickness"]
PHD = PARAMS["pin_hole_dia"]
PCZ = PARAMS["pin_center_z"]
PCD = PARAMS["base_mount_pcd"]
BMD = PARAMS["base_mount_dia"]

fork_outer_w = FG + 2.0 * FT

with BuildPart() as part:
    # 1. Circular base mounting flange
    with Locations((0, 0, BT / 2.0)):
        Cylinder(radius=BD / 2.0, height=BT)
        with PolarLocations(radius=PCD / 2.0, count=4):
            Cylinder(radius=BMD / 2.0, height=BT * 2.0, mode=Mode.SUBTRACT)
    # 2. Twin fork arms extending up from base
    for sy in [-1, 1]:
        fy = sy * (FG / 2.0 + FT / 2.0)
        with Locations((0, fy, BT + CH / 2.0)):
            Box(BD * 0.7, FT, CH)
    # 3. Horizontal pivot pin bore passing through both forks
    with Locations(Location((0, 0, BT + PCZ), (90, 0, 0))):
        Cylinder(radius=PHD / 2.0, height=fork_outer_w * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'folding_propeller_hub',
        "description": 'Aerospace folding propeller central rotor hub with two opposed blade hinge clevis forks, center motor drive bore, and blade stop pins',
        "tags": ['propeller hub', 'folding prop', 'rotor hub', 'drone propeller', 'uav', 'aeronautics', 'clevis hinge', 'quadcopter'],
        "code": """\
PARAMS = {
    "hub_length": 65.0,
    "hub_width": 20.0,
    "hub_thickness": 14.0,
    "clevis_slot_width": 6.5,
    "clevis_depth": 18.0,
    "center_bore_dia": 8.0,
    "pin_hole_dia": 3.2,
    "pin_offset_x": 22.0
}
import math
from build123d import *

HL = PARAMS["hub_length"]
HW = PARAMS["hub_width"]
HT = PARAMS["hub_thickness"]
CSW = PARAMS["clevis_slot_width"]
CD = PARAMS["clevis_depth"]
CBD = PARAMS["center_bore_dia"]
PHD = PARAMS["pin_hole_dia"]
POX = PARAMS["pin_offset_x"]

with BuildPart() as part:
    # 1. Main rounded hub bar
    with BuildSketch(Plane.XY):
        RectangleRounded(HL, HW, HW * 0.45)
    extrude(amount=HT)
    # 2. Central motor shaft bore
    with Locations((0, 0, HT / 2.0)):
        Cylinder(radius=CBD / 2.0, height=HT * 2.0, mode=Mode.SUBTRACT)
    # 3. Left and right blade hinge clevis slots
    for sx in [-1, 1]:
        slot_center_x = sx * (HL / 2.0 - CD / 2.0)
        with Locations((slot_center_x, 0, HT / 2.0)):
            Box(CD + 1.0, CSW, HT * 2.0, mode=Mode.SUBTRACT)
    # 4. Vertical blade hinge pin holes
    for sx in [-1, 1]:
        px = sx * POX
        with Locations((px, 0, HT / 2.0)):
            Cylinder(radius=PHD / 2.0, height=HT * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'leadscrew_nut_flange_housing',
        "description": 'CNC 3D printer anti-backlash T8 leadscrew brass flanged nut mounting block with clamping collar and linear carriage mounting pattern',
        "tags": ['leadscrew nut', 't8 leadscrew', 'nut housing', 'cnc', '3d printer', 'linear motion', 'z-axis', 'flanged nut'],
        "code": """\
PARAMS = {
    "block_length": 34.0,
    "block_width": 30.0,
    "block_height": 28.0,
    "nut_body_dia": 10.5,
    "nut_flange_dia": 22.5,
    "flange_recess_depth": 4.0,
    "screw_pcd": 16.0,
    "mount_screw_dia": 3.5,
    "carriage_hole_dia": 4.5,
    "carriage_hole_pitch": 24.0
}
import math
from build123d import *

BL = PARAMS["block_length"]
BW = PARAMS["block_width"]
BH = PARAMS["block_height"]
NBD = PARAMS["nut_body_dia"]
NFD = PARAMS["nut_flange_dia"]
FRD = PARAMS["flange_recess_depth"]
SPCD = PARAMS["screw_pcd"]
MSD = PARAMS["mount_screw_dia"]
CHD = PARAMS["carriage_hole_dia"]
CHP = PARAMS["carriage_hole_pitch"]

with BuildPart() as part:
    # 1. Main aluminum mounting block
    with Locations((0, 0, BH / 2.0)):
        Box(BL, BW, BH)
    # 2. Central leadscrew nut barrel through-bore
    with Locations((0, 0, BH / 2.0)):
        Cylinder(radius=NBD / 2.0, height=BH * 2.0, mode=Mode.SUBTRACT)
    # 3. Flange recess counterbore on top surface
    with Locations((0, 0, BH - FRD / 2.0)):
        Cylinder(radius=NFD / 2.0, height=FRD + 0.1, mode=Mode.SUBTRACT)
    # 4. 4 Nut retention screw holes on PCD
    with Locations((0, 0, BH / 2.0)):
        with PolarLocations(radius=SPCD / 2.0, count=4):
            Cylinder(radius=MSD / 2.0, height=BH * 2.0, mode=Mode.SUBTRACT)
    # 5. Horizontal carriage attachment holes
    for sy in [-1, 1]:
        cy = sy * (CHP / 2.0)
        with Locations(Location((0, cy, BH / 2.0), (0, 90, 0))):
            Cylinder(radius=CHD / 2.0, height=BL * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'pneumatic_cylinder_end_cap',
        "description": 'ISO square pneumatic cylinder front tie-rod end cap with central piston rod bushing bore, wiper recess, and 4 corner tie-rod holes',
        "tags": ['pneumatic cylinder', 'end cap', 'tie rod', 'air cylinder', 'actuator cap', 'piston rod bushing', 'fluid power'],
        "code": """\
PARAMS = {
    "cap_size": 60.0,
    "cap_thickness": 20.0,
    "rod_bushing_dia": 18.0,
    "wiper_cavity_dia": 26.0,
    "wiper_cavity_depth": 6.0,
    "tie_rod_pitch": 45.0,
    "tie_rod_hole_dia": 6.5,
    "port_thread_dia": 11.5
}
import math
from build123d import *

CS = PARAMS["cap_size"]
CT = PARAMS["cap_thickness"]
RBD = PARAMS["rod_bushing_dia"]
WCD = PARAMS["wiper_cavity_dia"]
WCH = PARAMS["wiper_cavity_depth"]
TRP = PARAMS["tie_rod_pitch"]
TRD = PARAMS["tie_rod_hole_dia"]
PTD = PARAMS["port_thread_dia"]

with BuildPart() as part:
    # 1. Main square end cap body
    with Locations((0, 0, CT / 2.0)):
        Box(CS, CS, CT)
    # 2. Central rod bushing through bore
    with Locations((0, 0, CT / 2.0)):
        Cylinder(radius=RBD / 2.0, height=CT * 2.0, mode=Mode.SUBTRACT)
    # 3. Front rod seal/wiper counterbore
    with Locations((0, 0, CT - WCH / 2.0)):
        Cylinder(radius=WCD / 2.0, height=WCH + 0.1, mode=Mode.SUBTRACT)
    # 4. 4 Corner tie-rod mounting holes
    for sx in [-1, 1]:
        for sy in [-1, 1]:
            tx = sx * (TRP / 2.0)
            ty = sy * (TRP / 2.0)
            with Locations((tx, ty, CT / 2.0)):
                Cylinder(radius=TRD / 2.0, height=CT * 2.0, mode=Mode.SUBTRACT)
    # 5. Pneumatic air inlet port on top edge
    with Locations(Location((0, CS / 2.0, CT / 2.0), (90, 0, 0))):
        Cylinder(radius=PTD / 2.0, height=CS / 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'planetary_gearbox_carrier',
        "description": 'Precision epicyclic planetary gearbox carrier plate with central sun shaft clearance bore, 3 equidistant planet gear pin support holes, and perimeter weight reduction pockets',
        "tags": ['planetary gearbox', 'carrier plate', 'planet carrier', 'gear train', 'epicyclic', 'sun gear', 'transmission'],
        "code": """\
PARAMS = {
    "carrier_dia": 85.0,
    "carrier_thickness": 10.0,
    "sun_bore_dia": 16.0,
    "planet_pcd": 54.0,
    "planet_pin_dia": 10.0,
    "pocket_depth": 5.0,
    "num_planets": 3
}
import math
from build123d import *

CD = PARAMS["carrier_dia"]
CT = PARAMS["carrier_thickness"]
SBD = PARAMS["sun_bore_dia"]
PPCD = PARAMS["planet_pcd"]
PPD = PARAMS["planet_pin_dia"]
PD_POCKET = PARAMS["pocket_depth"]
NP = int(PARAMS["num_planets"])

with BuildPart() as part:
    # 1. Main circular carrier disc
    with Locations((0, 0, CT / 2.0)):
        Cylinder(radius=CD / 2.0, height=CT)
    # 2. Central sun gear shaft clearance bore
    with Locations((0, 0, CT / 2.0)):
        Cylinder(radius=SBD / 2.0, height=CT * 2.0, mode=Mode.SUBTRACT)
    # 3. 3 Equidistant planet gear pin press-fit bores
    with Locations((0, 0, CT / 2.0)):
        with PolarLocations(radius=PPCD / 2.0, count=NP):
            Cylinder(radius=PPD / 2.0, height=CT * 2.0, mode=Mode.SUBTRACT)
    # 4. 3 Lightening scallops between planet pins
    pocket_angle_offset = 180.0 / NP
    with Locations((0, 0, CT - PD_POCKET / 2.0)):
        with PolarLocations(radius=PPCD / 2.0, count=NP, start_angle=pocket_angle_offset):
            Cylinder(radius=12.0, height=PD_POCKET + 0.1, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'swashplate_piston_pump_cradle',
        "description": 'Variable displacement axial piston hydraulic pump swashplate cradle with precision angled thrust slipper bearing face and side trunnion pivot journals',
        "tags": ['swashplate', 'axial piston pump', 'hydraulic pump', 'cradle', 'trunnion', 'thrust face', 'fluid power'],
        "code": """\
PARAMS = {
    "plate_length": 80.0,
    "plate_width": 65.0,
    "plate_thickness": 22.0,
    "center_clearance_bore": 30.0,
    "trunnion_dia": 18.0,
    "trunnion_length": 15.0,
    "tilt_angle_deg": 15.0
}
import math
from build123d import *

PL = PARAMS["plate_length"]
PW = PARAMS["plate_width"]
PT = PARAMS["plate_thickness"]
CCB = PARAMS["center_clearance_bore"]
TD = PARAMS["trunnion_dia"]
TL = PARAMS["trunnion_length"]
TILT = PARAMS["tilt_angle_deg"]

with BuildPart() as part:
    # 1. Main swashplate body block
    with Locations((0, 0, PT / 2.0)):
        Box(PL, PW, PT)
    # 2. Side cylindrical trunnion pivot pins (extending along Y)
    for sy in [-1, 1]:
        ty = sy * (PW / 2.0 + TL / 2.0)
        with Locations(Location((0, ty, PT / 2.0), (90, 0, 0))):
            Cylinder(radius=TD / 2.0, height=TL)
    # 3. Central drive shaft through-bore
    with Locations((0, 0, PT / 2.0)):
        Cylinder(radius=CCB / 2.0, height=PT * 2.0, mode=Mode.SUBTRACT)
    # 4. Inclined slipper face angled cut across top surface
    with Locations(Location((0, 0, PT), (0, TILT, 0))):
        Box(PL * 1.5, PW * 1.5, PT, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'bearing_km_locknut_blank',
        "description": 'Standard metric slotted spanner KM locknut blank with central threaded bore clearance, chamfered rim, and 4 perimeter hook spanner slots',
        "tags": ['km locknut', 'locknut', 'bearing nut', 'spanner slot', 'shaft retention', 'bearing retaining', 'threaded nut'],
        "code": """\
PARAMS = {
    "outer_dia": 42.0,
    "nut_thickness": 9.0,
    "bore_dia": 24.0,
    "slot_width": 5.0,
    "slot_depth": 3.0,
    "num_slots": 4
}
import math
from build123d import *

OD = PARAMS["outer_dia"]
T = PARAMS["nut_thickness"]
BD = PARAMS["bore_dia"]
SW = PARAMS["slot_width"]
SD = PARAMS["slot_depth"]
NS = int(PARAMS["num_slots"])

OR = OD / 2.0

with BuildPart() as part:
    # 1. Main circular nut disc
    with Locations((0, 0, T / 2.0)):
        Cylinder(radius=OR, height=T)
    # 2. Central shaft bore
    with Locations((0, 0, T / 2.0)):
        Cylinder(radius=BD / 2.0, height=T * 2.0, mode=Mode.SUBTRACT)
    # 3. Perimeter hook spanner slots
    for i in range(NS):
        angle = i * (360.0 / NS)
        rad = math.radians(angle)
        sx = (OR - SD / 2.0) * math.cos(rad)
        sy = (OR - SD / 2.0) * math.sin(rad)
        with Locations(Location((sx, sy, T / 2.0), (0, 0, angle))):
            Box(SD + 1.0, SW, T * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'hexagonal_threaded_standoff',
        "description": 'Machined brass hexagonal PCB standoff spacer with regular hexagonal outer flats and central clearance through-bore',
        "tags": ['hex standoff', 'spacer', 'hexagonal standoff', 'pcb hardware', 'fastener', 'chassis spacer', 'threaded post'],
        "code": """\
PARAMS = {
    "hex_width_flats": 10.0,
    "standoff_length": 25.0,
    "bore_dia": 4.2
}
import math
from build123d import *

W_FLATS = PARAMS["hex_width_flats"]
L = PARAMS["standoff_length"]
BD = PARAMS["bore_dia"]

# Radius to vertices for a regular hexagon
r_vertices = W_FLATS / math.sqrt(3)

with BuildPart() as part:
    # 1. Hexagonal prismatic body
    with BuildSketch(Plane.XY):
        RegularPolygon(radius=r_vertices, side_count=6)
    extrude(amount=L)
    # 2. Central through-bore
    with Locations((0, 0, L / 2.0)):
        Cylinder(radius=BD / 2.0, height=L * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'centrifugal_pump_volute_section',
        "description": 'Centrifugal fluid pump volute spiral casing section with axial suction inlet eye, expanding scroll gallery, and tangential discharge nozzle flange',
        "tags": ['pump volute', 'centrifugal pump', 'pump casing', 'discharge nozzle', 'impeller housing', 'fluid power', 'turbomachinery'],
        "code": """\
PARAMS = {
    "casing_outer_radius": 60.0,
    "casing_axial_width": 30.0,
    "inlet_eye_radius": 22.0,
    "discharge_pipe_dia": 24.0,
    "discharge_pipe_length": 45.0,
    "discharge_flange_dia": 48.0,
    "discharge_flange_thick": 6.0,
    "wall_thickness": 4.0
}
import math
from build123d import *

COR = PARAMS["casing_outer_radius"]
CAW = PARAMS["casing_axial_width"]
IER = PARAMS["inlet_eye_radius"]
DPD = PARAMS["discharge_pipe_dia"]
DPL = PARAMS["discharge_pipe_length"]
DFD = PARAMS["discharge_flange_dia"]
DFT = PARAMS["discharge_flange_thick"]
WT = PARAMS["wall_thickness"]

with BuildPart() as part:
    # 1. Main cylindrical volute scroll body
    with Locations((0, 0, CAW / 2.0)):
        Cylinder(radius=COR, height=CAW)
    # 2. Tangential discharge nozzle extension along X
    nozzle_center_y = COR - DPD / 2.0
    with Locations((COR + DPL / 2.0 - 5.0, nozzle_center_y, CAW / 2.0)):
        with Locations(Location((0, 0, 0), (0, 90, 0))):
            Cylinder(radius=DPD / 2.0, height=DPL)
    # 3. Discharge flange at end of nozzle
    with Locations((COR + DPL - 5.0, nozzle_center_y, CAW / 2.0)):
        with Locations(Location((0, 0, 0), (0, 90, 0))):
            Cylinder(radius=DFD / 2.0, height=DFT)
    # 4. Central axial suction inlet bore
    with Locations((0, 0, CAW / 2.0)):
        Cylinder(radius=IER, height=CAW * 2.0, mode=Mode.SUBTRACT)
    # 5. Hollow discharge nozzle through-bore
    with Locations((COR + DPL / 2.0, nozzle_center_y, CAW / 2.0)):
        with Locations(Location((0, 0, 0), (0, 90, 0))):
            Cylinder(radius=DPD / 2.0 - WT, height=DPL * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'timing_pulley_gt2_flanged',
        "description": 'Precision GT2 profile timing belt pulley with dual side retaining flange guides, central hub, shaft bore, and setscrew hole',
        "tags": ['timing pulley', 'gt2', 'timing belt', '3d printer pulley', 'stepper motor pulley', 'synchronous drive', 'toothed pulley'],
        "code": """\
PARAMS = {
    "pitch_radius": 18.0,
    "belt_width": 10.0,
    "flange_radius": 22.0,
    "flange_thickness": 1.5,
    "hub_radius": 12.0,
    "hub_height": 8.0,
    "bore_radius": 4.0,
    "setscrew_dia": 3.0
}
import math
from build123d import *

PR = PARAMS["pitch_radius"]
BW = PARAMS["belt_width"]
FR = PARAMS["flange_radius"]
FT = PARAMS["flange_thickness"]
HR = PARAMS["hub_radius"]
HH = PARAMS["hub_height"]
BR = PARAMS["bore_radius"]
SD = PARAMS["setscrew_dia"]

with BuildPart() as part:
    # 1. Timing tooth cylinder body
    with Locations((0, 0, BW / 2.0)):
        Cylinder(radius=PR, height=BW)
    # 2. Bottom flange guide
    with Locations((0, 0, -FT / 2.0)):
        Cylinder(radius=FR, height=FT)
    # 3. Top flange guide
    with Locations((0, 0, BW + FT / 2.0)):
        Cylinder(radius=FR, height=FT)
    # 4. Top hub
    with Locations((0, 0, BW + FT + HH / 2.0)):
        Cylinder(radius=HR, height=HH)
    # 5. Center bore through entire pulley
    total_h = BW + 2.0 * FT + HH + 5.0
    with Locations((0, 0, total_h / 2.0 - FT)):
        Cylinder(radius=BR, height=total_h * 2.0, mode=Mode.SUBTRACT)
    # 6. Radial M3 setscrew hole through hub
    with Locations(Location((0, 0, BW + FT + HH / 2.0), (0, 90, 0))):
        Cylinder(radius=SD / 2.0, height=HR * 2.0, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
    {
        "id": 'thrust_bearing_grooved_race',
        "description": 'Precision ball/roller thrust bearing grooved washer race plate with circular ball track guide groove and locating shaft bore',
        "tags": ['thrust bearing', 'bearing race', 'ball track', 'thrust washer', 'bearing ring', 'axial bearing', 'rotary table'],
        "code": """\
PARAMS = {
    "outer_radius": 40.0,
    "inner_radius": 20.0,
    "plate_thickness": 8.0,
    "track_radius": 30.0,
    "ball_groove_radius": 4.0
}
import math
from build123d import *

OR = PARAMS["outer_radius"]
IR = PARAMS["inner_radius"]
T = PARAMS["plate_thickness"]
TR = PARAMS["track_radius"]
BGR = PARAMS["ball_groove_radius"]

with BuildPart() as part:
    # 1. Annular flat washer plate
    with Locations((0, 0, T / 2.0)):
        Cylinder(radius=OR, height=T)
        Cylinder(radius=IR, height=T * 2.0, mode=Mode.SUBTRACT)
    # 2. Circular circular ball groove on top surface
    with BuildSketch(Plane.XZ) as sk:
        with Locations((TR, T)):
            Circle(BGR)
    revolve(axis=Axis.Z, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
"""
    },
]
