# autofillcvlac

A Python package for processing research data and automatically fill the CVLaC (Curriculum Vitae de Latinoamérica y el Caribe) information.

## Installation

```bash
pip install autofillcvlac
```

## Usage

```python
from autofillcvlac import flatten, authenticate_cvlac, fill_scientific_article, extract_scientific_article_data
from autofillcvlac.core import get_research_products, filter_products_by_year, create_products_dataframe, filter_missing_journal_articles

# Flatten a list of lists
nested_list = [[1, 2], [3, 4], [5]]
flat_list = flatten(nested_list)
print(flat_list)  # [1, 2, 3, 4, 5]

# Get research products and extract data for CVLaC forms
response = get_research_products('67dc9885444bab3c3f1a7df2')
if response.status_code == 200:
    products = response.json().get('data', [])
    
    # Filter journal articles missing in CvLAC
    missing_articles = filter_missing_journal_articles(products)
    
    # Extract data for each article to use with fill_scientific_article
    for product in missing_articles:
        extracted_data = extract_scientific_article_data(product)
        if extracted_data:
            print(f"Ready to fill: {extracted_data['title']}")
            # Use extracted data directly with fill_scientific_article
            # result = fill_scientific_article(**extracted_data)

# Authenticate with CVLaC system
auth_result = authenticate_cvlac('Colombian', 'John Doe', '12345678', 'your_password')
if auth_result['status'] == 'success':
    print("Authentication successful!")
    
    # Fill scientific article form
    article_result = fill_scientific_article(
        title="Machine Learning Applications in Healthcare",
        article_type="111",  # Completo
        initial_page="15",
        final_page="28", 
        language="EN",
        year=2023,
        month=6,
        volume="10",
        issue="2",
        publication_medium="H",  # Electrónico
        website_url="https://example-journal.com/article/123",
        doi="10.1234/example.2023.123"
    )
    
    if article_result['status'] == 'success':
        print("Article form filled successfully!")
    else:
        print(f"Error: {article_result['message']}")
else:
    print(f"Authentication failed: {auth_result['message']}")

# Authenticate with CVLaC system for foreign nationality
auth_result = authenticate_cvlac('Extranjero - otra', 'John Doe', 'dummy', 'your_password', 
                                pais_nacimiento='Estados Unidos', fecha_nacimiento='1990-05-15')
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
- **Filter journal articles missing in CvLAC** by criteria (issue #39)
- **Extract scientific article data** from research product dictionaries for CVLaC forms
- Convert research data to pandas DataFrames for analysis
- Extract citation counts from multiple sources (OpenAlex, Scholar)
- Process author information and external IDs
- Authenticate with CVLaC (Curriculum Vitae de Latinoamérica y el Caribe) system using web automation
- **Fill scientific article forms** in CVLaC with metadata including title, type, pages, language, publication details, and DOI

## Development

This package is built from research workflows originally developed in Jupyter notebooks for analyzing academic publication data from Latin American and Caribbean researchers.
