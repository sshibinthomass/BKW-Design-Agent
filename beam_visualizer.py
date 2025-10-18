"""
Beam Visualization Library
Generates 3D beam visualizations from dimension data.
"""

import plotly.graph_objects as go
import numpy as np

def parse_dimension(dim_str, key_name):
    """Extract numeric value from dimension string (e.g., '5000 mm' -> 5000)"""
    if not isinstance(dim_str, str) or ' ' not in dim_str:
        raise ValueError(f"Invalid format for '{key_name}'. Expected a string like '500 mm'.")
    try:
        return float(dim_str.split()[0])
    except (ValueError, IndexError):
        raise ValueError(f"Could not parse numeric value from '{dim_str}' for key '{key_name}'.")

def get_material_color(material):
    """Return RGB color based on material type"""
    colors = {
        'Wood': 'rgb(139, 69, 19)',      # Brown
        'Concrete': 'rgb(128, 128, 128)', # Gray
        'Steel': 'rgb(70, 130, 180)'      # Steel Blue
    }
    return colors.get(material, 'rgb(150, 150, 150)')  # Default gray

def create_rectangular_beam_geometry(length, height, width):
    """
    Create rectangular beam 3D mesh geometry.
    
    Parameters:
    - length: beam length (along x-axis)
    - height: beam height (along z-axis)
    - width: beam width (along y-axis)
    
    Returns vertices and faces for 3D mesh.
    """
    half_width = width / 2
    
    # 8 vertices of the rectangular prism (X=Length, Y=Width, Z=Height)
    vertices = np.array([
        [0, -half_width, 0],      # 0: front-bottom-left
        [0, half_width, 0],       # 1: front-bottom-right
        [0, half_width, height],  # 2: front-top-right
        [0, -half_width, height], # 3: front-top-left
        [length, -half_width, 0],      # 4: back-bottom-left
        [length, half_width, 0],       # 5: back-bottom-right
        [length, half_width, height],  # 6: back-top-right
        [length, -half_width, height], # 7: back-top-left
    ])
    
    # 12 triangles (2 per face)
    faces = np.array([
        # Front face
        [0, 1, 2], [0, 2, 3],
        # Back face
        [4, 6, 5], [4, 7, 6],
        # Bottom face
        [0, 4, 5], [0, 5, 1],
        # Top face
        [3, 2, 6], [3, 6, 7],
        # Left face
        [0, 3, 7], [0, 7, 4],
        # Right face
        [1, 5, 6], [1, 6, 2],
    ])
    
    return vertices, faces

def create_i_beam_geometry(length, height, width):
    """
    Create I-beam 3D mesh geometry
    
    Parameters:
    - length: beam length (along x-axis)
    - height: beam height (along z-axis)
    - width: flange width (along y-axis)
    
    Returns vertices and faces for 3D mesh
    """
    # Calculate thicknesses
    flange_thickness = height / 10
    web_thickness = width / 10  # Web thickness is based on width now
    
    # I-beam cross-section coordinates (in Y-Z plane)
    # Starting from bottom-left, going counter-clockwise
    half_width = width / 2
    half_web = web_thickness / 2
    
    # Define the I-beam profile points (12 vertices for the cross-section)
    # The profile is in the Y-Z plane (Y=width, Z=height)
    profile = [
        # Bottom flange - left to right
        [-half_width, 0],                                    # 0: bottom-left
        [half_width, 0],                                     # 1: bottom-right
        [half_width, flange_thickness],                      # 2: bottom-right inner
        [half_web, flange_thickness],                        # 3: web bottom-right
        # Web - bottom to top
        [half_web, height - flange_thickness],               # 4: web top-right
        # Top flange - right to left
        [half_width, height - flange_thickness],             # 5: top-right inner
        [half_width, height],                                # 6: top-right
        [-half_width, height],                               # 7: top-left
        [-half_width, height - flange_thickness],            # 8: top-left inner
        # Web - top to bottom
        [-half_web, height - flange_thickness],              # 9: web top-left
        [-half_web, flange_thickness],                       # 10: web bottom-left
        [-half_width, flange_thickness],                     # 11: bottom-left inner
    ]
    
    # Create vertices by extruding profile along length
    vertices = []
    num_points = len(profile)
    
    # Front face (x=0)
    for y, z in profile:
        vertices.append([0, y, z])
    
    # Back face (x=length)
    for y, z in profile:
        vertices.append([length, y, z])
    
    vertices = np.array(vertices)
    
    # Create faces (triangles) for a non-convex I-beam shape
    faces = []
    
    # Decompose the I-beam profile into 3 rectangles and define triangles
    faces.extend([[0, 1, 11], [1, 2, 11]])
    faces.extend([[10, 3, 9], [3, 4, 9]])
    faces.extend([[8, 5, 7], [5, 6, 7]])

    back_offset = num_points
    faces.extend([[back_offset + 0, back_offset + 11, back_offset + 1], [back_offset + 1, back_offset + 11, back_offset + 2]])
    faces.extend([[back_offset + 10, back_offset + 9, back_offset + 3], [back_offset + 3, back_offset + 9, back_offset + 4]])
    faces.extend([[back_offset + 8, back_offset + 7, back_offset + 5], [back_offset + 5, back_offset + 7, back_offset + 6]])
    
    for i in range(num_points):
        next_i = (i + 1) % num_points
        faces.append([i, back_offset + i, next_i])
        faces.append([next_i, back_offset + i, back_offset + next_i])
    
    return vertices, faces, flange_thickness, web_thickness

def create_dimension_annotations(length, height, width, shape, flange_thickness=None, web_thickness=None):
    """Create dimension lines and text annotations"""
    annotations = []
    dimension_lines = []
    
    def add_dimension_line(start, end, text, color='black'):
        x_coords, y_coords, z_coords = [start[0], end[0]], [start[1], end[1]], [start[2], end[2]]
        dimension_lines.append(go.Scatter3d(x=x_coords, y=y_coords, z=z_coords, mode='lines', line=dict(color=color, width=4), showlegend=False, hoverinfo='skip'))
        mid_point = [(start[i] + end[i]) / 2 for i in range(3)]
        annotations.append(dict(x=mid_point[0], y=mid_point[1], z=mid_point[2], text=text, showarrow=False, font=dict(size=12, color=color), bgcolor='rgba(255, 255, 255, 0.8)', borderpad=4))
    
    offset = max(length, height, width) * 0.15
    
    add_dimension_line([0, -width/2 - offset, -offset], [length, -width/2 - offset, -offset], f'Length: {length:.1f} mm', 'red')
    add_dimension_line([length + offset, -width/2, height/2], [length + offset, width/2, height/2], f'Width: {width:.1f} mm', 'blue')
    add_dimension_line([-offset, 0, 0], [-offset, 0, height], f'Height: {height:.1f} mm', 'green')
    
    if shape == 'I-Beam':
        add_dimension_line([length/2, width/2 + offset, 0], [length/2, width/2 + offset, flange_thickness], f'Flange: {flange_thickness:.1f} mm', 'purple')
        web_thickness_half = web_thickness / 2
        add_dimension_line([length/2, -web_thickness_half, height/2], [length/2, web_thickness_half, height/2], f'Web: {web_thickness:.1f} mm', 'orange')
    
    return dimension_lines, annotations

def visualize_beam_from_data(data):
    """
    Main function to create 3D visualization from JSON data.
    Returns a Plotly Figure object.
    """
    material = data.get('Material', 'Unknown')
    length = parse_dimension(data.get('Length'), 'Length')
    height = parse_dimension(data.get('Height'), 'Height')
    width = parse_dimension(data.get('Width'), 'Width')
    load = data.get('Load', 'N/A')
    
    if material == 'Steel':
        shape = 'I-Beam'
        vertices, faces, flange_thickness, web_thickness = create_i_beam_geometry(length, height, width)
    else:
        shape = 'Rectangular'
        vertices, faces = create_rectangular_beam_geometry(length, height, width)
        flange_thickness, web_thickness = None, None
    
    color = get_material_color(material)
    
    # Convert numpy arrays to lists for proper JSON serialization
    mesh = go.Mesh3d(
        x=vertices[:, 0].tolist(), y=vertices[:, 1].tolist(), z=vertices[:, 2].tolist(),
        i=[f[0] for f in faces], j=[f[1] for f in faces], k=[f[2] for f in faces],
        color=color, opacity=0.9, name=f'{material} {shape}',
        hovertemplate='<b>%{fullData.name}</b><br>X: %{x:.1f} mm<br>Y: %{y:.1f} mm<br>Z: %{z:.1f} mm<br><extra></extra>',
        lighting=dict(ambient=0.5, diffuse=0.8, specular=0.5, roughness=0.5),
        lightposition=dict(x=100, y=200, z=300)
    )
    
    dimension_lines, annotations = create_dimension_annotations(length, height, width, shape, flange_thickness, web_thickness)
    
    fig = go.Figure(data=[mesh] + dimension_lines)
    
    fig.update_layout(
        title=dict(
            text=f'<b>{material} {shape} - 3D Interactive Visualization</b><br>' +
                 f'<sub>Length: {length}mm | Height: {height}mm | Width: {width}mm | Load: {load}</sub>',
            x=0.5, xanchor='center', font=dict(size=20)
        ),
        scene=dict(
            xaxis=dict(title='Length (mm)', backgroundcolor="rgb(230, 230,230)", gridcolor="white", showbackground=True),
            yaxis=dict(title='Width (mm)', backgroundcolor="rgb(230, 230,230)", gridcolor="white", showbackground=True),
            zaxis=dict(title='Height (mm)', backgroundcolor="rgb(230, 230,230)", gridcolor="white", showbackground=True),
            aspectmode='data',
            camera=dict(eye=dict(x=1.5, y=1.5, z=1.2), center=dict(x=0, y=0, z=0)),
            annotations=annotations
        ),
        width=1400, height=900, showlegend=True,
        legend=dict(x=0.02, y=0.98, bgcolor='rgba(255, 255, 255, 0.8)', bordercolor='black', borderwidth=1),
        paper_bgcolor='rgb(245, 245, 245)',
        margin=dict(l=0, r=0, t=100, b=0)
    )
    
    return fig
