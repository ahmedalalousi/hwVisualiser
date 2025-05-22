#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hardware Inventory Visualisation Script

This script combines the parsing and visualisation of hardware inventory data.
It parses PlantUML or CSV files and generates an interactive HTML visualisation.

Usage:
    python visualise_hardware.py --input <input_file_or_dir> --output <output_html>

Arguments:
    --input             Input PlantUML file/directory or CSV directory
    --output            Output HTML file
    --input-type        Input type: 'puml' or 'csv' (default: auto-detect)
    --temp-dir          Directory for temporary files (default: system temp)
    --open-browser      Open the output HTML in a browser (default: False)
    --puml-pattern      Pattern to match PlantUML files (default: '*.puml')
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

def find_puml_files(input_path, pattern='*.puml'):
    """Find PlantUML files in the given path."""
    input_path = Path(input_path)
    
    if input_path.is_file():
        if input_path.suffix.lower() == '.puml':
            return [input_path]
        else:
            raise ValueError(f"File {input_path} is not a PlantUML file (.puml)")
    
    elif input_path.is_dir():
        puml_files = list(input_path.glob(pattern))
        if not puml_files:
            raise ValueError(f"No PlantUML files found in {input_path} matching pattern {pattern}")
        return puml_files
    
    else:
        raise FileNotFoundError(f"Input path '{input_path}' does not exist")

def process_puml_files(puml_files):
    """Process PlantUML files and combine their data."""
    all_data = {'chassis': []}
    
    for puml_file in puml_files:
        print(f"Processing PlantUML file: {puml_file}")
        try:
            data = parse_plantuml(puml_file)
            if data and 'chassis' in data:
                all_data['chassis'].extend(data['chassis'])
                print(f"Added {len(data['chassis'])} chassis from {puml_file}")
            else:
                print(f"Warning: No valid data found in {puml_file}")
        except Exception as e:
            print(f"Error processing {puml_file}: {e}")
            continue
    
    if not all_data['chassis']:
        print("Warning: No chassis data found in any PlantUML files")
        return None
    
    print(f"Total chassis loaded: {len(all_data['chassis'])}")
    return all_data

def find_csv_files(input_dir, boii2_pattern='*boii2*.csv', boi_pattern='*boi*.csv'):
    """Find CSV files based on patterns."""
    input_dir = Path(input_dir)
    
    # Search for files matching patterns
    boii2_files = list(input_dir.glob(boii2_pattern))
    boi_files = list(input_dir.glob(boi_pattern))
    
    # If patterns don't match, try case-insensitive search
    if not boii2_files:
        for file in input_dir.glob('*.csv'):
            if 'boii2' in file.name.lower():
                boii2_files.append(file)
    
    if not boi_files:
        for file in input_dir.glob('*.csv'):
            if 'boi' in file.name.lower() and 'boii2' not in file.name.lower():
                boi_files.append(file)
    
    return boii2_files, boi_files

def process_csv_files(input_dir, temp_dir):
    """Process CSV files to extract hardware inventory data."""
    if not csv_parser_available:
        print("CSV parser (csv2PlantUML.py) not available.")
        return None
    
    # Find input files using flexible patterns
    boii2_files, boi_files = find_csv_files(input_dir)
    
    if not boii2_files and not boi_files:
        print("Error: Could not find any BOII2 or BOI CSV files in the input directory.")
        return None
    
    # Process the first available combination
    boii2_file = boii2_files[0] if boii2_files else None
    boi_file = boi_files[0] if boi_files else None
    
    print(f"Using BOII2 file: {boii2_file}")
    print(f"Using BOI file: {boi_file}")
    
    # Generate PlantUML from CSV
    inventory = HardwareInventory()
    
    if boii2_file:
        inventory.load_boii2_csv(boii2_file)
    if boi_file:
        inventory.load_sample_boi_csv(boi_file)
    
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
    parser.add_argument('--input', required=True, help='Input PlantUML file/directory or CSV directory')
    parser.add_argument('--output', required=True, help='Output HTML file')
    parser.add_argument('--input-type', choices=['puml', 'csv'], help='Input type (default: auto-detect)')
    parser.add_argument('--temp-dir', help='Directory for temporary files')
    parser.add_argument('--open-browser', action='store_true', help='Open the output HTML in a browser')
    parser.add_argument('--puml-pattern', default='*.puml', help='Pattern to match PlantUML files (default: *.puml)')
    
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
            # Check if directory contains .puml files
            puml_files = list(Path(args.input).glob('*.puml'))
            csv_files = list(Path(args.input).glob('*.csv'))
            
            if puml_files and not csv_files:
                input_type = 'puml'
            elif csv_files and not puml_files:
                input_type = 'csv'
            elif puml_files and csv_files:
                print("Warning: Directory contains both PlantUML and CSV files. Defaulting to PlantUML.")
                input_type = 'puml'
            else:
                print("Error: Directory contains no recognisable files (.puml or .csv).")
                return 1
        elif args.input.lower().endswith('.puml'):
            input_type = 'puml'
        elif args.input.lower().endswith('.csv'):
            input_type = 'csv'
        else:
            print("Error: Could not auto-detect input type. Please specify --input-type.")
            return 1
    
    # Process input
    data = None
    try:
        if input_type == 'puml':
            puml_files = find_puml_files(args.input, args.puml_pattern)
            data = process_puml_files(puml_files)
        elif input_type == 'csv':
            if not os.path.isdir(args.input):
                print("Error: CSV input type requires a directory containing CSV files.")
                return 1
            data = process_csv_files(args.input, temp_dir)
    except Exception as e:
        print(f"Error during processing: {e}")
        return 1
    
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
