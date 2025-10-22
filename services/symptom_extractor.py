# services/symptom_extractor.py
from core.llm_client import get_llm_client
import re
import json

class SymptomExtractor:
    def __init__(self):
        self.llm = get_llm_client("groq")

    def extract_symptoms(self, user_input: str) -> dict:
        """
        Extract medical symptoms from user input.

        Args:
            user_input: Natural language text (e.g., "I have a cough and fever")

        Returns:
            {
                'present': set of symptoms user has,
                'absent': set of symptoms user denies
            }
        """
        prompt = f"""Extract medical symptoms from the patient's statement. 

Patient: "{user_input}"

IMPORTANT:
- If NO symptoms are mentioned, return empty lists
- Return ONLY valid JSON, no explanations
- Use simple medical terms

JSON format:
{{
  "present": ["symptom1", "symptom2"],
  "absent": ["symptom3"]
}}

JSON:"""  # ← Added "JSON:" to force format

        # Lower temperature for more consistent JSON structure
        response = self.llm.chat(
            [{"role": "user", "content": prompt}],
            temperature=0.1
        )

        try:
            # Try to isolate JSON even if LLM adds extra text
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                response = json_match.group()

            result = json.loads(response)

            return {
                'present': set(s.lower().strip() for s in result.get('present', [])),
                'absent': set(s.lower().strip() for s in result.get('absent', []))
            }

        except Exception:
            # Fallback for invalid or irrelevant responses
            return {'present': set(), 'absent': set()}

    def extract_symptoms_simple(self, user_input: str) -> set:
        """
        Simpler version that only returns present symptoms.
        """
        result = self.extract_symptoms(user_input)
        return result['present']


# Convenience function for direct use
def extract_symptoms(user_input: str) -> dict:
    """
    Standalone helper function to extract symptoms.

    Returns:
        {'present': set, 'absent': set}
    """
    extractor = SymptomExtractor()
    return extractor.extract_symptoms(user_input)
