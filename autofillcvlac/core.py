"""
Core functionality for autofillcvlac package.
"""

import requests
import pandas as pd
from datetime import datetime
from selenium.webdriver.common.by import By
from helium import start_chrome, go_to, write, click, kill_browser, Text, TextField, Button, S, select, wait_until, get_driver


def flatten(xss):
    """
    Flatten a list of lists into a single list.
    
    Args:
        xss: A list of lists
        
    Returns:
        A flattened list containing all elements
    """
    return [x for xs in xss for x in xs]


def get_research_products(cod_rh, max_results=200, page=1):
    """
    Get research products from the Impactu API.
    
    Args:
        cod_rh: The researcher ID
        max_results: Maximum number of results to return (default: 200)
        page: Page number (default: 1)
        
    Returns:
        Response object from the API call
    """
    url = f'https://api.impactu.colav.co/person/{cod_rh}/research/products?max={max_results}&page={page}'
    r = requests.get(url)
    if r.status_code == 200:
        return r.json()['data']
    else:
        return {
                "status": "error", 
                "message": f"Not research products for: {str(cod_rh)}",
                "session_active": False
            }

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


def filter_missing_journal_articles(products, current_year=None):
    """
    Filter journal articles which are missing in CvLAC for an author identificator.
    
    This function filters research products with the following criteria:
    1. No Scienti external IDs: external_ids must not contain entries with 
       both provenance='scienti' and source='scienti'
    2. Journal articles only: types must contain entries with 
       source='impactu' and type='Artículo de revista'
    3. Last five years: year_published must be from the last five years
    4. Must have ISSN/EISSN: source.external_ids must contain either 'issn' or 'eissn'
    
    Args:
        products: List of product dictionaries from get_research_products
        current_year: Current year for calculating last 6 years (default: uses datetime.now().year)
        
    Returns:
        Filtered list of journal article products meeting all criteria
    """
    if current_year is None:
        current_year = datetime.now().year
    
    start_year = current_year - 4  # Last 5 years: current + 4 previous years
    filtered = []
    
    for product in products:
        # Criterion 1: Filter out products with scienti provenance AND source
        external_ids = product.get("external_ids", [])
        has_scienti_both = any(
            ext_id.get('provenance') == 'scienti' and ext_id.get('source') == 'scienti'
            for ext_id in external_ids
        )
        
        if has_scienti_both:
            continue
            
        # Criterion 2: Include only journal articles (impactu source, "Artículo de revista" type)
        types = product.get("types", [])
        is_journal_article = any(
            type_entry.get('source') == 'impactu' and type_entry.get('type') == 'Artículo de revista'
            for type_entry in types
        )
        
        if not is_journal_article:
            continue
            
        # Criterion 3: Include only articles from last 5 years
        year_published = product.get("year_published")
        if not year_published or year_published < start_year:
            continue
            
        # Criterion 4: Include only articles with ISSN or EISSN
        source = product.get("source", {})
        source_external_ids = source.get("external_ids", {})
        has_issn = 'issn' in source_external_ids or 'eissn' in source_external_ids
        
        if not has_issn:
            continue
            
        # If all criteria are met, include the product
        filtered.append(product)
    
    return filtered


def extract_scientific_article_data(product):
    """
    Extract data from a research product dictionary to parameters for fill_scientific_article.
    
    This function extracts relevant fields from a research product dictionary (like the one 
    from issue #39) and maps them to the parameters required by the fill_scientific_article function.
    Only processes dictionaries where types contains an entry with source='impactu' and 
    type='Artículo de revista'.
    
    Args:
        product (dict): Research product dictionary from get_research_products
        
    Returns:
        dict: Dictionary with keys matching fill_scientific_article parameters, or None if 
              the product is not a journal article from impactu source
    """
    # Check if this is a journal article from impactu source
    types = product.get("types", [])
    is_journal_article = any(
        type_entry.get('source') == 'impactu' and type_entry.get('type') == 'Artículo de revista'
        for type_entry in types
    )
    
    if not is_journal_article:
        return None
    
    # Extract title from the first entry in titles list
    titles = product.get("titles", [])
    title = None
    title_language = None
    if titles:
        first_title = titles[0]
        title = first_title.get("title")
        title_language = first_title.get("lang")
    
    # Extract year
    year = product.get("year_published")
    
    # Extract month from date_published if available
    month = None
    date_published = product.get("date_published")
    if date_published:
        # Convert timestamp to month name in Spanish
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(date_published)
            month_names = {
                1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
                5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 
                9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
            }
            month = month_names.get(dt.month)
        except (ValueError, OSError):
            pass
    
    # Extract journal information
    source = product.get("source", {})
    journal_name = source.get("name")
    
    # Extract ISSN (prefer issn over eissn)
    source_external_ids = source.get("external_ids", {})
    journal_issn = source_external_ids.get("issn") or source_external_ids.get("eissn")
    
    # Extract bibliographic information
    bibliographic_info = product.get("bibliographic_info", {})
    volume = bibliographic_info.get("volume")
    issue = bibliographic_info.get("issue")
    initial_page = bibliographic_info.get("start_page")
    final_page = bibliographic_info.get("end_page")
    
    # Extract DOI directly from the doi key
    doi = product.get("doi")
    
    # Extract website URL (prefer DOI, then first available URL from external_urls)
    website_url = None
    if doi:
        website_url = doi
    else:
        external_urls = product.get("external_urls", [])
        if external_urls:
            website_url = external_urls[0].get("url")
    
    return {
        "title": title,
        "article_type": "111",  # Default to "Completo"
        "initial_page": initial_page,
        "final_page": final_page,
        "language": title_language or "ES",  # Use language from title, fallback to Spanish
        "year": year,
        "month": month,
        "journal_name": journal_name,
        "journal_issn": journal_issn,
        "volume": volume,
        "issue": issue,
        "series": None,  # Not available in the dictionary structure
        "publication_medium": "Electrónico",  # Default
        "website_url": website_url,
        "doi": doi
    }


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


def fill_date_of_birth(fecha_nacimiento):
    """
    Fill the 'Fecha de nacimiento' field in the CvLAC form whem 'Nacionalidad' is 'Extranjero - otra' 
    
    Args:
        fecha_nacimiento (str): Date of birth in format YYYY-MM-DD (required when nacionalidad is "Extranjero - otra" or "E")
    """    
    try:
        driver = get_driver()
        click(S(".ui-datepicker-trigger"))
        dt = datetime.strptime(fecha_nacimiento, '%Y-%m-%d').date()
        datepicker = driver.find_element(By.CLASS_NAME,'ui-datepicker-month')
        months = datepicker.find_elements(By.TAG_NAME,'option')
        B = [''] + [m.text for m in months]
        month = [k for k in months  if k.text == B[dt.month]][0]
        month.click()
        datepicker = driver.find_element(By.CLASS_NAME,'ui-datepicker-year')
        year = [k for k in datepicker.find_elements(By.TAG_NAME,'option') if k.text == str(dt.year)][0]
        year.click()
        month_days = driver.find_element(By.ID,'ui-datepicker-div')
        day = [d for d in month_days.find_elements(By.CLASS_NAME,"ui-state-default") 
                  if d.text == str(dt.day)][0]
        day.click()
    
    except Exception as e:
            return {
                "status": "error", 
                "message": f"Authentication failed: {str(e)}",
                "session_active": False
            }


def authenticate_cvlac(nacionalidad, nombres, documento_identificacion, password, pais_nacimiento=None, fecha_nacimiento=None, headless=True):
    """
    Authenticate with the CVLaC (Curriculum Vitae de Latinoamérica y el Caribe) system.
    
    Args:
        nacionalidad (str): The nationality option to select from dropdown
        nombres (str): The user's full name
        documento_identificacion (str): The identification document number (not used when nacionalidad is "Extranjero - otra")
        password (str): The password for CVLaC login
        pais_nacimiento (str, optional): Country of birth (required when nacionalidad is "Extranjero - otra" or "E")
        fecha_nacimiento (str, optional): Date of birth in format YYYY-MM-DD (required when nacionalidad is "Extranjero - otra" or "E")
        headless (bool): Whether to run browser in headless mode (default: True)
        
    Returns:
        dict: Authentication result with status and session information
        
    Raises:
        Exception: If authentication fails or browser operations encounter errors
    """
    # Validate inputs
    if not nacionalidad or not nombres or not password:
        return {
            "status": "error",
            "message": "Required fields (nacionalidad, nombres, password) are missing",
            "session_active": False
        }
    
    # Check if pais_nacimiento and fecha_nacimiento are required for "Extranjero - otra"
    if nacionalidad in ["Extranjero - otra", "E"]:
        if not pais_nacimiento:
            return {
                "status": "error",
                "message": "pais_nacimiento is required when nacionalidad is 'Extranjero - otra'",
                "session_active": False
            }
        if not fecha_nacimiento:
            return {
                "status": "error", 
                "message": "fecha_nacimiento is required when nacionalidad is 'Extranjero - otra'",
                "session_active": False
            }
    else:
        # For non-Extranjero nationalities, documento_identificacion is required
        if not documento_identificacion:
            return {
                "status": "error",
                "message": "documento_identificacion is required for this nationality",
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
        select("Nacionalidad", nacionalidad)
        
        # If "Extranjero - otra" is selected, wait for and fill "País de nacimiento" field
        if nacionalidad in ["Extranjero - otra", "E"]:
            # Wait for the country field to become visible and fill it
            wait_until(Text("País de nacimiento").exists)
            select("País de nacimiento",pais_nacimiento)
        
        # Fill in name using the exact field ID
        write(nombres, into=S("#txt_nmes_rh") or S("[name='txt_nmes_rh']") or TextField("Nombres"))
        
        # Fill identification field based on nationality
        if nacionalidad in ["Extranjero - otra", "E"]:
            # For foreign nationality, fill date of birth instead of document ID
            fill_date_of_birth(fecha_nacimiento)
        else:
            # Fill in identification document using the exact field ID
            write(documento_identificacion, into=S("#nro_documento_ident") or S("[name='nro_documento_ident']") or TextField("Documento de identificación"))
        
        # Fill in password using the exact field ID
        write(password, into=S("#txt_contrasena") or S("[name='txt_contrasena']") or S("[type='password']"))
        
        # Submit form using the exact button ID
        click(S("#botonEnviar") or Button("Ingresar") or Button("Login") or Button("Entrar") or S("input[type='submit']"))
        
        # Wait for page to respond after login attempt
        import time
        time.sleep(2)  # Give the page time to process the login
        
        # Check for successful authentication by looking for error indicators
        try:
            # Common error indicators in CVLaC login page
            error_indicators = [
                "Usuario y/o contraseña incorrectos",
                "Error de autenticación", 
                "Login failed",
                "Invalid credentials",
                "Credenciales incorrectas",
                "Error en el login",
                "Sus datos de identificación son erróneos o usted no se encuentra registrado en el sistema"
            ]
            
            # Check if any error messages are present on the page
            for error_text in error_indicators:
                if Text(error_text).exists():
                    return {
                        "status": "error",
                        "message": f"Authentication failed: Wrong credentials. {error_text}",
                        "session_active": False
                    }
            
            # Check for error elements by common CSS classes/IDs
            error_selectors = [
                ".error",
                ".alert-danger", 
                ".alert-error",
                "#error",
                ".mensaje-error",
                ".login-error"
            ]
            
            for selector in error_selectors:
                if S(selector).exists():
                    try:
                        error_element = S(selector)
                        # Try to get the text content if possible
                        return {
                            "status": "error", 
                            "message": "Authentication failed: Wrong credentials detected",
                            "session_active": False
                        }
                    except:
                        # If we can't read the element, still return error
                        return {
                            "status": "error",
                            "message": "Authentication failed: Login error detected on page", 
                            "session_active": False
                        }
                        
        except Exception:
            # If error checking fails, continue to assume success
            pass
        
        # If no error indicators found, assume successful authentication
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

def get_journal(journal_issn):
    driver = get_driver()
    try:
        click('Buscar')
        write(journal_issn,into='Código ISSN')
        click('Buscar')
        Text('Vincular').exists()
        wait_until(Text('Vincular').exists)
        driver.find_element(By.TAG_NAME, 'a').click()
        popup = driver.find_element(By.ID, 'bodyPrincipal')
        journal = popup.find_element(By.TAG_NAME, 'option')
        journal.click()
        click('Vincular')
    except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to fill scientific article form: {str(e)}",
                "session_active": True
            }

def select_from_list(name, match):
    """
    Select match from the list with name

    Parameters:
       name (str): name tag of the list
       match (str): element of the list
    """
    try:
        driver = get_driver()
        pe = driver.find_element(By.NAME, name)
        peb =pe.find_elements(By.TAG_NAME,'option')
        pm = [p for p in peb if p.text == str(match)][0]
        pm.click()
    except Exception as e:
        return {
                "status": "error",
                "message": f"Failed to fill scientific article form: {str(e)}",
                "session_active": True
        }

def fill_scientific_article(
    title,
    article_type="111",  # Default to "Completo" 
    initial_page=None,
    final_page=None,
    language="ES",  # Default to Spanish
    year=None,
    month=None,  # Default to January
    journal_name=None,
    journal_issn=None,
    volume=None,
    issue=None,
    series=None,
    publication_medium="Electrónico",  # Default to "Electrónico"
    website_url=None,
    doi=None
):
    """
    Fill the scientific article form in CVLaC after successful authentication.
    
    Args:
        title (str): The article title (required)
        article_type (str): Article type - "111" (Completo), "112" (Corto), "113" (Revisión), "114" (Caso Clínico). Default: "111"
        initial_page (str, optional): Initial page number
        final_page (str, optional): Final page number  
        language (str): Language code (default: "ES" for Spanish)
        year (int, optional): Publication year
        month (str): Publication month in Spanish (Enero a Diciembre, default: None)
        journal_name (str, optional): Journal name (note: actual journal selection requires manual search)
        journal_issn (str, optional): Journal issn
        volume (str, optional): Journal volume
        issue (str, optional): Journal issue/fascicle
        series (str, optional): Journal series
        publication_medium (str): Publication medium - "Papel" or "Electrónico". Default: "Electrónico"
        website_url (str, optional): Website URL
        doi (str, optional): DOI (Digital Object Identifier)
        
    Returns:
        dict: Status dictionary with 'status', 'message', and 'session_active' keys
    """
    # Validate required parameters
    if not title:
        return {
            "status": "error",
            "message": "title is required",
            "session_active": True
        }
    
    # Validate article_type
    valid_article_types = ["111", "112", "113", "114"]
    if article_type not in valid_article_types:
        return {
            "status": "error", 
            "message": f"article_type must be one of {valid_article_types}",
            "session_active": True
        }
    
    # Validate publication_medium
    valid_mediums = ["Papel", "Electrónico"]
    if publication_medium not in valid_mediums:
        return {
            "status": "error",
            "message": f"publication_medium must be one of {valid_mediums}",
            "session_active": True
        }
    
    # Validate month
    if month is not None and month not in ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo','Junio',
        'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']:
        return {
            "status": "error",
            "message": "month must be in Spanish starting with capital letter, e.g 'Enero'",
            "session_active": True
        }
    
    try:
        # Navigate to the article creation page
        article_url = "https://scienti.minciencias.gov.co/cvlac/EnProdArticulo/create.do"
        go_to(article_url)
        
        # Wait for page to load
        import time
        time.sleep(2)
        
        # Fill article type (radio button)
        if article_type == "111":
            click(S("#tipoProducto1") or S("input[value='111']"))
        elif article_type == "112":
            click(S("#tipoProducto2") or S("input[value='112']"))
        elif article_type == "113":
            click(S("#tipoProducto3") or S("input[value='113']"))
        elif article_type == "114":
            click(S("#tipoProducto4") or S("input[value='114']"))
        
        # Fill article title
        write(title, into=S("#txt_nme_prod") or S("[name='txt_nme_prod']"))
        
        # Fill page numbers if provided
        if initial_page:
            write(str(initial_page), into=S("[name='txt_pagina_inicial']"))
        
        if final_page:
            write(str(final_page), into=S("[name='txt_pagina_final']"))
        
        # Select language
        select_from_list('sgl_idioma', language)
        
        # Select year if provided
        if year:
            select_from_list('nro_ano_presenta', str(year))
        
        # Select month
        select_from_list('nro_mes_presenta', str(month))
        
        # Fill volume if provided
        if volume:
            write(str(volume), into=S("[name='txt_volumen_revista']"))
        
        # Fill issue/fascicle if provided
        if issue:
            write(str(issue), into=S("#txt_fasciculo_revista") or S("[name='txt_fasciculo_revista']"))
        
        # Fill series if provided
        if series:
            write(str(series), into=S("[name='txt_serie_revista']"))
        
        # Select publication medium
        if publication_medium:
            select_from_list('tpo_medio_divulgacion', publication_medium)
        
        # Fill website URL if provided
        if website_url:
            write(website_url, into=S("#url") or S("[name='txt_web_producto']"))
        
        # Fill DOI if provided
        if doi:
            write(doi, into=S("#doi") or S("[name='txt_doi']"))

        # Fill journal name if provided (note: this is a readonly field that normally requires search)
        # We'll just try to fill it directly, but user may need to use the search functionality
        if journal_name:
            try:
                write(journal_name, into=S("#txt_nme_revista") or S("[name='txt_nme_revista']"))
            except:
                # If readonly field can't be filled, continue (user will need to use search)
                pass
        if journal_issn:
            get_journal(journal_issn)

        wait_until(Text('Buscar').exists)
        
        return {
            "status": "success",
            "message": "Scientific article form filled successfully. Note: Journal selection may require manual search using the 'Buscar' button.",
            "session_active": True
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to fill scientific article form: {str(e)}",
            "session_active": True
        }
