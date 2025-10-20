from . import core
from . import utils

# Expose main classes and functions at package level for easier imports
from .core import Network, calculate_power_distribution_ratios
from .utils import (
    build_admittance_matrix,
    reduce_matrix,
    Converter,
    import_pfd_file,
    BusLoadFlowResult
)

__version__ = "0.1.0"

__all__ = [
    "Network",
    "calculate_power_distribution_ratios",
    "build_admittance_matrix",
    "reduce_matrix",
    "Converter",
    "import_pfd_file",
    "BusLoadFlowResult",
    "core",
    "utils",
]