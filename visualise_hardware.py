#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware Inventory Visualisation Script

This script combines the parsing and visualisation of hardware inventory data.
It parses PlantUML or CSV files and generates an interactive HTML visualisation.

Usage:
    python visualise_hardware.py --input <input_file_or_dir> --output <output_html>

Arguments:
    --input             Input PlantUML file or CSV directory
    --output            Output HTML file
    --input-type        Input type: 'puml' or 'csv' (default: auto-detect)
    --temp-dir          Directory for temporary files (default: system temp)
    --open-browser      Open the output HTML in a browser (default: False)
"""

import os
import sys
import argparse
import json
import tempfile
import shutil
import webbrowser
from pathlib import Path

# Import our PUML parser
from puml_to_json import parse_plantuml

# Try to import the CSV parser if available
try:
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from csv2PlantUML import HardwareInventory
    csv_parser_available = True
except ImportError:
    csv_parser_available = False

def process_csv_files(input_dir, temp_dir):
    """Process CSV files to extract hardware inventory data."""
    if not csv_parser_available:
        print("CSV parser (csv2PlantUML.py) not available.")
        return None
    
    # Find input files
    chasses_file = None
    fixed_inventory_file = None
    
    for file in Path(input_dir).glob('*.csv'):
        if file.name.lower() == 'chasses.csv':
            chasses_file = file
        elif file.name.lower() == 'fixed_inventory_file.csv':
            fixed_inventory_file = file
    
    if not chasses_file:
        print("Error: Could not find chasses.csv in the input directory.")
        return None
    
    if not fixed_inventory_file:
        print("Error: Could not find fixed_inventory_file.csv in the input directory.")
        return None
    
    # Generate PlantUML from CSV
    inventory = HardwareInventory()
    inventory.load_chasses_csv(chasses_file)
    inventory.load_fixed_inventory_file_csv(fixed_inventory_file)
    
    # Generate PlantUML file
    puml_output = os.path.join(temp_dir, 'hardware_inventory.puml')
    inventory.generate_plantuml(puml_output)
    
    # Parse the generated PlantUML
    return parse_plantuml(puml_output)

def generate_html(data, output_file):
    """Generate HTML visualisation from the data."""
    # Read the template HTML file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    template_path = os.path.join(script_dir, 'hardware_inventory_visualisation.html')
    
    if not os.path.exists(template_path):
        print(f"Error: Template file not found at {template_path}")
        # Generate a basic template if the file doesn't exist
        template_html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hardware Inventory Visualisation</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
    <style>
        /* CSS styles here */
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
        #visualisation { width: 100%; }
        /* More styles would be here */
    </style>
</head>
<body>
    <div id="visualisation">
        <h1>Hardware Inventory Visualisation</h1>
        <div id="content"></div>
    </div>
    <script>
        // Data will be loaded here
        const mockData = null;
        
        // JavaScript for visualisation would be here
        const data = mockData;
        console.log("Loaded data:", data);
        // Visualisation code would be here
    </script>
</body>
</html>"""
    else:
        with open(template_path, 'r', encoding='utf-8') as f:
            template_html = f.read()
    
    # Convert data to JSON string
    data_json = json.dumps(data, indent=2)
    
    # Fix for the data injection - look for the parseData function or mockData
    # First, try to find and replace the mock data directly
    if 'const mockData = {' in template_html:
        start_idx = template_html.find('const mockData = {')
        end_idx = template_html.find('};', start_idx) + 2
        
        if start_idx != -1 and end_idx != -1:
            modified_html = template_html[:start_idx] + f'const mockData = {data_json}' + template_html[end_idx:]
        else:
            # Fallback if we can't find proper markers
            modified_html = template_html.replace('parseData()', f'() => {{ return {data_json}; }}')
    else:
        # Try to modify the parseData function
        parse_data_start = template_html.find('async function parseData()')
        if parse_data_start != -1:
            try_block_start = template_html.find('try {', parse_data_start)
            return_stmt_idx = template_html.find('return mockData', try_block_start)
            
            if try_block_start != -1 and return_stmt_idx != -1:
                # Insert our data after the try block starts
                modified_part = f"""try {{
                // Data loaded from PlantUML/CSV files
                const mockData = {data_json};
                
                // No need to parse anything - data is already loaded
                """
                modified_html = template_html[:try_block_start] + modified_part + template_html[return_stmt_idx:]
            else:
                print("Warning: Couldn't find proper insertion points in the template.")
                # Last resort: inject a script tag at the beginning with our data
                modified_html = template_html.replace('<script>', f'<script>\n// Data loaded from PlantUML/CSV files\nconst mockData = {data_json};\n')
        else:
            print("Warning: Couldn't find parseData function in the template.")
            # Last resort: inject a script tag at the beginning with our data
            modified_html = template_html.replace('<script>', f'<script>\n// Data loaded from PlantUML/CSV files\nconst mockData = {data_json};\n')
    
    # Write the HTML file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(modified_html)
    
    print(f"Generated HTML visualisation: {output_file}")
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Generate interactive hardware inventory visualisation')
    parser.add_argument('--input', required=True, help='Input PlantUML file or CSV directory')
    parser.add_argument('--output', required=True, help='Output HTML file')
    parser.add_argument('--input-type', choices=['puml', 'csv'], help='Input type (default: auto-detect)')
    parser.add_argument('--temp-dir', help='Directory for temporary files')
    parser.add_argument('--open-browser', action='store_true', help='Open the output HTML in a browser')
    
    args = parser.parse_args()
    
    # Create temp directory if not provided
    temp_dir = args.temp_dir or tempfile.mkdtemp()
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    
    # Check if input exists
    if not os.path.exists(args.input):
        print(f"Error: Input '{args.input}' does not exist.")
        return 1
    
    # Create output directory if it doesn't exist
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Auto-detect input type if not specified
    input_type = args.input_type
    if not input_type:
        if os.path.isdir(args.input):
            input_type = 'csv'
        elif args.input.lower().endswith('.puml'):
            input_type = 'puml'
        else:
            print("Error: Could not auto-detect input type. Please specify --input-type.")
            return 1
    
    # Process input
    data = None
    if input_type == 'puml':
        data = parse_plantuml(args.input)
    elif input_type == 'csv':
        data = process_csv_files(args.input, temp_dir)
    
    if not data:
        print("Error: Failed to process input.")
        return 1
    
    # Generate HTML
    html_file = generate_html(data, args.output)
    
    # Open in browser if requested
    if args.open_browser:
        webbrowser.open('file://' + os.path.abspath(html_file))
    
    # Clean up temp directory
    if not args.temp_dir:  # Only remove if we created it
        shutil.rmtree(temp_dir)
    
    print("Visualisation completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
