"""
validator.py — AI Output Validation Pipeline

Connects:
  - core_mechanism.py   (FactBoundKernel: claim classification)
  - suchalgorythmus.py  (brute_force_find: exhaustive evidence testing)
  - AFRB.py             (optional: strategic classification of validation context)

Pipeline:
  AI text
    → claim extraction
    → FactBoundKernel classification (OBSERVATION / INFERENCE / HYPOTHESIS)
    → exhaustive evidence test per claim (brute_force_find over evidence items)
    → verdict per claim: VERIFIED / CONTRADICTED / UNVERIFIABLE / PARTIAL / SPIN
    → ValidationReport (reliability score + breakdown)

Design principles:
  - Plausibility is not a predicate.
  - Every claim is tested. Nothing is skipped.
  - Evidence predicates are caller-supplied (no semantic magic inside this module).
  - The pipeline is deterministic and auditable at every step.

Usage:
  See __main__ block for a minimal working example.
  For LLM-assisted claim splitting and predicate generation, see the
  `ClaimExtractor.from_llm_output()` classmethod and `EvidenceItem.from_text()`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional, Sequence

# --------------------------------------------------------------------------
# Local imports (assumes same directory as core_mechanism.py, suchalgorythmus.py)
# --------------------------------------------------------------------------
from core_mechanism import FactBoundKernel, StatementType
from suchalgorythmus import brute_force_find


# ==========================================================================
# Verdict
# ==========================================================================

class Verdict(Enum):
    VERIFIED      = auto()   # ≥1 evidence item confirms the claim
    CONTRADICTED  = auto()   # ≥1 evidence item directly negates the claim
    PARTIAL       = auto()   # Some evidence supports, some contradicts
    UNVERIFIABLE  = auto()   # No evidence item addresses the claim at all
    SPIN          = auto()   # Claim is structurally misleading despite partial truth
                             # (e.g. cherry-picked framing, absence-of-evidence reasoning)


VERDICT_LABEL: Dict[Verdict, str] = {
    Verdict.VERIFIED:     "VERIFIED",
    Verdict.CONTRADICTED: "CONTRADICTED",
    Verdict.PARTIAL:      "PARTIAL",
    Verdict.UNVERIFIABLE: "UNVERIFIABLE",
    Verdict.SPIN:         "SPIN",
}


# ==========================================================================
# Evidence Item
# ==========================================================================

@dataclass(frozen=True)
class EvidenceItem:
    """
    A single evidence unit.

    id:           Unique identifier (e.g. "DOC-001", "CHAT-2024-03-01")
    source:       Human-readable origin (filename, URL, document title)
    content:      Raw text or structured summary of the evidence
    confirms:     Callable[str → bool]  — returns True if this item *supports* the claim
    contradicts:  Callable[str → bool]  — returns True if this item *negates* the claim

    Both predicates are caller-supplied; they encode domain knowledge that
    cannot be inferred mechanically. For LLM-assisted predicate generation,
    see EvidenceItem.from_text().
    """
    id: str
    source: str
    content: str
    confirms: Callable[[str], bool]
    contradicts: Callable[[str], bool]

    @staticmethod
    def from_text(
        id: str,
        source: str,
        content: str,
        keywords_confirming: Sequence[str],
        keywords_contradicting: Sequence[str],
    ) -> "EvidenceItem":
        """
        Convenience factory: builds confirm/contradict predicates from keyword lists.
        Suitable for quick prototyping; replace with semantic predicates for production.

        keywords_confirming:    Terms whose presence in the claim suggests confirmation.
        keywords_contradicting: Terms whose presence in the claim suggests contradiction.
        """
        def _confirms(claim: str) -> bool:
            c = claim.lower()
            return any(kw.lower() in c for kw in keywords_confirming)

        def _contradicts(claim: str) -> bool:
            c = claim.lower()
            return any(kw.lower() in c for kw in keywords_contradicting)

        return EvidenceItem(
            id=id,
            source=source,
            content=content,
            confirms=_confirms,
            contradicts=_contradicts,
        )


# ==========================================================================
# Claim
# ==========================================================================

@dataclass
class Claim:
    """
    A single atomic claim extracted from the AI output.

    text:           The claim as extracted.
    stype:          OBSERVATION / INFERENCE / HYPOTHESIS (from FactBoundKernel).
    kernel_errors:  FactBoundKernel violations for this claim (empty = compliant).
    verdict:        Assigned after evidence testing.
    confirmed_by:   Evidence IDs that confirm the claim.
    contradicted_by: Evidence IDs that contradict the claim.
    spin_flag:      Manual or heuristic flag for spin detection.
    notes:          Auditor notes.
    """
    text: str
    stype: Optional[StatementType] = None
    kernel_errors: List[str] = field(default_factory=list)
    verdict: Optional[Verdict] = None
    confirmed_by: List[str] = field(default_factory=list)
    contradicted_by: List[str] = field(default_factory=list)
    spin_flag: bool = False
    notes: str = ""


# ==========================================================================
# Claim Extractor
# ==========================================================================

class ClaimExtractor:
    """
    Splits AI text into atomic claims.

    Default strategy: sentence boundary splitting.
    Override `extract()` for domain-specific splitting (e.g. bullet point lists,
    JSON fields, structured report sections).
    """

    # Sentence boundary pattern (conservative: split on ". ", "! ", "? ")
    _SENT_PATTERN = re.compile(r'(?<=[.!?])\s+')

    def extract(self, text: str) -> List[str]:
        """
        Returns a list of atomic claim strings from the input text.
        Filters empty strings and very short fragments (<= 5 chars).
        """
        raw = self._SENT_PATTERN.split(text.strip())
        return [s.strip() for s in raw if len(s.strip()) > 5]

    @classmethod
    def from_llm_output(cls, bundle: dict) -> List[str]:
        """
        Extracts claims from a FactBoundKernel-structured LLM output bundle:
        {
          "observations": [...],
          "inferences":   [...],
          "hypotheses":   [...]
        }
        Returns all statements as a flat list of (text, implied_stype) tuples.
        Use Validator.run_on_bundle() for direct bundle processing.
        """
        claims: List[str] = []
        for key in ("observations", "inferences", "hypotheses"):
            claims.extend(str(x) for x in bundle.get(key, []))
        return claims


# ==========================================================================
# Validation Report
# ==========================================================================

@dataclass
class ValidationReport:
    """
    Output of a full validation run.

    claims:             All processed claims with verdicts.
    reliability_score:  Fraction of VERIFIED claims over all claims (0.0 – 1.0).
                        Mirrors the case study metric in README.md.
    kernel_compliant:   True if zero FactBoundKernel violations across all claims.
    summary:            Dict[Verdict → count].
    """
    claims: List[Claim]
    reliability_score: float
    kernel_compliant: bool
    summary: Dict[str, int]

    def print_report(self) -> None:
        print("\n" + "=" * 60)
        print("AI OUTPUT VALIDATION REPORT")
        print("=" * 60)
        print(f"Total claims      : {len(self.claims)}")
        print(f"Reliability score : {self.reliability_score:.2f}  (VERIFIED / total)")
        print(f"Kernel compliant  : {self.kernel_compliant}")
        print()
        print("BREAKDOWN:")
        for verdict, count in self.summary.items():
            print(f"  {verdict:<14} : {count}")
        print()
        print("CLAIM DETAIL:")
        for i, claim in enumerate(self.claims, 1):
            stype_label = claim.stype.name if claim.stype else "UNCLASSIFIED"
            verdict_label = claim.verdict.name if claim.verdict else "PENDING"
            print(f"\n  [{i:02d}] {stype_label} | {verdict_label}")
            print(f"       Claim: {claim.text[:100]}{'...' if len(claim.text) > 100 else ''}")
            if claim.confirmed_by:
                print(f"       Confirmed by  : {', '.join(claim.confirmed_by)}")
            if claim.contradicted_by:
                print(f"       Contradicted  : {', '.join(claim.contradicted_by)}")
            if claim.kernel_errors:
                for err in claim.kernel_errors:
                    print(f"       KERNEL ERROR  : {err}")
            if claim.spin_flag:
                print(f"       SPIN FLAG     : {claim.notes or 'marked'}")
        print("\n" + "=" * 60)


# ==========================================================================
# Validator
# ==========================================================================

class Validator:
    """
    Main pipeline class.

    Usage:
        validator = Validator(evidence=my_evidence_list)
        report = validator.run(ai_text)
        report.print_report()

    Or for pre-structured LLM output (FactBoundKernel bundle):
        report = validator.run_on_bundle(bundle)
    """

    def __init__(
        self,
        evidence: Sequence[EvidenceItem],
        extractor: Optional[ClaimExtractor] = None,
    ) -> None:
        self.evidence = list(evidence)
        self.extractor = extractor or ClaimExtractor()
        self._kernel = FactBoundKernel()

    # ------------------------------------------------------------------
    # Core: classify one claim
    # ------------------------------------------------------------------

    def _classify_statement_type(self, text: str) -> StatementType:
        """
        Heuristic classification of a raw claim string into
        OBSERVATION / INFERENCE / HYPOTHESIS.
        For structured bundles use run_on_bundle() which preserves exact types.
        """
        t = text.lower()
        if any(m in t for m in FactBoundKernel.HYPOTHESIS_MARKERS):
            return StatementType.HYPOTHESIS
        if any(m in t for m in FactBoundKernel.INFERENCE_MARKERS):
            return StatementType.INFERENCE
        return StatementType.OBSERVATION

    def _kernel_errors_for(self, claim: Claim) -> List[str]:
        """
        Runs FactBoundKernel validation on a single claim.
        Maps claim type to the appropriate bundle field.
        """
        if claim.stype == StatementType.OBSERVATION:
            bundle = {"observations": [claim.text], "inferences": [], "hypotheses": []}
        elif claim.stype == StatementType.INFERENCE:
            bundle = {"observations": [], "inferences": [claim.text], "hypotheses": []}
        else:
            bundle = {"observations": [], "inferences": [], "hypotheses": [claim.text]}
        result = self._kernel.validate_bundle(bundle)
        return result.errors

    # ------------------------------------------------------------------
    # Core: brute-force evidence test
    # ------------------------------------------------------------------

    def _test_claim(self, claim: Claim) -> None:
        """
        Exhaustively tests claim against all evidence items using brute_force_find.
        Assigns verdict and populates confirmed_by / contradicted_by.
        """
        confirmed_by: List[str] = []
        contradicted_by: List[str] = []

        for ev in self.evidence:
            # brute_force_find over a single-element list:
            # clean separation of concern — the search primitive is reused as specified.
            if brute_force_find([ev], lambda e: e.confirms(claim.text)):
                confirmed_by.append(ev.id)
            if brute_force_find([ev], lambda e: e.contradicts(claim.text)):
                contradicted_by.append(ev.id)

        claim.confirmed_by = confirmed_by
        claim.contradicted_by = contradicted_by

        # Spin heuristic: absence-of-evidence reasoning
        # A claim that is structurally an OBSERVATION but has no evidence at all
        # and contains absence language is flagged as potential SPIN.
        _absence_markers = ["no evidence", "never", "no record", "not documented",
                            "no indication", "no proof", "lacks evidence"]
        is_absence_claim = any(m in claim.text.lower() for m in _absence_markers)

        if claim.spin_flag:
            claim.verdict = Verdict.SPIN
        elif confirmed_by and contradicted_by:
            claim.verdict = Verdict.PARTIAL
        elif confirmed_by:
            claim.verdict = Verdict.VERIFIED
        elif contradicted_by:
            claim.verdict = Verdict.CONTRADICTED
        elif is_absence_claim and claim.stype == StatementType.OBSERVATION:
            claim.verdict = Verdict.SPIN
            claim.notes = "Absence-of-evidence reasoning presented as observation."
        else:
            claim.verdict = Verdict.UNVERIFIABLE

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self, ai_text: str) -> ValidationReport:
        """
        Full pipeline on raw AI text.
        Claims are extracted, classified, kernel-validated, and evidence-tested.
        """
        raw_claims = self.extractor.extract(ai_text)
        claims: List[Claim] = []

        for text in raw_claims:
            claim = Claim(text=text)
            claim.stype = self._classify_statement_type(text)
            claim.kernel_errors = self._kernel_errors_for(claim)
            self._test_claim(claim)
            claims.append(claim)

        return self._build_report(claims)

    def run_on_bundle(self, bundle: dict) -> ValidationReport:
        """
        Pipeline on a FactBoundKernel-structured bundle.
        Preserves exact statement types as declared in the bundle.
        """
        claims: List[Claim] = []

        type_map = {
            "observations": StatementType.OBSERVATION,
            "inferences":   StatementType.INFERENCE,
            "hypotheses":   StatementType.HYPOTHESIS,
        }

        for key, stype in type_map.items():
            for text in bundle.get(key, []):
                claim = Claim(text=str(text), stype=stype)
                claim.kernel_errors = self._kernel_errors_for(claim)
                self._test_claim(claim)
                claims.append(claim)

        # Run kernel on full bundle for cross-field validation
        full_result = self._kernel.validate_bundle(bundle)
        # If full-bundle errors exist beyond per-claim errors, attach to first claim
        if not full_result.ok and claims:
            claims[0].kernel_errors = list(set(claims[0].kernel_errors + full_result.errors))

        return self._build_report(claims)

    @staticmethod
    def _build_report(claims: List[Claim]) -> ValidationReport:
        summary = {v.name: 0 for v in Verdict}
        for claim in claims:
            if claim.verdict:
                summary[claim.verdict.name] += 1

        n = len(claims)
        verified = summary.get(Verdict.VERIFIED.name, 0)
        reliability = verified / n if n > 0 else 0.0

        kernel_compliant = all(len(c.kernel_errors) == 0 for c in claims)

        return ValidationReport(
            claims=claims,
            reliability_score=reliability,
            kernel_compliant=kernel_compliant,
            summary=summary,
        )


# ==========================================================================
# Example Usage
# ==========================================================================

if __name__ == "__main__":

    # --- Evidence: three items with keyword-based predicates ---
    evidence = [
        EvidenceItem.from_text(
            id="DOC-001",
            source="Leibniz-Forschungsstelle Bestätigung 2024",
            content="The quoted passage attributed to Leibniz does not appear in any known work.",
            keywords_confirming=["leibniz", "quote", "falsely attributed"],
            keywords_contradicting=["leibniz quote is authentic", "leibniz did write"],
        ),
        EvidenceItem.from_text(
            id="DOC-002",
            source="Hattie Correspondence 2024",
            content="Prof. Hattie confirmed: explicit instruction outperforms discovery-based methods.",
            keywords_confirming=["hattie", "explicit instruction", "direct teaching"],
            keywords_contradicting=["hattie supports discovery", "hattie disagrees"],
        ),
        EvidenceItem.from_text(
            id="DOC-003",
            source="Klassenumfrage BFIA1 — 11/11 results",
            content="11 of 11 students confirmed the LPI learning material was never introduced.",
            keywords_confirming=["lpi", "learning material", "not introduced", "survey"],
            keywords_contradicting=["lpi was taught", "students knew the material"],
        ),
    ]

    # --- Example 1: raw AI text ---
    ai_text = (
        "The teacher used standard LPI learning material throughout the course. "
        "It is likely that students had prior exposure to the content. "
        "The Leibniz quote used in class is authentic and well-documented. "
        "Hypothesis: the student may have misremembered the curriculum structure. "
        "There is no evidence that explicit instruction was recommended for this context."
    )

    print("=== EXAMPLE 1: Raw AI text ===")
    validator = Validator(evidence=evidence)
    report = validator.run(ai_text)
    report.print_report()

    # --- Example 2: structured bundle ---
    bundle = {
        "observations": [
            "The LPI learning material was not introduced to the class.",
            "11 of 11 students confirmed this in a documented survey.",
        ],
        "inferences": [
            "It is likely that the assessment presupposed knowledge that was never taught.",
            "The evidence suggests the grading standard was misaligned with actual instruction.",
        ],
        "hypotheses": [
            "Hypothesis: the teacher might have assumed prior knowledge from a previous course.",
        ],
    }

    print("\n=== EXAMPLE 2: FactBoundKernel bundle ===")
    report2 = validator.run_on_bundle(bundle)
    report2.print_report()
