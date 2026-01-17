import sys

from os.path import join as join_path
import yaml

import math

import FreeCAD as App
from FreeCAD import Vector, Placement, Rotation
import Sketcher
import Part

# Paths
PROJECT_NAME = "ProjectAquarium"
PROJECT_PATH = join_path("/home/inbarm",PROJECT_NAME)
DESIGN_DIR = "design"
sys.path.append(PROJECT_PATH)

# Constants
RAD_PER_DEG = 2*math.pi / 360

def load_physical_constraints(yaml_file):
    """Load external parameters from YAML file"""
    with open(yaml_file, "r") as file:
        params = yaml.safe_load(file)
    return params

def createSketch_base(base, length, width):
    """Create base sketch with position and dimension parameters"""    
    # Create rectangle using shape-based approach
    # Bottom-left corner at position
    p1 = Vector(0, 0, 0)
    p2 = Vector(length, 0, 0)
    p3 = Vector(length, width, 0)
    p4 = Vector(0, width, 0)
    print("p1, p2, p3, p4 = ", p1, p2, p3, p4)
    # Main rectangle
    geo12_idx = base.addGeometry(Part.LineSegment(p1, p2))  # Bottom edge
    geo23_idx = base.addGeometry(Part.LineSegment(p2, p3))  # Right edge
    geo34_idx = base.addGeometry(Part.LineSegment(p3, p4))  # Top edge
    geo41_idx = base.addGeometry(Part.LineSegment(p4, p1))  # Left edge
    
    # Constraints
    base.addConstraint(Sketcher.Constraint('Coincident', geo12_idx, 1, -1, 1))
    base.addConstraint(Sketcher.Constraint('Coincident', geo41_idx, 2, geo12_idx, 1))
    base.addConstraint(Sketcher.Constraint('Coincident', geo12_idx, 2, geo23_idx, 1))
    base.addConstraint(Sketcher.Constraint('Coincident', geo23_idx, 2, geo34_idx, 1))
    base.addConstraint(Sketcher.Constraint('Coincident', geo34_idx, 2, geo41_idx, 1))
    base.addConstraint(Sketcher.Constraint('Perpendicular', geo41_idx, geo12_idx))
    base.addConstraint(Sketcher.Constraint('Perpendicular', geo12_idx, geo23_idx))
    base.addConstraint(Sketcher.Constraint('Perpendicular', geo23_idx, geo34_idx))
    base.addConstraint(Sketcher.Constraint('Distance', geo12_idx, 1, geo12_idx, 2, App.Units.Quantity(f"{length} mm")))
    base.addConstraint(Sketcher.Constraint('Distance', geo41_idx, 1, geo41_idx, 2, App.Units.Quantity(f"{width} mm")))
    base.addConstraint(Sketcher.Constraint('Horizontal', geo12_idx))

    # Store geometry as properties
    base.addProperty("App::PropertyInteger", "Edge12", "GeomIndices")
    base.Edge12 = geo12_idx
    base.addProperty("App::PropertyInteger", "Edge41", "GeomIndices")
    base.Edge41 = geo41_idx

    # Toggle visibility
    base.Visibility = False
    base.ViewObject.Visibility = False

    return base

def createSketch_pocket_base(base, pocket_base, margin_length, margin_width):
    """Create pocket base sketch with margins relative to parent"""
    STARTIDX = 0
    ENDIDX = 1
    # Get dimensions from parent
    # 1. Get aquarium base edges
    pocket_base.addExternal(base.Name, f"Edge{base.Edge12 + 1}")
    edge12_idx = -len(pocket_base.ExternalGeometry) - 1
    ref_obj, ref_edges = pocket_base.ExternalGeometry[0]
    edge12StartPoint = ref_obj.Shape.getElement(ref_edges[-1]).Vertexes[STARTIDX].Point
    edge12EndPoint = ref_obj.Shape.getElement(ref_edges[-1]).Vertexes[ENDIDX].Point

    pocket_base.addExternal(base.Name, f"Edge{base.Edge41 + 1}")
    edge41_idx = -len(pocket_base.ExternalGeometry) - 1 
    ref_obj, ref_edges = pocket_base.ExternalGeometry[0]
    edge41StartPoint = ref_obj.Shape.getElement(ref_edges[-1]).Vertexes[STARTIDX].Point
    edge41EndPoint = ref_obj.Shape.getElement(ref_edges[-1]).Vertexes[ENDIDX].Point
    print("edge12StartPoint, edge12EndPoint, edge41StartPoint, edge41EndPoint = ", edge12StartPoint, edge12EndPoint, edge41StartPoint, edge41EndPoint)

    # 2. Compute inner rectangle    
    margin_displacement_M = Vector(margin_length, margin_width)
    margin_displacement_m = Vector(-margin_length, margin_width)
    p1 = edge12StartPoint + margin_displacement_M
    p2 = edge12EndPoint + margin_displacement_m
    p4 = edge41StartPoint - margin_displacement_m
    p3 = Vector(p2.x, p4.y, 0)
    print("p1, p2, p3, p4 = ", p1, p2, p3, p4)
    # Create inner rectangle
    p_edge12_idx = pocket_base.addGeometry(Part.LineSegment(p1, p2))    
    p_edge23_idx = pocket_base.addGeometry(Part.LineSegment(p2, p3))
    p_edge34_idx = pocket_base.addGeometry(Part.LineSegment(p3, p4))
    p_edge41_idx = pocket_base.addGeometry(Part.LineSegment(p4, p1))
    
    # Constraints
    pocket_base.addConstraint(Sketcher.Constraint(
        'DistanceX',
        edge12_idx, 1,
        p_edge12_idx, 1,
        App.Units.Quantity(f"{margin_length} mm")
        ))
    pocket_base.addConstraint(Sketcher.Constraint(
        'DistanceY',
        edge12_idx, 1,
        p_edge12_idx, 1,
        App.Units.Quantity(f"{margin_width} mm")
        ))
    pocket_base.addConstraint(Sketcher.Constraint('Coincident', p_edge41_idx, 2, p_edge12_idx, 1))
    pocket_base.addConstraint(Sketcher.Constraint('Coincident', p_edge12_idx, 2, p_edge23_idx, 1))
    pocket_base.addConstraint(Sketcher.Constraint('Coincident', p_edge23_idx, 2, p_edge34_idx, 1))
    pocket_base.addConstraint(Sketcher.Constraint('Coincident', p_edge34_idx, 2, p_edge41_idx, 1))
    pocket_base.addConstraint(Sketcher.Constraint('Perpendicular', p_edge41_idx, p_edge12_idx))
    pocket_base.addConstraint(Sketcher.Constraint('Perpendicular', p_edge12_idx, p_edge23_idx))
    pocket_base.addConstraint(Sketcher.Constraint('Perpendicular', p_edge23_idx, p_edge34_idx))
    pocket_base.addConstraint(Sketcher.Constraint(
        'Distance',
        p_edge12_idx, 1,
        p_edge12_idx, 2,
        App.Units.Quantity(f"{abs(edge12EndPoint.x - edge12StartPoint.x) - 2*margin_length} mm")
        ))
    pocket_base.addConstraint(Sketcher.Constraint(
        'Distance',
        p_edge41_idx, 1,
        p_edge41_idx, 2,
        App.Units.Quantity(f"{abs(edge41EndPoint.y - edge41StartPoint.y) - 2*margin_width} mm")
        ))
    pocket_base.addConstraint(Sketcher.Constraint('Horizontal', p_edge12_idx))

    pocket_base.Visibility = False
    pocket_base.ViewObject.Visibility = False
    return pocket_base

# def createSketch_black_box_base(doc, position=Vector(90.5, 212.0, 0.0), width=120.0, height=90.0):
#     """Create black box base sketch with position parameters"""
#     black_box_base = doc.addObject('Sketcher::SketchObject', 'black_box_base')
    
#     # Create rectangle at specified position
#     p1 = Vector(position.x, position.y + height, 0.0)  # Top-left
#     p2 = Vector(position.x, position.y, 0.0)  # Bottom-left
#     p3 = Vector(position.x + width, position.y, 0.0)  # Bottom-right
#     p4 = Vector(position.x + width, position.y + height, 0.0)  # Top-right
    
#     geo0 = black_box_base.addGeometry(Part.LineSegment(p1, p2))
#     geo1 = black_box_base.addGeometry(Part.LineSegment(p2, p3))
#     geo2 = black_box_base.addGeometry(Part.LineSegment(p3, p4))
#     geo3 = black_box_base.addGeometry(Part.LineSegment(p4, p1))
    
#     # Construction line for symmetry
#     mid_x = position.x + width / 2
#     geo4 = black_box_base.addGeometry(Part.LineSegment(
#         Vector(mid_x, 399.0, 0.0),
#         Vector(mid_x, 0.0, 0.0)
#     ))
#     black_box_base.toggleConstruction(geo4)
    
#     # Constraints
#     black_box_base.addConstraint(Sketcher.Constraint('Coincident', geo0, 2, geo1, 1))
#     black_box_base.addConstraint(Sketcher.Constraint('Coincident', geo1, 2, geo2, 1))
#     black_box_base.addConstraint(Sketcher.Constraint('Coincident', geo2, 2, geo3, 1))
#     black_box_base.addConstraint(Sketcher.Constraint('Coincident', geo3, 2, geo0, 1))
#     black_box_base.addConstraint(Sketcher.Constraint('Vertical', geo0))
#     black_box_base.addConstraint(Sketcher.Constraint('Vertical', geo2))
#     black_box_base.addConstraint(Sketcher.Constraint('Horizontal', geo1))
#     black_box_base.addConstraint(Sketcher.Constraint('Horizontal', geo3))
#     black_box_base.addConstraint(Sketcher.Constraint('Symmetric', -3, 1, -3, 2, geo4, 1))
#     black_box_base.addConstraint(Sketcher.Constraint('PointOnObject', geo4, 2, -6))
#     black_box_base.addConstraint(Sketcher.Constraint('Symmetric', geo2, 2, geo0, 1, geo4, 0))
#     black_box_base.addConstraint(Sketcher.Constraint('DistanceX', geo1, 1, geo1, 2, width))
#     black_box_base.addConstraint(Sketcher.Constraint('DistanceY', geo2, 1, geo2, 2, height))
#     black_box_base.addConstraint(Sketcher.Constraint('DistanceY', -1, 1, geo0, 2, position.y))
    
#     black_box_base.AttacherEngine = 'Engine Plane'
#     black_box_base.MapMode = 'FlatFace'
#     black_box_base.Visibility = False
#     black_box_base.ViewObject.Visibility = False
#     return black_box_base

# def createSketch_Sketch005(doc):
#     Sketch005 = doc.addObject('Sketcher::SketchObject', 'Sketch005')
#     Sketch005.AttacherEngine = 'Engine Plane'
#     Sketch005.MapMode = 'FlatFace'
#     return Sketch005


def make_aquarium(
        length,
        width,
        depth,
        margin_legnth,
        margin_width,
        floor_thickness,
        transparency,
        position=Vector(0.0, 0.0, 0.0)
        ):
    """
    Create an aquarium with configurable position and dimensions
    
    Args:
        position: Vector for base sketch position (x, y, z)
        width: Width of aquarium (X dimension)
        height: Height of aquarium (Y dimension)
        depth: Depth of aquarium (Z dimension)
    """
    doc = App.newDocument("aquarium")

    Body = doc.addObject('PartDesign::Body', 'Body')
    Body.Placement = App.Placement(position, App.Rotation(0,0,0))
    Body.ViewObject.Deviation = 0.5     # percentage; default
    Body.ViewObject.Transparency = transparency

    # Create base sketch with position parameter
    base = doc.addObject('Sketcher::SketchObject', 'base')
    Body.addObject(base)
    base = createSketch_base(
        base=base,
        length=length,
        width=width)
    base.AttachmentSupport = [(doc.getObject('XY_Plane'), '')]

    # Pad operation
    aquarium = doc.addObject('PartDesign::Pad', 'aquarium')
    Body.addObject(aquarium)
    aquarium.Profile = (base, [''])
    aquarium.Length = depth
    aquarium.ReferenceAxis = (base, ['N_Axis'])
    aquarium.Visibility = False
    aquarium.ViewObject.Visibility = False
    
    doc.recompute()     # create pad geometry in memory, so datum can be 
                        # attached.

    # Pocket sketch
    # 1. Create frozen reference plane
    datum = doc.addObject('PartDesign::Plane', 'PadEndPlane')
    Body.addObject(datum)
    subname = f"Face{len(aquarium.Shape.Faces)}"
    datum.AttachmentSupport = [(aquarium, subname)]
    datum.MapMode = 'FlatFace'
    # 2. Hide helper geometry
    datum.Visibility = False
    datum.ViewObject.Visibility = False
    # 3. Create pocket
    pocket_base = doc.addObject('Sketcher::SketchObject', 'pocket_base')
    Body.addObject(pocket_base)
    pocket_base.AttachmentSupport = [(datum, '')]
    pocket_base.MapMode = 'FlatFace'
    pocket_base = createSketch_pocket_base(
        base, pocket_base, margin_legnth, margin_width
        )

    print("Datum placement:", datum.Placement)
    print("Pocket_base placement:", pocket_base.Placement)

    Pocket = doc.addObject('PartDesign::Pocket', 'Pocket')
    Body.addObject(Pocket)
    Pocket.Profile = (pocket_base, [''])
    Pocket.Length = depth - floor_thickness

    Pocket.ReferenceAxis = (pocket_base, ['N_Axis'])

    # # Fillets
    # Fillet_Edge9 = doc.addObject('PartDesign::Fillet', 'Fillet_Edge9')
    # Fillet_Edge9.Base = (Pocket, ['Edge9'])
    # Fillet_Edge9.BaseFeature = Pocket
    # Fillet_Edge9.Radius = 10.0
    # Fillet_Edge9.Visibility = False
    # Fillet_Edge9.ViewObject.Visibility = False

    # Fillet_Edge17 = doc.addObject('PartDesign::Fillet', 'Fillet_Edge17')
    # Fillet_Edge17.Base = (Fillet_Edge9, ['Edge17'])
    # Fillet_Edge17.BaseFeature = Fillet_Edge9
    # Fillet_Edge17.Radius = 10.0
    # Fillet_Edge17.Visibility = False
    # Fillet_Edge17.ViewObject.Visibility = False

    # # Black box sketch
    # black_box_base = createSketch_black_box_base(doc)
    # black_box_base.AttachmentSupport = [(Fillet_Edge17, 'Face8')]
    # black_box_base.ExternalGeo = [
    #     Part.LineSegment(Vector(0.0, 0.0, 0.0), Vector(1.0, 0.0, 0.0)),
    #     Part.LineSegment(Vector(0.0, 0.0, 0.0), Vector(0.0, 1.0, 0.0)),
    #     Part.LineSegment(Vector(0.0, 399.0, 0.0), Vector(301.0, 399.0, 0.0)),
    #     Part.LineSegment(Vector(301.0, 10.0, 0.0), Vector(301.0, 399.0, 0.0)),
    #     Part.LineSegment(Vector(0.0, 10.0, 0.0), Vector(0.0, 399.0, 0.0)),
    #     Part.LineSegment(Vector(10.0, 0.0, 0.0), Vector(291.0, 0.0, 0.0))
    # ]

    # Pocket001 = doc.addObject('PartDesign::Pocket', 'Pocket001')
    # Pocket001.BaseFeature = Fillet_Edge17
    # Pocket001.Length = 10.0
    # Pocket001.Profile = (black_box_base, [''])
    # Pocket001.ReferenceAxis = (black_box_base, ['N_Axis'])
    # Pocket001.Visibility = False
    # Pocket001.ViewObject.Visibility = False

    # Fillet002 = doc.addObject('PartDesign::Fillet', 'Fillet002')
    # Fillet002.Base = (Pocket001, ['Edge39', 'Edge41', 'Edge40', 'Edge42'])
    # Fillet002.BaseFeature = Pocket001
    # Fillet002.Radius = 3.0
    
    doc.recompute()

    # print("pocket_base.Shape.isNull(): ", pocket_base.Shape.isNull())
    # print(f"Pocket exists: {Pocket is not None}")
    # print("Pocket.Shape.isNull(): ", Pocket.Shape.isNull())
    # print(f"Body.Shape.isNull(): {Body.Shape.isNull()}")

def main():
    
    constraints_file = join_path(PROJECT_PATH, "design", "existing_parts.yaml")
    constraints_aq = load_physical_constraints(constraints_file)["aquarium"]["main_box"]

    # Physical parameters:
    aq_length = constraints_aq["x_outer"]
    aq_width = constraints_aq["y_outer"]
    aq_height = constraints_aq["z_outer"]
    aq_x_thick = (aq_length - constraints_aq["x_inner"])/2
    aq_y_thick = (aq_width - constraints_aq["y_inner"])/2
    aq_z_thick = (aq_height - constraints_aq["z_inner"])
    # aq_base_thickness = aq_height - constraints_aq["z_inner"]
    water_level_margin = 20
    water_depth = constraints_aq["z_down"] - water_level_margin    # mm, 

    # Virtual parameters:
    aq_transparency=70
    aq_corner_position=Vector(-aq_length/2, -aq_width/2, -water_depth)

    make_aquarium(
        length=aq_length,
        width=aq_width,
        depth=aq_height,
        margin_legnth=aq_x_thick,
        margin_width=aq_y_thick,
        floor_thickness=aq_z_thick,
        transparency=aq_transparency,
        position=aq_corner_position)

# Create aquarium at default position (0, 0, 0)
if __name__ == "__main__":
    sys.stdout = open(join_path(PROJECT_PATH, DESIGN_DIR, "aquarium", "aquarium_model.log"), "a")
    main()
    sys.stdout.close()

# Or create at custom position with custom dimensions:
# make_aquarium(position=Vector(100.0, 50.0, 0.0), width=700.0, height=350.0, depth=450.0)