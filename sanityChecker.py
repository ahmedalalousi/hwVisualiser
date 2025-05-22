#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PlantUML Sanity Checker

This script analyzes the generated PlantUML file and compares it with the source CSV files
to verify that the LPAR to chassis mapping and application assignments are correct.

Usage:
    python plantuml_sanity_checker.py --plantuml <plantuml_file> --chasses <chasses_csv> --apps <fixed_inventory_csv>
"""

import re
import argparse
import pandas as pd
from collections import defaultdict, Counter


class PlantUMLAnalyzer:
    def __init__(self):
        self.chassis_data = {}
        self.lpar_data = {}
        self.app_data = defaultdict(list)
        
    def parse_plantuml(self, plantuml_file):
        """Parse the PlantUML file and extract structure."""
        print(f"Analyzing PlantUML file: {plantuml_file}")
        
        with open(plantuml_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Extract chassis information
        chassis_pattern = r'rectangle\s+"([^"]+)\\nModel:\s+([^\\]+)\\nSerial:\s+([^\\]+)\\nTotal CPU:\s+([^\\]+)\\nTotal Memory:\s+([^\\]+)[^"]*"\s+as\s+(\w+)\s+<<Chassis>>'
        chassis_matches = re.findall(chassis_pattern, content)
        
        for match in chassis_matches:
            chassis_name, model, serial, total_cpu, total_memory, chassis_id = match
            
            # Parse CPU and memory values
            try:
                total_cpu = float(total_cpu)
            except ValueError:
                total_cpu = 0.0
            
            try:
                total_memory = float(total_memory.split()[0])  # Remove 'GB' if present
            except ValueError:
                total_memory = 0.0
            
            self.chassis_data[chassis_name] = {
                'id': chassis_id,
                'model': model,
                'serial': serial,
                'total_cpu': total_cpu,
                'total_memory': total_memory,
                'lpars': []
            }
        
        # Extract LPAR information
        lpar_pattern = r'rectangle\s+"([^"]+)\\nCPU:\s+([^\\]+)\\nMemory:\s+([^\\]+)\s*GB\\nOS:\s+([^"]+)"\s+as\s+(\w+)\s+<<LPAR>>'
        lpar_matches = re.findall(lpar_pattern, content)
        
        for match in lpar_matches:
            lpar_name, cpu, memory, os_version, lpar_id = match
            
            try:
                cpu = float(cpu)
            except ValueError:
                cpu = 0.0
            
            try:
                memory = float(memory)
            except ValueError:
                memory = 0.0
            
            self.lpar_data[lpar_name] = {
                'id': lpar_id,
                'cpu': cpu,
                'memory': memory,
                'os': os_version,
                'chassis': None,  # Will be determined by context
                'apps': []
            }
        
        # Extract application information
        package_pattern = r'package\s+"([^"]+)\s+\((\d+)\)"\s+as\s+(\w+)'
        component_pattern = r'component\s+"([^"]+)"\s+as\s+(\w+)'
        
        # Find packages (application groups)
        package_matches = re.findall(package_pattern, content)
        component_matches = re.findall(component_pattern, content)
        
        # Map chassis to LPARs by analyzing the nested structure
        self._map_chassis_to_lpars(content)
        
        print(f"Found {len(self.chassis_data)} chassis, {len(self.lpar_data)} LPARs")
        
        return self.chassis_data, self.lpar_data, self.app_data
    
    def _map_chassis_to_lpars(self, content):
        """Map LPARs to their parent chassis by analyzing the nested structure."""
        lines = content.split('\n')
        current_chassis = None
        brace_level = 0
        
        for line in lines:
            line = line.strip()
            
            # Find chassis start
            if '<<Chassis>>' in line and 'rectangle' in line:
                chassis_match = re.search(r'rectangle\s+"([^"]+)\\n', line)
                if chassis_match:
                    current_chassis = chassis_match.group(1)
                    brace_level = 0
            
            # Track brace levels
            if '{' in line:
                brace_level += line.count('{')
            if '}' in line:
                brace_level -= line.count('}')
                if brace_level <= 0:
                    current_chassis = None
            
            # Find LPARs within chassis
            if current_chassis and '<<LPAR>>' in line and 'rectangle' in line:
                lpar_match = re.search(r'rectangle\s+"([^"]+)\\n', line)
                if lpar_match:
                    lpar_name = lpar_match.group(1)
                    if lpar_name in self.lpar_data:
                        self.lpar_data[lpar_name]['chassis'] = current_chassis
                        if current_chassis in self.chassis_data:
                            self.chassis_data[current_chassis]['lpars'].append(lpar_name)


def load_csv_data(chasses_file, apps_file):
    """Load and return CSV data for comparison."""
    print(f"Loading CSV data from {chasses_file} and {apps_file}")
    
    # Load chassis data
    chasses_df = pd.read_csv(chasses_file)
    
    # Load application data
    apps_df = pd.read_csv(apps_file)
    
    return chasses_df, apps_df


def compare_chassis_data(plantuml_chassis, csv_chassis):
    """Compare chassis data between PlantUML and CSV."""
    print("\n=== CHASSIS COMPARISON ===")
    
    # Get unique chassis from CSV
    csv_chassis_names = set(csv_chassis['Managed System Name'].dropna().unique())
    plantuml_chassis_names = set(plantuml_chassis.keys())
    
    print(f"Chassis in CSV: {len(csv_chassis_names)}")
    print(f"Chassis in PlantUML: {len(plantuml_chassis_names)}")
    
    # Check for missing chassis
    missing_in_plantuml = csv_chassis_names - plantuml_chassis_names
    extra_in_plantuml = plantuml_chassis_names - csv_chassis_names
    
    if missing_in_plantuml:
        print(f"\nChassis in CSV but missing in PlantUML ({len(missing_in_plantuml)}):")
        for chassis in sorted(missing_in_plantuml):
            print(f"  - {chassis}")
    
    if extra_in_plantuml:
        print(f"\nChassis in PlantUML but not in CSV ({len(extra_in_plantuml)}):")
        for chassis in sorted(extra_in_plantuml):
            print(f"  - {chassis}")
    
    # Compare CPU and memory totals
    print(f"\n=== CPU/MEMORY VERIFICATION ===")
    for chassis_name in plantuml_chassis_names.intersection(csv_chassis_names):
        # Calculate totals from CSV
        chassis_lpars = csv_chassis[csv_chassis['Managed System Name'] == chassis_name]
        csv_total_cpu = chassis_lpars['LPAR CPU'].sum()
        csv_total_memory = chassis_lpars['LPAR MEM'].sum()
        
        # Get totals from PlantUML
        puml_total_cpu = plantuml_chassis[chassis_name]['total_cpu']
        puml_total_memory = plantuml_chassis[chassis_name]['total_memory']
        
        # Check for discrepancies
        cpu_diff = abs(csv_total_cpu - puml_total_cpu)
        mem_diff = abs(csv_total_memory - puml_total_memory)
        
        if cpu_diff > 0.1 or mem_diff > 0.1:  # Allow for small floating point differences
            print(f"\nDiscrepancy in {chassis_name}:")
            print(f"  CPU - CSV: {csv_total_cpu}, PlantUML: {puml_total_cpu} (diff: {cpu_diff})")
            print(f"  Memory - CSV: {csv_total_memory}, PlantUML: {puml_total_memory} (diff: {mem_diff})")


def compare_lpar_data(plantuml_lpars, csv_chassis):
    """Compare LPAR data between PlantUML and CSV."""
    print("\n=== LPAR COMPARISON ===")
    
    # Get LPAR names from CSV (using the preferred name column)
    csv_lpar_names = set()
    for _, row in csv_chassis.iterrows():
        lpar_name = (row.get('POR - Virtual Name - use this ONE') or 
                    row.get('POR - Virtual Name') or 
                    row.get('Name'))
        if pd.notna(lpar_name):
            csv_lpar_names.add(lpar_name)
    
    plantuml_lpar_names = set(plantuml_lpars.keys())
    
    print(f"LPARs in CSV: {len(csv_lpar_names)}")
    print(f"LPARs in PlantUML: {len(plantuml_lpar_names)}")
    
    # Check for missing LPARs
    missing_in_plantuml = csv_lpar_names - plantuml_lpar_names
    extra_in_plantuml = plantuml_lpar_names - csv_lpar_names
    
    if missing_in_plantuml:
        print(f"\nLPARs in CSV but missing in PlantUML ({len(missing_in_plantuml)}):")
        for lpar in sorted(list(missing_in_plantuml)[:10]):  # Show first 10
            print(f"  - {lpar}")
        if len(missing_in_plantuml) > 10:
            print(f"  ... and {len(missing_in_plantuml) - 10} more")
    
    if extra_in_plantuml:
        print(f"\nLPARs in PlantUML but not in CSV ({len(extra_in_plantuml)}):")
        for lpar in sorted(list(extra_in_plantuml)[:10]):  # Show first 10
            print(f"  - {lpar}")
        if len(extra_in_plantuml) > 10:
            print(f"  ... and {len(extra_in_plantuml) - 10} more")
    
    # Check CPU allocations for LPARs with 0 CPU
    zero_cpu_lpars = [name for name, data in plantuml_lpars.items() if data['cpu'] == 0]
    print(f"\nLPARs with 0 CPU in PlantUML: {len(zero_cpu_lpars)}")
    
    # Verify a sample of these against the CSV
    if zero_cpu_lpars:
        print("\nVerifying sample zero-CPU LPARs against CSV:")
        for lpar_name in zero_cpu_lpars[:5]:  # Check first 5
            csv_row = csv_chassis[
                (csv_chassis['POR - Virtual Name - use this ONE'] == lpar_name) |
                (csv_chassis['POR - Virtual Name'] == lpar_name) |
                (csv_chassis['Name'] == lpar_name)
            ]
            if not csv_row.empty:
                csv_cpu = csv_row.iloc[0]['LPAR CPU']
                csv_status = csv_row.iloc[0].get('Status', 'Unknown')
                print(f"  {lpar_name}: CSV CPU = {csv_cpu}, Status = {csv_status}")


def analyze_application_mapping(plantuml_lpars, apps_df):
    """Analyze application to LPAR mapping."""
    print("\n=== APPLICATION MAPPING ANALYSIS ===")
    
    # Get unique computer names from applications
    computer_names = set(apps_df['Computer Name'].dropna().unique())
    lpar_names = set(plantuml_lpars.keys())
    
    print(f"Unique computer names in applications: {len(computer_names)}")
    print(f"LPARs in PlantUML: {len(lpar_names)}")
    
    # Check exact matches
    exact_matches = computer_names.intersection(lpar_names)
    print(f"Exact name matches: {len(exact_matches)}")
    
    # Check partial matches (simulate the matching logic)
    partial_matches = 0
    unmatched_computers = []
    
    for comp_name in computer_names:
        matched = False
        # Try exact match first
        if comp_name in lpar_names:
            matched = True
        else:
            # Try partial matching
            for lpar_name in lpar_names:
                if (lpar_name.lower() in comp_name.lower() or 
                    comp_name.lower() in lpar_name.lower()):
                    partial_matches += 1
                    matched = True
                    break
        
        if not matched:
            unmatched_computers.append(comp_name)
    
    print(f"Additional partial matches: {partial_matches}")
    print(f"Unmatched computer names: {len(unmatched_computers)}")
    
    if unmatched_computers:
        print(f"\nSample unmatched computer names:")
        for comp in unmatched_computers[:10]:
            print(f"  - {comp}")
    
    # Show application distribution
    app_counts = apps_df.groupby('Computer Name').size().sort_values(ascending=False)
    print(f"\nTop 10 computers by application count:")
    print(app_counts.head(10))


def main():
    parser = argparse.ArgumentParser(description='Verify PlantUML generation against source CSV files')
    parser.add_argument('--plantuml', required=True, help='Generated PlantUML file')
    parser.add_argument('--chasses', required=True, help='Chasses CSV file')
    parser.add_argument('--apps', required=True, help='Fixed inventory CSV file')
    
    args = parser.parse_args()
    
    # Parse PlantUML file
    analyzer = PlantUMLAnalyzer()
    plantuml_chassis, plantuml_lpars, plantuml_apps = analyzer.parse_plantuml(args.plantuml)
    
    # Load CSV data
    csv_chassis, csv_apps = load_csv_data(args.chasses, args.apps)
    
    # Perform comparisons
    compare_chassis_data(plantuml_chassis, csv_chassis)
    compare_lpar_data(plantuml_lpars, csv_chassis)
    analyze_application_mapping(plantuml_lpars, csv_apps)
    
    print("\n=== SANITY CHECK COMPLETE ===")


if __name__ == '__main__':
    main()
