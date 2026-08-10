"""
RAG Corpus — 20 build123d Example Snippet Pairs
Each entry: natural language description + complete working build123d script.
Used by rag_service.py to populate ChromaDB for few-shot retrieval.
"""

EXAMPLES = [

    {
        "id": "box_basic",
        "description": "A simple rectangular box with configurable length, width, and height",
        "tags": ["box", "rectangular", "basic", "cube", "block"],
        "code": '''\
PARAMS = {"length": 60.0, "width": 40.0, "height": 20.0}

from build123d import *

length = PARAMS["length"]
width  = PARAMS["width"]
height = PARAMS["height"]

with BuildPart() as part:
    Box(length, width, height)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "cylinder_solid",
        "description": "A solid cylinder with configurable radius and height",
        "tags": ["cylinder", "rod", "shaft", "round", "solid"],
        "code": '''\
PARAMS = {"radius": 15.0, "height": 50.0}

from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["radius"], height=PARAMS["height"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "hollow_cylinder",
        "description": "A hollow cylinder or pipe with outer radius, wall thickness, and height",
        "tags": ["hollow", "pipe", "tube", "cylinder", "shell", "wall"],
        "code": '''\
PARAMS = {"outer_radius": 20.0, "wall_thickness": 3.0, "height": 60.0}

from build123d import *

outer = PARAMS["outer_radius"]
wall  = PARAMS["wall_thickness"]
h     = PARAMS["height"]
inner = outer - wall

with BuildPart() as part:
    Cylinder(radius=outer, height=h)
    Cylinder(radius=inner, height=h, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "cone",
        "description": "A solid cone with configurable base radius and height",
        "tags": ["cone", "tapered", "funnel", "pointed"],
        "code": '''\
PARAMS = {"base_radius": 20.0, "height": 45.0}

from build123d import *

with BuildPart() as part:
    Cone(bottom_radius=PARAMS["base_radius"], top_radius=0, height=PARAMS["height"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "truncated_cone",
        "description": "A truncated cone or frustum with configurable bottom radius, top radius, and height",
        "tags": ["frustum", "truncated cone", "tapered", "reducer", "bushing"],
        "code": '''\
PARAMS = {"bottom_radius": 25.0, "top_radius": 12.0, "height": 40.0}

from build123d import *

with BuildPart() as part:
    Cone(
        bottom_radius=PARAMS["bottom_radius"],
        top_radius=PARAMS["top_radius"],
        height=PARAMS["height"]
    )

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "box_with_hole",
        "description": "A rectangular box with a cylindrical through-hole drilled through the center",
        "tags": ["box", "hole", "drilling", "through-hole", "bore"],
        "code": '''\
PARAMS = {"length": 60.0, "width": 40.0, "height": 25.0, "hole_radius": 8.0}

from build123d import *

with BuildPart() as part:
    Box(PARAMS["length"], PARAMS["width"], PARAMS["height"])
    Cylinder(radius=PARAMS["hole_radius"], height=PARAMS["height"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "mounting_bracket_flat",
        "description": "A flat mounting bracket or plate with four corner holes for M5 bolts",
        "tags": ["bracket", "mounting", "plate", "holes", "M5", "flange", "base plate"],
        "code": '''\
PARAMS = {
    "length": 80.0, "width": 50.0, "thickness": 5.0,
    "hole_radius": 2.75, "hole_inset": 8.0
}

from build123d import *

l  = PARAMS["length"]
w  = PARAMS["width"]
t  = PARAMS["thickness"]
hr = PARAMS["hole_radius"]
d  = PARAMS["hole_inset"]

with BuildPart() as part:
    Box(l, w, t)
    # Four corner holes
    with GridLocations(l - 2*d, w - 2*d, 2, 2):
        Cylinder(radius=hr, height=t, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "l_bracket",
        "description": "An L-shaped bracket with two perpendicular arms and mounting holes",
        "tags": ["L-bracket", "angle bracket", "corner", "right angle", "structural"],
        "code": '''\
PARAMS = {
    "arm_length": 60.0, "arm_width": 40.0,
    "thickness": 5.0, "hole_radius": 3.0
}

from build123d import *

l  = PARAMS["arm_length"]
w  = PARAMS["arm_width"]
t  = PARAMS["thickness"]
hr = PARAMS["hole_radius"]

with BuildPart() as part:
    # Horizontal arm
    with Locations((0, 0, t / 2)):
        Box(l, w, t)
    # Vertical arm
    with Locations((0, (w - t) / 2, l / 2)):
        Box(l, t, l)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "sphere",
        "description": "A solid sphere with configurable radius",
        "tags": ["sphere", "ball", "round", "globe"],
        "code": '''\
PARAMS = {"radius": 25.0}

from build123d import *

with BuildPart() as part:
    Sphere(radius=PARAMS["radius"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "washer",
        "description": "A flat washer or ring with inner hole and outer radius",
        "tags": ["washer", "ring", "annulus", "gasket", "spacer", "flat ring"],
        "code": '''\
PARAMS = {"outer_radius": 15.0, "inner_radius": 6.0, "thickness": 2.0}

from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["outer_radius"], height=PARAMS["thickness"])
    Cylinder(radius=PARAMS["inner_radius"], height=PARAMS["thickness"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "hex_bolt_head",
        "description": "A hexagonal prism or bolt head shape with configurable flat-to-flat width and height",
        "tags": ["hex", "hexagonal", "bolt", "nut", "hexagon", "prism"],
        "code": '''\
PARAMS = {"flat_to_flat": 13.0, "height": 8.0}

from build123d import *

with BuildPart() as part:
    with BuildSketch() as sk:
        RegularPolygon(radius=PARAMS["flat_to_flat"] / 2, side_count=6, major_radius=False)
    extrude(amount=PARAMS["height"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "cylinder_with_fillet",
        "description": "A cylinder with filleted (rounded) top and bottom edges",
        "tags": ["cylinder", "fillet", "rounded edges", "smooth", "chamfer"],
        "code": '''\
PARAMS = {"radius": 20.0, "height": 50.0, "fillet_radius": 3.0}

from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["radius"], height=PARAMS["height"])
    fillet(part.edges().filter_by(Axis.Z), radius=PARAMS["fillet_radius"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "box_chamfered",
        "description": "A box with chamfered (angled) top edges",
        "tags": ["box", "chamfer", "bevel", "angled edges"],
        "code": '''\
PARAMS = {"length": 60.0, "width": 40.0, "height": 30.0, "chamfer": 4.0}

from build123d import *

with BuildPart() as part:
    Box(PARAMS["length"], PARAMS["width"], PARAMS["height"])
    chamfer(
        part.faces().sort_by(Axis.Z)[-1].edges(),
        length=PARAMS["chamfer"]
    )

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "extruded_slot",
        "description": "A flat plate with an elongated slot cut through it",
        "tags": ["slot", "elongated hole", "slotted plate", "key slot", "oblong"],
        "code": '''\
PARAMS = {
    "plate_length": 80.0, "plate_width": 40.0, "plate_thickness": 6.0,
    "slot_length": 30.0, "slot_width": 8.0
}

from build123d import *

with BuildPart() as part:
    Box(PARAMS["plate_length"], PARAMS["plate_width"], PARAMS["plate_thickness"])
    with BuildSketch(part.faces().sort_by(Axis.Z)[-1]) as sk:
        SlotOverall(width=PARAMS["slot_length"], height=PARAMS["slot_width"])
    extrude(amount=-PARAMS["plate_thickness"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "stepped_shaft",
        "description": "A two-diameter stepped shaft or shoulder bolt with two coaxial cylinders",
        "tags": ["stepped shaft", "shoulder bolt", "two diameter", "stepped", "spindle"],
        "code": '''\
PARAMS = {
    "large_radius": 15.0, "large_height": 20.0,
    "small_radius": 8.0,  "small_height": 40.0
}

from build123d import *

with BuildPart() as part:
    Cylinder(radius=PARAMS["large_radius"], height=PARAMS["large_height"])
    with Locations((0, 0, PARAMS["large_height"] / 2 + PARAMS["small_height"] / 2)):
        Cylinder(radius=PARAMS["small_radius"], height=PARAMS["small_height"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "rectangular_tube",
        "description": "A hollow rectangular tube or square profile with configurable wall thickness",
        "tags": ["rectangular tube", "square tube", "hollow square", "profile", "extrusion"],
        "code": '''\
PARAMS = {
    "outer_length": 50.0, "outer_width": 30.0,
    "height": 80.0, "wall": 4.0
}

from build123d import *

ol = PARAMS["outer_length"]
ow = PARAMS["outer_width"]
h  = PARAMS["height"]
w  = PARAMS["wall"]

with BuildPart() as part:
    Box(ol, ow, h)
    Box(ol - 2*w, ow - 2*w, h, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "dome",
        "description": "A dome or hemisphere shape with configurable radius",
        "tags": ["dome", "hemisphere", "half sphere", "cap", "bowl"],
        "code": '''\
PARAMS = {"radius": 30.0}

from build123d import *

with BuildPart() as part:
    Sphere(radius=PARAMS["radius"])
    # Cut off bottom half to make a dome
    with Locations((0, 0, -PARAMS["radius"] / 2)):
        Box(PARAMS["radius"]*3, PARAMS["radius"]*3, PARAMS["radius"], mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "wedge_ramp",
        "description": "A wedge or ramp shape — a triangular prism useful as a door stopper or inclined plane",
        "tags": ["wedge", "ramp", "inclined", "triangular", "door stop", "slope"],
        "code": '''\
PARAMS = {"length": 80.0, "width": 40.0, "height": 25.0}

from build123d import *

with BuildPart() as part:
    with BuildSketch() as sk:
        with BuildLine() as ln:
            Polyline(
                (0, 0),
                (PARAMS["length"], 0),
                (0, PARAMS["height"]),
                close=True
            )
        make_face()
    extrude(amount=PARAMS["width"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "torus",
        "description": "A torus or donut shape with configurable major and minor radius",
        "tags": ["torus", "donut", "ring", "o-ring", "toroid"],
        "code": '''\
PARAMS = {"major_radius": 30.0, "minor_radius": 8.0}

from build123d import *

with BuildPart() as part:
    Torus(major_radius=PARAMS["major_radius"], minor_radius=PARAMS["minor_radius"])

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

    {
        "id": "counterbore_plate",
        "description": "A plate with counterbore holes for recessed bolt heads",
        "tags": ["counterbore", "recessed", "bolt hole", "plate", "counter bore", "M6"],
        "code": '''\
PARAMS = {
    "length": 100.0, "width": 60.0, "thickness": 10.0,
    "bore_radius": 5.5, "cbore_radius": 9.0, "cbore_depth": 5.0,
    "hole_inset": 15.0
}

from build123d import *

l  = PARAMS["length"]
w  = PARAMS["width"]
t  = PARAMS["thickness"]

with BuildPart() as part:
    Box(l, w, t)
    top_face = part.faces().sort_by(Axis.Z)[-1]

    # Two counterbore holes (left and right)
    with GridLocations(l - 2*PARAMS["hole_inset"], 0, 2, 1):
        # Counterbore recess from top
        with Locations(top_face):
            Cylinder(radius=PARAMS["cbore_radius"], height=PARAMS["cbore_depth"],
                     mode=Mode.SUBTRACT)
        # Through-hole remainder
        Cylinder(radius=PARAMS["bore_radius"], height=t, mode=Mode.SUBTRACT)

export_stl(part.part, OUTPUT_STL)
export_step(part.part, OUTPUT_STEP)
'''
    },

]

# Total: 20 examples
assert len(EXAMPLES) == 20, f"Expected 20 examples, got {len(EXAMPLES)}"
