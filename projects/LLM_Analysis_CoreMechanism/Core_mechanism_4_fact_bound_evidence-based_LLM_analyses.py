# fact_bound_kernel.py

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum, auto
from typing import List, Dict, Any


class StatementType(Enum):
    OBSERVATION = auto()
    INFERENCE = auto()   # = evidence-based inference
    HYPOTHESIS = auto()


@dataclass
class Statement:
    text: str
    stype: StatementType


@dataclass
class KernelResult:
    ok: bool
    errors: List[str]


class FactBoundKernel:
    """
    Core mechanism for fact-bound, evidence-based LLM analyses.
    Expects structured LLM output of the form:
    {
      "observations": [ "...", ... ],
      "inferences":   [ "...", ... ],
      "hypotheses":   [ "...", ... ]
    }
    and validates it against formal rules.
    """

    # Rough patterns for inner states / intentions,
    # which are only permitted inside HYPOTHESIS and must be clearly marked there.
    FORBIDDEN_INNER_STATE = [
        "he thinks", "he believes", "he feels", "he wants",
        "he is afraid", "he is ashamed",
        "his psyche", "his personality structure",
        "he is narcissistic", "he is depressive"
    ]

    FORBIDDEN_INTENT = [
        "he wanted to show",
        "he wanted to hurt me",
        "deliberately tried",
        "with the intention",
        "intentionally"
    ]

    # Markers that explicitly identify a statement as a hypothesis
    HYPOTHESIS_MARKERS = [
        "hypothesis", "could be", "possibly", "one possible explanation is",
        "it is conceivable that", "might be"
    ]

    # Markers that frame an inference as probabilistic
    INFERENCE_MARKERS = [
        "likely", "very plausible", "probable",
        "the evidence suggests", "suggests that"
    ]

    def __init__(self) -> None:
        self._forbidden_patterns = [
            *self.FORBIDDEN_INNER_STATE,
            *self.FORBIDDEN_INTENT
        ]

    # -------- Low-Level Pattern Checks -------------------------------------

    @staticmethod
    def _normalize(text: str) -> str:
        return " ".join(text.lower().split())

    def _contains_forbidden(self, text: str) -> bool:
        t = self._normalize(text)
        return any(p in t for p in self._forbidden_patterns)

    def _has_any_marker(self, text: str, markers: List[str]) -> bool:
        t = self._normalize(text)
        return any(m in t for m in markers)

    # -------- Public API ---------------------------------------------------

    def validate_bundle(self, bundle: Dict[str, Any]) -> KernelResult:
        """
        bundle: LLM output
        {
          "observations": [ "...", ... ],
          "inferences":   [ "...", ... ],
          "hypotheses":   [ "...", ... ]
        }
        """

        obs_texts = [str(x) for x in bundle.get("observations", [])]
        inf_texts = [str(x) for x in bundle.get("inferences", [])]
        hyp_texts = [str(x) for x in bundle.get("hypotheses", [])]

        errors: List[str] = []

        # 1) Observations: only directly observable facts, no inner states/intentions
        for txt in obs_texts:
            if self._contains_forbidden(txt):
                errors.append(
                    f"Observation contains inner states/intentions "
                    f"(not permitted as factual): '{txt}'"
                )

        # 2) Inferences: probabilistic language + no direct psychological attribution
        for txt in inf_texts:
            if self._contains_forbidden(txt):
                errors.append(
                    f"Inference contains psychological attribution/intent "
                    f"without hypothesis framing: '{txt}'"
                )
            if not self._has_any_marker(txt, self.INFERENCE_MARKERS):
                errors.append(
                    f"Inference lacks probabilistic markers (e.g. 'likely', "
                    f"'evidence suggests'): '{txt}'"
                )

        # 3) Hypotheses: may include psychology/intent, but must be clearly marked
        for txt in hyp_texts:
            if self._contains_forbidden(txt):
                if not self._has_any_marker(txt, self.HYPOTHESIS_MARKERS):
                    errors.append(
                        f"Hypothesis contains inner states/intent, but lacks "
                        f"explicit hypothesis markers: '{txt}'"
                    )

        return KernelResult(ok=len(errors) == 0, errors=errors)

    # Optional: helper function to *force* an LLM to output in the required structure
    @staticmethod
    def system_prompt_template() -> str:
        """
        Template text that can be given to an LLM as a system/developer prompt
        to enforce the required structure. Can be extended as needed.
        """
        return (
            "You analyze interactions strictly based on facts. "
            "Return your answer *only* as JSON with exactly three fields: "
            "{'observations': [...], 'inferences': [...], 'hypotheses': [...]}.\n"
            "1) 'observations': Only directly observable facts (times, statuses, original text, "
            "countable properties). No thoughts, feelings, intentions.\n"
            "2) 'inferences': Evidence-based conclusions derived solely from the observations. "
            "Use probabilistic wording (e.g. 'likely', 'the evidence suggests'). "
            "No inner states stated as fact.\n"
            "3) 'hypotheses': Speculative explanatory models, clearly marked "
            "(e.g. 'Hypothesis:', 'might be', 'possibly'). "
            "Psychology or intention is allowed here, but only as a hypothesis.\n"
            "All three lists may be empty, but must exist."
        )


# Example integration into an LLM workflow (pseudocode):

if __name__ == "__main__":
    # Assume `llm_output` comes from a model as a Python dict
    example_output = {
        "observations": [
            "He was online for 4 minutes without typing.",
            "The message was opened at 18:03."
        ],
        "inferences": [
            "It is likely that he read the text at least twice, "
            "since the initial reading time was too short for full comprehension."
        ],
        "hypotheses": [
            "Hypothesis: He might have taken a screenshot to analyze the message later in more detail."
        ]
    }

    kernel = FactBoundKernel()
    result = kernel.validate_bundle(example_output)

    if not result.ok:
        for err in result.errors:
            print("KERNEL ERROR:", err)
    else:
        print("Bundle is kernel-compliant.")

