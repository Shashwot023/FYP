# FYP - SME Analytics Dashboard

This README provides instructions for setting up and running the SME Analytics Dashboard project.

## Prerequisites

- Python 3.10 or higher
- Git

## Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/Shashwot023/FYP.git
cd FYP
```

### 2. Set Up Environment

#### Option A: Using UV (Recommended)

```bash
# Install UV if not already installed
pip install uv

# Create a virtual environment
uv venv

# Activate the virtual environment
# On Linux/macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
uv pip sync pyproject.toml
```

#### Option B: Using pip

```bash
# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 3. Run the Application

```bash
# Make sure your virtual environment is activated
python app.py
```

### 4. Access the Dashboard

Open your web browser and navigate to:
```
http://127.0.0.1:8000
```

## Troubleshooting

- **Missing dependencies**: Ensure all packages from pyproject.toml are installed
- **Database errors**: Check if database.db file exists in the project root
- **Port already in use**: Change the port in app.py if 8000 is already in use

## Project Dependencies

This project uses several libraries including:
- FastAPI for the backend
- Plotly and Dash for visualizations
- Prophet for time series forecasting
- Pandas and NumPy for data processing

For the complete list of dependencies, refer to the pyproject.toml file.
