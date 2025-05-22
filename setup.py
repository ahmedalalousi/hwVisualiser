#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
boiVisualiser Setup Script

This script automates the setup process for the boiVisualiser project.
It handles:
- Checking for pyenv installation
- Installing pyenv via Homebrew on macOS if needed
- Setting up Python 3.13.3 via pyenv
- Creating a virtual environment
- Installing dependencies
- Cloning the repository if needed

Usage:
    python setup.py [--repo-dir <directory>] [--venv-name <name>]

Arguments:
    --repo-dir      Directory to clone/use the repository (default: ./boiVisualiser)
    --venv-name     Name for the virtual environment (default: boiVisualiser-env)
    --skip-clone    Skip cloning if repository already exists locally
"""

import os
import sys
import subprocess
import platform
import argparse
import shutil
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    BLUE = '\033[94m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_step(message):
    """Print a step message in blue."""
    print(f"{Colors.BLUE}{Colors.BOLD}[STEP]{Colors.END} {message}")

def print_success(message):
    """Print a success message in green."""
    print(f"{Colors.GREEN}{Colors.BOLD}[SUCCESS]{Colors.END} {message}")

def print_warning(message):
    """Print a warning message in yellow."""
    print(f"{Colors.YELLOW}{Colors.BOLD}[WARNING]{Colors.END} {message}")

def print_error(message):
    """Print an error message in red."""
    print(f"{Colors.RED}{Colors.BOLD}[ERROR]{Colors.END} {message}")

def run_command(command, shell=True, capture_output=True, text=True, check=False):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=shell, capture_output=capture_output, 
                              text=text, check=check)
        return result
    except subprocess.CalledProcessError as e:
        return e

def is_command_available(command):
    """Check if a command is available in the system PATH."""
    return shutil.which(command) is not None

def is_macos():
    """Check if the current system is macOS."""
    return platform.system() == "Darwin"

def check_pyenv():
    """Check if pyenv is installed and available."""
    print_step("Checking for pyenv installation...")
    
    if is_command_available("pyenv"):
        result = run_command("pyenv --version")
        if result.returncode == 0:
            print_success(f"pyenv is installed: {result.stdout.strip()}")
            return True
    
    print_warning("pyenv is not installed or not in PATH")
    return False

def check_homebrew():
    """Check if Homebrew is installed (macOS only)."""
    if not is_macos():
        return False
    
    print_step("Checking for Homebrew installation...")
    
    if is_command_available("brew"):
        result = run_command("brew --version")
        if result.returncode == 0:
            print_success("Homebrew is installed")
            return True
    
    print_warning("Homebrew is not installed")
    return False

def install_homebrew():
    """Install Homebrew on macOS."""
    print_step("Installing Homebrew...")
    print("This will install Homebrew. You may be prompted for your password.")
    
    install_cmd = '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
    result = run_command(install_cmd, capture_output=False)
    
    if result.returncode == 0:
        print_success("Homebrew installed successfully")
        
        # Add Homebrew to PATH for M1 Macs
        if platform.machine() == "arm64":
            print_step("Adding Homebrew to PATH for Apple Silicon Mac...")
            homebrew_path = '/opt/homebrew/bin'
            if homebrew_path not in os.environ.get('PATH', ''):
                os.environ['PATH'] = f"{homebrew_path}:{os.environ.get('PATH', '')}"
        
        return True
    else:
        print_error("Failed to install Homebrew")
        return False

def install_pyenv_macos():
    """Install pyenv via Homebrew on macOS."""
    print_step("Installing pyenv via Homebrew...")
    
    # Install pyenv and pyenv-virtualenv
    commands = [
        "brew install pyenv",
        "brew install pyenv-virtualenv"
    ]
    
    for cmd in commands:
        print(f"Running: {cmd}")
        result = run_command(cmd, capture_output=False)
        if result.returncode != 0:
            print_error(f"Failed to run: {cmd}")
            return False
    
    print_success("pyenv and pyenv-virtualenv installed via Homebrew")
    
    # Add pyenv to shell configuration
    setup_pyenv_shell()
    
    return True

def setup_pyenv_shell():
    """Add pyenv to shell configuration."""
    print_step("Setting up pyenv in shell configuration...")
    
    # Determine shell
    shell = os.environ.get('SHELL', '/bin/bash')
    shell_name = os.path.basename(shell)
    
    # Configuration lines to add
    pyenv_config = '''
# pyenv configuration
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
'''
    
    # Determine config file based on shell
    config_files = []
    if 'zsh' in shell_name:
        config_files = ['~/.zshrc', '~/.zprofile']
    elif 'bash' in shell_name:
        config_files = ['~/.bashrc', '~/.bash_profile']
    
    for config_file in config_files:
        config_path = Path(config_file).expanduser()
        if config_path.exists() or config_file == config_files[0]:  # Create first option if none exist
            try:
                with open(config_path, 'a') as f:
                    f.write(pyenv_config)
                print_success(f"Added pyenv configuration to {config_file}")
                break
            except Exception as e:
                print_warning(f"Could not write to {config_file}: {e}")
                continue
    
    print_warning("Please restart your terminal or run 'source ~/.zshrc' (or ~/.bashrc) to apply pyenv configuration")

def install_pyenv_linux():
    """Install pyenv on Linux."""
    print_step("Installing pyenv on Linux...")
    print("This will install pyenv using the official installer.")
    
    # Install pyenv
    install_cmd = 'curl https://pyenv.run | bash'
    result = run_command(install_cmd, capture_output=False)
    
    if result.returncode == 0:
        print_success("pyenv installed successfully")
        setup_pyenv_shell()
        return True
    else:
        print_error("Failed to install pyenv")
        return False

def prompt_pyenv_installation():
    """Prompt user for pyenv installation."""
    print_error("pyenv is required for this setup but is not installed.")
    
    if is_macos():
        print("\nFor macOS users:")
        print("1. First, we need to install Homebrew (if not already installed)")
        print("2. Then install pyenv via Homebrew")
        print("\nWould you like to proceed with automatic installation? (y/n): ", end="")
        
        response = input().lower().strip()
        if response in ['y', 'yes']:
            # Check/install Homebrew first
            if not check_homebrew():
                if not install_homebrew():
                    print_error("Cannot proceed without Homebrew")
                    return False
            
            # Install pyenv
            return install_pyenv_macos()
        else:
            print("\nTo install manually:")
            print("1. Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            print("2. Install pyenv: brew install pyenv pyenv-virtualenv")
            print("3. Add pyenv to your shell configuration")
            print("4. Restart your terminal and run this setup script again")
            return False
    else:
        print("\nFor Linux users:")
        print("Would you like to install pyenv automatically? (y/n): ", end="")
        
        response = input().lower().strip()
        if response in ['y', 'yes']:
            return install_pyenv_linux()
        else:
            print("\nTo install manually:")
            print("1. Run: curl https://pyenv.run | bash")
            print("2. Add pyenv to your shell configuration")
            print("3. Restart your terminal and run this setup script again")
            return False

def setup_python_version(version="3.13.3"):
    """Install and set up Python version via pyenv."""
    print_step(f"Setting up Python {version} via pyenv...")
    
    # Check if version is already installed
    result = run_command("pyenv versions")
    if result.returncode == 0 and version in result.stdout:
        print_success(f"Python {version} is already installed")
    else:
        print(f"Installing Python {version}... This may take a few minutes.")
        result = run_command(f"pyenv install {version}", capture_output=False)
        if result.returncode != 0:
            print_error(f"Failed to install Python {version}")
            return False
        print_success(f"Python {version} installed successfully")
    
    return True

def create_virtualenv(venv_name, python_version="3.13.3"):
    """Create a pyenv virtual environment."""
    print_step(f"Creating virtual environment '{venv_name}'...")
    
    # Check if virtualenv already exists
    result = run_command("pyenv versions")
    if result.returncode == 0 and venv_name in result.stdout:
        print_warning(f"Virtual environment '{venv_name}' already exists")
        response = input("Do you want to recreate it? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            run_command(f"pyenv virtualenv-delete -f {venv_name}")
        else:
            print_success(f"Using existing virtual environment '{venv_name}'")
            return True
    
    # Create new virtualenv
    result = run_command(f"pyenv virtualenv {python_version} {venv_name}")
    if result.returncode != 0:
        print_error(f"Failed to create virtual environment '{venv_name}'")
        return False
    
    print_success(f"Virtual environment '{venv_name}' created successfully")
    return True

def clone_repository(repo_url, repo_dir):
    """Clone the repository if it doesn't exist."""
    print_step(f"Setting up repository in {repo_dir}...")
    
    repo_path = Path(repo_dir)
    
    if repo_path.exists():
        if (repo_path / '.git').exists():
            print_success("Repository already exists locally")
            return True
        else:
            print_warning(f"Directory {repo_dir} exists but is not a git repository")
            response = input("Do you want to remove it and clone fresh? (y/n): ").lower().strip()
            if response in ['y', 'yes']:
                shutil.rmtree(repo_path)
            else:
                print_error("Cannot proceed with existing non-git directory")
                return False
    
    # Clone repository
    print(f"Cloning repository from {repo_url}...")
    result = run_command(f"git clone {repo_url} {repo_dir}", capture_output=False)
    
    if result.returncode == 0:
        print_success("Repository cloned successfully")
        return True
    else:
        print_error("Failed to clone repository")
        return False

def install_requirements(repo_dir, venv_name):
    """Install requirements in the virtual environment."""
    print_step("Installing Python dependencies...")
    
    requirements_file = Path(repo_dir) / "requirements.txt"
    
    if not requirements_file.exists():
        print_warning("requirements.txt not found, skipping dependency installation")
        return True
    
    # Activate virtualenv and install requirements
    activate_cmd = f"pyenv activate {venv_name}"
    install_cmd = f"pip install -r {requirements_file}"
    
    # Use pyenv exec to run in the virtualenv
    result = run_command(f"PYENV_VERSION={venv_name} pip install -r {requirements_file}", capture_output=False)
    
    if result.returncode == 0:
        print_success("Dependencies installed successfully")
        return True
    else:
        print_error("Failed to install dependencies")
        return False

def print_completion_instructions(repo_dir, venv_name):
    """Print final setup completion instructions."""
    print_success("Setup completed successfully!")
    print(f"\n{Colors.BOLD}Next steps:{Colors.END}")
    print(f"1. Navigate to the project directory: cd {repo_dir}")
    print(f"2. Activate the virtual environment: pyenv activate {venv_name}")
    print(f"3. You can now use the boiVisualiser tools:")
    print(f"   - Convert PlantUML to JSON: python puml_to_json.py --input <file.puml> --output <file.json>")
    print(f"   - Generate visualization: python visualise_hardware2.py --input <input> --output <output.html>")
    print(f"\n{Colors.BOLD}To deactivate the virtual environment later:{Colors.END}")
    print(f"   pyenv deactivate")
    print(f"\n{Colors.BOLD}Project directory:{Colors.END} {os.path.abspath(repo_dir)}")

def main():
    """Main setup function."""
    parser = argparse.ArgumentParser(description='Set up boiVisualiser project')
    parser.add_argument('--repo-dir', default='./boiVisualiser', 
                       help='Directory to clone/use the repository (default: ./boiVisualiser)')
    parser.add_argument('--venv-name', default='boiVisualiser-env',
                       help='Name for the virtual environment (default: boiVisualiser-env)')
    parser.add_argument('--skip-clone', action='store_true',
                       help='Skip cloning if repository already exists locally')
    
    args = parser.parse_args()
    
    print(f"{Colors.BOLD}boiVisualiser Setup Script{Colors.END}")
    print("=" * 50)
    
    # Step 1: Check/install pyenv
    if not check_pyenv():
        if not prompt_pyenv_installation():
            print_error("Setup cannot continue without pyenv")
            return 1
        
        # After installation, check again
        if not check_pyenv():
            print_error("pyenv installation verification failed")
            print_warning("You may need to restart your terminal and run this script again")
            return 1
    
    # Step 2: Setup Python version
    if not setup_python_version():
        return 1
    
    # Step 3: Create virtual environment
    if not create_virtualenv(args.venv_name):
        return 1
    
    # Step 4: Clone repository (if not skipped)
    if not args.skip_clone:
        repo_url = "https://github.com/ahmedalalousi/boiVisualiser.git"
        if not clone_repository(repo_url, args.repo_dir):
            return 1
    else:
        if not Path(args.repo_dir).exists():
            print_error(f"Repository directory {args.repo_dir} does not exist and --skip-clone was specified")
            return 1
        print_success(f"Using existing repository directory: {args.repo_dir}")
    
    # Step 5: Install requirements
    if not install_requirements(args.repo_dir, args.venv_name):
        return 1
    
    # Step 6: Print completion instructions
    print_completion_instructions(args.repo_dir, args.venv_name)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Setup interrupted by user{Colors.END}")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)
