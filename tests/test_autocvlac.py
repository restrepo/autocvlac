"""
Basic tests for autocvlac package.
"""

import unittest
from autocvlac import flatten
from autocvlac.core import filter_products_by_year, authenticate_cvlac


class TestAutocvlac(unittest.TestCase):
    
    def test_flatten(self):
        """Test the flatten function."""
        nested = [[1, 2], [3, 4], [5]]
        result = flatten(nested)
        expected = [1, 2, 3, 4, 5]
        self.assertEqual(result, expected)
        
    def test_flatten_empty(self):
        """Test flatten with empty list."""
        result = flatten([])
        self.assertEqual(result, [])
        
    def test_filter_products_by_year(self):
        """Test filtering products by year."""
        products = [
            {
                "year_published": 2020,
                "external_ids": [{"provenance": "other"}]
            },
            {
                "year_published": 2000,
                "external_ids": [{"provenance": "other"}]
            },
            {
                "year_published": 2021,
                "external_ids": [{"provenance": "scienti"}]
            }
        ]
        
        result = filter_products_by_year(products, 2010)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["year_published"], 2020)
    
    def test_authenticate_cvlac_function_exists(self):
        """Test that authentication function exists and has correct signature."""
        # Just test that the function exists and can be called
        self.assertTrue(callable(authenticate_cvlac))
        # Test with None values to trigger early validation
        result = authenticate_cvlac(None, None)
        self.assertIn("status", result)
        self.assertIn("message", result)
        self.assertIn("session_active", result)


if __name__ == '__main__':
    unittest.main()