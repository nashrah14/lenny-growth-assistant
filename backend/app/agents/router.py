"""
Deterministic Intent Router
Classifies incoming requests into NORMAL_QA, SHIP30, or ARTIFACT skills.
"""
import re
from enum import Enum
from typing import Optional
from backend.app.core.logging import logger

class IntentType(str, Enum):
    NORMAL_QA = "NORMAL_QA"
    SHIP30 = "SHIP30"
    ARTIFACT = "ARTIFACT"


# Keyword patterns for deterministic routing
SHIP30_PATTERNS = [
    r'\bship\s*30\b',
    r'\bship30\b',
    r'\batomic\s+essay\b',
    r'\bwrite\s+(?:an?\s+)?(?:essay|article|post|newsletter)\b',
    r'\bgenerate\s+(?:an?\s+)?(?:essay|article|post|newsletter)\b',
    r'\b1,?250\s*words?\b',
    r'\bthought\s+leadership\b',
]

ARTIFACT_PATTERNS = [
    r'\b(?:create|build|generate|make)\s+(?:an?\s+)?(?:artifact|calculator|dashboard|tool|component|widget|visualizer|model|table|checklist|template|spreadsheet)\b',
    r'\b(?:html|css|javascript|js|ui\s+component|interactive\s+tool)\b',
    r'\bcac\s+(?:calculator|model)\b',
    r'\bltv\s+(?:calculator|model)\b',
    r'\bpayback\s+calculator\b',
    r'\bretention\s+(?:curve|calculator|visualizer)\b',
    r'\bprioritization\s+(?:matrix|framework|template)\b',
    r'\blaunch\s+checklist\b',
]

class IntentRouter:
    @staticmethod
    def classify(query: str, explicit_intent: Optional[str] = None) -> IntentType:
        """Classify user query into IntentType."""
        if explicit_intent:
            try:
                return IntentType(explicit_intent.upper())
            except ValueError:
                pass

        normalized = query.lower().strip()

        # Check for Ship30 intent
        for pattern in SHIP30_PATTERNS:
            if re.search(pattern, normalized, re.IGNORECASE):
                logger.info(f"Routed query to SHIP30 skill (matched '{pattern}')", extra={"operation": "intent_routed", "intent": "SHIP30"})
                return IntentType.SHIP30

        # Check for Artifact intent
        for pattern in ARTIFACT_PATTERNS:
            if re.search(pattern, normalized, re.IGNORECASE):
                logger.info(f"Routed query to ARTIFACT skill (matched '{pattern}')", extra={"operation": "intent_routed", "intent": "ARTIFACT"})
                return IntentType.ARTIFACT

        # Default to NORMAL_QA
        logger.info("Routed query to NORMAL_QA skill", extra={"operation": "intent_routed", "intent": "NORMAL_QA"})
        return IntentType.NORMAL_QA


# Global intent router singleton
intent_router = IntentRouter()
