import sys

from os.path import join as join_path
import yaml

import math

import FreeCAD as App
import Part

# Paths
PROJECT_NAME = "ProjectAquarium"
PROJECT_PATH = join_path("/home/inbarm",PROJECT_NAME)
sys.path.append(PROJECT_PATH)

# Constants
RAD_PER_DEG = 2*math.pi / 360

def load_design_parameters(yaml_file):
    """Load intended parameters from YAML file"""
    with open(yaml_file, "r") as file:
        params = yaml.safe_load(file)
    return params['prism']

def load_constraints(yaml_file):
    """Load external parameters from YAML file"""
    with open(yaml_file, "r") as file:
        params = yaml.safe_load(file)
    return params

def create_polygon_wire(sides, radius, position):
    """Create a polygon wire for the prism base"""
    points = []
    angle_step = 2 * math.pi / sides
    
    for i in range(sides):
        angle = i * angle_step
        x = position['x'] + radius * math.cos(angle)
        y = position['y'] + radius * math.sin(angle)
        z = position['z']
        points.append(App.Vector(x, y, z))
    
    # Close the polygon
    points.append(points[0])
    
    # Create edges and wire
    edges = [Part.LineSegment(points[i], points[i+1]).toShape() 
             for i in range(len(points)-1)]
    wire = Part.Wire(edges)
    
    return wire

def create_circle_wire(radius, position):
    """Create a circular wire for the prism base"""
    center = App.Vector(position['x'], position['y'], position['z'])
    normal = App.Vector(0, 0, 1)
    circle = Part.Circle(center, normal, radius)
    wire = Part.Wire([circle.toShape()])
    
    return wire


def create_right_triangle_wire(base_height, base_angle, position):
    """Create a right-angle triangle wire for the prism base
    
    Params:
        base_angle (float): measured in radians.
    """
    # Define the three vertices of the right triangle
    # Right angle at the origin position
    base_width = base_height * math.tan(base_angle)
    p1 = App.Vector(position['x'], position['y'], position['z'])
    p2 = App.Vector(position['x'] + base_width, position['y'], position['z'])
    p3 = App.Vector(position['x'], position['y'] + base_height, position['z'])
    
    # Create edges
    edge1 = Part.LineSegment(p1, p2).toShape()
    edge2 = Part.LineSegment(p2, p3).toShape()
    edge3 = Part.LineSegment(p3, p1).toShape()
    
    # Create wire
    wire = Part.Wire([edge1, edge2, edge3])
    
    return wire

def create_prism(params):
    """Create a prism based on parameters"""
    # Create base wire
    if params['base_shape'] == 'polygon':
        wire = create_polygon_wire(
            params['sides'], 
            params['radius'], 
            params['position']
        )
    elif params['base_shape'] == 'circle':
        wire = create_circle_wire(
            params['radius'], 
            params['position']
        )
    elif params['base_shape'] == 'right_triangle':
        wire = create_right_triangle_wire(
            base_height=params['base_height'],
            base_angle=params['base_angle'] * RAD_PER_DEG,
            position = params['position']
        )
    else:
        raise ValueError(f"Unknown base_shape: {params['base_shape']}")
    
    # Create face from wire
    face = Part.Face(wire)
    
    # Extrude to create prism
    extrusion_vector = App.Vector(0, 0, params['depth'])
    prism = face.extrude(extrusion_vector)
    
    if 'rotation' in params:
        rotation = params['rotation']
        center = App.Vector(
            params['position']['x'], 
            params['position']['y'], 
            params['position']['z']
            )
        
        # Apply rotations in order: Z, Y, X (standard euler angle order)
        if rotation.get('z', 0) != 0:
            prism.rotate(center, App.Vector(0, 0, 1), rotation['z'])
        if rotation.get('y', 0) != 0:
            prism.rotate(center, App.Vector(0, 1, 0), rotation['y'])
        if rotation.get('x', 0) != 0:
            prism.rotate(center, App.Vector(1, 0, 0), rotation['x'])

    return prism

def main():
    # Load parameters from YAML
    constraints_file = join_path(PROJECT_PATH, "design", "existing_parts.yaml")

    # Create a new document
    doc = App.newDocument("wedge")

    # Parameteres
    constraints_aq = load_constraints(constraints_file)["aquarium"]
    aq_inner_length = constraints_aq["main_box"]["x_inner"] * 0.99  # tolerance
    wedge_width = constraints_aq["main_box"]["y_inner"] * 0.99  # tolerance
    print(wedge_width)
    params = {
        'base_shape': 'right_triangle',
        'base_height': 20.0,    # mm
        'base_angle': 30.0,     # deg
        'depth': wedge_width,
        'position': {
            'x': -aq_inner_length/2,
            'y': -wedge_width/2,
            'z': 0
        },
        'rotation': {
            'x': -90,
            'y': 0,
            'z': 0
        }
    }
    
    # Create the prism
    wedge = create_prism(params)
    
    # Add prism to document
    prism_obj = doc.addObject("Part::Feature", "wedge")
    prism_obj.Shape = wedge
    
    # Recompute document
    doc.recompute()
    
    # Save the document (optional)
    # doc.saveAs('prism_output.FCStd')
    
    print(f"Prism created successfully!")
    print(f"Base shape: {params['base_shape']}")

if __name__ == "__main__":
    main()

