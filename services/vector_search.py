# services/vector_search.py

def search_respiratory(query: str, k: int = 3):
    """Mock respiratory search - replace with their real function later"""
    return [
        {
            'disease_id': 'pneumonia',
            'name': 'Pneumonia',
            'score': 0.85,
            'symptoms': ['cough', 'fever', 'chest_pain', 'shortness_of_breath']
        },
        {
            'disease_id': 'bronchitis',
            'name': 'Bronchitis',
            'score': 0.72,
            'symptoms': ['cough', 'fatigue', 'mucus']
        },
        {
            'disease_id': 'covid19',
            'name': 'COVID-19',
            'score': 0.68,
            'symptoms': ['cough', 'fever', 'loss_of_taste', 'fatigue']
        }
    ]

def search_cardiac(query: str, k: int = 3):
    """Mock cardiac search"""
    return [
        {
            'disease_id': 'myocardial_infarction',
            'name': 'Myocardial Infarction',
            'score': 0.45,
            'symptoms': ['chest_pain', 'shortness_of_breath', 'sweating', 'nausea']
        },
        {
            'disease_id': 'angina',
            'name': 'Angina',
            'score': 0.38,
            'symptoms': ['chest_pain', 'pressure']
        }
    ]

def search_gastrointestinal(query: str, k: int = 3):
    """Mock GI search"""
    return [
        {
            'disease_id': 'gastritis',
            'name': 'Gastritis',
            'score': 0.32,
            'symptoms': ['abdominal_pain', 'nausea', 'bloating']
        },
        {
            'disease_id': 'gerd',
            'name': 'GERD',
            'score': 0.28,
            'symptoms': ['heartburn', 'acid_reflux']
        }
    ]

def search_musculoskeletal(query: str, k: int = 3):
    """Mock MSK search"""
    return [
        {
            'disease_id': 'arthritis',
            'name': 'Arthritis',
            'score': 0.28,
            'symptoms': ['joint_pain', 'stiffness', 'swelling']
        }
    ]

def search_dermatological(query: str, k: int = 3):
    """Mock derm search"""
    return [
        {
            'disease_id': 'eczema',
            'name': 'Eczema',
            'score': 0.25,
            'symptoms': ['itching', 'rash', 'dry_skin']
        }
    ]


# Wrapper function to search all categories
def search_all_categories(symptoms: set, k: int = 3):
    """
    Search all 5 category vector DBs
    
    Args:
        symptoms: Set of symptom strings
        k: Number of results per category
    
    Returns:
        dict: {category: [diseases]}
    """
    query = " ".join(symptoms)  # Convert set to query string
    
    return {
        'respiratory': search_respiratory(query, k),
        'cardiac': search_cardiac(query, k),
        'gastrointestinal': search_gastrointestinal(query, k),
        'musculoskeletal': search_musculoskeletal(query, k),
        'dermatological': search_dermatological(query, k)
    }