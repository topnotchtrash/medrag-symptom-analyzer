# services/specialist.py
import pandas as pd
import os

_specialist_map = None

def lookup_specialist(disease_id: str) -> str:
    """
    Lookup specialist for a given disease
    
    Args:
        disease_id: Disease identifier (e.g., 'pneumonia')
    
    Returns:
        Specialist name (e.g., 'Pulmonologist')
    """
    global _specialist_map
    
    # Fallback hardcoded mapping for testing without CSV
    fallback_map = {
        'pneumonia': 'Pulmonologist',
        'bronchitis': 'Pulmonologist',
        'covid19': 'Infectious Disease Specialist',
        'myocardial_infarction': 'Cardiologist',
        'angina': 'Cardiologist',
        'gastritis': 'Gastroenterologist',
        'gerd': 'Gastroenterologist',
        'arthritis': 'Rheumatologist',
        'eczema': 'Dermatologist'
    }
    
    csv_path = 'data/disease_specialist_mapping.csv'
    
    # Try to load CSV if exists
    if _specialist_map is None and os.path.exists(csv_path):
        try:
            _specialist_map = pd.read_csv(csv_path).set_index('disease_id')
        except Exception as e:
            print(f"Warning: Could not load specialist mapping CSV: {e}")
            return fallback_map.get(disease_id, "General Practitioner")
    
    # If CSV loaded successfully, use it
    if _specialist_map is not None:
        try:
            return str(_specialist_map.loc[disease_id, 'primary_specialist'])
        except KeyError:
            return fallback_map.get(disease_id, "General Practitioner")
    
    # Otherwise use fallback
    return fallback_map.get(disease_id, "General Practitioner")