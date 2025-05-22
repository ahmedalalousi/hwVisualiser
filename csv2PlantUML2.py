#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV to PlantUML/C4 Diagram Generator

This script parses hardware inventory CSV files and generates PlantUML and C4 diagram files 
representing the hardware/software architecture.

Usage:
    python csv2PlantUML.py --input <input_file_or_directory> --output <output_file_or_directory> --format <plantuml|c4|both>

Arguments:
    --input          Input CSV file or directory containing CSV files
    --output         Output file or directory where the output files will be written
    --format         Output format: 'plantuml', 'c4', or 'both'
    --boii2-pattern  Pattern to match BOII2-type files (default: '*boii2*.csv')
    --boi-pattern    Pattern to match BOI-type files (default: '*boi*.csv')
"""

import os
import sys
import csv
import argparse
import re
import glob
from pathlib import Path


def clean_id(text):
    """
    Convert a text string to a valid identifier by removing special characters
    and replacing spaces with underscores.
    """
    if not text:
        return "unknown"
    # Replace spaces and special characters
    clean = re.sub(r'[^a-zA-Z0-9]', '_', str(text))
    # Ensure it doesn't start with a number
    if clean and clean[0].isdigit():
        clean = 'id_' + clean
    return clean


class HardwareInventory:
    def __init__(self):
        self.systems = {}  # Chassis/systems
        self.lpars = {}    # Logical partitions
        self.apps = {}     # Applications

    def load_boii2_csv(self, filename):
        """
        Load and parse the BOII2 CSV file containing LPAR information.
        """
        print(f"Loading LPAR data from {filename}...")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Extract system (chassis) information
                    system_name = row.get('Managed System Name', '')
                    system_serial = row.get('Managed System Serial', '')
                    
                    if not system_name:
                        continue
                    
                    # Create system entry if it doesn't exist
                    if system_name not in self.systems:
                        # Parse model information from system name
                        system_parts = system_name.split('-')
                        model_type = system_parts[0] if system_parts else 'Unknown'
                        model_number = system_parts[1] if len(system_parts) > 1 else 'Unknown'
                        
                        self.systems[system_name] = {
                            'serial': system_serial,
                            'model_type': model_type,
                            'model_number': model_number,
                            'lpars': [],
                            'total_cpu': 0,
                            'total_memory': 0
                        }
                    
                    # Extract LPAR information
                    lpar_name = row.get('POR - Virtual Name - use this ONE') or \
                                row.get('POR - Virtual Name') or \
                                row.get('Name')
                    
                    if not lpar_name:
                        continue
                    
                    # Parse CPU and memory values
                    try:
                        lpar_cpu = float(row.get('LPAR CPU', 0))
                    except (ValueError, TypeError):
                        lpar_cpu = 0
                    
                    try:
                        lpar_memory = float(row.get('LPAR MEM', 0))
                    except (ValueError, TypeError):
                        lpar_memory = 0
                    
                    # Create LPAR entry
                    lpar_id = row.get('ID', '')
                    lpar_data = {
                        'id': lpar_id,
                        'name': lpar_name,
                        'status': row.get('Status', ''),
                        'environment': row.get('Environment', ''),
                        'os_version': row.get('OS Version', ''),
                        'cpu': lpar_cpu,
                        'memory': lpar_memory,
                        'system': system_name,
                        'applications': []
                    }
                    
                    # Add LPAR to system and to overall LPAR dictionary
                    self.systems[system_name]['lpars'].append(lpar_name)
                    self.systems[system_name]['total_cpu'] += lpar_cpu
                    self.systems[system_name]['total_memory'] += lpar_memory
                    self.lpars[lpar_name] = lpar_data
                    
            print(f"Loaded {len(self.systems)} systems and {len(self.lpars)} LPARs.")
            
        except Exception as e:
            print(f"Error loading BOII2 CSV: {e}")
            raise

    def load_sample_boi_csv(self, filename):
        """
        Load and parse the Sample BOI CSV file containing application information.
        """
        print(f"Loading application data from {filename}...")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Create a mapping from computer names to applications
                computer_apps = {}
                
                for row in reader:
                    computer_name = row.get('Computer Name', '')
                    
                    if not computer_name:
                        continue
                    
                    app_data = {
                        'name': row.get('Component Name', ''),
                        'type': row.get('App type', ''),
                        'version': row.get('Component Version', ''),
                        'product': row.get('Product Name', ''),
                        'metric': row.get('Product Metric', ''),
                        'computer': computer_name
                    }
                    
                    # Add application to computer's app list
                    if computer_name not in computer_apps:
                        computer_apps[computer_name] = []
                    
                    computer_apps[computer_name].append(app_data)
                    
                    # Add to global apps dictionary
                    app_id = f"{computer_name}_{clean_id(app_data['name'])}"
                    self.apps[app_id] = app_data
                
                # Match applications to LPARs based on name similarity
                self._match_apps_to_lpars(computer_apps)
                
            print(f"Loaded {len(self.apps)} applications.")
            
        except Exception as e:
            print(f"Error loading Sample BOI CSV: {e}")
            raise

    def _match_apps_to_lpars(self, computer_apps):
        """
        Match applications to LPARs based on name similarity.
        """
        matched_apps = 0
        unmatched_computers = []
        
        for computer_name, apps in computer_apps.items():
            matched = False
            
            # Try exact match first
            if computer_name in self.lpars:
                self.lpars[computer_name]['applications'].extend(apps)
                matched_apps += len(apps)
                matched = True
            else:
                # Try partial matching
                for lpar_name, lpar in self.lpars.items():
                    if (lpar_name.lower() in computer_name.lower() or 
                        computer_name.lower() in lpar_name.lower()):
                        lpar['applications'].extend(apps)
                        matched_apps += len(apps)
                        matched = True
                        break
            
            if not matched:
                unmatched_computers.append(computer_name)
        
        print(f"Matched {matched_apps} applications to LPARs.")
        if unmatched_computers:
            print(f"Could not match {len(unmatched_computers)} computers to LPARs.")

    def generate_plantuml(self, output_file):
        """
        Generate a PlantUML diagram from the loaded data.
        """
        print(f"Generating PlantUML diagram to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("@startuml\n")
            f.write("' Hardware Inventory Diagram\n")
            f.write("' Generated by csv2PlantUML.py\n\n")
            
            # Add title
            f.write("title Hardware Inventory Architecture\n\n")
            
            # Add styling
            f.write("' Styling\n")
            f.write("skinparam rectangle {\n")
            f.write("  BackgroundColor<<Chassis>> LightBlue\n")
            f.write("  BackgroundColor<<LPAR>> LightGreen\n")
            f.write("  BorderColor Black\n")
            f.write("  FontSize 12\n")
            f.write("}\n\n")
            f.write("skinparam component {\n")
            f.write("  BackgroundColor LightYellow\n")
            f.write("  BorderColor Black\n")
            f.write("  FontSize 10\n")
            f.write("}\n\n")
            
            # Generate diagram content for each system/chassis
            for system_name, system in self.systems.items():
                system_id = clean_id(system_name)
                
                # Write system rectangle header - all on one line to avoid issues
                system_string = (f"rectangle \"{system_name}\\n"
                            f"Model: {system['model_type']} {system['model_number']}\\n"
                            f"Serial: {system['serial']}\\n"
                            f"Total CPU: {system['total_cpu']}\\n"
                            f"Total Memory: {system['total_memory']} GB\" as {system_id} <<Chassis>> {{\n")
                f.write(system_string)
                
                # Add LPARs for this system
                for lpar_name in system['lpars']:
                    lpar = self.lpars.get(lpar_name, {})
                    lpar_id = clean_id(lpar_name)
                    
                    # Write LPAR rectangle header - all on one line to avoid issues
                    lpar_string = (f"  rectangle \"{lpar_name}\\n"
                               f"CPU: {lpar.get('cpu', 0)}\\n"
                               f"Memory: {lpar.get('memory', 0)} GB\\n"
                               f"OS: {lpar.get('os_version', 'Unknown')}\" "
                               f"as {lpar_id} <<LPAR>> {{\n")
                    f.write(lpar_string)
                    
                    # Add applications for this LPAR
                    app_types = {}
                    for app in lpar.get('applications', []):
                        app_type = app.get('type', 'Unknown')
                        if app_type not in app_types:
                            app_types[app_type] = []
                        app_types[app_type].append(app)
                    
                    # Group applications by type
                    for app_type, apps in app_types.items():
                        type_id = clean_id(f"{lpar_name}_{app_type}")
                        
                        # Write package header - all on one line to avoid issues
                        f.write(f"    package \"{app_type} ({len(apps)})\" as {type_id} {{\n")
                        
                        for app in apps:
                            app_name = app.get('name', 'Unknown')
                            app_version = app.get('version', '')
                            app_id = clean_id(f"{lpar_name}_{app_name}")
                            
                            version_str = f" v{app_version}" if app_version else ""
                            f.write(f"      component \"{app_name}{version_str}\" as {app_id}\n")
                        
                        f.write("    }\n")
                    
                    f.write("  }\n")
                
                f.write("}\n\n")
            
            f.write("@enduml\n")
            
        print(f"PlantUML diagram generated successfully.")

    def generate_c4(self, output_file):
        """
        Generate a C4 diagram from the loaded data.
        """
        print(f"Generating C4 diagram to {output_file}...")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("@startuml\n")
            f.write("' C4 Hardware Inventory Diagram\n")
            f.write("' Generated by csv2PlantUML.py\n\n")
            
            # Include C4 PlantUML macros
            f.write("!include https://raw.githubusercontent.com/plantuml-stdlib/C4-PlantUML/master/C4_Container.puml\n\n")
            
            # Add title
            f.write("title Hardware Inventory Architecture - C4 Diagram\n\n")
            
            # Define systems as System boundaries
            for system_name, system in self.systems.items():
                system_id = clean_id(system_name)
                description = f"Model: {system['model_type']} {system['model_number']}, "
                description += f"Serial: {system['serial']}, "
                description += f"CPU: {system['total_cpu']}, Memory: {system['total_memory']} GB"
                
                # Write System_Boundary - all on one line to avoid issues
                f.write(f"System_Boundary({system_id}, \"{system_name}\", \"{description}\") {{\n")
                
                # Add LPARs as Containers
                for lpar_name in system['lpars']:
                    lpar = self.lpars.get(lpar_name, {})
                    if not lpar:
                        continue
                        
                    lpar_id = clean_id(lpar_name)
                    lpar_desc = f"CPU: {lpar.get('cpu', 0)}, Memory: {lpar.get('memory', 0)} GB, "
                    lpar_desc += f"OS: {lpar.get('os_version', 'Unknown')}"
                    
                    f.write(f"  Container({lpar_id}, \"{lpar_name}\", \"LPAR\", \"{lpar_desc}\")\n")
                    
                    # Count applications by type
                    app_counts = {}
                    for app in lpar.get('applications', []):
                        app_type = app.get('type', 'Unknown')
                        app_counts[app_type] = app_counts.get(app_type, 0) + 1
                    
                    # Add application groups as Components
                    for app_type, count in app_counts.items():
                        app_group_id = clean_id(f"{lpar_name}_{app_type}")
                        app_group_desc = f"{count} applications"
                        
                        f.write(f"  Component({app_group_id}, \"{app_type}\", \"Application Group\", \"{app_group_desc}\")\n")
                        f.write(f"  Rel({lpar_id}, {app_group_id}, \"hosts\")\n")
                
                f.write("}\n\n")
            
            # Add legend
            f.write("SHOW_LEGEND()\n")
            f.write("@enduml\n")
            
        print(f"C4 diagram generated successfully.")

    def analyse(self):
        """
        Print analysis of the loaded data.
        """
        print("\n=== Data Analysis ===")
        
        print(f"Total Systems/Chassis: {len(self.systems)}")
        print(f"Total LPARs: {len(self.lpars)}")
        print(f"Total Applications: {len(self.apps)}")
        
        # Count application types
        app_types = {}
        for app in self.apps.values():
            app_type = app.get('type', 'Unknown')
            app_types[app_type] = app_types.get(app_type, 0) + 1
        
        print("\nApplication Types:")
        for app_type, count in sorted(app_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {app_type}: {count}")
        
        # System with most LPARs
        if self.systems:
            max_lpar_system = max(self.systems.items(), key=lambda x: len(x[1]['lpars']))
            print(f"\nSystem with most LPARs: {max_lpar_system[0]} ({len(max_lpar_system[1]['lpars'])} LPARs)")
        
        # LPAR with most applications
        if self.lpars:
            max_app_lpar = max(self.lpars.items(), key=lambda x: len(x[1].get('applications', [])))
            print(f"LPAR with most applications: {max_app_lpar[0]} ({len(max_app_lpar[1].get('applications', []))} apps)")


def find_csv_files(input_path, boii2_pattern='*boii2*.csv', boi_pattern='*boi*.csv'):
    """
    Find CSV files based on patterns. If input_path is a file, return it directly.
    If it's a directory, search for files matching the patterns.
    """
    input_path = Path(input_path)
    
    if input_path.is_file():
        # If it's a single file, determine its type based on filename
        filename_lower = input_path.name.lower()
        if 'boii2' in filename_lower:
            return [input_path], []
        elif 'boi' in filename_lower:
            return [], [input_path]
        else:
            # Try to guess based on content or return as potential boii2 file
            return [input_path], []
    
    elif input_path.is_dir():
        # Search for files matching patterns
        boii2_files = list(input_path.glob(boii2_pattern))
        boi_files = list(input_path.glob(boi_pattern))
        
        # If patterns don't match, try case-insensitive search
        if not boii2_files:
            for file in input_path.glob('*.csv'):
                if 'boii2' in file.name.lower():
                    boii2_files.append(file)
        
        if not boi_files:
            for file in input_path.glob('*.csv'):
                if 'boi' in file.name.lower() and 'boii2' not in file.name.lower():
                    boi_files.append(file)
        
        return boii2_files, boi_files
    
    else:
        raise FileNotFoundError(f"Input path '{input_path}' does not exist")


def process_csv_files(boii2_files, boi_files, output_path, format_type):
    """
    Process the CSV files and generate the requested output formats.
    """
    # Determine output file paths
    output_path = Path(output_path)
    
    if output_path.is_dir() or not output_path.suffix:
        # Output is a directory, generate standard filenames
        output_dir = output_path
        output_dir.mkdir(parents=True, exist_ok=True)
        plantuml_output = output_dir / 'hardware_inventory.puml'
        c4_output = output_dir / 'hardware_inventory_c4.puml'
    else:
        # Output is a file, use it as base for naming
        output_dir = output_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        base_name = output_path.stem
        plantuml_output = output_dir / f'{base_name}.puml'
        c4_output = output_dir / f'{base_name}_c4.puml'
    
    # Process each combination of BOII2 and BOI files
    if not boii2_files and not boi_files:
        print("Warning: No CSV files found to process.")
        return
    
    # If we have multiple files, process them in combinations
    processed_any = False
    
    for i, boii2_file in enumerate(boii2_files or [None]):
        for j, boi_file in enumerate(boi_files or [None]):
            
            # Skip if both are None
            if boii2_file is None and boi_file is None:
                continue
            
            # Create inventory instance
            inventory = HardwareInventory()
            
            # Load BOII2 file if available
            if boii2_file:
                try:
                    inventory.load_boii2_csv(boii2_file)
                except Exception as e:
                    print(f"Error loading {boii2_file}: {e}")
                    continue
            
            # Load BOI file if available
            if boi_file:
                try:
                    inventory.load_sample_boi_csv(boi_file)
                except Exception as e:
                    print(f"Error loading {boi_file}: {e}")
                    continue
            
            # If we have multiple files, adjust output names
            if len(boii2_files or []) > 1 or len(boi_files or []) > 1:
                suffix = f"_{i}_{j}" if boii2_file and boi_file else f"_{i if boii2_file else j}"
                current_plantuml = output_dir / f'{plantuml_output.stem}{suffix}.puml'
                current_c4 = output_dir / f'{c4_output.stem}{suffix}.puml'
            else:
                current_plantuml = plantuml_output
                current_c4 = c4_output
            
            # Analyse the loaded data
            inventory.analyse()
            
            # Generate the requested formats
            if format_type in ['plantuml', 'both']:
                try:
                    inventory.generate_plantuml(current_plantuml)
                    processed_any = True
                except Exception as e:
                    print(f"Error generating PlantUML: {e}")
            
            if format_type in ['c4', 'both']:
                try:
                    inventory.generate_c4(current_c4)
                    processed_any = True
                except Exception as e:
                    print(f"Error generating C4: {e}")
    
    return processed_any


def main():
    parser = argparse.ArgumentParser(description='Generate PlantUML and C4 diagrams from hardware inventory CSV files.')
    parser.add_argument('--input', required=True, 
                        help='Input CSV file or directory containing CSV files')
    parser.add_argument('--output', required=True, 
                        help='Output file or directory where the output files will be written')
    parser.add_argument('--format', choices=['plantuml', 'c4', 'both'], default='both', 
                        help='Output format: plantuml, c4, or both')
    parser.add_argument('--boii2-pattern', default='*boii2*.csv',
                        help='Pattern to match BOII2-type files (default: *boii2*.csv)')
    parser.add_argument('--boi-pattern', default='*boi*.csv',
                        help='Pattern to match BOI-type files (default: *boi*.csv)')
    
    args = parser.parse_args()
    
    try:
        # Find CSV files based on input
        boii2_files, boi_files = find_csv_files(args.input, args.boii2_pattern, args.boi_pattern)
        
        print(f"Found {len(boii2_files)} BOII2 files and {len(boi_files)} BOI files")
        
        if boii2_files:
            print("BOII2 files:", [str(f) for f in boii2_files])
        if boi_files:
            print("BOI files:", [str(f) for f in boi_files])
        
        # Process the files
        success = process_csv_files(boii2_files, boi_files, args.output, args.format)
        
        if success:
            print("\nAll operations completed successfully.")
            return 0
        else:
            print("\nNo files were successfully processed.")
            return 1
            
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
