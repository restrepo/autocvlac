# autofillcvlac

A Python package for processing research data and CVLaC (Curriculum Vitae de Latinoamérica y el Caribe) information.

## Installation

```bash
pip install autofillcvlac
```

## Usage

```python
from autofillcvlac import flatten, authenticate_cvlac
from autofillcvlac.core import get_research_products, filter_products_by_year, create_products_dataframe

# Flatten a list of lists
nested_list = [[1, 2], [3, 4], [5]]
flat_list = flatten(nested_list)
print(flat_list)  # [1, 2, 3, 4, 5]

# Authenticate with CVLaC system
auth_result = authenticate_cvlac('Colombian', 'John Doe', '12345678', 'your_password')
if auth_result['status'] == 'success':
    print("Authentication successful!")
else:
    print(f"Authentication failed: {auth_result['message']}")

# Authenticate with CVLaC system for foreign nationality
auth_result = authenticate_cvlac('Extranjero - otra', 'John Doe', '12345678', 'your_password', 'Estados Unidos')
if auth_result['status'] == 'success':
    print("Authentication successful!")
else:
    print(f"Authentication failed: {auth_result['message']}")

# Get research products from API
response = get_research_products('67dc9885444bab3c3f1a7df2')
if response.status_code == 200:
    products = response.json().get('data', [])
    
    # Filter products by year
    filtered_products = filter_products_by_year(products, 2002)
    
    # Create DataFrame for analysis
    df = create_products_dataframe(filtered_products)
    print(df.head())
```

## Features

- Fetch research products from the Impactu API
- Filter products by publication year and source
- Convert research data to pandas DataFrames for analysis
- Extract citation counts from multiple sources (OpenAlex, Scholar)
- Process author information and external IDs
- Authenticate with CVLaC (Curriculum Vitae de Latinoamérica y el Caribe) system using web automation

## Development

This package is built from research workflows originally developed in Jupyter notebooks for analyzing academic publication data from Latin American and Caribbean researchers.
