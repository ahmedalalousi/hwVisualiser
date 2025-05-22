#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CSV to PlantUML/C4 Diagram Generator

This script parses hardware inventory CSV files, specifically chasses.csv and fixed_inventory_file.csv,
and generates PlantUML and C4 diagram files representing the hardware/software architecture.

Usage:
    python csv2PlantUML.py --input-dir <input_directory> --output-dir <output_directory> --format <plantuml|c4|both>

Arguments:
    --input-dir      Directory containing the input CSV files
    --output-dir     Directory where the output files will be written
    --format         Output format: 'plantuml', 'c4', or 'both'
"""

import os
import sys
import csv
import argparse
import re
from pathlib import Path
from collections import defaultdict


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
        self.all_applications = []  # All application records from CSV
        self.matched_applications = defaultdict(list)  # Applications matched to LPARs
        self.unmatched_applications = []  # Applications that couldn't be matched

    def load_chasses_csv(self, filename):
        """
        Load and parse the chasses CSV file containing LPAR and chassis information.
        This extracts ONLY the LPAR-to-chassis mapping and LPAR specifications.
        """
        print(f"Loading LPAR and chassis data from {filename}...")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                row_count = 0
                
                for row in reader:
                    row_count += 1
                    
                    # Extract system (chassis) information
                    system_name = row.get('Managed System Name', '').strip()
                    system_serial = row.get('Managed System Serial', '').strip()
                    
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
                    lpar_name = (row.get('POR - Virtual Name - use this ONE') or 
                                row.get('POR - Virtual Name') or 
                                row.get('Name', '')).strip()
                    
                    if not lpar_name:
                        continue
                    
                    # Parse CPU and memory values
                    try:
                        lpar_cpu = float(row.get('LPAR CPU', 0) or 0)
                    except (ValueError, TypeError):
                        lpar_cpu = 0.0
                    
                    try:
                        lpar_memory = float(row.get('LPAR MEM', 0) or 0)
                    except (ValueError, TypeError):
                        lpar_memory = 0.0
                    
                    # Create LPAR entry
                    lpar_id = str(row.get('ID', '')).strip()
                    lpar_data = {
                        'id': lpar_id,
                        'name': lpar_name,
                        'status': row.get('Status', '').strip(),
                        'environment': row.get('Environment', '').strip(),
                        'os_version': row.get('OS Version', '').strip(),
                        'cpu': lpar_cpu,
                        'memory': lpar_memory,
                        'system': system_name
                    }
                    
                    # Add LPAR to system and to overall LPAR dictionary
                    if lpar_name not in [existing_lpar for existing_lpar in self.systems[system_name]['lpars']]:
                        self.systems[system_name]['lpars'].append(lpar_name)
                        self.systems[system_name]['total_cpu'] += lpar_cpu
                        self.systems[system_name]['total_memory'] += lpar_memory
                    
                    self.lpars[lpar_name] = lpar_data
                    
            print(f"Processed {row_count} rows from chasses CSV")
            print(f"Loaded {len(self.systems)} chassis and {len(self.lpars)} LPARs")
            
        except Exception as e:
            print(f"Error loading chasses CSV: {e}")
            raise

    def load_fixed_inventory_file_csv(self, filename):
        """
        Load and parse the fixed inventory file CSV containing ALL application information.
        This processes every single application record.
        """
        print(f"Loading application data from {filename}...")
        
        try:
            with open(filename, 'r', encoding='utf-8-sig') as f:  # utf-8-sig automatically removes BOM
                reader = csv.DictReader(f)
                
                # Check what columns are actually available
                columns = reader.fieldnames
                print(f"Available columns in CSV: {columns}")
                
                # Clean column names by stripping BOM and whitespace
                cleaned_columns = [col.strip().lstrip('\ufeff') for col in columns]
                print(f"Cleaned column names: {cleaned_columns}")
                
                row_count = 0
                skipped_no_computer = 0
                skipped_no_component = 0
                sample_rows = []
                
                for row in reader:
                    row_count += 1
                    
                    # Store first 3 rows for debugging
                    if row_count <= 3:
                        sample_rows.append(dict(row))
                    
                    # Handle BOM in column names by trying both versions
                    computer_name = (row.get('Computer Name', '') or 
                                   row.get('\ufeffComputer Name', '') or '').strip()
                    
                    component_name = (row.get('Component Name', '') or 
                                    row.get('\ufeffComponent Name', '') or '').strip()
                    
                    # Skip rows without computer name (can't match to LPAR)
                    if not computer_name:
                        skipped_no_computer += 1
                        if skipped_no_computer <= 5:  # Show first 5 examples
                            print(f"  No computer name in row {row_count}: {dict(row)}")
                        continue
                    
                    # Skip rows without component name (not a real application)
                    if not component_name:
                        skipped_no_component += 1
                        if skipped_no_component <= 5:  # Show first 5 examples
                            print(f"  No component name in row {row_count}: {dict(row)}")
                        continue
                    
                    app_data = {
                        'computer': computer_name,
                        'name': component_name,
                        'type': (row.get('App type', '') or 'Unknown').strip(),
                        'version': (row.get('Component Version', '') or '').strip(),
                        'product': (row.get('Product Name', '') or '').strip(),
                        'metric': (row.get('Product Metric', '') or '').strip(),
                        'cloud_pak': (row.get('Cloud Pak or FlexPoint Bundle', '') or '').strip(),
                        'entitled': (row.get('Entitled', '') or '').strip(),
                        'charged': (row.get('Charged', '') or '').strip(),
                        'installation_path': (row.get('Installation Path', '') or '').strip()
                    }
                    
                    # Add to all applications list
                    self.all_applications.append(app_data)
                
                print(f"Processed {row_count} rows from applications CSV")
                print(f"Skipped {skipped_no_computer} rows with no computer name")
                print(f"Skipped {skipped_no_component} rows with no component name")
                print(f"Loaded {len(self.all_applications)} valid application records")
                
                # Show sample data for debugging
                if sample_rows:
                    print(f"\nFirst few rows of CSV data:")
                    for i, row in enumerate(sample_rows, 1):
                        print(f"Row {i}: {row}")
                
                # Now match applications to LPARs
                if self.all_applications:
                    self._match_apps_to_lpars()
                else:
                    print("Warning: No valid application records found to match")
                
        except Exception as e:
            print(f"Error loading fixed inventory file CSV: {e}")
            raise

    def _match_apps_to_lpars(self):
        """
        Enhanced matching of ALL applications to LPARs with comprehensive strategies.
        """
        print(f"\n=== Application Matching Process ===")
        print(f"Attempting to match {len(self.all_applications)} applications to {len(self.lpars)} LPARs")
        
        # Get unique computer names
        computer_to_apps = defaultdict(list)
        for app in self.all_applications:
            computer_to_apps[app['computer']].append(app)
        
        print(f"Found {len(computer_to_apps)} unique computer names")
        
        # Matching statistics
        matched_computers = 0
        matched_applications = 0
        strategy_stats = {
            'exact': 0,
            'case_insensitive': 0,
            'partial': 0,
            'vm_cleanup': 0,
            'domain_cleanup': 0
        }
        
        # Create lookup sets for faster matching
        lpar_names_lower = {name.lower(): name for name in self.lpars.keys()}
        
        for computer_name, apps in computer_to_apps.items():
            matched_lpar = None
            strategy_used = None
            
            # Strategy 1: Exact match
            if computer_name in self.lpars:
                matched_lpar = computer_name
                strategy_used = 'exact'
            
            # Strategy 2: Case-insensitive exact match
            elif computer_name.lower() in lpar_names_lower:
                matched_lpar = lpar_names_lower[computer_name.lower()]
                strategy_used = 'case_insensitive'
            
            # Strategy 3: Remove domain suffix and try again (e.g., "server.domain.com" -> "server")
            elif '.' in computer_name:
                clean_name = computer_name.split('.')[0]
                if clean_name in self.lpars:
                    matched_lpar = clean_name
                    strategy_used = 'domain_cleanup'
                elif clean_name.lower() in lpar_names_lower:
                    matched_lpar = lpar_names_lower[clean_name.lower()]
                    strategy_used = 'domain_cleanup'
            
            # Strategy 4: Clean VM names (remove VM prefix and leading zeros)
            if not matched_lpar and computer_name.upper().startswith('VM'):
                clean_name = computer_name[2:].lstrip('0')
                if clean_name and clean_name in self.lpars:
                    matched_lpar = clean_name
                    strategy_used = 'vm_cleanup'
                elif clean_name and clean_name.lower() in lpar_names_lower:
                    matched_lpar = lpar_names_lower[clean_name.lower()]
                    strategy_used = 'vm_cleanup'
            
            # Strategy 5: Partial matching (substring search)
            if not matched_lpar:
                for lpar_name in self.lpars.keys():
                    if (len(computer_name) > 3 and computer_name.lower() in lpar_name.lower()) or \
                       (len(lpar_name) > 3 and lpar_name.lower() in computer_name.lower()):
                        matched_lpar = lpar_name
                        strategy_used = 'partial'
                        break
            
            # Record the match or lack thereof
            if matched_lpar:
                self.matched_applications[matched_lpar].extend(apps)
                matched_computers += 1
                matched_applications += len(apps)
                strategy_stats[strategy_used] += 1
            else:
                self.unmatched_applications.extend(apps)
        
        # Print detailed statistics
        print(f"\nMatching Results:")
        if len(computer_to_apps) > 0:
            print(f"  Matched computers: {matched_computers}/{len(computer_to_apps)} ({matched_computers/len(computer_to_apps)*100:.1f}%)")
        else:
            print(f"  Matched computers: {matched_computers}/0 (no computers to match)")
            
        if len(self.all_applications) > 0:
            print(f"  Matched applications: {matched_applications}/{len(self.all_applications)} ({matched_applications/len(self.all_applications)*100:.1f}%)")
        else:
            print(f"  Matched applications: {matched_applications}/0 (no applications to match)")
            
        print(f"  Unmatched applications: {len(self.unmatched_applications)}")
        
        print(f"\nMatching strategies used:")
        for strategy, count in strategy_stats.items():
            if count > 0:
                print(f"  {strategy.replace('_', ' ').title()}: {count} computers")
        
        # Show examples of unmatched vs matched
        unmatched_computers = list(set(app['computer'] for app in self.unmatched_applications))
        matched_computer_names = list(computer_to_apps.keys() - set(unmatched_computers))
        
        if unmatched_computers:
            print(f"\nSample unmatched computers (first 10):")
            for comp in sorted(unmatched_computers)[:10]:
                app_count = len(computer_to_apps[comp])
                print(f"  - {comp} ({app_count} apps)")
        
        if matched_computer_names:
            print(f"\nSample matched computers (first 10):")
            for comp in sorted(matched_computer_names)[:10]:
                app_count = len(computer_to_apps[comp])
                print(f"  - {comp} ({app_count} apps)")
        
        print(f"\nSample LPAR names:")
        for lpar in sorted(self.lpars.keys())[:10]:
            print(f"  - {lpar}")

    def create_unmatched_lpar(self):
        """
        Create a special LPAR to hold unmatched applications for visualisation purposes.
        """
        if not self.unmatched_applications:
            return
        
        # Create a special system for unmatched applications
        unmatched_system_name = "UNMATCHED-APPLICATIONS"
        unmatched_lpar_name = "UnmatchedApplications"
        
        if unmatched_system_name not in self.systems:
            self.systems[unmatched_system_name] = {
                'serial': 'N/A',
                'model_type': 'Virtual',
                'model_number': 'Unmatched',
                'lpars': [],
                'total_cpu': 0,
                'total_memory': 0
            }
        
        # Create the unmatched LPAR
        self.lpars[unmatched_lpar_name] = {
            'id': 'unmatched',
            'name': unmatched_lpar_name,
            'status': 'Unmatched',
            'environment': 'Various',
            'os_version': 'Multiple',
            'cpu': 0,
            'memory': 0,
            'system': unmatched_system_name
        }
        
        self.systems[unmatched_system_name]['lpars'].append(unmatched_lpar_name)
        self.matched_applications[unmatched_lpar_name] = self.unmatched_applications
        
        print(f"Created special LPAR for {len(self.unmatched_applications)} unmatched applications")

    def generate_plantuml(self, output_file):
        """
        Generate a PlantUML diagram from the loaded data.
        """
        print(f"Generating PlantUML diagram to {output_file}...")
        
        # Create unmatched LPAR if there are unmatched applications
        self.create_unmatched_lpar()
        
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
            f.write("  BackgroundColor<<UnmatchedLPAR>> LightPink\n")
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
                
                # Write system rectangle header
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
                    
                    # Determine LPAR type for styling
                    lpar_type = "UnmatchedLPAR" if lpar_name == "UnmatchedApplications" else "LPAR"
                    
                    # Write LPAR rectangle header
                    lpar_string = (f"  rectangle \"{lpar_name}\\n"
                               f"CPU: {lpar.get('cpu', 0)}\\n"
                               f"Memory: {lpar.get('memory', 0)} GB\\n"
                               f"OS: {lpar.get('os_version', 'Unknown')}\" "
                               f"as {lpar_id} <<{lpar_type}>> {{\n")
                    f.write(lpar_string)
                    
                    # Get applications for this LPAR
                    lpar_apps = self.matched_applications.get(lpar_name, [])
                    
                    if lpar_apps:
                        # Group applications by type
                        app_types = defaultdict(list)
                        for app in lpar_apps:
                            app_types[app.get('type', 'Unknown')].append(app)
                        
                        # Generate application groups
                        for app_type, apps in app_types.items():
                            type_id = clean_id(f"{lpar_name}_{app_type}")
                            
                            # Write package header
                            f.write(f"    package \"{app_type} ({len(apps)})\" as {type_id} {{\n")
                            
                            # Limit components shown to keep diagram manageable
                            max_components = 5 if lpar_name == "UnmatchedApplications" else 10
                            
                            for i, app in enumerate(apps[:max_components]):
                                app_name = app.get('name', 'Unknown')
                                app_version = app.get('version', '')
                                app_id = clean_id(f"{lpar_name}_{app_name}_{i}")
                                
                                version_str = f" v{app_version}" if app_version else ""
                                # Escape quotes in app names
                                safe_app_name = app_name.replace('"', '\\"')
                                f.write(f"      component \"{safe_app_name}{version_str}\" as {app_id}\n")
                            
                            # Add "more" indicator if needed
                            if len(apps) > max_components:
                                remaining = len(apps) - max_components
                                note_id = clean_id(f"{lpar_name}_{app_type}_more")
                                f.write(f"      component \"... and {remaining} more\" as {note_id}\n")
                            
                            f.write("    }\n")
                    
                    f.write("  }\n")
                
                f.write("}\n\n")
            
            f.write("@enduml\n")
            
        print(f"PlantUML diagram generated successfully")

    def generate_c4(self, output_file):
        """
        Generate a C4 diagram from the loaded data.
        """
        print(f"Generating C4 diagram to {output_file}...")
        
        # Create unmatched LPAR if there are unmatched applications
        self.create_unmatched_lpar()
        
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
                
                # Write System_Boundary
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
                    
                    # Get applications for this LPAR and count by type
                    lpar_apps = self.matched_applications.get(lpar_name, [])
                    app_counts = defaultdict(int)
                    for app in lpar_apps:
                        app_counts[app.get('type', 'Unknown')] += 1
                    
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
            
        print(f"C4 diagram generated successfully")

    def analyse(self):
        """
        Print comprehensive analysis of the loaded data.
        """
        print("\n=== Data Analysis ===")
        
        print(f"Total Systems/Chassis: {len(self.systems)}")
        print(f"Total LPARs: {len(self.lpars)}")
        print(f"Total Application Records: {len(self.all_applications)}")
        print(f"Matched Applications: {sum(len(apps) for apps in self.matched_applications.values())}")
        print(f"Unmatched Applications: {len(self.unmatched_applications)}")
        
        # Count application types across all applications
        app_types = defaultdict(int)
        for app in self.all_applications:
            app_types[app.get('type', 'Unknown')] += 1
        
        print(f"\nApplication Types (across all {len(self.all_applications)} applications):")
        for app_type, count in sorted(app_types.items(), key=lambda x: x[1], reverse=True):
            print(f"  {app_type}: {count}")
        
        # System with most LPARs
        if self.systems:
            max_lpar_system = max(self.systems.items(), key=lambda x: len(x[1]['lpars']))
            print(f"\nSystem with most LPARs: {max_lpar_system[0]} ({len(max_lpar_system[1]['lpars'])} LPARs)")
        
        # LPAR with most applications
        if self.matched_applications:
            max_app_lpar = max(self.matched_applications.items(), key=lambda x: len(x[1]))
            print(f"LPAR with most applications: {max_app_lpar[0]} ({len(max_app_lpar[1])} apps)")


def main():
    parser = argparse.ArgumentParser(description='Generate PlantUML and C4 diagrams from hardware inventory CSV files.')
    parser.add_argument('--input-dir', required=True, help='Directory containing the input CSV files')
    parser.add_argument('--output-dir', required=True, help='Directory where the output files will be written')
    parser.add_argument('--format', choices=['plantuml', 'c4', 'both'], default='both', 
                        help='Output format: plantuml, c4, or both')
    
    args = parser.parse_args()
    
    # Check if input directory exists
    input_dir = Path(args.input_dir)
    if not input_dir.exists() or not input_dir.is_dir():
        print(f"Error: Input directory '{args.input_dir}' does not exist or is not a directory.")
        return 1
    
    # Create output directory if it doesn't exist
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find input files
    chasses_file = None
    fixed_inventory_file = None
    
    for file in input_dir.glob('*.csv'):
        if file.name.lower() == 'chasses.csv':
            chasses_file = file
        elif file.name.lower() == 'fixed_inventory_file.csv':
            fixed_inventory_file = file
    
    if not chasses_file:
        print("Error: Could not find chasses.csv in the input directory.")
        return 1
    
    if not fixed_inventory_file:
        print("Error: Could not find 'fixed_inventory_file.csv' in the input directory.")
        return 1
    
    # Load and process the data
    inventory = HardwareInventory()
    inventory.load_chasses_csv(chasses_file)
    inventory.load_fixed_inventory_file_csv(fixed_inventory_file)
    inventory.analyse()
    
    # Generate the diagrams
    if args.format in ['plantuml', 'both']:
        plantuml_output = output_dir / 'hardware_inventory.puml'
        inventory.generate_plantuml(plantuml_output)
    
    if args.format in ['c4', 'both']:
        c4_output = output_dir / 'hardware_inventory_c4.puml'
        inventory.generate_c4(c4_output)
    
    print("\nAll operations completed successfully.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
