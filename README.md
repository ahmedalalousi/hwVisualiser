# Hardware Inventory Visualisation

This project contains Python scripts to parse hardware inventory CSV files and generate interactive visualisations, allowing you to explore the relationship between hardware chassis, LPARs (Logical Partitions), and applications.

## 📋 Scripts Overview

This project includes two main scripts:

1. `parse_csv_to_diagrams.py` - Parses CSV files containing hardware inventory data and generates PlantUML and C4 diagram files
2. `generate_interactive_svg.py` - Converts PlantUML files into interactive SVG diagrams with drill-down capabilities

## 🔧 Requirements

- Python 3.6+
- Java Runtime Environment (JRE) - Required for PlantUML
- Internet connection (for automatically downloading PlantUML.jar if not provided)

## 📥 Installation

### Option 1: Using PyEnv (Recommended)

See the `pyenv_setup.md` file for detailed instructions on setting up a PyEnv virtual environment.

### Option 2: Manual Installation

1. Clone or download this repository
2. Install required Python packages:
   ```
   pip install -r requirements.txt
   ```

## 🚀 Usage Workflows

The tool supports several workflows depending on your needs:

### Standard Workflow: CSV → PlantUML → Interactive SVG

This is the most common workflow:

1. Start with your hardware inventory CSV files
2. Parse them into PlantUML diagrams
3. Generate an interactive SVG visualisation

```bash
# Step 1: Parse CSV files
python parse_csv_to_diagrams.py --input-dir ./data --output-dir ./diagrams

# Step 2: Generate interactive SVG
python generate_interactive_svg.py --input ./diagrams/hardware_inventory.puml --output ./visualisations/interactive_diagram.svg
```

### Batch Processing Workflow

For processing multiple files or generating multiple outputs:

```bash
# Generate all diagram types for all CSV files in a directory
python parse_csv_to_diagrams.py --input-dir ./data --output-dir ./diagrams --format both

# Generate interactive SVGs for all PlantUML files in a directory
python generate_interactive_svg.py --input ./diagrams --output ./visualisations/interactive_diagram.svg --pattern "*.puml"
```

### Integration Workflow

For integration with other tools or processes:

```bash
# Generate C4 diagrams only
python parse_csv_to_diagrams.py --input-dir ./data --output-dir ./diagrams --format c4

# Use a specific PlantUML jar
python generate_interactive_svg.py --input ./diagrams/hardware_inventory.puml --output ./vis/interactive.svg --plantuml-jar /path/to/plantuml.jar
```

## 📊 Use Cases

### 1. Hardware Infrastructure Documentation

Document and visualize your hardware infrastructure for documentation purposes:

```bash
python parse_csv_to_diagrams.py --input-dir ./inventory --output-dir ./docs/diagrams
python generate_interactive_svg.py --input ./docs/diagrams --output ./docs/infrastructure.svg
```

### 2. Application Deployment Analysis

Analyze application deployment across your infrastructure:

```bash
# Focus on application distribution
python parse_csv_to_diagrams.py --input-dir ./app_inventory --output-dir ./analysis
python generate_interactive_svg.py --input ./analysis/hardware_inventory.puml --output ./reports/app_distribution.svg
```

### 3. Capacity Planning

Use the visualisations to assist with capacity planning:

```bash
# Generate detailed diagrams showing resource allocation
python parse_csv_to_diagrams.py --input-dir ./current_state --output-dir ./capacity_planning
python generate_interactive_svg.py --input ./capacity_planning/hardware_inventory.puml --output ./capacity_planning/resource_allocation.svg
```

### 4. Migration Planning

Plan system migrations by visualizing current state:

```bash
# Generate diagrams for migration planning
python parse_csv_to_diagrams.py --input-dir ./pre_migration --output-dir ./migration_planning
python generate_interactive_svg.py --input ./migration_planning/hardware_inventory.puml --output ./migration_planning/current_state.svg
```

## 📝 Detailed Script Usage

### Step 1: Parse CSV Files to Generate Diagram Files

```
python parse_csv_to_diagrams.py --input-dir <input_directory> --output-dir <output_directory> [--format <plantuml|c4|both>]
```

**Arguments:**
- `--input-dir`: Directory containing the input CSV files (boii2.csv and sample BOI.csv)
- `--output-dir`: Directory where the output diagram files will be written
- `--format`: Output format: 'plantuml', 'c4', or 'both' (default: 'both')

**Example:**
```
python parse_csv_to_diagrams.py --input-dir ./data --output-dir ./diagrams --format both
```

This will generate files like:
- `./diagrams/hardware_inventory.puml` (PlantUML format)
- `./diagrams/hardware_inventory_c4.puml` (C4 format)

### Step 2: Generate Interactive SVG from PlantUML

```
python generate_interactive_svg.py --input <input_file_or_directory> --output <output_file> [options]
```

**Arguments:**
- `--input`: Input PlantUML file or directory containing PlantUML files
- `--output`: Output SVG file path
- `--plantuml-jar`: Path to plantuml.jar (optional, will download if not provided)
- `--temp-dir`: Directory for temporary files (optional)
- `--pattern`: File pattern to match when input is a directory (default: "*.puml")

**Example:**
```
python generate_interactive_svg.py --input ./diagrams/hardware_inventory.puml --output ./visualisations/interactive_diagram.svg
```

## 🖱️ Interactive SVG Features

The generated interactive SVG diagram provides the following features:

1. **System Overview**: Shows all chassis/systems at the top level
2. **Click to Explore**: Click on any component to view its details
3. **Drill-Down Navigation**: Click on child items to navigate deeper into the hierarchy
4. **Breadcrumb Navigation**: Navigate back up the hierarchy using breadcrumbs
5. **Detailed Information**: View detailed specifications and metadata for each component

### Interactive SVG Navigation Instructions

1. **Initial View**: The SVG opens with an overview of all chassis/systems
2. **Exploring Components**: 
   - Click on a chassis to view its details and see LPARs within it
   - Click on an LPAR to view its details and see applications it hosts
   - Click on an application group to see individual applications
3. **Using the Details Panel**:
   - View detailed information in the panel that appears when clicking on items
   - Use the breadcrumb trail at the top of the panel to navigate back up
   - Click the X in the top-right to close the panel
4. **Returning to Overview**: Click outside any component to return to the overview

## 📄 CSV File Requirements

The scripts expect two CSV files with specific information:

1. `boii2.csv` - Contains information about chassis (systems) and LPARs (logical partitions)
2. `sample BOI.csv` - Contains information about applications running on the LPARs

### Expected CSV Structure

**boii2.csv columns:**
- Name
- POR - Virtual Name
- POR - Virtual Name - use this ONE
- ID
- Status
- Environment
- OS Version
- Managed System Name
- Managed System Serial
- LPAR CPU
- LPAR MEM
- (other columns will be ignored)

**sample BOI.csv columns:**
- Component Name
- App type
- Component Version
- Product Name
- Product Metric
- Computer Name
- Installation Path
- (other columns will be ignored)

### Data Matching Logic

The scripts use the following logic to match applications to LPARs:

1. First attempt: Exact match between Computer Name and LPAR Name
2. Second attempt: Partial match (one is contained within the other)
3. If no match is found, the application will not be associated with any LPAR

## 🛠️ Customizing the Output

### Customizing PlantUML Output

You can modify the PlantUML styling in the generated `.puml` files before converting to SVG:

- Change colors by modifying the `skinparam` sections
- Adjust layout by modifying the component arrangements
- Add additional metadata or styling as needed

### Customizing the Interactive SVG

The interactive SVG includes JavaScript that can be modified:

- Edit the CSS styles in the `style` tag to change appearance
- Modify the JavaScript in the `script` tag to change behavior
- Add additional interactive features as needed

## ❓ Troubleshooting

- **Java not found**: Ensure Java is installed and available in your PATH
- **PlantUML download issues**: If you experience problems downloading PlantUML, manually download it from [the PlantUML website](https://plantuml.com/download) and specify its path using the `--plantuml-jar` argument
- **Matching issues**: If your applications aren't correctly matched to LPARs, check that the computer names in `sample BOI.csv` match or are similar to the LPAR names in `boii2.csv`
- **SVG not interactive**: Ensure you're opening the SVG in a modern web browser that supports JavaScript and SVG
- **Empty diagrams**: Verify that your input CSV files contain the expected data in the expected format

## 📁 Project Structure

```
hardware-inventory-viz/
├── parse_csv_to_diagrams.py    # CSV to PlantUML/C4 converter
├── generate_interactive_svg.py # PlantUML to interactive SVG converter
├── README.md                   # This file
├── pyenv_setup.md              # PyEnv setup instructions
├── requirements.txt            # Python dependencies
├── examples/                   # Example outputs
│   ├── sample_plantuml.puml    # Sample PlantUML output
│   ├── sample_c4.puml          # Sample C4 output
│   └── interactive_diagram.svg # Sample interactive SVG
├── data/                       # Sample input data (add your CSV files here)
│   ├── boii2.csv               # LPAR/system data
│   └── sample BOI.csv          # Application data
└── docs/                       # Documentation
    └── technical_details.tex   # LaTeX technical documentation
```

## 📋 Examples

The repository includes example outputs:
- `examples/sample_plantuml.puml` - Sample PlantUML output
- `examples/sample_c4.puml` - Sample C4 output
- `examples/interactive_diagram.svg` - Sample interactive SVG

## 📜 License

MIT License - See LICENSE file for details
# boiVisualiser
