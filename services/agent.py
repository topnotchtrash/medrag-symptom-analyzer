# services/agent.py
from __future__ import annotations
from typing import Dict, Any, List
from core.llm_client import get_llm_client
import json
import re

NO_SYMPTOMS_REPLY = {
    "top_diseases": [],
    "clarifying_question": (
        "I'm here to help with medical symptoms. Could you describe what symptoms you're experiencing?"
    ),
    "reasoning": "No symptoms detected yet",
    "should_continue": True,
}

class DiagnosticAgent:
    def __init__(self):
        self.llm = get_llm_client("groq")

    def process(self, search_results: Dict[str, List[Dict[str, Any]]], session_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Args:
            search_results: {category: [ {name, score, ...}, ... ]}
            session_state:  {symptoms: set/list[str], question_count: int, ...}

        Returns:
            {
              "top_diseases": [ {"disease": str, "confidence": float, "category": str} ],
              "clarifying_question": str,
              "reasoning": str,
              "should_continue": bool
            }
        """
        # --- 1) Early return if we don't have symptoms yet ---
        symptoms = session_state.get("symptoms") or []
        if not symptoms:
            return dict(NO_SYMPTOMS_REPLY)

        # --- 2) Build context for the LLM ---
        context = self._build_context(search_results, session_state)

        prompt = f"""{context}

Provide exactly:
1) Top 3 likely diseases with confidence (0-1). Include a "category" field if known.
2) ONE yes/no clarifying question tailored to narrow the top hypothesis.
3) Brief reasoning (1-2 lines).

IMPORTANT:
- If uncertain, keep confidences conservative (e.g., 0.3–0.6).
- Only return valid JSON. No extra prose.
- Confidence must be a number between 0 and 1.
- If you cannot find 3 diseases, return fewer.

JSON format:
{{
  "top_diseases": [{{"disease": "string", "confidence": 0.xx, "category": "string"}}],
  "clarifying_question": "string",
  "reasoning": "string"
}}

JSON:"""

        # Lower-ish temperature to keep structure stable
        raw = self.llm.chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=400)

        # --- 3) Parse JSON robustly ---
        result = self._safe_parse_json(raw)
        if result is None:
            # Fallback minimal structure if model returns junk
            result = {
                "top_diseases": [],
                "clarifying_question": "Is there a key symptom you’re worried about (e.g., fever, cough, pain)?",
                "reasoning": "Model output could not be parsed as JSON."
            }

        # --- 4) Normalize + clamp result fields ---
        top = self._normalize_top_diseases(result.get("top_diseases", []))
        clar_q = result.get("clarifying_question") or "Is there a key symptom you’re worried about?"
        reasoning = result.get("reasoning") or "Initial differential based on reported symptoms and vector hints."

        # --- 5) Decide whether to stop asking ---
        should_stop = self.check_threshold(top, int(session_state.get("question_count", 0)))
        return {
            "top_diseases": top,
            "clarifying_question": clar_q,
            "reasoning": reasoning,
            "should_continue": not should_stop,
        }

    # ------------------------
    # Helpers
    # ------------------------

    def _build_context(self, search_results: Dict[str, List[Dict[str, Any]]], session_state: Dict[str, Any]) -> str:
        sym_list = list(session_state.get("symptoms", []))
        question_count = int(session_state.get("question_count", 0))

        lines = []
        lines.append(f"Symptoms reported: {', '.join(sym_list) if sym_list else 'none'}")
        lines.append(f"Questions asked so far: {question_count}")
        lines.append("")
        lines.append("Vector search hints (top matches per category):")

        for category, diseases in (search_results or {}).items():
            if not diseases:
                continue
            lines.append(f"- {category}:")
            for d in diseases[:2]:
                name = d.get("name") or d.get("disease") or "Unknown"
                score = d.get("score")
                if isinstance(score, (int, float)):
                    lines.append(f"   • {name} (similarity: {score:.2f})")
                else:
                    lines.append(f"   • {name}")

        return "\n".join(lines)

    def _safe_parse_json(self, raw: str) -> Dict[str, Any] | None:
        """
        Extract the first JSON object from the string and parse it.
        """
        if not isinstance(raw, str) or not raw.strip():
            return None
        # Try direct parse first
        try:
            return json.loads(raw)
        except Exception:
            pass

        # Try to isolate a JSON object with regex
        m = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not m:
            return None
        try:
            return json.loads(m.group(0))
        except Exception:
            return None

    def _normalize_top_diseases(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        - Keep only dict items with `disease` (str) and `confidence` (number).
        - Clamp confidence to [0,1].
        - Ensure category is a string (optional).
        - Sort by confidence desc and truncate to top 3.
        """
        norm: List[Dict[str, Any]] = []
        for it in items or []:
            if not isinstance(it, dict):
                continue
            disease = it.get("disease")
            conf = it.get("confidence")
            if not isinstance(disease, str):
                continue
            if not isinstance(conf, (int, float)):
                continue
            # clamp
            c = float(conf)
            if c < 0.0: c = 0.0
            if c > 1.0: c = 1.0
            cat = it.get("category")
            if cat is not None and not isinstance(cat, str):
                cat = str(cat)
            norm.append({"disease": disease.strip(), "confidence": c, "category": cat or ""})

        norm.sort(key=lambda x: x["confidence"], reverse=True)
        return norm[:3]

    def check_threshold(self, diseases: List[Dict[str, Any]], question_count: int) -> bool:
        """
        Stop asking questions if:
        - Asked 5+ questions already
        - Top disease confidence > 0.80 (very confident)
        - Top disease > 0.70 AND gap to 2nd > 0.20 (clear winner)
        """
        if question_count >= 5:
            return True

        if not diseases:
            return False

        top1_conf = float(diseases[0].get("confidence", 0.0))
        if top1_conf > 0.80:
            return True

        if len(diseases) > 1:
            top2_conf = float(diseases[1].get("confidence", 0.0))
            if top1_conf > 0.70 and (top1_conf - top2_conf) > 0.20:
                return True

        return False
