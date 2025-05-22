# boiVisualiser Setup

## Quick Setup (Automated)

The easiest way to get started is to use the automated setup script:

```bash
# Download and run the setup script
curl -O https://raw.githubusercontent.com/ahmedalalousi/boiVisualiser/main/setup.py
python3 setup.py
```

This will automatically:
1. Check for pyenv installation (install if needed)
2. Set up Python 3.13.3 via pyenv
3. Create a virtual environment
4. Clone the repository
5. Install all dependencies

### Setup Script Options

```bash
python3 setup.py [options]

Options:
  --repo-dir DIRECTORY    Directory to clone the repository (default: ./boiVisualiser)
  --venv-name NAME       Name for virtual environment (default: boiVisualiser-env)
  --skip-clone           Skip cloning if repository already exists locally
```

### What the Setup Script Does

**For macOS users:**
- Checks for Homebrew installation (installs if needed)
- Installs pyenv and pyenv-virtualenv via Homebrew
- Configures your shell for pyenv

**For Linux users:**
- Installs pyenv using the official installer
- Configures your shell for pyenv

**For all platforms:**
- Installs Python 3.13.3 via pyenv
- Creates a dedicated virtual environment
- Clones the repository from GitHub
- Installs all required dependencies

## Manual Setup

If you prefer to set up manually:

### Prerequisites

1. **pyenv** (Python version manager)
   - macOS: `brew install pyenv pyenv-virtualenv`
   - Linux: `curl https://pyenv.run | bash`

2. **Python 3.13.3**
   ```bash
   pyenv install 3.13.3
   ```

### Installation Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ahmedalalousi/boiVisualiser.git
   cd boiVisualiser
   ```

2. **Create and activate virtual environment:**
   ```bash
   pyenv virtualenv 3.13.3 boiVisualiser-env
   pyenv activate boiVisualiser-env
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

After setup, activate your virtual environment and use the tools:

```bash
# Activate the virtual environment
pyenv activate boiVisualiser-env

# Convert PlantUML to JSON
python puml_to_json.py --input hardware.puml --output data.json

# Generate interactive visualization
python visualise_hardware.py --input hardware.puml --output visualization.html --open-browser
```

## Troubleshooting

### pyenv not found after installation
Restart your terminal or run:
```bash
# For zsh users
source ~/.zshrc

# For bash users  
source ~/.bashrc
```

### Permission errors on macOS
You may need to accept Xcode command line tools installation when prompted.

### Virtual environment activation issues
Make sure pyenv is properly configured in your shell:
```bash
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.zshrc
echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.zshrc  
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.zshrc
```
