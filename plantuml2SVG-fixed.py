#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PlantUML to Interactive SVG Generator

This script converts PlantUML diagram files into interactive SVG diagrams with drill-down
capabilities. It provides visualization of hardware inventory by chassis, with the ability
to click on components to see details and drill down into the hierarchy.

Usage:
    python plantuml2SVG.py --input <input_file_or_directory> --output <output_file> [options]

Arguments:
    --input           Input PlantUML file or directory containing PlantUML files
    --output          Output SVG file path
    --plantuml-jar    Path to plantuml.jar (optional, will download if not provided)
    --temp-dir        Directory for temporary files (optional)
    --pattern         File pattern to match when input is a directory (default: "*.puml")
"""

import os
import sys
import argparse
import subprocess
import tempfile
import shutil
import re
import glob
import json
import urllib.request
import traceback
from pathlib import Path
from xml.etree import ElementTree as ET

class PlantUMLProcessor:
    def __init__(self, plantuml_jar=None, temp_dir=None):
        self.temp_dir = temp_dir or tempfile.mkdtemp()

        # First try to find local plantuml installation from homebrew
        try:
            which_result = subprocess.run(['which', 'plantuml'],
                                          capture_output=True,
                                          text=True)

            if which_result.returncode == 0 and which_result.stdout.strip():
                self.use_local_command = True
                self.plantuml_command = which_result.stdout.strip()
                print(f"Using local PlantUML command: {self.plantuml_command}")
                return

        except Exception as e:
            print(f"Could not find local PlantUML command: {e}")

        # Fall back to JAR file approach
        self.use_local_command = False
        if plantuml_jar:
            self.plantuml_jar = plantuml_jar
        else:
            self.plantuml_jar = self._download_plantuml()

        print(f"Using PlantUML jar: {self.plantuml_jar}")
        print(f"Using temporary directory: {self.temp_dir}")

    def _download_plantuml(self):
        """
        Download the PlantUML jar file if it doesn't exist.
        """
        plantuml_path = os.path.join(self.temp_dir, "plantuml.jar")

        if not os.path.exists(plantuml_path):
            print("PlantUML jar not found. Downloading...")
            plantuml_url = "https://sourceforge.net/projects/plantuml/files/plantuml.jar/download"

            try:
                urllib.request.urlretrieve(plantuml_url, plantuml_path)
                print(f"Downloaded PlantUML jar to {plantuml_path}")

            except Exception as e:
                print(f"Error downloading PlantUML jar: {e}")
                print("Please provide the path to plantuml.jar using --plantuml-jar")
                sys.exit(1)

        return plantuml_path

    def generate_svg(self, input_file, output_file=None):
        """
        Generate an SVG file from a PlantUML file.
        """
        if not output_file:
            output_file = os.path.splitext(input_file)[0] + ".svg"

        try:
            # Make sure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)

            # Run PlantUML to generate the SVG
            if self.use_local_command:
                # Use local PlantUML command
                cmd = [self.plantuml_command, "-tsvg", input_file, "-o", os.path.dirname(output_file)]
            else:
                # Use Java with PlantUML JAR
                cmd = ["java", "-jar", self.plantuml_jar, "-tsvg", input_file, "-o", os.path.dirname(output_file)]

            print(f"Running command: {' '.join(cmd)}")

            # Use JAVA_OPTS to increase memory if needed
            env = os.environ.copy()
            env['JAVA_OPTS'] = "-Xmx1024m"  # Allocate up to 1GB of memory

            result = subprocess.run(cmd, capture_output=True, text=True, env=env)

            if result.returncode != 0:
                print(f"Error running PlantUML: {result.stderr}")
                return None

            # Check if the output file exists
            if not os.path.exists(output_file):
                # Try to find the output file in the same directory as the input file
                base_name = os.path.basename(os.path.splitext(input_file)[0])
                output_file = os.path.join(os.path.dirname(output_file), base_name + ".svg")

                if not os.path.exists(output_file):
                    print(f"Error: Could not find generated SVG file at {output_file}")
                    return None

            print(f"Generated SVG: {output_file}")
            return output_file

        except Exception as e:
            print(f"Error generating SVG: {e}")
            return None

    def _parse_plantuml(self, plantuml_file):
        """
        Parse a PlantUML file to extract the hierarchy structure.
        """
        print(f"Parsing PlantUML file: {plantuml_file}")
        
        hierarchy = {}
        current_path = []
        objects_by_id = {}  # Store all objects by ID for direct access
        
        try:
            with open(plantuml_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Skip empty lines and comments
                    if not line or line.startswith("'"):
                        continue
                    
                    # Extract rectangles, packages, and components (objects in the hierarchy)
                    rectangle_match = re.search(r'rectangle\s+"([^"]+)"\s+as\s+(\w+)', line)
                    if rectangle_match:
                        label, id_name = rectangle_match.groups()
                        
                        # Check if this is followed by an opening brace (has children)
                        has_children = line.endswith("{")
                        
                        # Extract metadata from the label (split by newline)
                        metadata = label.split("\\n")
                        name = metadata[0]
                        
                        # Check for stereotype to determine type
                        type_match = re.search(r'<<([^>]+)>>', line)
                        obj_type = type_match.group(1) if type_match else "rectangle"
                        
                        # Create object entry
                        obj = {
                            "id": id_name,
                            "name": name,
                            "type": obj_type,
                            "metadata": metadata[1:] if len(metadata) > 1 else [],
                            "children": []
                        }
                        
                        # Store in our lookup dictionary
                        objects_by_id[id_name] = obj
                        
                        # Add to hierarchy
                        if current_path:
                            # Find parent object and add this as a child
                            parent_id = current_path[-1]
                            if parent_id in objects_by_id:
                                objects_by_id[parent_id]["children"].append(obj)
                            else:
                                # If parent not found, add to root
                                hierarchy[id_name] = obj
                        else:
                            # Add as root object
                            hierarchy[id_name] = obj
                        
                        if has_children:
                            current_path.append(id_name)
                    
                    # Handle component definitions
                    component_match = re.search(r'component\s+"([^"]+)"\s+as\s+(\w+)', line)
                    if component_match:
                        label, id_name = component_match.groups()
                        
                        # Create component entry
                        obj = {
                            "id": id_name,
                            "name": label,
                            "type": "component",
                            "metadata": [],
                            "children": []  # Empty list for consistency
                        }
                        
                        # Store in our lookup dictionary
                        objects_by_id[id_name] = obj
                        
                        # Add to hierarchy
                        if current_path:
                            # Find parent object and add this as a child
                            parent_id = current_path[-1]
                            if parent_id in objects_by_id:
                                objects_by_id[parent_id]["children"].append(obj)
                            else:
                                # If parent not found, add to root
                                hierarchy[id_name] = obj
                        else:
                            # Add as root object
                            hierarchy[id_name] = obj
                    
                    # Handle package definitions
                    package_match = re.search(r'package\s+"([^"]+)"\s+as\s+(\w+)', line)
                    if package_match:
                        label, id_name = package_match.groups()
                        
                        # Check if this is followed by an opening brace (has children)
                        has_children = line.endswith("{")
                        
                        # Create package entry
                        obj = {
                            "id": id_name,
                            "name": label,
                            "type": "package",
                            "metadata": [],
                            "children": []
                        }
                        
                        # Store in our lookup dictionary
                        objects_by_id[id_name] = obj
                        
                        # Add to hierarchy
                        if current_path:
                            # Find parent object and add this as a child
                            parent_id = current_path[-1]
                            if parent_id in objects_by_id:
                                objects_by_id[parent_id]["children"].append(obj)
                            else:
                                # If parent not found, add to root
                                hierarchy[id_name] = obj
                        else:
                            # Add as root object
                            hierarchy[id_name] = obj
                        
                        if has_children:
                            current_path.append(id_name)
                    
                    # Handle closing braces (end of a container)
                    if line == "}":
                        if current_path:
                            current_path.pop()
            
            return hierarchy
            
        except Exception as e:
            print(f"Error parsing PlantUML file: {e}")
            traceback.print_exc()  # Print the full stack trace
            return {}
    
    def make_interactive(self, svg_file, plantuml_file, output_file):
        """
        Make the SVG interactive by adding JavaScript to enable drill-down capabilities.
        """
        print(f"Making SVG interactive: {svg_file}")
        
        try:
            # Parse the PlantUML file to get the hierarchy structure
            hierarchy = self._parse_plantuml(plantuml_file)
            if not hierarchy:
                print("Warning: Hierarchy is empty. The SVG may not be properly interactive.")
            
            # Make sure the output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_file)), exist_ok=True)
            
            # Parse the SVG file
            ET.register_namespace("", "http://www.w3.org/2000/svg")
            tree = ET.parse(svg_file)
            root = tree.getroot()
            
            # Get all group elements (these contain the diagram components)
            xmlns = {"svg": "http://www.w3.org/2000/svg"}
            groups = root.findall(".//svg:g", xmlns)
            
            # Keep track of element IDs and their positions/dimensions
            element_info = {}
            
            # Modify SVG to add interactive elements
            for g in groups:
                # Check if this group has an ID
                group_id = g.get("id")
                if not group_id:
                    continue
                
                # Find title element (contains the identifier from PlantUML)
                title = g.find(".//svg:title", xmlns)
                if title is not None and title.text:
                    # The title might contain the PlantUML ID
                    plantuml_id = title.text
                    
                    # Find matching element in hierarchy
                    for obj_id, obj_data in hierarchy.items():
                        if obj_id == plantuml_id or obj_id.lower() == plantuml_id.lower():
                            # Store element info
                            rect = g.find(".//svg:rect", xmlns) or g.find(".//svg:polygon", xmlns)
                            if rect is not None:
                                # Get element position and size
                                if rect.tag.endswith("rect"):
                                    x = float(rect.get("x", 0))
                                    y = float(rect.get("y", 0))
                                    width = float(rect.get("width", 0))
                                    height = float(rect.get("height", 0))
                                else:  # polygon
                                    # For polygons, calculate bounding box
                                    points = rect.get("points", "").split()
                                    x_values = []
                                    y_values = []
                                    for point in points:
                                        if "," in point:
                                            x_val, y_val = point.split(",")
                                            x_values.append(float(x_val))
                                            y_values.append(float(y_val))
                                    
                                    if x_values and y_values:
                                        x = min(x_values)
                                        y = min(y_values)
                                        width = max(x_values) - x
                                        height = max(y_values) - y
                                    else:
                                        x, y, width, height = 0, 0, 0, 0
                                
                                element_info[obj_id] = {
                                    "id": obj_id,
                                    "group_id": group_id,
                                    "x": x,
                                    "y": y,
                                    "width": width,
                                    "height": height,
                                    "data": obj_data
                                }
                                
                                # Add click handler
                                g.set("onclick", f"showDetails('{obj_id}')")
                                g.set("class", "clickable")
                                
                                # Add hover effect styling
                                if "style" in rect.attrib:
                                    rect.set("style", rect.get("style") + "; cursor: pointer;")
                                else:
                                    rect.set("style", "cursor: pointer;")
                            
                            break
            
            # Add JavaScript and CSS to make the SVG interactive
            # Create a script element
            script = ET.SubElement(root, "{http://www.w3.org/2000/svg}script")
            script.set("type", "text/javascript")
            
            # Create a style element
            style = ET.SubElement(root, "{http://www.w3.org/2000/svg}style")
            style.set("type", "text/css")
            style.text = """
                .clickable:hover rect, .clickable:hover polygon {
                    stroke: #ff0000;
                    stroke-width: 2;
                }
                #detailsPanel {
                    background-color: white;
                    border: 1px solid black;
                    border-radius: 5px;
                    padding: 10px;
                    position: absolute;
                    display: none;
                    max-width: 400px;
                    box-shadow: 3px 3px 10px rgba(0,0,0,0.3);
                }
                #detailsPanel h3 {
                    margin-top: 0;
                    border-bottom: 1px solid #ccc;
                    padding-bottom: 5px;
                }
                .detailRow {
                    margin-bottom: 5px;
                }
                .detailLabel {
                    font-weight: bold;
                }
                .closeButton {
                    position: absolute;
                    top: 5px;
                    right: 5px;
                    cursor: pointer;
                    font-weight: bold;
                }
                .childItem {
                    margin: 5px 0;
                    padding: 5px;
                    border: 1px solid #eee;
                    border-radius: 3px;
                    cursor: pointer;
                }
                .childItem:hover {
                    background-color: #f0f0f0;
                }
                .breadcrumbs {
                    margin-bottom: 10px;
                    padding: 5px;
                    background-color: #f0f0f0;
                    border-radius: 3px;
                }
                .breadcrumb {
                    cursor: pointer;
                    color: blue;
                    text-decoration: underline;
                    margin-right: 5px;
                }
                .breadcrumb:after {
                    content: " > ";
                    color: black;
                    text-decoration: none;
                }
                .breadcrumb:last-child:after {
                    content: "";
                }
            """
            
            # Create the HTML panel for displaying details
            foreignObject = ET.SubElement(root, "{http://www.w3.org/2000/svg}foreignObject")
            foreignObject.set("id", "detailsPanelContainer")
            foreignObject.set("x", "0")
            foreignObject.set("y", "0")
            foreignObject.set("width", "100%")
            foreignObject.set("height", "100%")
            foreignObject.set("style", "pointer-events: none;")
            
            div = ET.SubElement(foreignObject, "{http://www.w3.org/1999/xhtml}div")
            div.set("id", "detailsPanel")
            div.set("xmlns", "http://www.w3.org/1999/xhtml")
            
            # JavaScript content with hierarchy data and interactive functions
            js_content = f"""
                // Hierarchy data from PlantUML
                const hierarchyData = {json.dumps(hierarchy)};
                
                // Element position data
                const elementInfo = {json.dumps(element_info)};
                
                // Navigation path
                let currentPath = [];
                
                // Show details for an element
                function showDetails(id) {{
                    const element = elementInfo[id];
                    if (!element) return;
                    
                    const panel = document.getElementById('detailsPanel');
                    const data = element.data;
                    
                    // Build HTML content for the panel
                    let html = `<span class="closeButton" onclick="hideDetails()">×</span>
                               <h3>${{data.name}}</h3>`;
                    
                    // Add breadcrumbs for navigation
                    if (currentPath.length > 0) {{
                        html += '<div class="breadcrumbs">';
                        for (let i = 0; i < currentPath.length; i++) {{
                            const pathItem = currentPath[i];
                            if (elementInfo[pathItem]) {{
                                html += `<span class="breadcrumb" onclick="navigateTo(${{i}})">${{elementInfo[pathItem].data.name}}</span>`;
                            }}
                        }}
                        html += '</div>';
                    }}
                    
                    // Add metadata
                    if (data.metadata && data.metadata.length > 0) {{
                        html += '<div class="metadata">';
                        for (const meta of data.metadata) {{
                            const parts = meta.split(':');
                            if (parts.length > 1) {{
                                const label = parts[0].trim();
                                const value = parts.slice(1).join(':').trim();
                                html += `<div class="detailRow"><span class="detailLabel">${{label}}:</span> ${{value}}</div>`;
                            }} else {{
                                html += `<div class="detailRow">${{meta}}</div>`;
                            }}
                        }}
                        html += '</div>';
                    }}
                    
                    // Add child items if available
                    if (data.children && data.children.length > 0) {{
                        html += '<h4>Child Items:</h4>';
                        html += '<div class="childrenList">';
                        for (const child of data.children) {{
                            html += `<div class="childItem" onclick="drillDown('${{child.id}}')">
                                      <span class="childName">${{child.name}}</span>
                                      <span class="childType"> (${{child.type}})</span>
                                     </div>`;
                        }}
                        html += '</div>';
                    }}
                    
                    // Set panel content and position
                    panel.innerHTML = html;
                    
                    // Position the panel near the clicked element
                    const svgRect = document.querySelector('svg').getBoundingClientRect();
                    
                    panel.style.left = (element.x + element.width + 10) + 'px';
                    panel.style.top = element.y + 'px';
                    panel.style.display = 'block';
                }}
                
                // Hide the details panel
                function hideDetails() {{
                    const panel = document.getElementById('detailsPanel');
                    panel.style.display = 'none';
                }}
                
                // Drill down to a child element
                function drillDown(id) {{
                    if (!elementInfo[id]) return;
                    
                    // Add current element to path
                    if (currentPath.length === 0) {{
                        // If we're starting from root, find the parent first
                        for (const [parentId, info] of Object.entries(elementInfo)) {{
                            if (info.data.children && info.data.children.some(child => child.id === id)) {{
                                currentPath.push(parentId);
                                break;
                            }}
                        }}
                    }}
                    
                    // Add child to path
                    currentPath.push(id);
                    
                    // Show details for the child
                    showDetails(id);
                }}
                
                // Navigate to a specific level in the path
                function navigateTo(index) {{
                    if (index >= 0 && index < currentPath.length) {{
                        // Truncate the path to the selected index
                        currentPath = currentPath.slice(0, index + 1);
                        // Show details for the last item in the path
                        showDetails(currentPath[currentPath.length - 1]);
                    }}
                }}
                
                // Initialize with root elements
                document.addEventListener('DOMContentLoaded', function() {{
                    // Initialize panel
                    const panel = document.getElementById('detailsPanel');
                    panel.addEventListener('click', function(e) {{
                        e.stopPropagation();
                    }});
                    
                    // Add click handler to close panel when clicking outside
                    document.querySelector('svg').addEventListener('click', function(e) {{
                        if (!e.target.closest('.clickable')) {{
                            hideDetails();
                        }}
                    }});
                }});
            """
            
            script.text = js_content
            
            # Save the modified SVG
            tree.write(output_file, encoding="utf-8", xml_declaration=True)
            print(f"Created interactive SVG: {output_file}")
            
            return output_file
            
        except Exception as e:
            print(f"Error making SVG interactive: {e}")
            traceback.print_exc()  # Print the full stack trace
            return None
    
    def process_files(self, input_path, output_file, pattern="*.puml"):
        """
        Process PlantUML files to create an interactive SVG diagram.
        """
        if os.path.isdir(input_path):
            # Find all matching files in the directory
            input_files = glob.glob(os.path.join(input_path, pattern))
            
            if not input_files:
                print(f"Error: No files matching '{pattern}' found in '{input_path}'.")
                return False
            
            print(f"Found {len(input_files)} PlantUML files.")
            
            # Process the first file (for multi-file support, a more complex merge would be needed)
            input_file = input_files[0]
            print(f"Processing {input_file}")
            
            # Generate SVG from PlantUML
            temp_svg = os.path.join(self.temp_dir, os.path.basename(os.path.splitext(input_file)[0]) + ".svg")
            generated_svg = self.generate_svg(input_file, temp_svg)
            
            if not generated_svg:
                return False
            
            # Make the SVG interactive
            return self.make_interactive(generated_svg, input_file, output_file)
        else:
            # Process a single file
            if not os.path.exists(input_path):
                print(f"Error: Input file '{input_path}' does not exist.")
                return False
            
            # Generate SVG from PlantUML
            temp_svg = os.path.join(self.temp_dir, os.path.basename(os.path.splitext(input_path)[0]) + ".svg")
            generated_svg = self.generate_svg(input_path, temp_svg)
            
            if not generated_svg:
                return False
            
            # Make the SVG interactive
            return self.make_interactive(generated_svg, input_path, output_file)
    
    def cleanup(self):
        """
        Clean up temporary files and directories.
        """
        if os.path.exists(self.temp_dir) and self.temp_dir.startswith(tempfile.gettempdir()):
            shutil.rmtree(self.temp_dir)
            print(f"Cleaned up temporary directory: {self.temp_dir}")


def main():
    parser = argparse.ArgumentParser(description='Generate interactive SVG diagrams from PlantUML files.')
    parser.add_argument('--input', required=True, help='Input PlantUML file or directory')
    parser.add_argument('--output', required=True, help='Output SVG file path')
    parser.add_argument('--plantuml-jar', help='Path to plantuml.jar (optional, will download if not provided)')
    parser.add_argument('--temp-dir', help='Directory for temporary files (optional)')
    parser.add_argument('--pattern', default="*.puml", help='File pattern to match when input is a directory')
    
    args = parser.parse_args()
    
    # Create processor
    processor = PlantUMLProcessor(args.plantuml_jar, args.temp_dir)
    
    try:
        # Process the files
        success = processor.process_files(args.input, args.output, args.pattern)
        
        if success:
            print(f"Successfully created interactive SVG: {args.output}")
            print(f"Open this file in a web browser to view the interactive diagram.")
            return 0
        else:
            print("Failed to create interactive SVG.")
            return 1
    finally:
        # Clean up
        processor.cleanup()


if __name__ == '__main__':
    sys.exit(main())
