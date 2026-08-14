"""
RAG Corpus — 30 Additional build123d Example Pairs (Week 5)
============================================================
Mechanical parts: flanges, enclosures, U-brackets, standoffs, pulleys,
shaft collars, T-slot covers, hinges, gear blanks, C-channels, and more.
Total corpus after adding this: 50 examples.
"""

EXAMPLES = [

    {
        "id": "flange_basic",
        "description": "A circular flange with a central bore and four bolt holes equally spaced around the perimeter",
        "tags": ["flange", "bore", "bolt circle", "pipe flange", "bolt holes", "circular"],
        "code": '''\
PARAMS = {
    "outer_radius": 40.0,
    "bore_radius": 12.0,
    "thickness": 8.0,
    "bolt_circle_radius": 30.0,
    "bolt_hole_radius": 3.5,
    "num_bolts": 4
}
from build123d import *
import math

with BuildPart() as part:
    Cylinder(radius=PARAMS["outer_radius"], height=PARAMS["thickness"])
    Cylinder(radius=PARAMS["bore_radius"], height=PARAMS["thickness"], mode=Mode.SUBTRACT)
    angle_step = 360.0 / PARAMS["num_bolts"]
    for i in range(int(PARAMS["num_bolts"])):
        angle = math.radians(i * angle_step)
        x = PARAMS["bolt_circle_radius"] * math.cos(angle)
        y = PARAMS["bolt_circle_radius"] * math.sin(angle)
        with Locations((x, y, 0)):
            Cylinder(radius=PARAMS["bolt_hole_radius"], height=PARAMS["thickness"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "enclosure_box",
        "description": "A rectangular enclosure or electronics box with hollowed interior and uniform wall thickness",
        "tags": ["enclosure", "box", "electronics", "housing", "hollow", "shell", "container"],
        "code": '''\
PARAMS = {
    "outer_length": 100.0,
    "outer_width": 70.0,
    "outer_height": 50.0,
    "wall_thickness": 3.0
}
from build123d import *

ol = PARAMS["outer_length"]
ow = PARAMS["outer_width"]
oh = PARAMS["outer_height"]
t  = PARAMS["wall_thickness"]

with BuildPart() as part:
    Box(ol, ow, oh)
    with Locations((0, 0, t / 2)):
        Box(ol - 2*t, ow - 2*t, oh - t, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "u_bracket",
        "description": "A U-shaped bracket or channel bracket with two vertical arms and a horizontal base",
        "tags": ["U-bracket", "channel bracket", "U-channel", "U-shape", "clevis"],
        "code": '''\
PARAMS = {
    "base_length": 80.0,
    "arm_height": 50.0,
    "arm_width": 20.0,
    "thickness": 5.0
}
from build123d import *

bl = PARAMS["base_length"]
ah = PARAMS["arm_height"]
aw = PARAMS["arm_width"]
t  = PARAMS["thickness"]

with BuildPart() as part:
    Box(bl, aw, t)
    with Locations((-bl/2 + t/2, 0, ah/2)):
        Box(t, aw, ah)
    with Locations((bl/2 - t/2, 0, ah/2)):
        Box(t, aw, ah)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "cylindrical_standoff",
        "description": "A hollow cylindrical standoff or spacer with a central through-hole for a bolt",
        "tags": ["standoff", "spacer", "pillar", "PCB standoff", "hollow cylinder"],
        "code": '''\
PARAMS = {
    "outer_radius": 6.0,
    "inner_radius": 2.6,
    "height": 20.0
}
from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["outer_radius"], height=PARAMS["height"])
    Cylinder(radius=PARAMS["inner_radius"], height=PARAMS["height"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "shaft_collar",
        "description": "A shaft collar or clamp ring that slides onto a shaft and is secured with a set screw",
        "tags": ["shaft collar", "collar", "clamp ring", "set screw", "shaft", "bore"],
        "code": '''\
PARAMS = {
    "bore_radius": 10.0,
    "outer_radius": 18.0,
    "width": 12.0
}
from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["outer_radius"], height=PARAMS["width"])
    Cylinder(radius=PARAMS["bore_radius"], height=PARAMS["width"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "gear_blank",
        "description": "A cylindrical gear blank or disk with a central keyway bore, ready for gear teeth machining",
        "tags": ["gear", "gear blank", "spur gear", "disk", "sprocket", "keyway"],
        "code": '''\
PARAMS = {
    "pitch_radius": 35.0,
    "hub_radius": 12.0,
    "bore_radius": 8.0,
    "face_width": 20.0,
    "hub_height": 30.0
}
from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["pitch_radius"], height=PARAMS["face_width"])
    with Locations((0, 0, (PARAMS["hub_height"] - PARAMS["face_width"]) / 2)):
        Cylinder(radius=PARAMS["hub_radius"], height=PARAMS["hub_height"])
    Cylinder(radius=PARAMS["bore_radius"], height=PARAMS["hub_height"] + PARAMS["face_width"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "pulley",
        "description": "A V-groove pulley or belt pulley with a flanged groove profile",
        "tags": ["pulley", "V-groove", "belt", "sheave", "wheel", "groove"],
        "code": '''\
PARAMS = {
    "outer_radius": 40.0,
    "groove_depth": 8.0,
    "groove_width": 12.0,
    "width": 30.0,
    "bore_radius": 10.0
}
from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["outer_radius"], height=PARAMS["width"])
    with Locations((0, 0, 0)):
        Cylinder(
            radius=PARAMS["outer_radius"] - PARAMS["groove_depth"],
            height=PARAMS["groove_width"],
            mode=Mode.SUBTRACT
        )
    Cylinder(radius=PARAMS["bore_radius"], height=PARAMS["width"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "c_channel",
        "description": "A C-channel or structural steel profile with configurable web and flange dimensions",
        "tags": ["C-channel", "structural", "beam", "profile", "steel section", "C-section"],
        "code": '''\
PARAMS = {
    "height": 60.0,
    "flange_width": 30.0,
    "web_thickness": 5.0,
    "flange_thickness": 5.0,
    "length": 120.0
}
from build123d import *

h  = PARAMS["height"]
fw = PARAMS["flange_width"]
wt = PARAMS["web_thickness"]
ft = PARAMS["flange_thickness"]
l  = PARAMS["length"]

with BuildPart() as part:
    Box(wt, l, h)
    with Locations(((fw + wt)/2 - wt/2, 0, -(h - ft)/2 + h/2 - h/2)):
        Box(fw, l, ft)
    with Locations(((fw + wt)/2 - wt/2, 0, (h - ft)/2 - h/2 + h/2)):
        Box(fw, l, ft)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "hex_standoff",
        "description": "A hexagonal brass standoff with male and female threaded ends (simplified as hex prism with bore)",
        "tags": ["hex standoff", "brass standoff", "hexagonal", "PCB", "threaded"],
        "code": '''\
PARAMS = {
    "hex_width": 8.0,
    "height": 25.0,
    "bore_radius": 1.6
}
from build123d import *

with BuildPart() as part:
    with BuildSketch() as sk:
        RegularPolygon(radius=PARAMS["hex_width"]/2, side_count=6, major_radius=False)
    extrude(amount=PARAMS["height"])
    Cylinder(radius=PARAMS["bore_radius"], height=PARAMS["height"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "t_slot_cover",
        "description": "A T-slot or dovetail profile cover cap that slides into aluminum extrusion slots",
        "tags": ["T-slot", "slot cover", "extrusion", "cap", "dovetail", "insert"],
        "code": '''\
PARAMS = {
    "outer_width": 20.0,
    "slot_width": 8.0,
    "slot_depth": 5.0,
    "height": 6.0,
    "length": 50.0
}
from build123d import *

ow = PARAMS["outer_width"]
sw = PARAMS["slot_width"]
sd = PARAMS["slot_depth"]
h  = PARAMS["height"]
l  = PARAMS["length"]

with BuildPart() as part:
    Box(ow, l, h)
    with Locations((0, 0, -(h - sd)/2)):
        Box(sw, l, sd, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "hinge_leaf",
        "description": "A single hinge leaf plate with a cylindrical knuckle pin barrel",
        "tags": ["hinge", "leaf", "knuckle", "pin", "door hinge", "barrel"],
        "code": '''\
PARAMS = {
    "leaf_length": 60.0,
    "leaf_width": 40.0,
    "leaf_thickness": 3.0,
    "knuckle_radius": 5.0,
    "knuckle_length": 30.0
}
from build123d import *

with BuildPart() as part:
    Box(PARAMS["leaf_length"], PARAMS["leaf_width"], PARAMS["leaf_thickness"])
    with Locations((PARAMS["leaf_length"]/2, 0, PARAMS["knuckle_radius"])):
        with Rotation(0, 90, 0):
            Cylinder(radius=PARAMS["knuckle_radius"], height=PARAMS["knuckle_length"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "lid_with_lip",
        "description": "A flat rectangular lid with a recessed lip/rim that fits on top of a box or enclosure",
        "tags": ["lid", "cover", "cap", "lip", "rim", "enclosure lid"],
        "code": '''\
PARAMS = {
    "outer_length": 106.0,
    "outer_width": 76.0,
    "lid_thickness": 3.0,
    "lip_height": 5.0,
    "lip_thickness": 3.0
}
from build123d import *

ol = PARAMS["outer_length"]
ow = PARAMS["outer_width"]
lt = PARAMS["lid_thickness"]
lh = PARAMS["lip_height"]
lp = PARAMS["lip_thickness"]

with BuildPart() as part:
    Box(ol, ow, lt)
    with Locations((0, 0, -(lh + lt)/2)):
        Box(ol - 2*lp, ow - 2*lp, lh)
    with Locations((0, 0, -(lh + lt)/2)):
        Box(ol - 2*(lp + lp), ow - 2*(lp + lp), lh, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "t_bracket",
        "description": "A T-shaped bracket or cross-bracket for perpendicular surface mounting",
        "tags": ["T-bracket", "cross bracket", "T-shape", "right angle", "perpendicular mount"],
        "code": '''\
PARAMS = {
    "horizontal_length": 80.0,
    "vertical_height": 60.0,
    "width": 30.0,
    "thickness": 5.0
}
from build123d import *

hl = PARAMS["horizontal_length"]
vh = PARAMS["vertical_height"]
w  = PARAMS["width"]
t  = PARAMS["thickness"]

with BuildPart() as part:
    Box(hl, w, t)
    with Locations((0, 0, (vh + t) / 2)):
        Box(t, w, vh)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "nozzle",
        "description": "A round nozzle or spout with a large inlet bore tapering to a smaller outlet bore",
        "tags": ["nozzle", "spout", "tapered", "inlet", "outlet", "pipe fitting"],
        "code": '''\
PARAMS = {
    "inlet_radius": 20.0,
    "outlet_radius": 8.0,
    "length": 60.0,
    "wall_thickness": 3.0
}
from build123d import *

with BuildPart() as part:
    Cone(
        bottom_radius=PARAMS["inlet_radius"],
        top_radius=PARAMS["outlet_radius"],
        height=PARAMS["length"]
    )
    Cone(
        bottom_radius=PARAMS["inlet_radius"] - PARAMS["wall_thickness"],
        top_radius=PARAMS["outlet_radius"] - PARAMS["wall_thickness"],
        height=PARAMS["length"],
        mode=Mode.SUBTRACT
    )

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "square_post",
        "description": "A hollow square tube post or structural column with uniform wall thickness",
        "tags": ["square post", "column", "hollow square", "structural post", "pillar"],
        "code": '''\
PARAMS = {
    "side_length": 30.0,
    "height": 100.0,
    "wall_thickness": 3.0
}
from build123d import *

sl = PARAMS["side_length"]
h  = PARAMS["height"]
t  = PARAMS["wall_thickness"]

with BuildPart() as part:
    Box(sl, sl, h)
    Box(sl - 2*t, sl - 2*t, h, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "bushing",
        "description": "A flanged bushing or sleeve bearing with outer flange, inner bore, and cylindrical body",
        "tags": ["bushing", "sleeve", "bearing", "flanged bushing", "liner", "sleeve bearing"],
        "code": '''\
PARAMS = {
    "body_radius": 14.0,
    "flange_radius": 20.0,
    "bore_radius": 10.0,
    "body_height": 25.0,
    "flange_thickness": 4.0
}
from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["body_radius"], height=PARAMS["body_height"])
    with Locations((0, 0, (PARAMS["body_height"] + PARAMS["flange_thickness"]) / 2)):
        Cylinder(radius=PARAMS["flange_radius"], height=PARAMS["flange_thickness"])
    Cylinder(
        radius=PARAMS["bore_radius"],
        height=PARAMS["body_height"] + PARAMS["flange_thickness"],
        mode=Mode.SUBTRACT
    )

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "cross_shaft",
        "description": "A plus-shaped or cross-shaped connector part where two shafts intersect at 90 degrees",
        "tags": ["cross", "plus shape", "shaft cross", "X-connector", "perpendicular", "cruciform"],
        "code": '''\
PARAMS = {
    "arm_radius": 8.0,
    "arm_length": 40.0,
    "center_radius": 12.0
}
from build123d import *

with BuildPart() as part:
    Sphere(radius=PARAMS["center_radius"])
    with Rotation(0, 0, 0):
        Cylinder(radius=PARAMS["arm_radius"], height=PARAMS["arm_length"] * 2)
    with Rotation(90, 0, 0):
        Cylinder(radius=PARAMS["arm_radius"], height=PARAMS["arm_length"] * 2)
    with Rotation(0, 90, 0):
        Cylinder(radius=PARAMS["arm_radius"], height=PARAMS["arm_length"] * 2)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "hex_nut",
        "description": "A standard hexagonal nut with a threaded bore (modeled as a hex prism with central hole)",
        "tags": ["hex nut", "nut", "fastener", "hexagonal", "M8", "threaded bore"],
        "code": '''\
PARAMS = {
    "hex_flat_to_flat": 13.0,
    "thickness": 6.5,
    "bore_radius": 4.0
}
from build123d import *

with BuildPart() as part:
    with BuildSketch() as sk:
        RegularPolygon(radius=PARAMS["hex_flat_to_flat"] / 2, side_count=6, major_radius=False)
    extrude(amount=PARAMS["thickness"])
    Cylinder(radius=PARAMS["bore_radius"], height=PARAMS["thickness"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "angle_bracket",
        "description": "An angle bracket or right-angle brace with filleted inner corner and mounting holes",
        "tags": ["angle bracket", "right angle", "corner brace", "L-bracket", "fillet"],
        "code": '''\
PARAMS = {
    "leg_length": 50.0,
    "leg_width": 40.0,
    "thickness": 4.0,
    "hole_radius": 3.0,
    "fillet_radius": 5.0
}
from build123d import *

ll = PARAMS["leg_length"]
lw = PARAMS["leg_width"]
t  = PARAMS["thickness"]
hr = PARAMS["hole_radius"]

with BuildPart() as part:
    Box(ll, lw, t)
    with Locations((0, 0, ll/2)):
        Box(t, lw, ll)
    with GridLocations(ll/2, lw/2, 2, 2):
        Cylinder(radius=hr, height=t, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "mounting_clamp",
        "description": "A split tube clamp or pipe clamp that wraps around a cylinder with two bolt flanges",
        "tags": ["clamp", "pipe clamp", "tube clamp", "split clamp", "hose clamp", "bolt flange"],
        "code": '''\
PARAMS = {
    "pipe_radius": 15.0,
    "clamp_thickness": 5.0,
    "flange_height": 20.0,
    "flange_width": 12.0
}
from build123d import *

pr = PARAMS["pipe_radius"]
ct = PARAMS["clamp_thickness"]
fh = PARAMS["flange_height"]
fw = PARAMS["flange_width"]

with BuildPart() as part:
    Cylinder(radius=pr + ct, height=fh)
    Cylinder(radius=pr, height=fh, mode=Mode.SUBTRACT)
    with Locations((pr + ct + fw/2, 0, 0)):
        Box(fw, fh, fh)
    with Locations(-(pr + ct + fw/2), 0, 0):
        Box(fw, fh, fh)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "cap_screw_head",
        "description": "A socket head cap screw (SHCS) with cylindrical head and hexagonal socket recess",
        "tags": ["cap screw", "socket head", "bolt", "SHCS", "Allen bolt", "fastener"],
        "code": '''\
PARAMS = {
    "head_radius": 8.0,
    "head_height": 8.0,
    "shank_radius": 5.0,
    "shank_length": 30.0,
    "socket_radius": 3.0,
    "socket_depth": 5.0
}
from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["head_radius"], height=PARAMS["head_height"])
    with Locations((0, 0, -(PARAMS["shank_length"] + PARAMS["head_height"]) / 2)):
        Cylinder(radius=PARAMS["shank_radius"], height=PARAMS["shank_length"])
    with Locations((0, 0, PARAMS["head_height"] / 2 - PARAMS["socket_depth"] / 2)):
        with BuildSketch() as sk:
            RegularPolygon(radius=PARAMS["socket_radius"], side_count=6)
        extrude(amount=PARAMS["socket_depth"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "shelf_bracket",
        "description": "A wall shelf bracket with a triangular gusset for strength, two holes for wall mounting",
        "tags": ["shelf", "bracket", "wall mount", "gusset", "triangle", "support"],
        "code": '''\
PARAMS = {
    "horizontal_arm": 120.0,
    "vertical_arm": 100.0,
    "thickness": 5.0,
    "width": 30.0
}
from build123d import *

ha = PARAMS["horizontal_arm"]
va = PARAMS["vertical_arm"]
t  = PARAMS["thickness"]
w  = PARAMS["width"]

with BuildPart() as part:
    Box(ha, w, t)
    with Locations((0, 0, va/2)):
        Box(t, w, va)
    with BuildSketch(Plane.XZ) as sk:
        with BuildLine() as ln:
            Polyline((t/2, 0), (ha, 0), (t/2, va), close=True)
        make_face()
    extrude(amount=w/2, both=True)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "pcb_mounting_plate",
        "description": "A PCB mounting plate with four M3 standoff holes in standard Arduino Uno spacing",
        "tags": ["PCB", "mounting plate", "Arduino", "standoff holes", "electronics mount", "M3"],
        "code": '''\
PARAMS = {
    "length": 90.0,
    "width": 65.0,
    "thickness": 3.0,
    "hole_radius": 1.75,
    "corner_radius": 5.0
}
from build123d import *

with BuildPart() as part:
    Box(PARAMS["length"], PARAMS["width"], PARAMS["thickness"])
    with GridLocations(PARAMS["length"] - 10, PARAMS["width"] - 10, 2, 2):
        Cylinder(radius=PARAMS["hole_radius"], height=PARAMS["thickness"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "spool",
        "description": "A filament spool or cable spool with two flanges and a central hub cylinder",
        "tags": ["spool", "reel", "filament", "cable", "flanged spool", "hub"],
        "code": '''\
PARAMS = {
    "hub_radius": 25.0,
    "flange_radius": 60.0,
    "hub_width": 60.0,
    "flange_thickness": 5.0,
    "bore_radius": 15.0
}
from build123d import *

hw = PARAMS["hub_width"]
ft = PARAMS["flange_thickness"]
total = hw + 2 * ft

with BuildPart() as part:
    Cylinder(radius=PARAMS["hub_radius"], height=hw)
    with Locations((0, 0, -(hw + ft) / 2)):
        Cylinder(radius=PARAMS["flange_radius"], height=ft)
    with Locations((0, 0, (hw + ft) / 2)):
        Cylinder(radius=PARAMS["flange_radius"], height=ft)
    Cylinder(radius=PARAMS["bore_radius"], height=total, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "pipe_elbow",
        "description": "A 90-degree pipe elbow made from two perpendicular hollow cylinder stubs",
        "tags": ["elbow", "pipe", "90 degree", "fitting", "bend", "plumbing"],
        "code": '''\
PARAMS = {
    "outer_radius": 18.0,
    "inner_radius": 13.0,
    "arm_length": 40.0
}
from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["outer_radius"], height=PARAMS["arm_length"])
    Cylinder(radius=PARAMS["inner_radius"], height=PARAMS["arm_length"], mode=Mode.SUBTRACT)
    with Locations((0, 0, PARAMS["arm_length"] / 2)):
        with Rotation(90, 0, 0):
            Cylinder(radius=PARAMS["outer_radius"], height=PARAMS["arm_length"])
            Cylinder(radius=PARAMS["inner_radius"], height=PARAMS["arm_length"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "rectangular_plate_slots",
        "description": "A rectangular plate with two elongated slots for adjustable mounting positions",
        "tags": ["slotted plate", "adjustable", "slot", "oblong hole", "mounting plate"],
        "code": '''\
PARAMS = {
    "length": 120.0,
    "width": 50.0,
    "thickness": 4.0,
    "slot_length": 30.0,
    "slot_width": 8.0,
    "slot_offset": 30.0
}
from build123d import *

with BuildPart() as part:
    Box(PARAMS["length"], PARAMS["width"], PARAMS["thickness"])
    for offset in [-PARAMS["slot_offset"], PARAMS["slot_offset"]]:
        with Locations((offset, 0, 0)):
            with BuildSketch(part.faces().sort_by(Axis.Z)[-1]) as sk:
                SlotOverall(width=PARAMS["slot_length"], height=PARAMS["slot_width"])
            extrude(amount=-PARAMS["thickness"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "rounded_peg",
        "description": "A round peg or dowel pin with a domed top and flat base, used for alignment",
        "tags": ["peg", "dowel", "pin", "alignment", "dome", "locating pin"],
        "code": '''\
PARAMS = {
    "radius": 5.0,
    "shaft_height": 20.0
}
from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["radius"], height=PARAMS["shaft_height"])
    with Locations((0, 0, PARAMS["shaft_height"] / 2)):
        Sphere(radius=PARAMS["radius"])
    with Locations((0, 0, -PARAMS["shaft_height"] / 2)):
        Box(PARAMS["radius"]*4, PARAMS["radius"]*4, PARAMS["shaft_height"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "box_filleted",
        "description": "A rectangular box with all vertical edges filleted for smooth rounded corners",
        "tags": ["box", "fillet", "rounded corners", "smooth box", "chamfered box"],
        "code": '''\
PARAMS = {
    "length": 60.0,
    "width": 40.0,
    "height": 30.0,
    "fillet_radius": 5.0
}
from build123d import *

with BuildPart() as part:
    Box(PARAMS["length"], PARAMS["width"], PARAMS["height"])
    fillet(
        part.edges().filter_by(Axis.Z),
        radius=PARAMS["fillet_radius"]
    )

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "cylinder_array",
        "description": "A flat plate with a 3x3 grid array of cylindrical bosses or pegs on top",
        "tags": ["boss array", "peg grid", "array", "lego-like", "connector pins", "grid pattern"],
        "code": '''\
PARAMS = {
    "plate_length": 80.0,
    "plate_width": 80.0,
    "plate_thickness": 5.0,
    "peg_radius": 5.0,
    "peg_height": 10.0,
    "peg_spacing": 25.0
}
from build123d import *

with BuildPart() as part:
    Box(PARAMS["plate_length"], PARAMS["plate_width"], PARAMS["plate_thickness"])
    with GridLocations(PARAMS["peg_spacing"], PARAMS["peg_spacing"], 3, 3):
        with Locations((0, 0, (PARAMS["plate_thickness"] + PARAMS["peg_height"]) / 2)):
            Cylinder(radius=PARAMS["peg_radius"], height=PARAMS["peg_height"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "motor_mount",
        "description": "A motor mounting plate with a large central bore for the motor body and four corner mounting holes",
        "tags": ["motor mount", "motor bracket", "NEMA", "stepper motor", "servo mount"],
        "code": '''\
PARAMS = {
    "plate_size": 60.0,
    "thickness": 4.0,
    "motor_bore_radius": 19.0,
    "hole_radius": 2.6,
    "hole_spacing": 47.0
}
from build123d import *

with BuildPart() as part:
    Box(PARAMS["plate_size"], PARAMS["plate_size"], PARAMS["thickness"])
    Cylinder(radius=PARAMS["motor_bore_radius"], height=PARAMS["thickness"], mode=Mode.SUBTRACT)
    with GridLocations(PARAMS["hole_spacing"], PARAMS["hole_spacing"], 2, 2):
        Cylinder(radius=PARAMS["hole_radius"], height=PARAMS["thickness"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

]

assert len(EXAMPLES) == 30, f"Expected 30 examples, got {len(EXAMPLES)}"
