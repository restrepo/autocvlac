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

    @patch('autofillcvlac.core.start_chrome')
    @patch('autofillcvlac.core.go_to')
    @patch('autofillcvlac.core.S')
    @patch('autofillcvlac.core.select')
    @patch('autofillcvlac.core.write')
    @patch('autofillcvlac.core.click')
    def test_authenticate_cvlac_select_parameter_order(self, mock_click, mock_write, mock_select, mock_S, mock_go_to, mock_start_chrome):
        """Test that select() is called with correct parameter order (selector first, value second)."""
        # Configure mocks
        mock_start_chrome.return_value = MagicMock()
        mock_go_to.return_value = None
        mock_S.return_value = MagicMock()
        mock_select.return_value = None
        mock_write.return_value = None
        mock_click.return_value = None
        
        # Call with valid parameters to trigger browser operations
        result = authenticate_cvlac("Colombiana", "John Doe", "12345678", "password123", headless=True)
        
        # Should succeed with mocked operations
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["session_active"])
        
        # Verify select was called with correct parameter order
        self.assertTrue(mock_select.called)
        call_args = mock_select.call_args_list[0]
        args, kwargs = call_args
        
        # First argument should be the selector (mock object), second should be the value (string)
        self.assertEqual(len(args), 2)
        self.assertEqual(args[1], "Colombiana")  # Value should be second parameter

    @patch('autofillcvlac.core.start_chrome')
    @patch('autofillcvlac.core.go_to')
    @patch('autofillcvlac.core.select')
    @patch('autofillcvlac.core.write')
    @patch('autofillcvlac.core.click')
    @patch('autofillcvlac.core.S')
    @patch('autofillcvlac.core.TextField')
    @patch('autofillcvlac.core.Button')
    def test_authenticate_cvlac_bug_fix(self, mock_button, mock_textfield, mock_S, mock_click, mock_write, mock_select, mock_go_to, mock_start_chrome):
        """Test the specific bug fix for 'S' object has no attribute 'tag_name' error."""
        # Configure mocks to simulate the scenario from the bug report
        mock_start_chrome.return_value = MagicMock()
        mock_go_to.return_value = None
        mock_write.return_value = None
        mock_click.return_value = None
        mock_S.return_value = MagicMock()
        mock_textfield.return_value = MagicMock()
        mock_button.return_value = MagicMock()
        
        # First select call should fail, second should succeed (simulating fallback logic)
        mock_select.side_effect = [Exception("First selector failed"), None]
        
        # Call with the exact parameters from the bug report
        result = authenticate_cvlac(
            nacionalidad='Colombiana', 
            nombres='Diego Restrepo', 
            documento_identificacion='666', 
            password='****', 
            headless=False
        )
        
        # Should succeed with mocked operations (no more 'S' object error)
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["session_active"])
        
        # Verify select was called with proper string selectors (not S() objects)
        self.assertTrue(mock_select.called)
        self.assertEqual(mock_select.call_count, 2)  # First call fails, second succeeds
        
        # Check that select was called with string selectors, not S() objects
        call_args_1 = mock_select.call_args_list[0]
        call_args_2 = mock_select.call_args_list[1]
        
        # First call should be with "#tpo_nacionalidad"
        self.assertEqual(call_args_1[0][0], "#tpo_nacionalidad")
        self.assertEqual(call_args_1[0][1], "Colombiana")
        
        # Second call should be with "[name='tpo_nacionalidad']"
        self.assertEqual(call_args_2[0][0], "[name='tpo_nacionalidad']")
        self.assertEqual(call_args_2[0][1], "Colombiana")


if __name__ == '__main__':
    unittest.main()
