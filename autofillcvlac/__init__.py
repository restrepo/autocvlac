"""
autofillcvlac - A Python package for processing research data and CVLaC information.
"""

__version__ = "0.1.0"

from .core import flatten, authenticate_cvlac, fill_scientific_article, filter_missing_journal_articles

__all__ = ["flatten", "authenticate_cvlac", "fill_scientific_article", "filter_missing_journal_articles", "__version__"]
