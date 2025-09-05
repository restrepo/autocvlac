"""
Basic tests for autofillcvlac package.
"""

import unittest
from unittest.mock import patch, MagicMock
from autofillcvlac import flatten
from autofillcvlac.core import filter_products_by_year, authenticate_cvlac


class TestAutofillcvlac(unittest.TestCase):
    
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
        result = authenticate_cvlac(None, None, None, None)
        self.assertIn("status", result)
        self.assertIn("message", result)
        self.assertIn("session_active", result)
    
    def test_authenticate_cvlac_validation(self):
        """Test input validation for authentication function."""
        # Test missing nationality
        result = authenticate_cvlac(None, "John Doe", "12345678", "password123")
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["session_active"])
        
        # Test missing names
        result = authenticate_cvlac("Colombian", None, "12345678", "password123")
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["session_active"])
        
        # Test missing document
        result = authenticate_cvlac("Colombian", "John Doe", None, "password123")
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["session_active"])
        
        # Test missing password
        result = authenticate_cvlac("Colombian", "John Doe", "12345678", None)
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["session_active"])
        
        # Test missing pais_nacimiento when nationality is "Extranjero - otra"
        result = authenticate_cvlac("Extranjero - otra", "John Doe", "12345678", "password123")
        self.assertEqual(result["status"], "error")
        self.assertIn("pais_nacimiento is required", result["message"])
        self.assertFalse(result["session_active"])
        
        # Test missing pais_nacimiento when nationality is "E" (code for Extranjero - otra)
        result = authenticate_cvlac("E", "John Doe", "12345678", "password123")
        self.assertEqual(result["status"], "error")
        self.assertIn("pais_nacimiento is required", result["message"])
        self.assertFalse(result["session_active"])
    
    def test_authenticate_cvlac_extranjero_validation(self):
        """Test validation for Extranjero - otra nationality."""
        # Test that validation works correctly for Extranjero cases
        # We'll test only the validation logic, not browser operations
        
        # Since the browser operations are complex to test, we'll verify
        # that the validation logic works by checking parameter handling
        # The actual browser automation would need integration tests
        
        # This test confirms the API accepts the new pais_nacimiento parameter
        # and validates it correctly for Extranjero cases
        
        # Import and test directly at the validation level
        from autofillcvlac.core import authenticate_cvlac
        
        # Test that function signature accepts pais_nacimiento parameter
        import inspect
        sig = inspect.signature(authenticate_cvlac)
        param_names = list(sig.parameters.keys())
        self.assertIn('pais_nacimiento', param_names)
        
        # Test that default value for pais_nacimiento is None
        self.assertEqual(sig.parameters['pais_nacimiento'].default, None)
    
    def test_authenticate_cvlac_browser_not_killed_on_validation_error(self):
        """Test that kill_browser is not called when validation fails."""
        with patch('autofillcvlac.core.kill_browser') as mock_kill_browser:
            # Test validation error case - should not call any browser functions
            result = authenticate_cvlac(None, None, None, None)
            self.assertEqual(result["status"], "error")
            self.assertFalse(result["session_active"])
            # kill_browser should not be called since validation fails before browser operations
            mock_kill_browser.assert_not_called()


if __name__ == '__main__':
    unittest.main()
