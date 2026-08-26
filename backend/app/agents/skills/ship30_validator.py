"""
Ship 30 for 30 Essay Validator
Deterministic, non-LLM structural and word-count validation for generated essays.

Specification:
  Target:       ~1,250 words
  Allowed:      900–1,600 words (±28% / ±350 from target)

  The lower bound (900) permits concise, punchy essays that hit all structural
  requirements without bloat. The upper bound (1,600) prevents runaway verbosity
  that would exceed typical Ship 30 for 30 newsletter constraints.

  These boundaries are wider than a strict ±10% window to account for the
  inherent variability of LLM outputs for a given topic. They are tight enough
  that a clearly non-compliant output (500 words or 3,000 words) will fail.

Structural requirements (deterministic regex detection):
  1. HOOK:      First non-empty paragraph must be <= 3 sentences (punchy opener)
  2. PILLARS:   At least 3 `###` subheadings (the framework breakdown)
  3. TACTICAL:  A section containing action-oriented language
                (keywords: monday morning / action / step / implement / tactical)
  4. TAKEAWAY:  Final paragraph/sentence must exist and contain a closing insight

Why deterministic?
  LLM-based validators can be fooled by the same LLM that produced the content.
  Regex and word-count checks are reproducible, testable, and transparent.
"""
import re
from typing import List, Optional
from pydantic import BaseModel, Field


# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

WORD_COUNT_MIN = 900
WORD_COUNT_MAX = 1600
WORD_COUNT_TARGET = 1250

PILLAR_REGEX = re.compile(r"^###\s+.+", re.MULTILINE)
TACTICAL_KEYWORDS = re.compile(
    r"\b(monday\s+morning|action|step\s+\d|implement|tactical|playbook|next\s+step|how\s+to)\b",
    re.IGNORECASE
)
HOOK_MAX_SENTENCES = 3


# ─────────────────────────────────────────────────────────────────────────────
# Result Models
# ─────────────────────────────────────────────────────────────────────────────

class ValidationIssue(BaseModel):
    code: str = Field(..., description="Machine-readable issue code")
    description: str = Field(..., description="Human-readable description of the issue")


class Ship30ValidationResult(BaseModel):
    """
    Result of deterministic Ship 30 essay validation.

    Fields:
      valid:          True if ALL checks passed
      word_count:     Actual word count of the essay
      issues:         List of validation issues (empty if valid)
      checks:         Dict of individual check results for observability
    """
    valid: bool
    word_count: int
    issues: List[ValidationIssue] = Field(default_factory=list)
    checks: dict = Field(default_factory=dict)


# ─────────────────────────────────────────────────────────────────────────────
# Validator
# ─────────────────────────────────────────────────────────────────────────────

def _count_words(text: str) -> int:
    """Count whitespace-delimited words in text."""
    return len(text.split())


def _extract_first_paragraph(text: str) -> str:
    """Return the first non-empty paragraph (double-newline separated)."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs[0] if paragraphs else ""


def _count_sentences(text: str) -> int:
    """Rough sentence count using terminal punctuation."""
    return len(re.findall(r"[.!?]+", text))


def _get_final_paragraph(text: str) -> str:
    """Return the last non-empty paragraph."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    return paragraphs[-1] if paragraphs else ""


def validate_ship30_essay(content: str) -> Ship30ValidationResult:
    """
    Run all deterministic checks against a Ship 30 essay.

    Checks:
      1. Word count within [WORD_COUNT_MIN, WORD_COUNT_MAX]
      2. Hook: first paragraph is <= HOOK_MAX_SENTENCES sentences
      3. Pillars: at least 3 `###` subheadings
      4. Tactical section: contains action-oriented language
      5. Takeaway: final paragraph exists and has >= 1 sentence

    Returns a Ship30ValidationResult with valid=True only if ALL checks pass.
    """
    issues: List[ValidationIssue] = []
    checks: dict = {}

    # ── Check 1: Word count ────────────────────────────────────────────────
    word_count = _count_words(content)
    wc_ok = WORD_COUNT_MIN <= word_count <= WORD_COUNT_MAX
    checks["word_count"] = {
        "value": word_count,
        "min": WORD_COUNT_MIN,
        "max": WORD_COUNT_MAX,
        "pass": wc_ok
    }
    if not wc_ok:
        if word_count < WORD_COUNT_MIN:
            issues.append(ValidationIssue(
                code="WORD_COUNT_TOO_SHORT",
                description=f"Essay has {word_count} words, minimum is {WORD_COUNT_MIN}."
            ))
        else:
            issues.append(ValidationIssue(
                code="WORD_COUNT_TOO_LONG",
                description=f"Essay has {word_count} words, maximum is {WORD_COUNT_MAX}."
            ))

    # ── Check 2: Hook (punchy opener) ─────────────────────────────────────
    first_para = _extract_first_paragraph(content)
    hook_sentences = _count_sentences(first_para)
    hook_ok = bool(first_para) and hook_sentences <= HOOK_MAX_SENTENCES
    checks["hook"] = {
        "first_paragraph_length_sentences": hook_sentences,
        "max_sentences": HOOK_MAX_SENTENCES,
        "pass": hook_ok
    }
    if not hook_ok:
        if not first_para:
            issues.append(ValidationIssue(
                code="MISSING_HOOK",
                description="Essay has no opening paragraph (hook)."
            ))
        else:
            issues.append(ValidationIssue(
                code="HOOK_TOO_LONG",
                description=(
                    f"Opening hook has {hook_sentences} sentences "
                    f"(max {HOOK_MAX_SENTENCES}). Ship 30 hooks should be punchy — 1–3 sentences."
                )
            ))

    # ── Check 3: Framework pillars (### subheadings) ──────────────────────
    pillar_matches = PILLAR_REGEX.findall(content)
    n_pillars = len(pillar_matches)
    pillars_ok = n_pillars >= 3
    checks["pillars"] = {
        "count": n_pillars,
        "required": 3,
        "pass": pillars_ok
    }
    if not pillars_ok:
        issues.append(ValidationIssue(
            code="INSUFFICIENT_PILLARS",
            description=f"Essay has {n_pillars} `###` subheadings; need at least 3 framework pillars."
        ))

    # ── Check 4: Tactical/actionable section ──────────────────────────────
    tactical_ok = bool(TACTICAL_KEYWORDS.search(content))
    checks["tactical_section"] = {
        "keywords_matched": tactical_ok,
        "pass": tactical_ok
    }
    if not tactical_ok:
        issues.append(ValidationIssue(
            code="MISSING_TACTICAL_SECTION",
            description=(
                "Essay does not contain a tactical/implementation section. "
                "Add action-oriented language (e.g. 'Here's what to do on Monday morning...')."
            )
        ))

    # ── Check 5: Closing takeaway ─────────────────────────────────────────
    final_para = _get_final_paragraph(content)
    takeaway_ok = bool(final_para) and _count_sentences(final_para) >= 1
    checks["takeaway"] = {
        "final_paragraph_present": bool(final_para),
        "pass": takeaway_ok
    }
    if not takeaway_ok:
        issues.append(ValidationIssue(
            code="MISSING_TAKEAWAY",
            description="Essay is missing a closing takeaway paragraph."
        ))

    valid = len(issues) == 0
    return Ship30ValidationResult(
        valid=valid,
        word_count=word_count,
        issues=issues,
        checks=checks
    )
