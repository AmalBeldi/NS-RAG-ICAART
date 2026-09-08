# NS-RAG experimental pipeline

Reference implementation of the experimental protocol described in
Section 5 of the CIKM 2026 submission *"NS-RAG: Graph-Grounded
Neuro-Symbolic Retrieval-Augmented Generation for Verifiable EHR
Summarization"*. Running this pipeline against real MIMIC-III / i2b2
2010 data produces the numbers reported in Tables 3, 5, 6, 7, 8, 9 and
Figures 2-6 of the paper.

**This code was written and unit-tested in an environment with no
internet access, no GPU, and no MIMIC-III/i2b2 data.** Every module
that doesn't need those things (graph construction, summarization, RDF
transformation, retrieval scoring, three-state verification, minimal
-explanation extraction, and every metric) is implemented for real and
covered by the test suite in `tests/` (30 tests, all passing). Every
module that *does* need them (the HuggingFace generation backend,
SciSpacy models, GraphRAG/LightRAG, and the actual MIMIC-III/i2b2
readers) is implemented against the real, documented APIs but is
**untested here** -- run `tests/` and the smoke test below on your own
machine before trusting it with a full experimental run.

## 1. Getting the data

Both datasets require credentialed access; nothing is bundled here.

- **MIMIC-III**: complete CITI "Data or Specimens Only Research"
  training, sign the data use agreement, then download from
  <https://physionet.org/content/mimiciii/>. Point `data.mimic_dir` in
  `configs/default.yaml` at the folder containing the raw CSVs
  (`NOTEEVENTS.csv`, `LABEVENTS.csv`, `PRESCRIPTIONS.csv`,
  `DIAGNOSES_ICD.csv`, `D_LABITEMS.csv`, `D_ICD_DIAGNOSES.csv`).
- **i2b2/n2c2 2010**: sign the n2c2 data use agreement at
  <https://n2c2.dbmi.hms.harvard.edu/2010-challenge>. Point
  `data.i2b2_dir` at the extracted folder (one `<id>.txt` /
  `<id>.con` / `<id>.ast` / `<id>.rel` triple per document).

## 2. Installation

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# SciSpacy model (not on PyPI as a normal dependency; separate archive)
pip install https://s3-us-west-2.amazonaws.com/ai2-s2-scispacy/releases/v0.5.4/en_core_sci_lg-0.5.4.tar.gz

# Only if you're running the B4/B5 baselines:
pip install graphrag lightrag-hku
```

Run the test suite (no data/GPU required -- this is the part that's
actually verified in this repository):

```bash
python -m unittest discover -s tests -v
```

## 3. Preparing instances

The paper's protocol (Section 5.2) defines the *tasks* (clinical QA,
clinical summarization) but not a fixed public question set for QA --
so this pipeline takes your prepared instances as a JSONL file rather
than silently generating questions for you (see
`src/nsrag/scripts/common.py` for why). Two example files are provided
in `sample_data/` showing the expected schema:

- `sample_data/qa_instances.jsonl` -- one QA instance per line
- `sample_data/summarization_instances.jsonl` -- one summarization
  instance per line

A typical way to build the real ones: iterate the MIMIC-III test split
from `MimicLoader.make_split()`, pull each patient's notes/events via
`MimicLoader.load_notes` / `load_structured_events`, and attach
whatever question set and independently-constructed reference
assertions your annotation protocol produces (Section 5.7,
"Independent Reference Construction" -- reference assertions must NOT
be derived from NS-RAG's own output).

## 4. Running the experiments

```bash
bash scripts/run_all.sh
```

or run each stage independently:

```bash
python -m nsrag.scripts.run_qa_cli            --instances sample_data/qa_instances.jsonl --out results/table5_qa.json
python -m nsrag.scripts.run_summarization_cli --instances sample_data/summarization_instances.jsonl --out results/table6_summarization.json
python -m nsrag.scripts.run_i2b2_cli          --out results/table7_i2b2.json
python -m nsrag.scripts.run_ablation_cli      --instances sample_data/qa_instances.jsonl --out results/table8_ablation.json
python -m nsrag.scripts.run_robustness_cli    --instances sample_data/qa_instances.jsonl --out results/figure5_robustness.json
python -m nsrag.scripts.run_efficiency_cli    --instances sample_data/qa_instances.jsonl --out results/table9_efficiency.json
```

Add `--mock` to any of these to smoke-test the wiring with
`MockGenerator` instead of a real model -- **this produces
placeholder, non-meaningful text and must never be used to report
numbers.** Without `--mock`, `HFGenerator` loads the model named in
`configs/default.yaml` (`google/flan-t5-large` by default, per
Section 5.6) and needs a GPU for reasonable latency.

Then render every table as LaTeX rows:

```bash
python -m nsrag.scripts.results_to_paper --results-dir results
```

Paste the printed rows directly into the corresponding `tabular` block
in `main.tex`.

## 5. Package layout

```
src/nsrag/
  schema.py              shared dataclasses (Node, Edge, Triple, Assertion, ...)
  graph/
    extraction.py         SciSpacy + rule-based entity/relation extraction
    graphsynth.py          GraphSynth: patient graph construction
    dgsumm.py               DGsumm: task-oriented graph summarization (Table 3)
    rdf_transform.py         HERSE: RDF triple transformation
  retrieval/
    graph_retriever.py     NS-RAG's graph-grounded retrieval
    text_retriever.py       B2 (Textual RAG) TF-IDF retrieval
  generation/
    generator.py            HFGenerator (real) / MockGenerator (testing only)
  verification/
    assertion_extraction.py  splits generated text into atomic assertions
    verifier.py               three-state (SUPPORTED/CONTRADICTED/UNKNOWN) verification
    explain.py                  minimal explanation subgraph + Minimality Ratio
  baselines/                B1-B8 (Section 5.4), one file per method
  metrics/                  every metric in Section 5.8, plus efficiency timing
  data/                     MIMIC-III / i2b2 2010 loaders
  pipeline/                 one end-to-end runner per paper table/figure
  scripts/                  CLI entry points + LaTeX rendering
  utils/
    results_to_latex.py     results -> LaTeX table rows

tests/                     unittest suite (30 tests, dependency-free, all passing)
configs/default.yaml       every hyperparameter referenced in Section 5.6
sample_data/                example JSONL instances + a tiny i2b2 doc, for smoke tests
scripts/run_all.sh          orchestrates all six experiments
```

## 6. Known limitations / where to focus review effort

- **Assertion matching (Fact P/R/F1) and the verifier are
  lexical-overlap baselines**, documented as such in their docstrings.
  They are transparent and fully inspectable, but a paraphrase-heavy
  generation backbone will likely need a stronger matcher (e.g. an NLI
  model) behind the same interface to avoid undercounting correct
  answers phrased differently from the reference. Swap the matcher,
  re-run `tests/`, and note the choice in the paper.
- **B4 (GraphRAG) / B5 (LightRAG)** wrap the official packages rather
  than reimplementing them, and are untested here (no network access
  in the environment this was built in). Smoke-test them on your own
  infrastructure before trusting the numbers.
- **B6 (External KG + LLM)** needs an `ExternalKGClient` implementation
  against whatever biomedical KG you have access to (UMLS/SNOMED-CT
  via a local store, or a public API) -- the interface is defined but
  no client ships here.
- **Question generation for the Clinical QA task** is intentionally
  left to you (see Section 3 above) rather than templated inside this
  pipeline, since the paper doesn't specify one.
