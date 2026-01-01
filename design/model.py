import FreeCAD as App
import Part
import sys
import os
import yaml
from os.path import join as join_path
import math

sys.path.append(join_path("~","ProjectAquarium"))

# paths
if __name__ == "__main__":  # Should be run from inside the project!!!
    # project name
    PROJECT_NAME = "ProjectAquarium"

    path = os.getcwd()
    while True:
        if os.path.basename(path) == PROJECT_NAME:
            PROJECT_PATH = path
            break

        parent = os.path.dirname(path)
        if parent == path:
            raise RuntimeError("ProjectAquarium not found")

        path = parent

def load_design_parameters(yaml_file):
    """Load intended parameters from YAML file"""
    with open(yaml_file, "r") as file:
        params = yaml.safe_load(file)
    return params['prism']

def load_constraints(yaml_file, part):
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


def create_right_triangle_wire(base_width, base_height, position):
    """Create a right-angle triangle wire for the prism base"""
    # Define the three vertices of the right triangle
    # Right angle at the origin position
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
            params['base_width'],
            params['base_height'],
            params['position']
        )
    else:
        raise ValueError(f"Unknown base_shape: {params['base_shape']}")
    
    # Create face from wire
    face = Part.Face(wire)
    
    # Extrude to create prism
    extrusion_vector = App.Vector(0, 0, params['height'])
    prism = face.extrude(extrusion_vector)
    
    return prism

    # Create face from wire
    face = Part.Face(wire)
    
    # Extrude to create prism
    extrusion_vector = App.Vector(0, 0, params['height'])
    prism = face.extrude(extrusion_vector)
    
    return prism


def main():
    # Load parameters from YAML
    yaml_file = join_path(PROJECT_PATH, "design", "existing_parts.yaml")
    aquarium_params = load_parameters(yaml_file)["aquarium"]

    # Parameters
    wedge_H = 20.0
    wedge_W = aquarium_params.main_box.y_inner * 0.99   # tolerance
    wedge_angle = 30    # deg

    # Create a new document
    doc = App.newDocument("PrismDoc")

    # Create the prism
    prism = create_prism(params)
    
    # Add prism to document
    prism_obj = doc.addObject("Part::Feature", "Prism")
    prism_obj.Shape = prism
    
    # Recompute document
    doc.recompute()
    
    # Save the document (optional)
    # doc.saveAs('prism_output.FCStd')
    
    print(f"Prism created successfully!")
    print(f"Base shape: {params['base_shape']}")
    if params['base_shape'] == 'polygon':
        print(f"Sides: {params['sides']}")
    print(f"Radius: {params['radius']} mm")
    print(f"Height: {params['height']} mm")


if __name__ == "__main__":
    main()

