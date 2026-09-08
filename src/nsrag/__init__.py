"""NS-RAG: Graph-Grounded Neuro-Symbolic Retrieval-Augmented Generation.

Reference implementation of the experimental pipeline described in the
CIKM 2026 submission "NS-RAG: Graph-Grounded Neuro-Symbolic
Retrieval-Augmented Generation for Verifiable EHR Summarization".

This package is organized to mirror the paper's architecture
(Section 3) and experimental protocol (Section 5):

    data          -> MIMIC-III / i2b2 2010 loaders
    graph         -> GraphSynth (construction), DGsumm (summarization),
                     HERSE (RDF transformation)
    retrieval     -> graph-grounded and textual retrieval
    baselines     -> B1-B7 comparison methods
    generation    -> LLM generation backend (HuggingFace)
    verification  -> three-state symbolic verification + explanation
    metrics       -> all metrics defined in Section 5.8 of the paper
    pipeline      -> end-to-end experiment runners (one per paper table)
    utils         -> results -> LaTeX table generation, timing, I/O
"""

__version__ = "0.1.0"
