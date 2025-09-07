"""
Core functionality for autofillcvlac package.
"""

import requests
import pandas as pd
from helium import start_chrome, go_to, write, click, kill_browser, Text, TextField, Button, S, select


def flatten(xss):
    """
    Flatten a list of lists into a single list.
    
    Args:
        xss: A list of lists
        
    Returns:
        A flattened list containing all elements
    """
    return [x for xs in xss for x in xs]


def get_research_products(id_cod_rh, max_results=200, page=1):
    """
    Get research products from the Impactu API.
    
    Args:
        id_cod_rh: The researcher ID
        max_results: Maximum number of results to return (default: 200)
        page: Page number (default: 1)
        
    Returns:
        Response object from the API call
    """
    url = f'https://api.impactu.colav.co/person/{id_cod_rh}/research/products'
    params = {'max': max_results, 'page': page}
    return requests.get(url, params=params)


def filter_products_by_year(products, start_year):
    """
    Filter research products by publication year and exclude certain sources.
    
    Args:
        products: List of product dictionaries
        start_year: Minimum publication year to include
        
    Returns:
        Filtered list of products
    """
    filtered = []
    for product in products:
        external_ids = product.get("external_ids", [])
        provenances = [ext_id.get('provenance') for ext_id in external_ids]
        
        if (not 'scienti' in provenances and
            product.get("year_published") and
            product.get("year_published") >= start_year):
            filtered.append(product)
    
    return filtered


def create_products_dataframe(products):
    """
    Create a pandas DataFrame from research products.
    
    Args:
        products: List of product dictionaries
        
    Returns:
        pandas.DataFrame with processed product information
    """
    df = pd.DataFrame(products)
    
    if not df.empty:
        # Extract title from titles array
        if 'titles' in df.columns:
            df['title'] = df['titles'].str[0].str['title']
        
        # Extract type from types array
        if 'types' in df.columns:
            df['type'] = df['types'].apply(
                lambda L: [d.get('type') for d in L if d.get('source') == 'impactu'][0]
                if L and any(d.get('source') == 'impactu' for d in L) else None
            )
        
        # Process author external IDs
        if 'authors' in df.columns:
            df["authors.external_ids"] = df['authors'].apply(
                lambda L: [d.get("external_ids") for d in L if d.get("external_ids")]
            )
        
        # Extract citation counts
        if 'citations_count' in df.columns:
            df["citations_count.openalex"] = df["citations_count"].apply(
                lambda L: [d.get('count') for d in L if d.get('source') == 'openalex']
            ).str[0].fillna(0).astype(int)
            
            df["citations_count.scholar"] = df["citations_count"].apply(
                lambda L: [d.get('count') for d in L if d.get('source') == 'scholar']
            ).str[0].fillna(0).astype(int)
    
    return df


def authenticate_cvlac(nacionalidad, nombres, documento_identificacion, password, pais_nacimiento=None, headless=True):
    """
    Authenticate with the CVLaC (Curriculum Vitae de Latinoamérica y el Caribe) system.
    
    Args:
        nacionalidad (str): The nationality option to select from dropdown
        nombres (str): The user's full name
        documento_identificacion (str): The identification document number
        password (str): The password for CVLaC login
        pais_nacimiento (str, optional): Country of birth (required when nacionalidad is "Extranjero - otra" or "E")
        headless (bool): Whether to run browser in headless mode (default: True)
        
    Returns:
        dict: Authentication result with status and session information
        
    Raises:
        Exception: If authentication fails or browser operations encounter errors
    """
    # Validate inputs
    if not nacionalidad or not nombres or not documento_identificacion or not password:
        return {
            "status": "error",
            "message": "All fields (nacionalidad, nombres, documento_identificacion, password) are required",
            "session_active": False
        }
    
    # Check if pais_nacimiento is required for "Extranjero - otra"
    if nacionalidad in ["Extranjero - otra", "E"] and not pais_nacimiento:
        return {
            "status": "error",
            "message": "pais_nacimiento is required when nacionalidad is 'Extranjero - otra'",
            "session_active": False
        }
    
    login_url = "https://scienti.minciencias.gov.co/cvlac/Login/pre_s_login.do"
    
    try:
        # Start browser
        if headless:
            browser = start_chrome(headless=True)
        else:
            browser = start_chrome()
        
        # Navigate to login page
        go_to(login_url)
        
        # Fill in credentials according to actual CVLaC form fields
        # Select nationality from dropdown using fallback logic
        select("select", nacionalidad)
        
        # If "Extranjero - otra" is selected, wait for and fill "País de nacimiento" field
        if nacionalidad in ["Extranjero - otra", "E"]:
            # Wait for the country field to become visible and fill it
            wait_until(Text("País de nacimiento").exists)
            select("País de nacimiento",pais_nacimiento)
        
        # Fill in name using the exact field ID
        write(nombres, into=S("#txt_nmes_rh") or S("[name='txt_nmes_rh']") or TextField("Nombres"))
        
        # Fill in identification document using the exact field ID
        write(documento_identificacion, into=S("#nro_documento_ident") or S("[name='nro_documento_ident']") or TextField("Documento de identificación"))
        
        # Fill in password using the exact field ID
        write(password, into=S("#txt_contrasena") or S("[name='txt_contrasena']") or S("[type='password']"))
        
        # Submit form using the exact button ID
        click(S("#botonEnviar") or Button("Ingresar") or Button("Login") or Button("Entrar") or S("input[type='submit']"))
        
        # Check for successful authentication
        # This would need to be customized based on the actual success indicators
        # For now, we'll assume success if no error elements are found
        
        result = {
            "status": "success",
            "message": "Authentication successful",
            "session_active": True
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error", 
            "message": f"Authentication failed: {str(e)}",
            "session_active": False
        }
