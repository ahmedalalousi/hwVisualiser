#!/usr/bin/env bash
# Script to rename files from US to UK English and update references

# Exit on error
set -e

# Set colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Print colored status messages
status() {
    echo -e "${GREEN}[+] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[!] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}"
    exit 1
}

# Check if running in a git repository
if [ ! -d .git ]; then
    error "This script must be run in the root of a git repository"
fi

# Create a new branch for UK English naming
status "Creating a new branch for UK English naming"
git checkout -b uk-english-naming || error "Failed to create new branch"

# Define file mappings (US to UK)
declare -A file_mappings=(
    ["visualize_hardware.py"]="visualise_hardware.py"
    ["hardware_inventory_visualization.html"]="hardware_inventory_visualisation.html"
)

# Create a backup directory
backup_dir="backup_us_english_$(date +%Y%m%d_%H%M%S)"
status "Creating backup directory: $backup_dir"
mkdir -p "$backup_dir" || error "Failed to create backup directory"

# Create .gitignore entry for backup directory if it doesn't exist
if ! grep -q "$backup_dir" .gitignore 2>/dev/null; then
    echo "# Backup directory for US English files" >> .gitignore
    echo "$backup_dir/" >> .gitignore
    status "Added backup directory to .gitignore"
fi

# Copy original files to backup directory
status "Creating backups of original files"
for us_file in "${!file_mappings[@]}"; do
    if [ -f "$us_file" ]; then
        cp "$us_file" "$backup_dir/" || warning "Failed to backup $us_file"
        status "Backed up $us_file to $backup_dir/"
    else
        warning "File $us_file not found, skipping backup"
    fi
done

# Update references in source files before renaming
status "Updating references in source files"

# Function to update references in a file
update_references() {
    local file=$1
    local old_pattern=$2
    local new_pattern=$3
    
    if [ -f "$file" ]; then
        # Create a temporary file
        tmp_file=$(mktemp)
        
        # Replace the pattern and write to temp file
        sed "s|$old_pattern|$new_pattern|g" "$file" > "$tmp_file"
        
        # Check if changes were made
        if cmp -s "$file" "$tmp_file"; then
            rm "$tmp_file"
            return 0  # No changes
        else
            mv "$tmp_file" "$file"
            return 1  # Changes made
        fi
    fi
}

# Update references in all Python files
find . -name "*.py" -type f | while read file; do
    # Skip backup directory
    if [[ "$file" == *"$backup_dir"* ]]; then
        continue
    fi
    
    # Update import statements
    update_references "$file" "from visualize_hardware import" "from visualise_hardware import"
    update_references "$file" "import visualize_hardware" "import visualise_hardware"
    
    # Update file references
    update_references "$file" "hardware_inventory_visualization.html" "hardware_inventory_visualisation.html"
    
    # Update other references
    update_references "$file" "visualization" "visualisation"
    update_references "$file" "Visualization" "Visualisation"
done

# Update README.md and other documentation
if [ -f "README.md" ]; then
    status "Updating README.md"
    update_references "README.md" "visualization" "visualisation"
    update_references "README.md" "Visualization" "Visualisation"
    update_references "README.md" "visualize_hardware\.py" "visualise_hardware.py"
fi

# Rename files using git
status "Renaming files with git"
for us_file in "${!file_mappings[@]}"; do
    uk_file="${file_mappings[$us_file]}"
    if [ -f "$us_file" ]; then
        git mv "$us_file" "$uk_file" || error "Failed to rename $us_file to $uk_file"
        status "Renamed $us_file to $uk_file"
    else
        warning "File $us_file not found, skipping rename"
    fi
done

# Check if any changes were made
if git diff --quiet && git diff --staged --quiet; then
    warning "No changes were made"
    exit 0
fi

# Commit changes
status "Committing changes"
git add . || error "Failed to stage changes"
git commit -m "Rename files from US to UK English spelling (visualization → visualisation)" || error "Failed to commit changes"

# Instructions for pushing
echo
status "Changes committed successfully!"
echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Test your code to make sure everything works:"
echo "   python visualise_hardware.py --input hardware_inventory.puml.txt --output test_output.html"
echo
echo "2. If everything works, push the changes to GitHub:"
echo "   git push -u origin uk-english-naming"
echo
echo "3. Create a pull request on GitHub and merge the changes"
echo
echo -e "${YELLOW}Your original files are backed up in: $backup_dir/${NC}"
echo "These won't be pushed to GitHub (they're in .gitignore)"

exit 0
