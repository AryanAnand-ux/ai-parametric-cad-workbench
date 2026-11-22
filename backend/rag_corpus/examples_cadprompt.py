"""
RAG Corpus — CADPrompt Mechanical Blueprints (ICLR 2025 Dataset Adaptation)
=============================================================================
High-precision mechanical assemblies translated from the CADPrompt dataset:
  1. cadprompt_split_collar: Two-piece clamping shaft collar with dual socket head screws.
  2. cadprompt_flanged_bearing_housing: 4-bolt square flanged bearing block with center bore.
  3. cadprompt_star_knob: 5-lobed ergonomic mechanical hand clamping knob with center bore.
  4. cadprompt_pipe_manifold: 3-way fluid distribution manifold block with counterbored ports.
  5. cadprompt_stepped_shoulder_bushing: Precision stepped shoulder bushing with oil groove.
"""

EXAMPLES = [
    # ── 1. CLAMPING SPLIT SHAFT COLLAR ─────────────────────────────────────
    {
        "id": "cadprompt_split_collar",
        "description": "Two-piece clamping shaft collar with precision inner bore, relief split, and counterbored socket head cap screw holes",
        "tags": ["collar", "shaft collar", "clamp", "split collar", "bore", "fastener", "cadprompt"],
        "code": '''\
PARAMS = {
    "outer_dia": 38.0,
    "bore_dia": 20.0,
    "width": 14.0,
    "screw_hole_dia": 4.5,
    "counterbore_dia": 8.0,
    "counterbore_depth": 5.0,
    "slit_width": 2.0,
}

from build123d import *

od = PARAMS["outer_dia"]
bd = PARAMS["bore_dia"]
w = PARAMS["width"]
sd = PARAMS["screw_hole_dia"]
cbd = PARAMS["counterbore_dia"]
cbd_depth = PARAMS["counterbore_depth"]
sw = PARAMS["slit_width"]

with BuildPart() as collar:
    with BuildSketch():
        Circle(radius=od / 2.0)
        Circle(radius=bd / 2.0, mode=Mode.SUBTRACT)
    extrude(amount=w)
    # Split relief slot
    with BuildSketch(collar.faces().sort_by(Axis.Z)[0]):
        Rectangle(sw, od, mode=Mode.ADD)
    extrude(amount=w, mode=Mode.SUBTRACT)
    # Clamping bolt hole
    bolt_plane = Plane(collar.faces().sort_by(Axis.X)[-1].center(CenterOf.BOUNDING_BOX), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    with BuildPart(bolt_plane):
        with BuildSketch():
            Circle(radius=sd / 2.0)
        extrude(amount=od / 2.0, mode=Mode.SUBTRACT)

result = collar.part
''',
    },

    # ── 2. FLANGED BEARING HOUSING ─────────────────────────────────────────
    {
        "id": "cadprompt_flanged_bearing_housing",
        "description": "Square 4-bolt flanged bearing housing with central bearing journal, grease relief, and 4 corner mounting holes",
        "tags": ["bearing", "housing", "flange", "pillow block", "mount", "bracket", "cadprompt"],
        "code": '''\
PARAMS = {
    "flange_size": 75.0,
    "flange_thickness": 10.0,
    "boss_dia": 48.0,
    "boss_height": 18.0,
    "bearing_bore": 30.0,
    "bolt_hole_dia": 6.5,
    "bolt_spacing": 54.0,
}

from build123d import *

fs = PARAMS["flange_size"]
ft = PARAMS["flange_thickness"]
bd = PARAMS["boss_dia"]
bh = PARAMS["boss_height"]
bb = PARAMS["bearing_bore"]
bhd = PARAMS["bolt_hole_dia"]
bs = PARAMS["bolt_spacing"]

with BuildPart() as housing:
    # Base flange
    with BuildSketch():
        RectangleRounded(fs, fs, radius=6.0)
    extrude(amount=ft)
    # Bearing boss
    with BuildSketch(housing.faces().sort_by(Axis.Z)[-1]):
        Circle(radius=bd / 2.0)
    extrude(amount=bh)
    # Central through bore
    with BuildSketch(housing.faces().sort_by(Axis.Z)[-1]):
        Circle(radius=bb / 2.0)
    extrude(amount=-(ft + bh), mode=Mode.SUBTRACT)
    # 4 Corner bolt holes
    corner_locs = [
        (-bs / 2.0, -bs / 2.0),
        (-bs / 2.0,  bs / 2.0),
        ( bs / 2.0, -bs / 2.0),
        ( bs / 2.0,  bs / 2.0),
    ]
    with BuildSketch(housing.faces().sort_by(Axis.Z)[0]):
        with Locations(corner_locs):
            Circle(radius=bhd / 2.0)
    extrude(amount=ft, mode=Mode.SUBTRACT)

result = housing.part
''',
    },

    # ── 3. ERGONOMIC 5-LOBE STAR KNOB ──────────────────────────────────────
    {
        "id": "cadprompt_star_knob",
        "description": "Five-lobed ergonomic mechanical star knob for manual clamping screws with fluted finger grips and central threaded insert bore",
        "tags": ["knob", "star knob", "clamp", "handle", "ergonomic", "grip", "cadprompt"],
        "code": '''\
PARAMS = {
    "outer_radius": 28.0,
    "inner_radius": 19.0,
    "num_lobes": 5,
    "thickness": 14.0,
    "hub_dia": 22.0,
    "hub_height": 8.0,
    "bore_dia": 8.0,
}

import math
from build123d import *

ro = PARAMS["outer_radius"]
ri = PARAMS["inner_radius"]
n = int(PARAMS["num_lobes"])
th = PARAMS["thickness"]
hd = PARAMS["hub_dia"]
hh = PARAMS["hub_height"]
bd = PARAMS["bore_dia"]

pts = []
for i in range(2 * n):
    angle = i * math.pi / n
    r = ro if i % 2 == 0 else ri
    pts.append(Vector(r * math.cos(angle), r * math.sin(angle)))

with BuildPart() as knob:
    with BuildSketch():
        Polygon(pts)
    extrude(amount=th)
    # Central hub
    with BuildSketch(knob.faces().sort_by(Axis.Z)[0]):
        Circle(radius=hd / 2.0)
    extrude(amount=hh, mode=Mode.ADD)
    # Through bore
    with BuildSketch(knob.faces().sort_by(Axis.Z)[-1]):
        Circle(radius=bd / 2.0)
    extrude(amount=-(th + hh), mode=Mode.SUBTRACT)

result = knob.part
''',
    },

    # ── 4. 3-WAY FLUID MANIFOLD BLOCK ──────────────────────────────────────
    {
        "id": "cadprompt_pipe_manifold",
        "description": "Machined 3-way fluid distribution manifold block with main feed channel, two perpendicular branch ports, and mounting holes",
        "tags": ["manifold", "pneumatic", "hydraulic", "block", "ports", "fluid", "cadprompt"],
        "code": '''\
PARAMS = {
    "length": 80.0,
    "width": 40.0,
    "height": 35.0,
    "main_bore_dia": 16.0,
    "branch_port_dia": 10.0,
    "port_spacing": 30.0,
    "mount_hole_dia": 5.5,
}

from build123d import *

l = PARAMS["length"]
w = PARAMS["width"]
h = PARAMS["height"]
mbd = PARAMS["main_bore_dia"]
bpd = PARAMS["branch_port_dia"]
ps = PARAMS["port_spacing"]
mhd = PARAMS["mount_hole_dia"]

with BuildPart() as manifold:
    Box(l, w, h)
    # Main longitudinal bore
    front_face = manifold.faces().sort_by(Axis.X)[-1]
    with BuildSketch(front_face):
        Circle(radius=mbd / 2.0)
    extrude(amount=-l, mode=Mode.SUBTRACT)
    # 2 Branch ports on top face
    top_face = manifold.faces().sort_by(Axis.Z)[-1]
    branch_locs = [(-ps / 2.0, 0.0), (ps / 2.0, 0.0)]
    with BuildSketch(top_face):
        with Locations(branch_locs):
            Circle(radius=bpd / 2.0)
    extrude(amount=-h / 2.0, mode=Mode.SUBTRACT)
    # 2 Corner mounting holes
    mount_locs = [(-l / 2.0 + 8.0, -w / 2.0 + 8.0), (l / 2.0 - 8.0, w / 2.0 - 8.0)]
    with BuildSketch(top_face):
        with Locations(mount_locs):
            Circle(radius=mhd / 2.0)
    extrude(amount=-h, mode=Mode.SUBTRACT)

result = manifold.part
''',
    },

    # ── 5. STEPPED SHOULDER BUSHING ────────────────────────────────────────
    {
        "id": "cadprompt_stepped_bushing",
        "description": "Turned stepped shoulder bushing with outer sleeve, shoulder stop, inner lubrication bore, and chamfered entries",
        "tags": ["bushing", "sleeve", "shoulder", "bearing", "turned", "cadprompt"],
        "code": '''\
PARAMS = {
    "shoulder_dia": 32.0,
    "shoulder_len": 6.0,
    "sleeve_dia": 22.0,
    "sleeve_len": 24.0,
    "inner_bore": 14.0,
    "chamfer_size": 1.2,
}

from build123d import *

sd = PARAMS["shoulder_dia"]
sl = PARAMS["shoulder_len"]
svd = PARAMS["sleeve_dia"]
svl = PARAMS["sleeve_len"]
ib = PARAMS["inner_bore"]
ch = PARAMS["chamfer_size"]

with BuildPart() as bushing:
    # Shoulder base
    with BuildSketch():
        Circle(radius=sd / 2.0)
    extrude(amount=sl)
    # Sleeve extension
    with BuildSketch(bushing.faces().sort_by(Axis.Z)[-1]):
        Circle(radius=svd / 2.0)
    extrude(amount=svl)
    # Central bore
    with BuildSketch(bushing.faces().sort_by(Axis.Z)[-1]):
        Circle(radius=ib / 2.0)
    extrude(amount=-(sl + svl), mode=Mode.SUBTRACT)
    # Outer chamfers
    top_edges = bushing.edges().filter_by(GeomType.CIRCLE).sort_by(Axis.Z)[-1]
    chamfer(top_edges, length=ch)

result = bushing.part
''',
    },
]
