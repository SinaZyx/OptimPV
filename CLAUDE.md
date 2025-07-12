# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OptimPV is a comprehensive photovoltaic optimization application built with Streamlit. It provides financial analysis, visualization, and reporting capabilities for solar energy installations, with a focus on the French market.

## Commands

### Running the Application

```bash
# Activate virtual environment first
venv\Scripts\activate.bat  # Windows
source venv/bin/activate   # Linux/Mac

# Run the application
streamlit run app.py           # Direct Streamlit run
python launcher_fixed.py       # With license protection and port management
python run_secure.py          # Secure launcher wrapper
```

Default password: `panel123`

### Running Tests

The project uses unittest framework. Tests are organized in `/tests/` with unit, integration, and system categories:

```bash
# Run specific test module
python -m unittest tests.test_core_analyzer

# Run all repartition tests
python tests/run_all_repartition_tests.py

# Run specific repartition test category
python tests/run_all_repartition_tests.py models|validators|calculations|manager|integration

# Run placement tests
python tests/run_placement_tests.py

# Run navigation tests (Selenium-based)
python tests/run_navigation_tests.py

# Run ERP client tests
python -m unittest discover -s tests/test_erp_client -p "test_*.py"

# Run individual test file
python tests/test_[name].py
```

### Building for Production

```bash
# Production build with PyArmor protection
BUILD_WITH_PYARMOR.bat

# Quick build without PyArmor (for testing)
BUILD_QUICK_FIX.bat
```

Creates `dist\OptimPV_Final_Protected.exe` (~150-200 MB) with all dependencies and PyArmor protection.

### Installing Dependencies

```bash
pip install -r requirements.txt
```

## Architecture

### Core Structure

- **`app.py`** - Main Streamlit application entry point with page navigation
- **`launcher_fixed.py`** - Anti-loop launcher with automatic port detection (8501-8505)
- **`licence_guard.py`** - License verification system
- **`server_controller.py`** - Server control for OptimPV instances
- **`modules/`** - All application modules
  - **`engine_module/`** - Financial analysis engine (PyArmor protected in production)
    - `core_analyzer.py` - Main analysis logic with NPV, IRR calculations
    - `financial_calculations.py` - Financial computations and cash flow modeling
    - `tax_engine.py` - Tax calculations and optimization
    - `treasury_placement.py` - Treasury and investment management
    - `equity_calculations.py` - Equity-related calculations
    - `engine_utils.py` - Utility functions (also protected)
    - `data_processing.py` - Data processing utilities (also protected)
  - **`visualization/`** - Modern UI with theme support (Light/Dark/Corporate)
  - **`optimisation_analyse/`** - Solar optimization algorithms
  - **`prospect_mapping/`** - Geographic analysis with French cadastre integration
  - **`reporting/`** - DOCX/PDF report generation with commercial templates
  - **`storage/`** - Project persistence and data management
  - **`table_finance/`** - Financial table displays
  - **`facturation/`** - Billing module with SQLite database
  - **`repartition_keys/`** - Distribution key management for multi-entity projects
  - **`erp_client/`** - Enterprise resource planning client integration
  - **`historique/`** - Historical data management

### Data Flow

1. User inputs project parameters through Streamlit UI
2. `engine_module` performs financial calculations
3. Results are visualized through `visualization` module
4. Projects can be saved/loaded via `storage` module
5. Reports generated through `reporting` module

### Key Dependencies

- **Streamlit** - Web UI framework
- **Pandas/NumPy** - Data processing
- **Plotly/Pydeck/Folium** - Visualization and mapping
- **PyArmor** - Code protection for production
- **bcrypt** - Password hashing
- **python-docx** - Report generation
- **pyproj/shapely** - Geographic calculations
- **selenium** - Navigation testing

### Security Architecture

- Password-protected admin panel (`modules/security_config.py`)
- PyArmor protection on critical business logic
- License verification system (`licence_guard.py`)
- Token-based admin access (`create_token_admin.py`)

## Development Guidelines

### Module Structure

When adding new features:
1. Place business logic in appropriate module directory
2. Follow existing naming conventions (snake_case for files, PascalCase for classes)
3. Add tests in `/tests/` directory
4. Update visualization components if UI changes needed

### Protected Modules

These modules are PyArmor-protected in production builds:
- Complete `modules/engine_module/` directory (all files)
- `modules/optimisation_analyse/logique_optimisation.py`
- `modules/security_config.py`
- `launcher_fixed.py`

### State Management

The application uses Streamlit's session state extensively:
- `st.session_state.data` - Main project data
- `st.session_state.user_inputs` - User input parameters
- `st.session_state.results` - Calculation results
- `st.session_state.theme` - UI theme settings

### Port Management

The application automatically detects available ports (8501-8505) through `launcher_fixed.py` to prevent conflicts. If OptimPV is already running, new launches will just open the browser to the existing instance.

## Common Tasks

### Adding a New Analysis Module

1. Create module in `/modules/your_module/`
2. Add to `modules/__init__.py` if needed
3. Import in `app.py` or relevant parent module
4. Add tests in `/tests/test_your_module.py`
5. Update UI in `modules/visualization/` if needed

### Modifying Financial Calculations

1. Check `modules/engine_module/financial_calculations.py`
2. Ensure changes are compatible with `core_analyzer.py`
3. Update related tests in `/tests/test_core_analyzer.py`
4. Consider impact on reports in `modules/reporting/`

### Working with Cadastre Data

1. Prospect mapping logic in `modules/prospect_mapping/`
2. Uses French cadastre API for parcel data
3. DPE (energy performance) integration available
4. Coordinate transformations handled via pyproj

### Database Operations

- Billing database: `/data/billing.db` (SQLite)
- Project storage: `/projects/` directory (JSON files)
- Configuration storage: `/saved_configs/` directory

## Technical Solutions

### Known Issues and Solutions

1. **Streamlit Infinite Loops**: Resolved by using `os.execv()` instead of `subprocess.Popen()` in launcher
2. **PyArmor + Streamlit Conflicts**: Selective protection of critical modules only
3. **Import Errors (RGBColor, Document)**: Mock classes added when python-docx not available
4. **Development Mode**: Use `--global.developmentMode false` for proper port handling
5. **Port Detection**: Checks if OptimPV already running and opens browser to existing instance

### Build Process Details

The `BUILD_WITH_PYARMOR.bat` script:
1. Kills existing processes to ensure clean build
2. Activates virtual environment
3. Protects critical modules with PyArmor
4. Uses PyInstaller with specific options:
   - `--onefile`: Single executable
   - `--console`: Keep console visible for logs
   - `--add-data`: Include all necessary files
   - `--collect-all streamlit`: All Streamlit dependencies

## Important Notes

- No linting tools configured - maintain code style consistency manually
- The application targets Windows deployment primarily
- French market focus (UI elements, cadastre integration, tax calculations)
- Production builds require PyArmor license (already configured)
- Always test financial calculations thoroughly - they are business-critical
- Logging available in `optimpv_launcher.log` for debugging deployment issues
- Console window must remain open during runtime (closing it stops OptimPV)