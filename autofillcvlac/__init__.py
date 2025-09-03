"""
autofillcvlac - A Python package for processing research data and CVLaC information.
"""

__version__ = "0.1.0"

from .core import flatten, authenticate_cvlac

__all__ = ["flatten", "authenticate_cvlac", "__version__"]
