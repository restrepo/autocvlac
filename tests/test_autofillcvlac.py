"""
Basic tests for autofillcvlac package.
"""

import unittest
from unittest.mock import patch, MagicMock
from autofillcvlac import flatten
from autofillcvlac.core import filter_products_by_year, authenticate_cvlac, fill_scientific_article, filter_missing_journal_articles, extract_scientific_article_data


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
        
        # Test missing fecha_nacimiento when nationality is "Extranjero - otra"
        result = authenticate_cvlac("Extranjero - otra", "John Doe", "12345678", "password123", pais_nacimiento="Estados Unidos")
        self.assertEqual(result["status"], "error")
        self.assertIn("fecha_nacimiento is required", result["message"])
        self.assertFalse(result["session_active"])
        
        # Test missing fecha_nacimiento when nationality is "E" (code for Extranjero - otra)
        result = authenticate_cvlac("E", "John Doe", "12345678", "password123", pais_nacimiento="Estados Unidos")
        self.assertEqual(result["status"], "error")
        self.assertIn("fecha_nacimiento is required", result["message"])
        self.assertFalse(result["session_active"])
        
        # Test missing documento_identificacion for non-Extranjero nationality
        result = authenticate_cvlac("Colombiana", "John Doe", None, "password123")
        self.assertEqual(result["status"], "error")
        self.assertIn("documento_identificacion is required", result["message"])
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
        
        # Test that function signature accepts pais_nacimiento and fecha_nacimiento parameters
        import inspect
        sig = inspect.signature(authenticate_cvlac)
        param_names = list(sig.parameters.keys())
        self.assertIn('pais_nacimiento', param_names)
        self.assertIn('fecha_nacimiento', param_names)
        
        # Test that default values are None
        self.assertEqual(sig.parameters['pais_nacimiento'].default, None)
        self.assertEqual(sig.parameters['fecha_nacimiento'].default, None)
    
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
        
        # Mock select to succeed (simulating successful operation)
        mock_select.return_value = None
        
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
        self.assertEqual(mock_select.call_count, 1)  # One call to select
        
        # Check that select was called with string selectors, not S() objects
        call_args = mock_select.call_args_list[0]
        
        # Should be called with "Nacionalidad" and the nationality value
        self.assertEqual(call_args[0][0], "Nacionalidad")
        self.assertEqual(call_args[0][1], "Colombiana")

    @patch('autofillcvlac.core.start_chrome')
    @patch('autofillcvlac.core.go_to')
    @patch('autofillcvlac.core.select')
    @patch('autofillcvlac.core.write')
    @patch('autofillcvlac.core.click')
    @patch('autofillcvlac.core.S')
    @patch('autofillcvlac.core.TextField')
    @patch('autofillcvlac.core.Button')
    @patch('autofillcvlac.core.wait_until')
    @patch('autofillcvlac.core.Text')
    @patch('autofillcvlac.core.fill_date_of_birth')
    def test_authenticate_cvlac_extranjero_fecha_nacimiento(self, mock_fill_date_of_birth, mock_text, mock_wait_until, mock_button, mock_textfield, mock_S, mock_click, mock_write, mock_select, mock_go_to, mock_start_chrome):
        """Test that fecha_nacimiento field is used for Extranjero - otra nationality."""
        # Configure mocks
        mock_start_chrome.return_value = MagicMock()
        mock_go_to.return_value = None
        mock_write.return_value = None
        mock_click.return_value = None
        mock_S.return_value = MagicMock()
        mock_textfield.return_value = MagicMock()
        mock_button.return_value = MagicMock()
        mock_select.return_value = None
        mock_wait_until.return_value = None
        mock_text.return_value = MagicMock(exists=True)
        mock_fill_date_of_birth.return_value = None
        
        # Call with Extranjero nationality and fecha_nacimiento
        result = authenticate_cvlac(
            nacionalidad='Extranjero - otra', 
            nombres='John Doe', 
            documento_identificacion='dummy',  # Not used for Extranjero but pass something to avoid confusion
            password='****', 
            pais_nacimiento='Estados Unidos',
            fecha_nacimiento='1990-05-15',
            headless=True
        )
        
        # Should succeed with mocked operations
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["session_active"])
        
        # Verify fill_date_of_birth was called with fecha_nacimiento
        mock_fill_date_of_birth.assert_called_once_with('1990-05-15')

    def test_fill_date_of_birth_function(self):
        """Test the fill_date_of_birth function exists and handles basic scenarios."""
        from autofillcvlac.core import fill_date_of_birth
        
        # Test function existence
        self.assertTrue(callable(fill_date_of_birth))
        
        # Test with invalid date format should return error
        result = fill_date_of_birth('invalid-date')
        self.assertIsInstance(result, dict)
        self.assertEqual(result['status'], 'error')
        self.assertFalse(result['session_active'])

    def test_fill_date_of_birth_invalid_date_format(self):
        """Test fill_date_of_birth with invalid date format."""
        from autofillcvlac.core import fill_date_of_birth
        
        # Test with invalid date format
        result = fill_date_of_birth('invalid-date')
        
        # Should return error result
        self.assertIsInstance(result, dict)
        self.assertEqual(result['status'], 'error')
        self.assertIn('Authentication failed', result['message'])
        self.assertFalse(result['session_active'])

    @patch('autofillcvlac.core.start_chrome')
    @patch('autofillcvlac.core.go_to')
    @patch('autofillcvlac.core.select')
    @patch('autofillcvlac.core.write')
    @patch('autofillcvlac.core.click')
    @patch('autofillcvlac.core.S')
    @patch('autofillcvlac.core.TextField')
    @patch('autofillcvlac.core.Button')
    @patch('autofillcvlac.core.Text')
    @patch('time.sleep')
    def test_authenticate_cvlac_login_success_check(self, mock_sleep, mock_text, mock_button, mock_textfield, mock_S, mock_click, mock_write, mock_select, mock_go_to, mock_start_chrome):
        """Test that login success/failure is properly checked after form submission."""
        # Configure mocks for successful case (no error indicators)
        mock_start_chrome.return_value = MagicMock()
        mock_go_to.return_value = None
        mock_write.return_value = None
        mock_click.return_value = None
        mock_S.return_value = MagicMock()
        mock_textfield.return_value = MagicMock()
        mock_button.return_value = MagicMock()
        mock_select.return_value = None
        mock_sleep.return_value = None
        
        # Mock Text.exists() to return False (no error messages found)
        mock_text_instance = MagicMock()
        mock_text_instance.exists.return_value = False
        mock_text.return_value = mock_text_instance
        
        # Mock S().exists() to return False (no error elements found)
        mock_S_instance = MagicMock()
        mock_S_instance.exists.return_value = False
        mock_S.return_value = mock_S_instance
        
        # Call with valid parameters
        result = authenticate_cvlac("Colombiana", "John Doe", "12345678", "password123", headless=True)
        
        # Should succeed when no error indicators are found
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["session_active"])
        self.assertEqual(result["message"], "Authentication successful")
        
        # Verify that sleep was called to wait for page response
        mock_sleep.assert_called_once_with(2)

    @patch('autofillcvlac.core.start_chrome')
    @patch('autofillcvlac.core.go_to')
    @patch('autofillcvlac.core.select')
    @patch('autofillcvlac.core.write')
    @patch('autofillcvlac.core.click')
    @patch('autofillcvlac.core.S')
    @patch('autofillcvlac.core.TextField')
    @patch('autofillcvlac.core.Button')
    @patch('autofillcvlac.core.Text')
    @patch('time.sleep')
    def test_authenticate_cvlac_login_failure_detection(self, mock_sleep, mock_text, mock_button, mock_textfield, mock_S, mock_click, mock_write, mock_select, mock_go_to, mock_start_chrome):
        """Test that login failure is properly detected when error messages are present."""
        # Configure mocks for failure case (error indicators present)
        mock_start_chrome.return_value = MagicMock()
        mock_go_to.return_value = None
        mock_write.return_value = None
        mock_click.return_value = None
        mock_S.return_value = MagicMock()
        mock_textfield.return_value = MagicMock()
        mock_button.return_value = MagicMock()
        mock_select.return_value = None
        mock_sleep.return_value = None
        
        # Mock Text.exists() to return True for error message
        mock_text_instance = MagicMock()
        mock_text_instance.exists.return_value = True
        mock_text.return_value = mock_text_instance
        
        # Call with valid parameters but simulate login failure
        result = authenticate_cvlac("Colombiana", "John Doe", "12345678", "wrong_password", headless=True)
        
        # Should fail when error indicators are found
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["session_active"])
        self.assertIn("Authentication failed: Wrong credentials", result["message"])
        
        # Verify that sleep was called to wait for page response
        mock_sleep.assert_called_once_with(2)

    @patch('autofillcvlac.core.start_chrome')
    @patch('autofillcvlac.core.go_to')
    @patch('autofillcvlac.core.select')
    @patch('autofillcvlac.core.write')
    @patch('autofillcvlac.core.click')
    @patch('autofillcvlac.core.S')
    @patch('autofillcvlac.core.TextField')
    @patch('autofillcvlac.core.Button')
    @patch('autofillcvlac.core.Text')
    @patch('time.sleep')
    def test_authenticate_cvlac_error_element_detection(self, mock_sleep, mock_text, mock_button, mock_textfield, mock_S, mock_click, mock_write, mock_select, mock_go_to, mock_start_chrome):
        """Test that login failure is detected via error CSS elements."""
        # Configure mocks
        mock_start_chrome.return_value = MagicMock()
        mock_go_to.return_value = None
        mock_write.return_value = None
        mock_click.return_value = None
        mock_textfield.return_value = MagicMock()
        mock_button.return_value = MagicMock()
        mock_select.return_value = None
        mock_sleep.return_value = None
        
        # Mock Text.exists() to return False (no text error messages)
        mock_text_instance = MagicMock()
        mock_text_instance.exists.return_value = False
        mock_text.return_value = mock_text_instance
        
        # Mock S().exists() to return True for error element
        mock_S_instance = MagicMock()
        mock_S_instance.exists.return_value = True
        mock_S.return_value = mock_S_instance
        
        # Call with valid parameters but simulate error element present
        result = authenticate_cvlac("Colombiana", "John Doe", "12345678", "wrong_password", headless=True)
        
        # Should fail when error elements are found
        self.assertEqual(result["status"], "error")
        self.assertFalse(result["session_active"])
        self.assertIn("Authentication failed: Wrong credentials detected", result["message"])

    def test_fill_scientific_article_function_exists(self):
        """Test that fill_scientific_article function exists and has correct signature."""
        # Just test that the function exists and can be called
        self.assertTrue(callable(fill_scientific_article))
        # Test with None title to trigger early validation
        result = fill_scientific_article(None)
        self.assertIn("status", result)
        self.assertIn("message", result)
        self.assertIn("session_active", result)

    def test_fill_scientific_article_validation(self):
        """Test input validation for fill_scientific_article function."""
        # Test missing title
        result = fill_scientific_article(None)
        self.assertEqual(result["status"], "error")
        self.assertIn("title is required", result["message"])
        self.assertTrue(result["session_active"])
        
        # Test invalid article type
        result = fill_scientific_article("Test Title", article_type="999")
        self.assertEqual(result["status"], "error")
        self.assertIn("article_type must be one of", result["message"])
        self.assertTrue(result["session_active"])
        
        # Test invalid publication medium
        result = fill_scientific_article("Test Title", publication_medium="X")
        self.assertEqual(result["status"], "error")
        self.assertIn("publication_medium must be one of", result["message"])
        self.assertTrue(result["session_active"])
        
        # Test valid publication mediums
        result = fill_scientific_article("Test Title", publication_medium="Papel")
        # Should not fail on publication_medium validation (will fail later on browser requirement)
        self.assertNotIn("publication_medium must be one of", result.get("message", ""))
        
        result = fill_scientific_article("Test Title", publication_medium="Electrónico")
        # Should not fail on publication_medium validation (will fail later on browser requirement)
        self.assertNotIn("publication_medium must be one of", result.get("message", ""))
        
        # Test invalid month
        result = fill_scientific_article("Test Title", month="InvalidMonth")
        self.assertEqual(result["status"], "error")
        self.assertIn("month must be in Spanish starting with capital letter", result["message"])
        self.assertTrue(result["session_active"])
        
        # Test valid Spanish month
        result = fill_scientific_article("Test Title", month="Enero")
        # Should not fail on month validation (will fail later on browser requirement)
        self.assertNotIn("month must be in Spanish", result.get("message", ""))

    @patch('autofillcvlac.core.get_driver')
    @patch('autofillcvlac.core.wait_until')
    @patch('autofillcvlac.core.Text')
    @patch('autofillcvlac.core.go_to')
    @patch('autofillcvlac.core.click')
    @patch('autofillcvlac.core.write')
    @patch('autofillcvlac.core.select_from_list')
    @patch('autofillcvlac.core.S')
    @patch('time.sleep')
    def test_fill_scientific_article_success(self, mock_sleep, mock_S, mock_select_from_list, mock_write, mock_click, mock_go_to, mock_Text, mock_wait_until, mock_get_driver):
        """Test successful scientific article form filling."""
        # Configure mocks
        mock_go_to.return_value = None
        mock_click.return_value = None
        mock_write.return_value = None
        mock_select_from_list.return_value = None
        mock_S.return_value = MagicMock()
        mock_sleep.return_value = None
        mock_Text.return_value = MagicMock()
        mock_wait_until.return_value = None
        
        # Mock selenium WebDriver elements
        mock_driver = MagicMock()
        mock_element = MagicMock()
        mock_driver.find_element.return_value = mock_element
        mock_driver.find_elements.return_value = [mock_element]
        mock_get_driver.return_value = mock_driver
        
        # Call with valid parameters
        result = fill_scientific_article(
            title="Test Article Title",
            article_type="111",
            initial_page="1",
            final_page="10",
            language="EN",
            year=2023,
            month="Junio",
            volume="10",
            issue="2",
            website_url="https://example.com",
            doi="10.1234/example"
        )
        
        # Should succeed with mocked operations
        self.assertEqual(result["status"], "success")
        self.assertTrue(result["session_active"])
        self.assertIn("Scientific article form filled successfully", result["message"])
        
        # Verify key functions were called
        mock_go_to.assert_called_once_with("https://scienti.minciencias.gov.co/cvlac/EnProdArticulo/create.do")
        self.assertTrue(mock_write.called)
        self.assertTrue(mock_select_from_list.called)
        self.assertTrue(mock_click.called)

    @patch('autofillcvlac.core.get_driver')
    @patch('autofillcvlac.core.wait_until')
    @patch('autofillcvlac.core.Text')
    @patch('autofillcvlac.core.go_to')
    def test_fill_scientific_article_exception_handling(self, mock_go_to, mock_Text, mock_wait_until, mock_get_driver):
        """Test exception handling in fill_scientific_article."""
        # Mock an exception during navigation
        mock_go_to.side_effect = Exception("Navigation failed")
        
        # Configure other mocks to avoid browser requirement errors
        mock_Text.return_value = MagicMock()
        mock_wait_until.return_value = None
        mock_driver = MagicMock()
        mock_get_driver.return_value = mock_driver
        
        result = fill_scientific_article("Test Title")
        
        # Should return error status
        self.assertEqual(result["status"], "error")
        self.assertTrue(result["session_active"])
        self.assertIn("Failed to fill scientific article form", result["message"])

    def test_filter_missing_journal_articles_function_exists(self):
        """Test that filter_missing_journal_articles function exists."""
        self.assertTrue(callable(filter_missing_journal_articles))
    
    def test_filter_missing_journal_articles_basic_filtering(self):
        """Test basic filtering criteria for journal articles missing in CvLAC."""
        products = [
            # Product 1: Valid journal article (should be included)
            {
                "external_ids": [
                    {"provenance": "openalex", "source": "openalex"},
                    {"provenance": "scholar", "source": "scholar"}
                ],
                "types": [
                    {"source": "impactu", "type": "Artículo de revista"},
                    {"source": "openalex", "type": "article"}
                ],
                "year_published": 2023,
                "source": {
                    "external_ids": {"issn": "1234-5678", "openalex": "S123456"}
                }
            },
            # Product 2: Has scienti provenance AND source (should be excluded)
            {
                "external_ids": [
                    {"provenance": "scienti", "source": "scienti"},
                    {"provenance": "openalex", "source": "openalex"}
                ],
                "types": [
                    {"source": "impactu", "type": "Artículo de revista"}
                ],
                "year_published": 2023,
                "source": {
                    "external_ids": {"issn": "1234-5678"}
                }
            },
            # Product 3: Not a journal article (should be excluded)
            {
                "external_ids": [
                    {"provenance": "openalex", "source": "openalex"}
                ],
                "types": [
                    {"source": "impactu", "type": "Libro"}
                ],
                "year_published": 2023,
                "source": {
                    "external_ids": {"issn": "1234-5678"}
                }
            },
            # Product 4: Too old (should be excluded)
            {
                "external_ids": [
                    {"provenance": "openalex", "source": "openalex"}
                ],
                "types": [
                    {"source": "impactu", "type": "Artículo de revista"}
                ],
                "year_published": 2015,
                "source": {
                    "external_ids": {"issn": "1234-5678"}
                }
            },
            # Product 5: No ISSN/EISSN (should be excluded)
            {
                "external_ids": [
                    {"provenance": "openalex", "source": "openalex"}
                ],
                "types": [
                    {"source": "impactu", "type": "Artículo de revista"}
                ],
                "year_published": 2023,
                "source": {
                    "external_ids": {"openalex": "S123456"}
                }
            }
        ]
        
        result = filter_missing_journal_articles(products, current_year=2025)
        
        # Only the first product should pass all criteria
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["year_published"], 2023)
        
    def test_filter_missing_journal_articles_scienti_filtering(self):
        """Test filtering of products with scienti provenance AND source."""
        products = [
            # Should be included: has scienti provenance but different source
            {
                "external_ids": [
                    {"provenance": "scienti", "source": "minciencias"}
                ],
                "types": [{"source": "impactu", "type": "Artículo de revista"}],
                "year_published": 2023,
                "source": {"external_ids": {"issn": "1234-5678"}}
            },
            # Should be included: has scienti source but different provenance
            {
                "external_ids": [
                    {"provenance": "minciencias", "source": "scienti"}
                ],
                "types": [{"source": "impactu", "type": "Artículo de revista"}],
                "year_published": 2023,
                "source": {"external_ids": {"issn": "1234-5678"}}
            },
            # Should be excluded: has both scienti provenance AND source
            {
                "external_ids": [
                    {"provenance": "scienti", "source": "scienti"}
                ],
                "types": [{"source": "impactu", "type": "Artículo de revista"}],
                "year_published": 2023,
                "source": {"external_ids": {"issn": "1234-5678"}}
            }
        ]
        
        result = filter_missing_journal_articles(products, current_year=2025)
        
        # Should include 2 products (first two), exclude the third
        self.assertEqual(len(result), 2)
        
    def test_filter_missing_journal_articles_eissn_support(self):
        """Test that EISSN is treated as equivalent to ISSN."""
        products = [
            # Product with ISSN
            {
                "external_ids": [{"provenance": "openalex", "source": "openalex"}],
                "types": [{"source": "impactu", "type": "Artículo de revista"}],
                "year_published": 2023,
                "source": {"external_ids": {"issn": "1234-5678"}}
            },
            # Product with EISSN
            {
                "external_ids": [{"provenance": "openalex", "source": "openalex"}],
                "types": [{"source": "impactu", "type": "Artículo de revista"}],
                "year_published": 2023,
                "source": {"external_ids": {"eissn": "5678-1234"}}
            },
            # Product with both ISSN and EISSN
            {
                "external_ids": [{"provenance": "openalex", "source": "openalex"}],
                "types": [{"source": "impactu", "type": "Artículo de revista"}],
                "year_published": 2023,
                "source": {"external_ids": {"issn": "1234-5678", "eissn": "5678-1234"}}
            }
        ]
        
        result = filter_missing_journal_articles(products, current_year=2025)
        
        # All three should be included (ISSN and EISSN are equivalent)
        self.assertEqual(len(result), 3)
        
    def test_filter_missing_journal_articles_year_calculation(self):
        """Test year filtering calculation for last 5 years."""
        products = [
            {"external_ids": [{"provenance": "openalex", "source": "openalex"}],
             "types": [{"source": "impactu", "type": "Artículo de revista"}],
             "year_published": 2025, "source": {"external_ids": {"issn": "1234-5678"}}},
            {"external_ids": [{"provenance": "openalex", "source": "openalex"}],
             "types": [{"source": "impactu", "type": "Artículo de revista"}],
             "year_published": 2024, "source": {"external_ids": {"issn": "1234-5678"}}},
            {"external_ids": [{"provenance": "openalex", "source": "openalex"}],
             "types": [{"source": "impactu", "type": "Artículo de revista"}],
             "year_published": 2021, "source": {"external_ids": {"issn": "1234-5678"}}},  # 5th year back
            {"external_ids": [{"provenance": "openalex", "source": "openalex"}],
             "types": [{"source": "impactu", "type": "Artículo de revista"}],
             "year_published": 2020, "source": {"external_ids": {"issn": "1234-5678"}}},  # 6th year back (should be excluded)
        ]
        
        result = filter_missing_journal_articles(products, current_year=2025)
        
        # Should include 2025, 2024, 2021 but not 2020 (2025-4=2021 is the cutoff)
        self.assertEqual(len(result), 3)
        years = [p["year_published"] for p in result]
        self.assertIn(2025, years)
        self.assertIn(2024, years)
        self.assertIn(2021, years)
        self.assertNotIn(2020, years)
        
    def test_filter_missing_journal_articles_missing_fields(self):
        """Test handling of products with missing or empty fields."""
        products = [
            # Missing external_ids - should be INCLUDED (no scienti entries to exclude)
            {
                "types": [{"source": "impactu", "type": "Artículo de revista"}],
                "year_published": 2023,
                "source": {"external_ids": {"issn": "1234-5678"}}
            },
            # Missing types - should be EXCLUDED
            {
                "external_ids": [{"provenance": "openalex", "source": "openalex"}],
                "year_published": 2023,
                "source": {"external_ids": {"issn": "1234-5678"}}
            },
            # Missing year_published - should be EXCLUDED
            {
                "external_ids": [{"provenance": "openalex", "source": "openalex"}],
                "types": [{"source": "impactu", "type": "Artículo de revista"}],
                "source": {"external_ids": {"issn": "1234-5678"}}
            },
            # Missing source - should be EXCLUDED
            {
                "external_ids": [{"provenance": "openalex", "source": "openalex"}],
                "types": [{"source": "impactu", "type": "Artículo de revista"}],
                "year_published": 2023
            },
            # Complete valid product - should be INCLUDED
            {
                "external_ids": [{"provenance": "openalex", "source": "openalex"}],
                "types": [{"source": "impactu", "type": "Artículo de revista"}],
                "year_published": 2023,
                "source": {"external_ids": {"issn": "1234-5678"}}
            }
        ]
        
        result = filter_missing_journal_articles(products, current_year=2025)
        
        # Should include 2 products: the one with missing external_ids and the complete one
        self.assertEqual(len(result), 2)
        
        # Verify the included products have required year and ISSN
        for product in result:
            self.assertEqual(product["year_published"], 2023)
            self.assertIn("issn", product["source"]["external_ids"])
        
    def test_filter_missing_journal_articles_empty_input(self):
        """Test filtering with empty product list."""
        result = filter_missing_journal_articles([], current_year=2025)
        self.assertEqual(result, [])
        
    def test_filter_missing_journal_articles_default_current_year(self):
        """Test that function works with default current year."""
        products = [
            {
                "external_ids": [{"provenance": "openalex", "source": "openalex"}],
                "types": [{"source": "impactu", "type": "Artículo de revista"}],
                "year_published": 2023,
                "source": {"external_ids": {"issn": "1234-5678"}}
            }
        ]
        
        # Should work without specifying current_year
        result = filter_missing_journal_articles(products)
        self.assertIsInstance(result, list)

    def test_extract_scientific_article_data_valid_journal_article(self):
        """Test extraction of data from a valid journal article dictionary."""
        # Sample product dictionary like the one from issue #39
        product = {
            'titles': [
                {'lang': 'en', 'source': 'openalex', 'title': 'Neutrino masses in SU(5)×U(1) F with adjoint flavons'},
                {'lang': 'es', 'source': 'scienti', 'title': 'Masas de neutrinos en SU(5)×U(1) F con flavones adjuntos'}
            ],
            'types': [
                {'provenance': 'openalex', 'source': 'openalex', 'type': 'article'},
                {'provenance': 'minciencias', 'source': 'impactu', 'type': 'Artículo de revista'}
            ],
            'year_published': 2012,
            'date_published': 1330578000,  # March 1, 2012
            'source': {
                'name': 'The European Physical Journal C',
                'external_ids': {
                    'issn': '1434-6044',
                    'eissn': '1434-6052'
                }
            },
            'bibliographic_info': {
                'volume': '72',
                'issue': '3',
                'start_page': '1',
                'end_page': '9'
            },
            'doi': 'https://doi.org/10.1140/epjc/s10052-012-1941-1',
            'external_ids': [
                {'id': 'https://doi.org/10.1140/epjc/s10052-012-1941-1', 'source': 'doi'},
                {'id': 'https://openalex.org/W1571169636', 'source': 'openalex'}
            ],
            'external_urls': [
                {'source': 'open_access', 'url': 'http://arxiv.org/pdf/1108.0722'}
            ]
        }
        
        result = extract_scientific_article_data(product)
        
        # Verify the extraction was successful
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Neutrino masses in SU(5)×U(1) F with adjoint flavons')  # First title
        self.assertEqual(result['language'], 'en')  # Language from first title
        self.assertEqual(result['year'], 2012)
        self.assertEqual(result['month'], 'Marzo')  # March in Spanish
        self.assertEqual(result['journal_name'], 'The European Physical Journal C')
        self.assertEqual(result['journal_issn'], '1434-6044')  # Prefers issn over eissn
        self.assertEqual(result['volume'], '72')
        self.assertEqual(result['issue'], '3')
        self.assertEqual(result['initial_page'], '1')
        self.assertEqual(result['final_page'], '9')
        self.assertEqual(result['doi'], 'https://doi.org/10.1140/epjc/s10052-012-1941-1')  # Full DOI URL
        self.assertEqual(result['website_url'], 'https://doi.org/10.1140/epjc/s10052-012-1941-1')  # Website URL uses DOI when available
        self.assertEqual(result['article_type'], '111')  # Default
        self.assertEqual(result['publication_medium'], 'Electrónico')  # Default

    def test_extract_scientific_article_data_not_journal_article(self):
        """Test that function returns None for non-journal articles."""
        product = {
            'titles': [{'title': 'Some other work'}],
            'types': [
                {'source': 'openalex', 'type': 'article'},
                {'source': 'impactu', 'type': 'Book chapter'}  # Not a journal article
            ]
        }
        
        result = extract_scientific_article_data(product)
        self.assertIsNone(result)

    def test_extract_scientific_article_data_missing_impactu_source(self):
        """Test that function returns None when no impactu source is present."""
        product = {
            'titles': [{'title': 'Some article'}],
            'types': [
                {'source': 'openalex', 'type': 'article'},
                {'source': 'scienti', 'type': 'Artículo de revista'}  # Not impactu source
            ]
        }
        
        result = extract_scientific_article_data(product)
        self.assertIsNone(result)

    def test_extract_scientific_article_data_minimal_fields(self):
        """Test extraction with minimal required fields."""
        product = {
            'titles': [{'title': 'Minimal Article'}],
            'types': [{'source': 'impactu', 'type': 'Artículo de revista'}],
            'year_published': 2023
        }
        
        result = extract_scientific_article_data(product)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['title'], 'Minimal Article')
        self.assertEqual(result['language'], 'ES')  # Falls back to ES when no lang in title
        self.assertEqual(result['year'], 2023)
        self.assertIsNone(result['month'])
        self.assertIsNone(result['journal_name'])
        self.assertIsNone(result['journal_issn'])

    def test_extract_scientific_article_data_eissn_fallback(self):
        """Test that eissn is used when issn is not available."""
        product = {
            'titles': [{'title': 'EISSN Article'}],
            'types': [{'source': 'impactu', 'type': 'Artículo de revista'}],
            'source': {
                'external_ids': {
                    'eissn': '2345-6789'  # Only eissn available
                }
            }
        }
        
        result = extract_scientific_article_data(product)
        
        self.assertIsNotNone(result)
        self.assertEqual(result['journal_issn'], '2345-6789')

    def test_extract_scientific_article_data_function_exists(self):
        """Test that extract_scientific_article_data function exists."""
        self.assertTrue(callable(extract_scientific_article_data))

    def test_extract_scientific_article_data_website_url_fallback(self):
        """Test that website_url falls back to external_urls when DOI is not available."""
        product = {
            'titles': [{'title': 'Article without DOI', 'lang': 'en'}],
            'types': [{'source': 'impactu', 'type': 'Artículo de revista'}],
            'year_published': 2023,
            'external_urls': [
                {'source': 'publisher', 'url': 'https://example.com/article'},
                {'source': 'other', 'url': 'https://other.com/article'}
            ]
            # Note: no 'doi' key
        }
        
        result = extract_scientific_article_data(product)
        
        self.assertIsNotNone(result)
        self.assertIsNone(result['doi'])  # No DOI available
        self.assertEqual(result['website_url'], 'https://example.com/article')  # First external URL


if __name__ == '__main__':
    unittest.main()
