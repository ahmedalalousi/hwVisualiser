# Hardware Inventory Visualisation

A comprehensive tool suite for visualising hardware inventory data from PlantUML diagrams or CSV files, providing an interactive HTML exploration of server infrastructure.

## 📋 Overview

This project provides tools to:

1. Parse hardware inventory data from PlantUML diagrams
2. Convert inventory data to JSON format
3. Generate interactive HTML visualisations
4. Allow exploration of hardware assets through a hierarchical interface

The system visualises hardware inventory at three levels:
- **Chassis**: Physical server hardware
- **LPARs** (Logical Partitions): Virtual machine instances
- **Applications**: Software running on each LPAR

## 🔧 Components

### 📜 Scripts and Their Functionality

#### 1. `puml_to_json.py`

This script parses a PlantUML hardware inventory diagram and converts it to JSON format for visualisation.

```bash
python puml_to_json.py --input <input_file> --output <output_file>
```

**Key Functionality**:
- Parses PlantUML syntax using regex patterns
- Extracts hierarchical data (chassis -> LPARs -> applications)
- Captures metadata like CPU, memory, OS versions, etc.
- Outputs structured JSON with complete inventory hierarchy

The parser processes:
- Chassis rectangles with attributes (name, model, serial, CPU, memory)
- LPAR rectangles inside each chassis
- Application packages and components
- Maintains proper parent-child relationships

#### 2. `visualise_hardware.py`

The main script that combines parsing and visualisation functions to produce an interactive HTML display.

```bash
python visualise_hardware.py --input <input_file_or_dir> --output <output_html>
```

**Arguments**:
- `--input`: Input PlantUML file or CSV directory
- `--output`: Output HTML file
- `--input-type`: Input type: 'puml' or 'csv' (default: auto-detect)
- `--temp-dir`: Directory for temporary files (default: system temp)
- `--open-browser`: Open the output HTML in a browser

**Key Functionality**:
- Determines input type (PlantUML or CSV)
- Calls appropriate parser based on input type
- Generates HTML using template
- Injects parsed JSON data into the HTML template
- Opens the result in a browser if requested

#### 3. `csv2PlantUML.py` (External Component)

An additional script that converts CSV inventory data to PlantUML format. This script:
- Processes standardised CSV inventory files (BOII2.csv and sample BOI.csv)
- Extracts hardware specifications and relationships
- Generates PlantUML diagrams representing the hardware inventory
- Creates a hierarchical structure similar to the final visualisation

### 🖥️ HTML Template Design

The project uses a responsive HTML template (`hardware_inventory_visualisation.html`) for visualising the hardware inventory data. Key features include:

1. **Interactive Layout**:
   - Responsive grid design for different screen sizes
   - Collapsible/expandable sections for exploring the hierarchy
   - Breadcrumb navigation for tracking current location

2. **Three-Level Hierarchy**:
   - Chassis level (top) - Physical servers
   - LPAR level (middle) - Virtual machines
   - Application level (bottom) - Software components

3. **Visual Design Elements**:
   - Color-coded sections for different hierarchy levels
   - Hover effects for interactive elements
   - Summary statistics and metadata displays
   - Loading indicators for data processing

4. **Technical Implementation**:
   - Pure JavaScript with no external dependencies (except D3.js for utilities)
   - CSS Grid and Flexbox for layout
   - Dynamic DOM creation based on JSON data
   - Event handlers for navigation and interaction

5. **Data Loading**:
   - Parses embedded JSON data injected by the Python script
   - Provides real-time filtering and navigation
   - Handles errors and empty states gracefully

### 📊 PlantUML Format

The PlantUML format used for hardware inventory follows this structure:

```
@startuml
title Hardware Inventory Architecture

skinparam rectangle {
  BackgroundColor<<Chassis>> LightBlue
  BackgroundColor<<LPAR>> LightGreen
  BorderColor Black
  FontSize 12
}

rectangle "CHASSIS-NAME\nModel: MODEL\nSerial: SERIAL\nTotal CPU: CPU\nTotal Memory: MEM GB" as CHASSIS_ID <<Chassis>> {
  rectangle "LPAR-NAME\nCPU: CPU\nMemory: MEM GB\nOS: OS_VERSION" as LPAR_ID <<LPAR>> {
    package "APPLICATION-TYPE (COUNT)" as APP_GROUP_ID {
      component "APP-NAME vVERSION" as APP_ID
    }
  }
}
@enduml
```

This format defines:
- Chassis (physical servers) as the top-level rectangles
- LPARs (logical partitions) as rectangles inside chassis
- Application groups as packages inside LPARs
- Individual applications as components inside packages

Each element includes metadata like CPU allocation, memory, OS version, etc.

### 📋 CSV to PlantUML Conversion Process

The CSV parsing functionality (provided by the external `csv2PlantUML.py` script) handles two primary file types:

1. **BOII2.csv**: Contains server hardware details
   - Chassis information (model, serial, etc.)
   - Physical specifications
   - Location data

2. **sample BOI.csv**: Contains LPAR and application data
   - LPAR specifications and OS versions
   - Applications installed on each LPAR
   - Software versions and counts

The conversion process:
1. Loads and parses both CSV files
2. Maps servers from BOII2 to LPARs in sample BOI
3. Builds a hierarchical model of the infrastructure
4. Generates PlantUML notation representing this hierarchy
5. Outputs a complete PlantUML file

This PlantUML file then serves as input for the visualisation pipeline.

## 📊 Use Cases

### 1. Hardware Infrastructure Documentation

Document and visualize your hardware infrastructure:

```bash
python puml_to_json.py --input hardware_inventory.puml --output inventory_data.json
python visualise_hardware.py --input hardware_inventory.puml --output infrastructure.html --open-browser
```

### 2. Application Deployment Analysis

Analyze application deployment across your infrastructure:

```bash
# Focus on application distribution
python visualise_hardware.py --input hardware_inventory.puml --output app_distribution.html
```

### 3. Capacity Planning

Use the visualisations to assist with capacity planning:

```bash
# Generate detailed visualisation showing resource allocation
python visualise_hardware.py --input hardware_inventory.puml --output resource_allocation.html
```

### 4. Migration Planning

Plan system migrations by visualizing current state:

```bash
# Generate visualisation for migration planning
python visualise_hardware.py --input pre_migration.puml --output current_state.html --open-browser
```

## 🖱️ Generated Visualisation

The final HTML visualisation provides:

1. **Overview Level**: Grid of all chassis/servers with key metrics
   - Total CPU and memory
   - LPAR count
   - Application count
   - Chassis model and serial information

2. **Chassis Level**: Detailed view of a selected chassis
   - List of all LPARs on the chassis
   - CPU and memory utilisation
   - OS distribution

3. **LPAR Level**: Detailed view of a selected LPAR
   - Applications installed
   - Application versions
   - CPU and memory allocation
   - OS version details

## 📝 Detailed Script Usage

### 1. Using `puml_to_json.py`

```
python puml_to_json.py --input <input_file> --output <output_file>
```

**Arguments:**
- `--input`: Input PlantUML file path
- `--output`: Output JSON file path

**Example:**
```
python puml_to_json.py --input ./diagrams/hardware_inventory.puml --output ./data/inventory_data.json
```

### 2. Using `visualise_hardware.py`

```
python visualise_hardware.py --input <input_file_or_dir> --output <output_html> [options]
```

**Arguments:**
- `--input`: Input PlantUML file or CSV directory
- `--output`: Output HTML file path
- `--input-type`: Input type: 'puml' or 'csv' (default: auto-detect)
- `--temp-dir`: Directory for temporary files (optional)
- `--open-browser`: Open the output HTML in a browser

**Example:**
```
python visualise_hardware.py --input ./diagrams/hardware_inventory.puml --output ./visualisations/interactive_diagram.html --open-browser
```

## 🚀 Usage Examples

### Converting PlantUML to JSON

```bash
python puml_to_json.py --input hardware_inventory.puml --output inventory_data.json
```

### Generating Visualisation from PlantUML

```bash
python visualise_hardware.py --input hardware_inventory.puml --output visualisation.html --open-browser
```

### Generating Visualisation from CSV Files

```bash
python visualise_hardware.py --input csv_directory/ --output visualisation.html --input-type csv
```

### Full Pipeline: CSV to Visualisation

```bash
# Step 1: Convert CSV to PlantUML (uses external csv2PlantUML.py)
python csv2PlantUML.py --boii2 BOII2.csv --boi "sample BOI.csv" --output inventory.puml

# Step 2: Generate visualisation from PlantUML
python visualise_hardware.py --input inventory.puml --output visualisation.html --open-browser
```

## 📥 Installation and Requirements

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hardware-inventory-visualisation.git
   cd hardware-inventory-visualisation
   ```

2. Requirements:
   - Python 3.6 or higher
   - Modern web browser for visualisation

No external Python packages are required as the scripts use only standard library modules.

## 🛠️ Development and Contribution

Contributions are welcome! Please feel free to submit pull requests or open issues to improve the tool.

### 📁 Project Structure

```
hardware-inventory-visualisation/
├── puml_to_json.py              # PlantUML to JSON converter
├── visualise_hardware.py        # Main visualisation script
├── hardware_inventory_visualisation.html  # HTML template
├── csv2PlantUML.py              # (External) CSV to PlantUML converter
├── examples/                    # Example files
│   ├── hardware_inventory.puml  # Example PlantUML file
│   ├── BOII2.csv               # Example server inventory CSV
│   └── sample BOI.csv          # Example LPAR/application CSV
└── README.md                    # This file
```

## ❓ Troubleshooting

If you encounter any issues while using this project, try these troubleshooting steps:

- **Missing template files**: Ensure all HTML and script files are in the correct locations
- **Parser errors**: Verify your PlantUML file follows the expected syntax
- **Visualisation not loading**: Check browser console for JavaScript errors
- **Empty output**: Verify input files contain valid data
- **Parsing errors**: Check if your PlantUML syntax is correct and follows the format shown in the PlantUML Format section

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
