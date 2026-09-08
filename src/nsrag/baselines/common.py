"""Common interface implemented by every compared method (B1-B8,
Section 5.4). Having one interface means `pipeline/run_qa.py` and
`pipeline/run_summarization.py` don't need any per-method branching.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

from nsrag.generation.generator import Generator, build_prompt
from nsrag.graph.graphsynth import ClinicalNote, StructuredEvent
from nsrag.schema import GenerationOutput


class Method(ABC):
    """One comparison method from Table 5/6 (B1-B8)."""

    name: str

    def __init__(self, generator: Generator):
        self.generator = generator

    @abstractmethod
    def run(
        self,
        patient_id: str,
        notes: list[ClinicalNote],
        structured_events: list[StructuredEvent],
        question: Optional[str],
        task: str,
    ) -> GenerationOutput:
        """`question` is None for the summarization task (Section 5.12),
        in which case implementations should generate a full patient
        summary instead of answering a specific question."""

    def _generate(self, evidence_text: str, question: Optional[str]) -> tuple:
        prompt = build_prompt(
            evidence=evidence_text,
            question=question or "Summarize this patient's clinical course.",
        )
        result = self.generator.generate(prompt)
        return result, prompt
