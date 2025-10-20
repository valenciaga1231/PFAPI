# About the tool

This tool provides a Python interface for building admittance matrices from PowerFactory network models for stability analysis. Tool simplifies the process of extracting network topology, reading element parameters, and constructing system matrices for power system stability analysis.

## Overview

The PowerFactory API tool reads network data from DIgSILENT PowerFactory models and converts them into structured Python objects that can be used for various power system analyses. The primary functionality includes:

- Reading network topology and busbar information
- Extracting electrical parameters of network elements
- Building complete admittance matrices (Y-bus)
- Supporting reduced network analysis (generator buses only) by Kron's reduction
- Calculating synchronizing power coefficients


## Getting Started

### Prerequisites

- DIgSILENT PowerFactory installed on your system
- Python 3.8 or higher
- Required Python packages (see `requirements.txt`)

### Installation

1. Clone or download this repository
2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Update the PowerFactory Python API path in your scripts (see examples)

### Install as a pip package from GitHub

You can also install this library directly as a pip package from GitHub:

```bash
pip install git+https://github.com/valenciaga1231/PFAPI.git
```

This will always install the latest version from the repository.

### Quick Start Example

Check the `examples` folder to get started:

1. **Update PowerFactory API Path**: Before running any examples, update the PowerFactory Python API path in the first cell of `examples/example_Ybus.ipynb`:
   
   ```python
   # Update this path to match your PowerFactory installation
   sys.path.append("C:/Program Files/DIgSILENT/PowerFactory 2024 SP4A/Python/3.12")
   ```

2. **Run the Example**: Open and run `examples/example_Ybus.ipynb` to see how to:
   - Initialize PowerFactory connection
   - Import network models
   - Build admittance matrices
   - Calculate synchronizing power coefficients

## Supported Network Elements

The PFAPI currently supports the following PowerFactory network elements:

### Element Classification

The tool automatically reads and classifies PowerFactory elements:
- `ElmLne`: Lines
- `ElmTr2`: Two-winding transformers
- `ElmTr3`: Three-winding transformers
- `ElmLod`: Loads
- `ElmSym`: Synchronous machines
- `ElmCoup`: Switches/couplers
- `ElmZpu`: Common impedance elements
- `ElmVac`: AC voltage sources
- `ElmShnt`: Shunt elements (partial)
- `ElmXnet`: External grids

## Project Structure

```
PFAPI/
├── README.md                          # Project documentation
├── requirements.txt                   # Python dependencies
├── src/pfapi/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── Network.py                 # Main network reader class
│   │   └── synchro_power_coefficients.py  # Power coefficient calculations
│   └── utils/
│       ├── AdmittanceMatrix.py        # Y-bus construction utilities
│       ├── Converter.py               # PF to internal object conversion
│       ├── Elements.py                # Network element definitions
│       ├── ImportModels.py            # Model import utilities
│       └── LoadFlowResults.py         # Load flow data handling
└── examples/
    ├── example_Ybus.ipynb             # Example script
    └── grid_models/
        ├── 39 Bus New England System.pfd    # IEEE 39-bus test system
        ├── Meshed Network.pfd               # Meshed network example
        ├── Radial System.pfd                # Radial network example
        └── Simple Mesh 5-bus.pfd            # Simple 5-bus test case
```